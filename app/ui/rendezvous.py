from datetime import date, datetime
import tkinter as tk
from tkinter import ttk, messagebox

from app.utils.pdf_utils import create_pdf, open_pdf, table_lines
from app.ui.ui_utils import DateTimeEntry, FormTableFrame, ask_delete, clear_entries, selected_id, show_pdf


class RendezVousFrame(FormTableFrame):
    STATUTS = ("Confirme", "Annule", "Termine", "En attente", "En Service")

    def __init__(self, parent, db, refresh_dashboard):
        super().__init__(parent, "Gestion des rendez-vous")
        self.db = db
        self.refresh_dashboard = refresh_dashboard
        self.current_id = None
        self.entries = {}
        self.build_form()
        self.add_search(self.search, self.print_today, "Imprimer RDV du jour")
        self.total_var = tk.StringVar(value="Total: 0.00 MAD")
        ttk.Button(self.right.children["!frame"], text="Ticket RDV", command=self.print_ticket).grid(row=0, column=4, padx=3)
        ttk.Label(self.right.children["!frame"], textvariable=self.total_var, style="Muted.TLabel").grid(row=0, column=5, padx=(16, 0), sticky="w")
        self.add_tree(
            ("id", "client", "service", "employe", "date", "heure", "statut"),
            ("ID", "Client", "Service", "Employe", "Date", "Heure", "Statut"),
            (50, 170, 140, 160, 100, 80, 90),
        )
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.refresh_combos()
        self.load()

    def build_form(self):
        fields = [
            ("client", "Client", ttk.Combobox(self.form, state="readonly", width=26)),
            ("service", "Service", ttk.Combobox(self.form, state="readonly", width=26)),
            ("employe", "Employe", ttk.Combobox(self.form, state="readonly", width=26)),
            ("date_heure", "Date et heure", DateTimeEntry(self.form, include_time=True, width=22)),
            ("statut", "Statut", ttk.Combobox(self.form, values=self.STATUTS, state="readonly", width=26)),
        ]
        for row, (key, label, widget) in enumerate(fields):
            ttk.Label(self.form, text=label).grid(row=row, column=0, sticky="w", pady=4)
            widget.grid(row=row, column=1, sticky="ew", pady=4)
            self.entries[key] = widget
        self.entries["statut"].set("Confirme")
        self.button_row(
            len(fields),
            [
                ("Ajouter", self.add),
                ("Modifier", self.update),
                ("Supprimer", self.delete),
            ],
        )

    def refresh_combos(self):
        clients = self.db.fetchall("SELECT id_client, nom, prenom FROM client ORDER BY nom")
        services = self.db.fetchall("SELECT id_service, nom_service FROM service ORDER BY nom_service")
        current_employee = selected_id(self.entries["employe"].get()) if "employe" in self.entries else None
        employees = self.db.employees_with_availability(only_available=True)
        if current_employee and all(row["id_employe"] != current_employee for row in employees):
            row = self.db.fetchone("SELECT * FROM employe WHERE id_employe=?", (current_employee,))
            if row:
                employees.append(dict(row))
        self.entries["client"]["values"] = [f"{r['id_client']} - {r['nom']} {r['prenom']}" for r in clients]
        self.entries["service"]["values"] = [f"{r['id_service']} - {r['nom_service']}" for r in services]
        self.entries["employe"]["values"] = [f"{r['id_employe']} - {r['nom']} {r['prenom']}" for r in employees]

    def values(self):
        date_heure = self.entries["date_heure"].get().strip()
        try:
            parsed = datetime.strptime(date_heure, "%Y-%m-%d %H:%M")
            date_rdv = parsed.date().isoformat()
            heure_rdv = parsed.strftime("%H:%M")
        except ValueError:
            date_rdv = ""
            heure_rdv = ""
        return {
            "id_client": selected_id(self.entries["client"].get()),
            "id_service": selected_id(self.entries["service"].get()),
            "id_employe": selected_id(self.entries["employe"].get()),
            "date_rdv": date_rdv,
            "heure_rdv": heure_rdv,
            "statut": self.entries["statut"].get().strip(),
        }

    def validate(self, data):
        if not all(data.values()):
            messagebox.showwarning("Validation", "Tous les champs du rendez-vous sont obligatoires.")
            return False
        employee = self.db.fetchone("SELECT disponibilite FROM employe WHERE id_employe=?", (data["id_employe"],))
        runtime = self.db.employee_runtime_status(data["id_employe"], employee["disponibilite"]) if employee else "Available"
        if employee and runtime not in ("Available",) and not self.current_id:
            messagebox.showwarning("Disponibilite", "Cet employe n'est pas disponible actuellement.")
            return False
        conflict = self.db.fetchone(
            """
            SELECT id_rdv FROM rendez_vous
            WHERE id_employe=? AND date_rdv=? AND heure_rdv=? AND id_rdv<>?
            """,
            (data["id_employe"], data["date_rdv"], data["heure_rdv"], self.current_id or 0),
        )
        if conflict:
            messagebox.showwarning("Conflit", "Cet employe a deja un rendez-vous a cette date et heure.")
            return False
        return True

    def status_tag(self, status):
        if status.startswith("Confirm"):
            return "green"
        if status.startswith("Annul") or status.startswith("Termine"):
            return "red"
        if status.startswith("En Service"):
            return "blue"
        return "yellow"

    def status_label(self, status):
        dot = {
            "green": "●",
            "red": "●",
            "blue": "●",
            "yellow": "●",
        }[self.status_tag(status)]
        return f"{dot} {status}"

    def add(self):
        self.refresh_combos()
        data = self.values()
        if not self.validate(data):
            return
        self.db.execute(
            """
            INSERT INTO rendez_vous (id_client, id_service, id_employe, date_rdv, heure_rdv, statut)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (data["id_client"], data["id_service"], data["id_employe"], data["date_rdv"], data["heure_rdv"], data["statut"]),
        )
        self.clear()
        self.load()
        self.refresh_dashboard()

    def update(self):
        if not self.current_id:
            messagebox.showinfo("Selection", "Selectionnez un rendez-vous a modifier.")
            return
        data = self.values()
        if not self.validate(data):
            return
        self.db.execute(
            """
            UPDATE rendez_vous
            SET id_client=?, id_service=?, id_employe=?, date_rdv=?, heure_rdv=?, statut=?
            WHERE id_rdv=?
            """,
            (
                data["id_client"],
                data["id_service"],
                data["id_employe"],
                data["date_rdv"],
                data["heure_rdv"],
                data["statut"],
                self.current_id,
            ),
        )
        self.clear()
        self.load()
        self.refresh_dashboard()

    def delete(self):
        if not self.current_id:
            messagebox.showinfo("Selection", "Selectionnez un rendez-vous a supprimer.")
            return
        if ask_delete():
            self.db.execute("DELETE FROM rendez_vous WHERE id_rdv=?", (self.current_id,))
            self.clear()
            self.load()
            self.refresh_dashboard()

    def clear(self):
        self.current_id = None
        clear_entries(self.entries)
        self.entries["date_heure"].set_now()
        self.entries["statut"].set("Confirme")
        self.refresh_combos()
        self.tree.selection_remove(self.tree.selection())

    def query_rows(self, where="", params=()):
        return self.db.fetchall(
            f"""
            SELECT r.id_rdv, r.id_client, r.id_service, r.id_employe, r.date_rdv, r.heure_rdv, r.statut,
                   c.nom || ' ' || c.prenom AS client,
                   s.nom_service AS service,
                   e.nom || ' ' || e.prenom AS employe
            FROM rendez_vous r
            JOIN client c ON c.id_client = r.id_client
            JOIN service s ON s.id_service = r.id_service
            JOIN employe e ON e.id_employe = r.id_employe
            {where}
            ORDER BY r.date_rdv DESC, r.heure_rdv DESC
            """,
            params,
        )

    def load(self, rows=None):
        self.refresh_combos()
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows = rows if rows is not None else self.query_rows()
        for row in rows:
            tag = self.status_tag(row["statut"])
            self.insert_row((row["id_rdv"], row["client"], row["service"], row["employe"], row["date_rdv"], row["heure_rdv"], self.status_label(row["statut"])), tags=(tag,))

    def select_rdv(self, rdv_id):
        # find the item with matching id in the tree values and select it
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if not values:
                continue
            try:
                if int(values[0]) == int(rdv_id):
                    self.tree.selection_set(item)
                    self.tree.see(item)
                    self.on_select()
                    return
            except Exception:
                continue

    def search(self, show_all=False):
        term = self.search_var.get().strip()
        if show_all or not term:
            self.load()
            return
        like = f"%{term}%"
        rows = self.query_rows("WHERE r.date_rdv LIKE ? OR c.nom LIKE ? OR c.prenom LIKE ?", (like, like, like))
        self.load(rows)

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            self.current_id = None
            self.total_var.set("0.00 MAD")
            return
        rdv_ids = [self.tree.item(item, "values")[0] for item in selected]
        rows = [self.query_rows("WHERE r.id_rdv=?", (rdv_id,))[0] for rdv_id in rdv_ids]
        total = 0.0
        for row in rows:
            price = self.db.fetchone(
                "SELECT s.prix FROM service s JOIN rendez_vous r ON s.id_service = r.id_service WHERE r.id_rdv=?",
                (row["id_rdv"],),
            )
            total += float(price["prix"] if price else 0)
        self.total_var.set(f"Total: {total:.2f} MAD")
        row = rows[0]
        self.current_id = row["id_rdv"]
        self.entries["client"].set(f"{row['id_client']} - {row['client']}")
        self.entries["service"].set(f"{row['id_service']} - {row['service']}")
        self.entries["employe"].set(f"{row['id_employe']} - {row['employe']}")
        self.entries["date_heure"].set(f"{row['date_rdv']} {row['heure_rdv']}")
        self.entries["statut"].set(row["statut"])

    def print_today(self):
        rows = self.query_rows("WHERE r.date_rdv=?", (date.today().isoformat(),))
        data = [(r["id_rdv"], r["client"], r["service"], r["employe"], r["heure_rdv"], r["statut"]) for r in rows]
        path = create_pdf(
            "rendez_vous_du_jour.pdf",
            "Rendez-vous du jour",
            table_lines(("ID", "Client", "Service", "Employe", "Heure", "Statut"), data),
        )
        open_pdf(path)
        show_pdf(path)

    def print_ticket(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection", "Selectionnez un rendez-vous.")
            return
        rdv_ids = [self.tree.item(item, "values")[0] for item in selected]
        rows = [self.query_rows("WHERE r.id_rdv=?", (rdv_id,))[0] for rdv_id in rdv_ids]
        lines = [
            "╔═══════════════════════════════════╗",
            "         GESTION DE SPA",
            "            Ticket RDV",
            "╚═══════════════════════════════════╝",
            "",
        ]
        total = 0.0
        for row in rows:
            price_row = self.db.fetchone(
                "SELECT s.prix FROM service s JOIN rendez_vous r ON s.id_service = r.id_service WHERE r.id_rdv=?",
                (row["id_rdv"],),
            )
            prix = float(price_row["prix"] if price_row else 0)
            total += prix
            lines.extend(
                [
                    f"RDV #{row['id_rdv']}",
                    f"Client : {row['client']}",
                    f"Service : {row['service']}",
                    f"Employe: {row['employe']}",
                    f"Date   : {row['date_rdv']} {row['heure_rdv']}",
                    f"Statut : {row['statut']}",
                    f"Montant: {prix:.2f} MAD",
                    "",
                ]
            )
        lines.append(f"Montant total : {total:.2f} MAD")
        lines.append("Merci de votre visite ! ✨")
        path = create_pdf(f"ticket_rdv_{'_'.join(str(r) for r in rdv_ids)}.pdf", "Ticket rendez-vous", lines)
        open_pdf(path)
        show_pdf(path)
