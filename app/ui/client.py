from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox

from app.utils.pdf_utils import create_pdf, open_pdf, table_lines
from app.ui.ui_utils import DateEntry, FormTableFrame, ask_delete, clear_entries, show_pdf, valid_date, valid_email, valid_phone


class ClientFrame(FormTableFrame):
    def __init__(self, parent, db, refresh_dashboard):
        super().__init__(parent, "Gestion des clients")
        self.db = db
        self.refresh_dashboard = refresh_dashboard
        self.current_id = None
        self.entries = {}
        self.build_form()
        self.add_search(self.search, self.print_clients, "Imprimer la liste")
        self.add_tree(
            ("id", "nom", "prenom", "telephone", "email", "adresse", "date"),
            ("ID", "Nom", "Prenom", "Telephone", "Email", "Adresse", "Date inscription"),
            (50, 110, 110, 110, 170, 180, 110),
        )
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.load()

    def build_form(self):
        labels = [
            ("nom", "Nom"),
            ("prenom", "Prenom"),
            ("telephone", "Telephone *"),
            ("email", "Email"),
            ("adresse", "Adresse"),
            ("date_inscription", "Date inscription"),
        ]
        for row, (key, label) in enumerate(labels):
            ttk.Label(self.form, text=label).grid(row=row, column=0, sticky="w", pady=4)
            if key == "date_inscription":
                entry = DateEntry(self.form)
            else:
                entry = ttk.Entry(self.form, width=28)
                if key == "telephone":
                    vcmd = (self.register(lambda value: value.isdigit() or value == ""), "%P")
                    entry.configure(validate="key", validatecommand=vcmd)
            entry.grid(row=row, column=1, sticky="ew", pady=4)
            self.entries[key] = entry
        self.entries["date_inscription"].insert(0, date.today().isoformat())
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
        if not data["nom"] or not data["prenom"] or not data["telephone"]:
            messagebox.showwarning("Validation", "Nom, prenom et telephone sont obligatoires.")
            return False
        if not valid_phone(data["telephone"], required=True):
            messagebox.showwarning("Validation", "Le telephone doit contenir uniquement des chiffres et au moins 10 numeros.")
            return False
        if not valid_email(data["email"]):
            messagebox.showwarning("Validation", "Email invalide.")
            return False
        if not valid_date(data["date_inscription"], required=True):
            messagebox.showwarning("Validation", "Le format de date doit etre AAAA-MM-JJ.")
            return False
        return True

    def add(self):
        data = self.values()
        if not self.validate(data):
            return
        self.db.execute(
            """
            INSERT INTO client (nom, prenom, telephone, email, adresse, date_inscription)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (data["nom"], data["prenom"], data["telephone"], data["email"], data["adresse"], data["date_inscription"]),
        )
        self.clear()
        self.load()
        self.refresh_dashboard()

    def update(self):
        if not self.current_id:
            messagebox.showinfo("Selection", "Selectionnez un client a modifier.")
            return
        data = self.values()
        if not self.validate(data):
            return
        self.db.execute(
            """
            UPDATE client
            SET nom=?, prenom=?, telephone=?, email=?, adresse=?, date_inscription=?
            WHERE id_client=?
            """,
            (
                data["nom"],
                data["prenom"],
                data["telephone"],
                data["email"],
                data["adresse"],
                data["date_inscription"],
                self.current_id,
            ),
        )
        self.clear()
        self.load()
        self.refresh_dashboard()

    def delete(self):
        if not self.current_id:
            messagebox.showinfo("Selection", "Selectionnez un client a supprimer.")
            return
        if ask_delete():
            self.db.execute("DELETE FROM client WHERE id_client=?", (self.current_id,))
            self.clear()
            self.load()
            self.refresh_dashboard()

    def clear(self):
        self.current_id = None
        clear_entries(self.entries)
        self.entries["date_inscription"].insert(0, date.today().isoformat())
        self.tree.selection_remove(self.tree.selection())

    def load(self, rows=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows = rows if rows is not None else self.db.fetchall("SELECT * FROM client ORDER BY id_client DESC")
        for row in rows:
            self.insert_row(
                (
                    row["id_client"],
                    row["nom"],
                    row["prenom"],
                    row["telephone"],
                    row["email"],
                    row["adresse"],
                    row["date_inscription"],
                )
            )

    def search(self, show_all=False):
        term = self.search_var.get().strip()
        if show_all or not term:
            self.load()
            return
        like = f"%{term}%"
        rows = self.db.fetchall(
            """
            SELECT * FROM client
            WHERE nom LIKE ? OR prenom LIKE ? OR telephone LIKE ?
            ORDER BY id_client DESC
            """,
            (like, like, like),
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

    def print_clients(self):
        rows = self.db.fetchall("SELECT * FROM client ORDER BY nom, prenom")
        data = [
            (r["id_client"], r["nom"], r["prenom"], r["telephone"], r["email"], r["date_inscription"])
            for r in rows
        ]
        path = create_pdf(
            "liste_clients.pdf",
            "Liste des clients",
            table_lines(("ID", "Nom", "Prenom", "Telephone", "Email", "Date"), data),
        )
        open_pdf(path)
        show_pdf(path)
