import tkinter as tk
from tkinter import ttk, messagebox

from app.utils.pdf_utils import create_pdf, open_pdf, table_lines
from app.ui.ui_utils import FormTableFrame, ask_delete, clear_entries, show_pdf


class ServiceFrame(FormTableFrame):
    def __init__(self, parent, db, refresh_dashboard):
        super().__init__(parent, "Catalogue des services")
        self.db = db
        self.refresh_dashboard = refresh_dashboard
        self.current_id = None
        self.entries = {}
        self.build_form()
        self.add_search(self.search, self.print_services, "Imprimer catalogue")
        self.add_tree(
            ("id", "nom", "description", "prix", "duree"),
            ("ID", "Service", "Description", "Prix", "Duree minutes"),
            (50, 140, 260, 80, 110),
        )
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.load()

    def build_form(self):
        labels = [
            ("nom_service", "Nom service"),
            ("description", "Description"),
            ("prix", "Prix"),
            ("duree_minutes", "Duree minutes"),
        ]
        for row, (key, label) in enumerate(labels):
            ttk.Label(self.form, text=label).grid(row=row, column=0, sticky="w", pady=4)
            entry = ttk.Entry(self.form, width=28)
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
        try:
            float(data["prix"])
            int(data["duree_minutes"])
        except ValueError:
            messagebox.showwarning("Validation", "Prix et duree doivent etre numeriques.")
            return False
        if not data["nom_service"]:
            messagebox.showwarning("Validation", "Le nom du service est obligatoire.")
            return False
        return True

    def add(self):
        data = self.values()
        if not self.validate(data):
            return
        self.db.execute(
            "INSERT INTO service (nom_service, description, prix, duree_minutes) VALUES (?, ?, ?, ?)",
            (data["nom_service"], data["description"], float(data["prix"]), int(data["duree_minutes"])),
        )
        self.clear()
        self.load()
        self.refresh_dashboard()

    def update(self):
        if not self.current_id:
            messagebox.showinfo("Selection", "Selectionnez un service a modifier.")
            return
        data = self.values()
        if not self.validate(data):
            return
        self.db.execute(
            "UPDATE service SET nom_service=?, description=?, prix=?, duree_minutes=? WHERE id_service=?",
            (
                data["nom_service"],
                data["description"],
                float(data["prix"]),
                int(data["duree_minutes"]),
                self.current_id,
            ),
        )
        self.clear()
        self.load()
        self.refresh_dashboard()

    def delete(self):
        if not self.current_id:
            messagebox.showinfo("Selection", "Selectionnez un service a supprimer.")
            return
        if ask_delete():
            self.db.execute("DELETE FROM service WHERE id_service=?", (self.current_id,))
            self.clear()
            self.load()
            self.refresh_dashboard()

    def clear(self):
        self.current_id = None
        clear_entries(self.entries)
        self.tree.selection_remove(self.tree.selection())

    def load(self, rows=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows = rows if rows is not None else self.db.fetchall("SELECT * FROM service ORDER BY id_service DESC")
        for row in rows:
            self.insert_row((row["id_service"], row["nom_service"], row["description"], row["prix"], row["duree_minutes"]))

    def search(self, show_all=False):
        term = self.search_var.get().strip()
        if show_all or not term:
            self.load()
            return
        rows = self.db.fetchall(
            "SELECT * FROM service WHERE nom_service LIKE ? OR description LIKE ? ORDER BY id_service DESC",
            (f"%{term}%", f"%{term}%"),
        )
        self.load(rows)

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.current_id = values[0]
        for key, value in zip(self.entries.keys(), values[1:]):
            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, value)

    def print_services(self):
        rows = self.db.fetchall("SELECT * FROM service ORDER BY nom_service")
        data = [(r["id_service"], r["nom_service"], r["prix"], r["duree_minutes"]) for r in rows]
        path = create_pdf(
            "catalogue_services.pdf",
            "Catalogue des services",
            table_lines(("ID", "Service", "Prix", "Duree"), data),
        )
        open_pdf(path)
        show_pdf(path)
