from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox

from app.utils.pdf_utils import create_pdf, open_pdf
from app.ui.ui_utils import DateEntry, attach_modern_scrollbar, bind_mousewheel, show_pdf


class ReportsFrame(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=22, style="App.TFrame")
        self.db = db
        self.month_var = tk.StringVar(value=date.today().strftime("%Y-%m"))
        self.day_entry = None
        self.stats_vars = {
            "clients": tk.StringVar(value="0"),
            "revenue": tk.StringVar(value="0"),
            "appointments": tk.StringVar(value="0"),
        }
        root = self.winfo_toplevel()
        self.theme = getattr(root, "theme", "dark")
        self.chart_bg = "#020617" if self.theme == "dark" else "#FFFFFF"
        self.chart_fg = "#E5E7EB" if self.theme == "dark" else "#0F172A"
        self.chart_muted = "#94A3B8" if self.theme == "dark" else "#64748B"
        self.scroll_canvas = tk.Canvas(self, bg=self.chart_bg, highlightthickness=0)
        self.scrollbar = attach_modern_scrollbar(self, self.scroll_canvas)
        self.scroll_canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.content_frame = ttk.Frame(self.scroll_canvas, style="App.TFrame")
        self.content_window = self.scroll_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.content_frame.bind("<Configure>", self._on_content_configure)
        self.scroll_canvas.bind("<Configure>", self._on_canvas_configure)
        bind_mousewheel(self.scroll_canvas, self.scroll_canvas)
        bind_mousewheel(self.content_frame, self.scroll_canvas)
        self.build()
        self.generate()

    def _on_content_configure(self, event):
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.scroll_canvas.itemconfigure(self.content_window, width=event.width)

    def build(self):
        self.content_frame.columnconfigure(0, weight=1)
        ttk.Label(self.content_frame, text="Rapports", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")

        controls = ttk.Frame(self.content_frame, style="Card.TFrame", padding=14)
        controls.grid(row=1, column=0, sticky="ew", pady=16)
        ttk.Label(controls, text="Mois (AAAA-MM)", style="CardLabel.TLabel").pack(side="left")
        ttk.Entry(controls, textvariable=self.month_var, width=12).pack(side="left", padx=8)
        ttk.Button(controls, text="Generer mois", command=self.generate).pack(side="left", padx=4)
        ttk.Button(controls, text="Imprimer mois", command=self.print_report).pack(side="left", padx=4)

        day_controls = ttk.LabelFrame(self.content_frame, text="Rapport journalier", padding=12, style="Panel.TLabelframe")
        day_controls.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        ttk.Label(day_controls, text="Jour").pack(side="left")
        self.day_entry = DateEntry(day_controls)
        self.day_entry.pack(side="left", padx=8)
        ttk.Button(day_controls, text="Generer jour", command=self.generate_day).pack(side="left", padx=4)
        ttk.Button(day_controls, text="Imprimer jour", command=self.print_day_report).pack(side="left", padx=4)

        cards = ttk.Frame(self.content_frame, style="App.TFrame")
        cards.grid(row=3, column=0, sticky="ew")
        for i in range(3):
            cards.columnconfigure(i, weight=1)
        for col, (title, var) in enumerate(
            [("Nouveaux clients", self.stats_vars["clients"]), ("Revenu mensuel", self.stats_vars["revenue"]), ("Rendez-vous", self.stats_vars["appointments"])]
        ):
            card = ttk.Frame(cards, style="Card.TFrame", padding=18)
            card.grid(row=0, column=col, sticky="nsew", padx=6)
            ttk.Label(card, text=title, style="CardLabel.TLabel").pack(anchor="w")
            ttk.Label(card, textvariable=var, style="Metric.TLabel", wraplength=180).pack(anchor="w", pady=(8, 0))

        self.details = tk.Text(
            self.content_frame,
            height=8,
            wrap="word",
            relief="flat",
            bg=self.chart_bg,
            fg=self.chart_fg,
            insertbackground="#38BDF8",
            selectbackground="#2563EB",
            padx=14,
            pady=14,
        )
        self.details.grid(row=4, column=0, sticky="ew", pady=(18, 12))

        charts = ttk.Frame(self.content_frame, style="App.TFrame")
        charts.grid(row=5, column=0, sticky="nsew")
        charts.columnconfigure(0, weight=1)
        charts.columnconfigure(1, weight=1)
        self.content_frame.rowconfigure(5, weight=1)
        self.services_canvas = tk.Canvas(charts, height=230, bg=self.chart_bg, highlightthickness=0)
        self.days_canvas = tk.Canvas(charts, height=230, bg=self.chart_bg, highlightthickness=0)
        self.services_canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.days_canvas.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        payments_frame = ttk.LabelFrame(self.content_frame, text="Paiements", padding=14, style="Panel.TLabelframe")
        payments_frame.grid(row=6, column=0, sticky="nsew")
        self.content_frame.rowconfigure(6, weight=1)
        self.payments_tree = ttk.Treeview(payments_frame, columns=("client", "montant", "services", "date"), show="headings", height=8)
        for col, heading, width in (("client", "Client", 220), ("montant", "Montant", 120), ("services", "Services", 220), ("date", "Date", 120)):
            self.payments_tree.heading(col, text=heading)
            self.payments_tree.column(col, width=width, anchor="w")
        payments_scroll = attach_modern_scrollbar(payments_frame, self.payments_tree)
        self.payments_tree.grid(row=0, column=0, sticky="nsew")
        payments_scroll.grid(row=0, column=1, sticky="ns")
        bind_mousewheel(self.payments_tree, self.payments_tree)
        payments_frame.columnconfigure(0, weight=1)

    def stats(self):
        month = self.month_var.get().strip()
        if len(month) != 7:
            messagebox.showwarning("Validation", "Format du mois attendu : AAAA-MM")
            return None
        clients = self.db.fetchone("SELECT COUNT(*) AS total FROM client WHERE date_inscription LIKE ?", (f"{month}%",))["total"]
        revenue = self.db.fetchone("SELECT COALESCE(SUM(montant), 0) AS total FROM paiement WHERE date_paiement LIKE ?", (f"{month}%",))["total"]
        appointments = self.db.fetchone("SELECT COUNT(*) AS total FROM rendez_vous WHERE date_rdv LIKE ?", (f"{month}%",))["total"]
        return {"month": month, "clients": clients, "revenue": revenue, "appointments": appointments}

    def popular_services(self, month):
        return self.db.fetchall(
            """
            SELECT s.nom_service AS label, COUNT(*) AS total
            FROM rendez_vous r
            JOIN service s ON s.id_service = r.id_service
            WHERE r.date_rdv LIKE ?
            GROUP BY s.id_service
            ORDER BY total DESC
            LIMIT 5
            """,
            (f"{month}%",),
        )

    def appointments_by_day(self, month):
        return self.db.fetchall(
            """
            SELECT date_rdv AS label, COUNT(*) AS total
            FROM rendez_vous
            WHERE date_rdv LIKE ?
            GROUP BY date_rdv
            ORDER BY date_rdv ASC
            LIMIT 10
            """,
            (f"{month}%",),
        )

    def payments_for_period(self, month=None, day=None):
        if day:
            return self.db.fetchall(
                """
                SELECT c.nom || ' ' || c.prenom AS client,
                       SUM(p.montant) AS montant,
                       GROUP_CONCAT(s.nom_service, ', ') AS services,
                       p.date_paiement AS date
                FROM paiement p
                JOIN client c ON c.id_client = p.id_client
                JOIN rendez_vous r ON r.id_rdv = p.id_rdv
                JOIN service s ON s.id_service = r.id_service
                WHERE p.date_paiement = ?
                GROUP BY c.id_client, p.date_paiement
                ORDER BY p.date_paiement DESC
                """,
                (day,),
            )
        return self.db.fetchall(
            """
            SELECT c.nom || ' ' || c.prenom AS client,
                   SUM(p.montant) AS montant,
                   GROUP_CONCAT(s.nom_service, ', ') AS services,
                   p.date_paiement AS date
            FROM paiement p
            JOIN client c ON c.id_client = p.id_client
            JOIN rendez_vous r ON r.id_rdv = p.id_rdv
            JOIN service s ON s.id_service = r.id_service
            WHERE p.date_paiement LIKE ?
            GROUP BY c.id_client, p.date_paiement
            ORDER BY p.date_paiement DESC
            """,
            (f"{month}%",),
        )

    def load_payments(self, month=None, day=None):
        for item in self.payments_tree.get_children():
            self.payments_tree.delete(item)
        rows = self.payments_for_period(month=month, day=day)
        for row in rows:
            self.payments_tree.insert("", tk.END, values=(row["client"], f"{row['montant']:.2f} MAD", row["services"], row["date"]))

    def draw_bars(self, canvas, title, rows, color):
        canvas.delete("all")
        canvas.create_text(18, 18, text=title, fill=self.chart_fg, anchor="w", font=("Segoe UI", 12, "bold"))
        if not rows:
            canvas.create_text(18, 70, text="Aucune donnée", fill=self.chart_muted, anchor="w", font=("Segoe UI", 10))
            return
        max_value = max(row["total"] for row in rows) or 1
        y = 52
        for row in rows:
            label = str(row["label"])[-10:]
            total = int(row["total"])
            width = int((total / max_value) * 250)
            canvas.create_text(18, y + 8, text=label, fill=self.chart_muted, anchor="w", font=("Segoe UI", 9))
            canvas.create_rectangle(120, y, 120 + width, y + 16, fill=color, outline="")
            canvas.create_text(130 + width, y + 8, text=str(total), fill=self.chart_fg, anchor="w", font=("Segoe UI", 9, "bold"))
            y += 30

    def generate(self):
        stats = self.stats()
        if not stats:
            return
        self.stats_vars["clients"].set(str(stats["clients"]))
        self.stats_vars["revenue"].set(f"{stats['revenue']:.2f} MAD")
        self.stats_vars["appointments"].set(str(stats["appointments"]))
        self.details.delete("1.0", tk.END)
        self.details.insert(
            tk.END,
            "\n".join(
                [
                    f"Rapport du mois : {stats['month']}",
                    "",
                    f"Nombre de nouveaux clients : {stats['clients']}",
                    f"Revenu total : {stats['revenue']:.2f} MAD",
                    f"Nombre de rendez-vous : {stats['appointments']}",
                ]
            ),
        )
        self.draw_bars(self.services_canvas, "Services les plus demandes", self.popular_services(stats["month"]), "#38BDF8")
        self.draw_bars(self.days_canvas, "Rendez-vous par jour", self.appointments_by_day(stats["month"]), "#22C55E")
        self.load_payments(month=stats["month"])

    def print_report(self):
        stats = self.stats()
        if not stats:
            return
        lines = [
            "GESTION DE SPA",
            "",
            f"Mois : {stats['month']}",
            f"Nombre de clients : {stats['clients']}",
            f"Revenue : {stats['revenue']:.2f} MAD",
            f"Nombre de rendez-vous : {stats['appointments']}",
        ]
        path = create_pdf(f"rapport_mensuel_{stats['month']}.pdf", "Rapport mensuel", lines)
        open_pdf(path)
        show_pdf(path)

    def day_stats(self):
        selected_day = self.day_entry.get().strip()
        if len(selected_day) != 10:
            messagebox.showwarning("Validation", "Choisissez un jour valide.")
            return None
        clients = self.db.fetchone("SELECT COUNT(*) AS total FROM client WHERE date_inscription = ?", (selected_day,))["total"]
        revenue = self.db.fetchone("SELECT COALESCE(SUM(montant), 0) AS total FROM paiement WHERE date_paiement = ?", (selected_day,))["total"]
        appointments = self.db.fetchone("SELECT COUNT(*) AS total FROM rendez_vous WHERE date_rdv = ?", (selected_day,))["total"]
        return {"day": selected_day, "clients": clients, "revenue": revenue, "appointments": appointments}

    def generate_day(self):
        stats = self.day_stats()
        if not stats:
            return
        self.stats_vars["clients"].set(str(stats["clients"]))
        self.stats_vars["revenue"].set(f"{stats['revenue']:.2f} MAD")
        self.stats_vars["appointments"].set(str(stats["appointments"]))
        self.details.delete("1.0", tk.END)
        self.details.insert(
            tk.END,
            "\n".join(
                [
                    f"Rapport du jour : {stats['day']}",
                    "",
                    f"Nouveaux clients : {stats['clients']}",
                    f"Revenu total : {stats['revenue']:.2f} MAD",
                    f"Nombre de rendez-vous : {stats['appointments']}",
                ]
            ),
        )
        self.load_payments(day=stats['day'])

    def print_day_report(self):
        stats = self.day_stats()
        if not stats:
            return
        lines = [
            "GESTION DE SPA",
            "",
            f"Jour : {stats['day']}",
            f"Nombre de clients : {stats['clients']}",
            f"Revenue : {stats['revenue']:.2f} MAD",
            f"Nombre de rendez-vous : {stats['appointments']}",
        ]
        path = create_pdf(f"rapport_journalier_{stats['day']}.pdf", "Rapport journalier", lines)
        open_pdf(path)
        show_pdf(path)
