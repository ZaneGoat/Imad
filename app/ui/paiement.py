from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox

from app.utils.pdf_utils import create_pdf, open_pdf
from app.ui.ui_utils import DateEntry, FormTableFrame, ask_delete, clear_entries, create_modern_listbox, selected_id, show_pdf, valid_date


class PaiementFrame(FormTableFrame):
    METHODES = ("Cash", "Carte bancaire", "Mobile payment")

    def __init__(self, parent, db, refresh_dashboard):
        super().__init__(parent, "Gestion des paiements")
        self.db = db
        self.refresh_dashboard = refresh_dashboard
        self.current_id = None
        self.entries = {}
        self.build_form()
        self.add_search(self.search, self.print_receipt, "Imprimer recu")
        self.add_tree(
            ("id", "client", "rdv", "service", "montant", "methode", "date"),
            ("ID", "Client", "RDV", "Service", "Montant", "Methode", "Date paiement"),
            (50, 170, 90, 180, 90, 130, 110),
        )
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.refresh_combos()
        self.load()

    def build_form(self):
        fields = [
            ("client", "Client", ttk.Combobox(self.form, state="readonly", width=26)),
            ("rdv", "Rendez-vous", None),
            ("montant", "Montant", ttk.Entry(self.form, width=28)),
            ("methode", "Methode", ttk.Combobox(self.form, values=self.METHODES, state="readonly", width=26)),
            ("date_paiement", "Date paiement", None),
        ]
        for row, (key, label, widget) in enumerate(fields):
            if key == "rdv":
                label_frame = ttk.Frame(self.form)
                label_frame.grid(row=row, column=0, sticky="nw", pady=4)
                ttk.Label(label_frame, text=label).pack(anchor="w")
                ttk.Label(label_frame, text="Ctrl+clic : multiple", style="Muted.TLabel").pack(anchor="w")
            else:
                ttk.Label(self.form, text=label).grid(row=row, column=0, sticky="w", pady=4)
            if key == "rdv":
                list_frame, widget = create_modern_listbox(self.form, height=6, selectmode="extended")
                list_frame.grid(row=row, column=1, sticky="nsew", pady=4)
            elif key == "date_paiement":
                widget = DateEntry(self.form)
                widget.grid(row=row, column=1, sticky="ew", pady=4)
            else:
                widget.grid(row=row, column=1, sticky="ew", pady=4)
            self.entries[key] = widget
        self.entries["montant"].insert(0, "0.00")
        self.entries["date_paiement"].insert(0, date.today().isoformat())
        self.entries["methode"].set("Cash")
        self.entries["client"].bind("<<ComboboxSelected>>", lambda _e: self.refresh_rdv_for_client())
        self.entries["rdv"].bind("<<ListboxSelect>>", lambda _e: self.fill_amount_from_rdv())
        self.button_row(
            len(fields),
            [
                ("Ajouter", self.add),
                ("Modifier", self.update),
                ("Supprimer", self.delete),
            ],
        )

    def payment_rdv_ids(self, paiement_id):
        rows = self.db.fetchall(
            "SELECT id_rdv FROM paiement_rdv WHERE id_paiement=? ORDER BY id_rdv",
            (paiement_id,),
        )
        if rows:
            return [row["id_rdv"] for row in rows]
        row = self.db.fetchone("SELECT id_rdv FROM paiement WHERE id_paiement=?", (paiement_id,))
        return [row["id_rdv"]] if row else []

    def rdv_is_paid(self, rdv_id, exclude_paiement=None):
        query = "SELECT id_paiement FROM paiement_rdv WHERE id_rdv=?"
        params = [rdv_id]
        if exclude_paiement:
            query += " AND id_paiement<>?"
            params.append(exclude_paiement)
        legacy = self.db.fetchone("SELECT id_paiement FROM paiement WHERE id_rdv=?", (rdv_id,))
        if legacy and (not exclude_paiement or legacy["id_paiement"] != exclude_paiement):
            if not self.db.fetchone(query, tuple(params)):
                return legacy["id_paiement"]
        row = self.db.fetchone(query, tuple(params))
        return row["id_paiement"] if row else None

    def refresh_combos(self):
        clients = self.db.fetchall("SELECT id_client, nom, prenom FROM client ORDER BY nom")
        self.entries["client"]["values"] = [f"{r['id_client']} - {r['nom']} {r['prenom']}" for r in clients]
        self.refresh_rdv_for_client()

    def refresh_rdv_for_client(self):
        client_id = selected_id(self.entries["client"].get())
        exclude = self.current_id
        if client_id:
            rows = self.db.fetchall(
                """
                SELECT r.id_rdv, r.date_rdv, r.heure_rdv, s.nom_service
                FROM rendez_vous r
                JOIN service s ON s.id_service = r.id_service
                WHERE r.id_client=?
                ORDER BY r.date_rdv DESC, r.heure_rdv DESC
                """,
                (client_id,),
            )
        else:
            rows = self.db.fetchall(
                """
                SELECT r.id_rdv, r.date_rdv, r.heure_rdv, s.nom_service
                FROM rendez_vous r
                JOIN service s ON s.id_service = r.id_service
                ORDER BY r.date_rdv DESC, r.heure_rdv DESC
                """
            )
        selected_ids = set(self.payment_rdv_ids(self.current_id)) if self.current_id else set()
        listbox = self.entries["rdv"]
        listbox.delete(0, tk.END)
        for r in rows:
            paid = self.rdv_is_paid(r["id_rdv"], exclude_paiement=exclude)
            if paid and r["id_rdv"] not in selected_ids:
                continue
            listbox.insert(tk.END, f"{r['id_rdv']} - {r['date_rdv']} {r['heure_rdv']} - {r['nom_service']}")
        listbox.selection_clear(0, tk.END)
        if selected_ids:
            for index, value in enumerate(listbox.get(0, tk.END)):
                rdv_id = int(value.split(" - ", 1)[0])
                if rdv_id in selected_ids:
                    listbox.selection_set(index)
        self.fill_amount_from_rdv()

    def selected_rdv_ids(self):
        listbox = self.entries["rdv"]
        return [int(listbox.get(i).split(" - ", 1)[0]) for i in listbox.curselection()]

    def fill_amount_from_rdv(self):
        rdv_ids = self.selected_rdv_ids()
        total = 0.0
        for rdv_id in rdv_ids:
            row = self.db.fetchone(
                """
                SELECT s.prix FROM rendez_vous r
                JOIN service s ON s.id_service = r.id_service
                WHERE r.id_rdv=?
                """,
                (rdv_id,),
            )
            total += float(row["prix"] if row else 0)
        self.entries["montant"].delete(0, tk.END)
        self.entries["montant"].insert(0, f"{total:.2f}")

    def values(self):
        return {
            "id_client": selected_id(self.entries["client"].get()),
            "id_rdv": self.selected_rdv_ids(),
            "montant": self.entries["montant"].get().strip(),
            "methode": self.entries["methode"].get().strip(),
            "date_paiement": self.entries["date_paiement"].get().strip(),
        }

    def validate(self, data):
        if not data["id_client"] or not data["id_rdv"] or not data["methode"] or not data["date_paiement"]:
            messagebox.showwarning("Validation", "Tous les champs sont obligatoires.")
            return False
        if not valid_date(data["date_paiement"], required=True):
            messagebox.showwarning("Validation", "Le format de date doit etre AAAA-MM-JJ.")
            return False
        try:
            if float(data["montant"]) <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Validation", "Le montant doit etre un nombre positif.")
            return False
        return True

    def add(self):
        data = self.values()
        if not self.validate(data):
            return
        skipped = []
        for rdv_id in data["id_rdv"]:
            if self.rdv_is_paid(rdv_id):
                skipped.append(rdv_id)
        payable = [rdv_id for rdv_id in data["id_rdv"] if rdv_id not in skipped]
        if skipped:
            messagebox.showwarning(
                "Doublon",
                f"Les rendez-vous suivants ont deja un paiement et ont ete ignores: {', '.join(str(s) for s in skipped)}",
            )
        if not payable:
            return
        paiement_id = self.db.execute(
            "INSERT INTO paiement (id_client, id_rdv, montant, methode_paiement, date_paiement) VALUES (?, ?, ?, ?, ?)",
            (data["id_client"], payable[0], float(data["montant"]), data["methode"], data["date_paiement"]),
        )
        for rdv_id in payable:
            self.db.execute(
                "INSERT OR IGNORE INTO paiement_rdv (id_paiement, id_rdv) VALUES (?, ?)",
                (paiement_id, rdv_id),
            )
        self.clear()
        self.load()
        self.refresh_dashboard()
        messagebox.showinfo("Paiement", f"Paiement #{paiement_id} enregistre pour {len(payable)} rendez-vous.")

    def update(self):
        if not self.current_id:
            messagebox.showinfo("Selection", "Selectionnez un paiement a modifier.")
            return
        data = self.values()
        if not self.validate(data):
            return
        skipped = []
        for rdv_id in data["id_rdv"]:
            paid = self.rdv_is_paid(rdv_id, exclude_paiement=self.current_id)
            if paid:
                skipped.append(rdv_id)
        payable = [rdv_id for rdv_id in data["id_rdv"] if rdv_id not in skipped]
        if skipped:
            messagebox.showwarning(
                "Doublon",
                f"Les rendez-vous suivants sont deja lies a un autre paiement: {', '.join(str(s) for s in skipped)}",
            )
        if not payable:
            return
        self.db.execute(
            """
            UPDATE paiement
            SET id_client=?, id_rdv=?, montant=?, methode_paiement=?, date_paiement=?
            WHERE id_paiement=?
            """,
            (data["id_client"], payable[0], float(data["montant"]), data["methode"], data["date_paiement"], self.current_id),
        )
        self.db.execute("DELETE FROM paiement_rdv WHERE id_paiement=?", (self.current_id,))
        for rdv_id in payable:
            self.db.execute(
                "INSERT OR IGNORE INTO paiement_rdv (id_paiement, id_rdv) VALUES (?, ?)",
                (self.current_id, rdv_id),
            )
        self.clear()
        self.load()
        self.refresh_dashboard()

    def delete(self):
        if not self.current_id:
            messagebox.showinfo("Selection", "Selectionnez un paiement a supprimer.")
            return
        if ask_delete():
            self.db.execute("DELETE FROM paiement_rdv WHERE id_paiement=?", (self.current_id,))
            self.db.execute("DELETE FROM paiement WHERE id_paiement=?", (self.current_id,))
            self.clear()
            self.load()
            self.refresh_dashboard()

    def clear(self):
        self.current_id = None
        clear_entries(self.entries)
        self.entries["date_paiement"].insert(0, date.today().isoformat())
        self.entries["methode"].set("Cash")
        self.refresh_combos()
        self.entries["rdv"].selection_clear(0, tk.END)
        self.tree.selection_remove(self.tree.selection())

    def query_rows(self, where="", params=()):
        return self.db.fetchall(
            f"""
            SELECT p.id_paiement, p.id_client, p.montant, p.methode_paiement, p.date_paiement,
                   c.nom || ' ' || c.prenom AS client,
                   COALESCE(
                       (SELECT GROUP_CONCAT(pr.id_rdv, ', ')
                        FROM paiement_rdv pr
                        WHERE pr.id_paiement = p.id_paiement),
                       CAST(p.id_rdv AS TEXT)
                   ) AS rdv_display,
                   COALESCE(
                       (SELECT GROUP_CONCAT(s.nom_service, ', ')
                        FROM paiement_rdv pr
                        JOIN rendez_vous r ON r.id_rdv = pr.id_rdv
                        JOIN service s ON s.id_service = r.id_service
                        WHERE pr.id_paiement = p.id_paiement),
                       (SELECT s.nom_service
                        FROM rendez_vous r
                        JOIN service s ON s.id_service = r.id_service
                        WHERE r.id_rdv = p.id_rdv)
                   ) AS service
            FROM paiement p
            JOIN client c ON c.id_client = p.id_client
            {where}
            ORDER BY p.date_paiement DESC, p.id_paiement DESC
            """,
            params,
        )

    def load(self, rows=None):
        self.refresh_combos()
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows = rows if rows is not None else self.query_rows()
        for row in rows:
            self.insert_row(
                (
                    row["id_paiement"],
                    row["client"],
                    row["rdv_display"],
                    row["service"],
                    row["montant"],
                    row["methode_paiement"],
                    row["date_paiement"],
                )
            )

    def search(self, show_all=False):
        term = self.search_var.get().strip()
        if show_all or not term:
            self.load()
            return
        like = f"%{term}%"
        rows = self.query_rows(
            """
            WHERE p.date_paiement LIKE ? OR c.nom LIKE ? OR c.prenom LIKE ?
               OR CAST(p.id_paiement AS TEXT) LIKE ?
               OR EXISTS (
                    SELECT 1 FROM paiement_rdv pr
                    WHERE pr.id_paiement = p.id_paiement AND CAST(pr.id_rdv AS TEXT) LIKE ?
               )
            """,
            (like, like, like, like, like),
        )
        self.load(rows)

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        paiement_id = self.tree.item(selected[0], "values")[0]
        row = self.query_rows("WHERE p.id_paiement=?", (paiement_id,))[0]
        self.current_id = row["id_paiement"]
        self.entries["client"].set(f"{row['id_client']} - {row['client']}")
        self.refresh_rdv_for_client()
        self.entries["methode"].set(row["methode_paiement"])
        self.entries["date_paiement"].delete(0, tk.END)
        self.entries["date_paiement"].insert(0, row["date_paiement"])
        self.entries["montant"].delete(0, tk.END)
        self.entries["montant"].insert(0, f"{float(row['montant']):.2f}")

    def rdv_rows_for_ids(self, rdv_ids):
        rows = []
        for rdv_id in rdv_ids:
            row = self.db.fetchone(
                """
                SELECT r.id_rdv, c.nom || ' ' || c.prenom AS client, s.nom_service AS service,
                       e.nom || ' ' || e.prenom AS employe, r.date_rdv, r.heure_rdv,
                       s.prix AS montant
                FROM rendez_vous r
                JOIN client c ON c.id_client = r.id_client
                JOIN service s ON s.id_service = r.id_service
                JOIN employe e ON e.id_employe = r.id_employe
                WHERE r.id_rdv=?
                """,
                (rdv_id,),
            )
            if row:
                rows.append(row)
        return rows

    def build_receipt_lines(self, paiement_id, date_paiement, methode, rdv_rows, total=None):
        lines = [
            "╔════════════════════════════════════╗",
            "         GESTION DE SPA",
            "          Recu de paiement",
            "╚════════════════════════════════════╝",
            "",
            f"Numero recu       : {paiement_id}",
            f"Date              : {date_paiement}",
            f"Methode paiement  : {methode}",
            "",
            "Rendez-vous inclus :",
            "",
        ]
        amount_total = 0.0
        for row in rdv_rows:
            amount_total += float(row["montant"])
            lines.extend(
                [
                    f"RDV #{row['id_rdv']}",
                    f"Client  : {row['client']}",
                    f"Service : {row['service']}",
                    f"Employe : {row['employe']}",
                    f"Date    : {row['date_rdv']} {row['heure_rdv']}",
                    f"Montant : {row['montant']:.2f} MAD",
                    "",
                ]
            )
        if total is None:
            total = amount_total
        lines.append(f"Total general : {float(total):.2f} MAD")
        lines.append("Merci pour votre confiance !")
        return lines

    def print_receipt(self):
        selected_rdv_ids = self.selected_rdv_ids()
        if selected_rdv_ids and not self.current_id:
            rows = self.rdv_rows_for_ids(selected_rdv_ids)
            total = sum(float(row["montant"]) for row in rows)
            lines = self.build_receipt_lines("BROUILLON", self.entries["date_paiement"].get().strip(), self.entries["methode"].get().strip(), rows, total=total)
            path = create_pdf(f"recu_paiement_{'_'.join(str(r) for r in selected_rdv_ids)}.pdf", "Recu de paiement", lines)
            open_pdf(path)
            show_pdf(path)
            return
        if not self.current_id:
            messagebox.showinfo("Selection", "Selectionnez un paiement ou des rendez-vous pour imprimer le recu.")
            return
        row = self.query_rows("WHERE p.id_paiement=?", (self.current_id,))[0]
        rdv_ids = self.payment_rdv_ids(self.current_id)
        rows = self.rdv_rows_for_ids(rdv_ids)
        lines = self.build_receipt_lines(
            self.current_id,
            row["date_paiement"],
            row["methode_paiement"],
            rows,
            total=row["montant"],
        )
        path = create_pdf(f"recu_paiement_{self.current_id}.pdf", "Recu de paiement", lines)
        open_pdf(path)
        show_pdf(path)
