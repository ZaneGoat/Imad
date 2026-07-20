import tkinter as tk
from tkinter import ttk, messagebox

from app.utils.pdf_utils import create_pdf, open_pdf, table_lines
from app.ui.ui_utils import FormTableFrame, ask_delete, clear_entries, show_pdf, valid_phone


class EmployeFrame(FormTableFrame):
    def __init__(self, parent, db, refresh_dashboard):
        super().__init__(parent, "Gestion des employes")
        self.db = db
        self.refresh_dashboard = refresh_dashboard
        self.current_id = None
        self.available_only = tk.BooleanVar(value=False)
        self.entries = {}
        self.build_form()
        self.add_search(self.search, self.print_employees, "Imprimer la liste")
        ttk.Checkbutton(
            self.right.children["!frame"],
            text="Disponibles seulement",
            variable=self.available_only,
            command=self.load,
        ).grid(row=0, column=4, padx=8)
        self.add_tree(
            ("id", "nom", "prenom", "specialite", "telephone", "salaire", "disponibilite"),
            ("ID", "Nom", "Prenom", "Specialite", "Telephone", "Salaire", "Disponibilité"),
            (50, 110, 110, 150, 120, 90, 150),
        )
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.load()

    def build_form(self):
        labels = [
            ("nom", "Nom"),
            ("prenom", "Prenom"),
            ("specialite", "Specialite"),
            ("telephone", "Telephone"),
            ("salaire", "Salaire"),
            ("disponibilite", "Disponibilite"),
        ]
        for row, (key, label) in enumerate(labels):
            ttk.Label(self.form, text=label).grid(row=row, column=0, sticky="w", pady=4)
            if key == "disponibilite":
                entry = ttk.Combobox(self.form, values=("Available", "Not Available"), state="readonly", width=26)
                entry.set("Available")
            else:
                entry = ttk.Entry(self.form, width=28)
            if key == "telephone":
                vcmd = (self.register(lambda value: value.isdigit() or value == ""), "%P")
                entry.configure(validate="key", validatecommand=vcmd)
            if key == "salaire":
                vcmd = (self.register(lambda value: value == "" or value.isdigit() or (value.count(".") == 1 and value.replace(".", "").isdigit())), "%P")
                entry.configure(validate="key", validatecommand=vcmd)
            entry.grid(row=row, column=1, sticky="ew", pady=4)
            self.entries[key] = entry
        self.button_row(
            len(labels),
            [
                ("Ajouter", self.add),
                ("Modifier", self.update),
                ("Supprimer", self.delete),
            ],
        )

    def values(self):
        return {key: entry.get().strip() for key, entry in self.entries.items()}

    def validate(self, data):
        if not data["nom"] or not data["prenom"]:
            messagebox.showwarning("Validation", "Nom et prenom sont obligatoires.")
            return False
        if not valid_phone(data["telephone"]):
            messagebox.showwarning("Validation", "Le telephone doit contenir uniquement des chiffres et au moins 10 numeros.")
            return False
        try:
            float(data["salaire"] or 0)
        except ValueError:
            messagebox.showwarning("Validation", "Le salaire doit etre numerique.")
            return False
        return True

    def add(self):
        data = self.values()
        if not self.validate(data):
            return
        self.db.execute(
            "INSERT INTO employe (nom, prenom, specialite, telephone, salaire, disponibilite) VALUES (?, ?, ?, ?, ?, ?)",
            (data["nom"], data["prenom"], data["specialite"], data["telephone"], float(data["salaire"] or 0), data["disponibilite"]),
        )
        self.clear()
        self.load()
        self.refresh_dashboard()

    def update(self):
        if not self.current_id:
            messagebox.showinfo("Selection", "Selectionnez un employe a modifier.")
            return
        data = self.values()
        if not self.validate(data):
            return
        self.db.execute(
            "UPDATE employe SET nom=?, prenom=?, specialite=?, telephone=?, salaire=?, disponibilite=? WHERE id_employe=?",
            (
                data["nom"],
                data["prenom"],
                data["specialite"],
                data["telephone"],
                float(data["salaire"] or 0),
                data["disponibilite"],
                self.current_id,
            ),
        )
        self.clear()
        self.load()
        self.refresh_dashboard()

    def delete(self):
        if not self.current_id:
            messagebox.showinfo("Selection", "Selectionnez un employe a supprimer.")
            return
        if ask_delete():
            self.db.execute("DELETE FROM employe WHERE id_employe=?", (self.current_id,))
            self.clear()
            self.load()
            self.refresh_dashboard()

    def clear(self):
        self.current_id = None
        clear_entries(self.entries)
        self.entries["disponibilite"].set("Available")
        self.tree.selection_remove(self.tree.selection())

    def load(self, rows=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows = rows if rows is not None else self.db.employees_with_availability(self.available_only.get())
        for row in rows:
            tag = {
                "Available": "green",
                "En Service": "blue",
                "Not Available": "red",
            }.get(row["status_runtime"], "")
            self.insert_row((row["id_employe"], row["nom"], row["prenom"], row["specialite"], row["telephone"], row["salaire"], row["status_label"]), tags=(tag,))

    def search(self, show_all=False):
        term = self.search_var.get().strip()
        if show_all or not term:
            self.load()
            return
        like = f"%{term}%"
        rows = [
            row for row in self.db.employees_with_availability(self.available_only.get())
            if term.lower() in f"{row['nom']} {row['prenom']} {row['specialite']}".lower()
        ]
        self.load(rows)

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.current_id = values[0]
        row = self.db.fetchone("SELECT * FROM employe WHERE id_employe=?", (self.current_id,))
        for key in self.entries:
            value = row[key]
            if isinstance(self.entries[key], ttk.Combobox):
                self.entries[key].set(value)
            else:
                self.entries[key].delete(0, tk.END)
                self.entries[key].insert(0, value)

    def print_employees(self):
        rows = self.db.fetchall("SELECT * FROM employe ORDER BY nom, prenom")
        data = [(r["id_employe"], r["nom"], r["prenom"], r["specialite"], r["telephone"], r["salaire"], r["disponibilite"]) for r in rows]
        path = create_pdf(
            "liste_employes.pdf",
            "Liste des employes",
            table_lines(("ID", "Nom", "Prenom", "Specialite", "Telephone", "Salaire", "Disponibilite"), data),
        )
        open_pdf(path)
        show_pdf(path)
