from datetime import date, datetime
import tkinter as tk
from tkinter import ttk
from app.ui.rendezvous import RendezVousFrame
from app.ui.ui_utils import attach_modern_scrollbar, bind_mousewheel


class DashboardFrame(ttk.Frame):
    SERVICE_WINDOW_MINUTES = 180

    def __init__(self, parent, db, actions):
        super().__init__(parent, padding=22, style="App.TFrame")
        self.db = db
        self.actions = actions
        self.sort_time_reverse = False
        self.today_rows = []
        self.vars = {
            "clients": tk.StringVar(),
            "appointments_today": tk.StringVar(),
            "revenue_today": tk.StringVar(),
            "available_employees": tk.StringVar(),
            "popular_service": tk.StringVar(),
        }
        self.build()
        self.refresh()

    def build(self):
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text="Dashboard", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text=f"Aujourd'hui - {datetime.now().strftime('%d/%m/%Y')}", style="Subtle.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 18))

        cards = ttk.Frame(self, style="App.TFrame")
        cards.grid(row=2, column=0, sticky="ew")
        for i in range(5):
            cards.columnconfigure(i, weight=1)
        card_data = (
            ("◉ Total Clients", "clients", "#38BDF8"),
            ("□ Rendez-vous", "appointments_today", "#22C55E"),
            ("◇ Revenus", "revenue_today", "#FACC15"),
            ("▣ Disponibles", "available_employees", "#2DD4BF"),
            ("△ Service demandé", "popular_service", "#A78BFA"),
        )
        for col, (label, key, accent) in enumerate(card_data):
            card = ttk.Frame(cards, style="Card.TFrame", padding=18)
            card.grid(row=0, column=col, sticky="nsew", padx=7)
            ttk.Label(card, text=label, style="CardLabel.TLabel").pack(anchor="w")
            ttk.Label(card, textvariable=self.vars[key], style="Metric.TLabel", wraplength=145).pack(anchor="w", pady=(10, 0))
            tk.Frame(card, bg=accent, height=3).pack(fill="x", pady=(14, 0))

        body = ttk.Frame(self, style="App.TFrame")
        body.grid(row=3, column=0, sticky="nsew", pady=22)
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        self.rowconfigure(3, weight=1)

        quick = ttk.LabelFrame(body, text="Actions rapides", padding=18, style="Panel.TLabelframe")
        quick.grid(row=0, column=0, sticky="nsw", padx=(0, 16))
        quick_buttons = [
            ("+ Nouveau Rendez-vous", self.actions["rdv"]),
            ("+ Nouveau Client", self.actions["client"]),
        ]
        if self.actions.get("paiement"):
            quick_buttons.append(("◈ Paiements", self.actions["paiement"]))
        for text, command in quick_buttons:
            ttk.Button(quick, text=text, style="Primary.TButton", command=command).pack(fill="x", pady=7)

        today = ttk.LabelFrame(body, text="Rendez-vous aujourd'hui", padding=14, style="Panel.TLabelframe")
        today.grid(row=0, column=1, sticky="nsew")
        today.columnconfigure(0, weight=1)
        today.rowconfigure(0, weight=1)
        tree_wrap = ttk.Frame(today, style="App.TFrame")
        tree_wrap.grid(row=0, column=0, sticky="nsew")
        tree_wrap.rowconfigure(0, weight=1)
        tree_wrap.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(tree_wrap, columns=("id", "etat", "heure", "client", "service", "employe", "statut"), show="headings", height=10)
        for col, heading, width in (
            ("id", "", 0),
            ("etat", "", 38),
            ("heure", "Heure", 80),
            ("client", "Client", 180),
            ("service", "Service", 150),
            ("employe", "Employé", 170),
            ("statut", "Statut", 120),
        ):
            if col == "heure":
                self.tree.heading(col, text=heading, command=self.toggle_time_sort)
            else:
                self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor="center" if col == "etat" else "w", stretch=(col != "id"))
        self.tree.tag_configure("green", foreground="#22C55E")
        self.tree.tag_configure("red", foreground="#EF4444")
        self.tree.tag_configure("yellow", foreground="#FACC15")
        self.tree.tag_configure("blue", foreground="#38BDF8")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y = attach_modern_scrollbar(tree_wrap, self.tree)
        scroll_y.grid(row=0, column=1, sticky="ns")
        bind_mousewheel(self.tree, self.tree)
        self.tree.bind("<Double-1>", self.on_double_click)

    def minutes_from_midnight(self, heure):
        hour, minute = heure.split(":")
        return int(hour) * 60 + int(minute)

    def effective_status(self, statut, heure_rdv):
        statut = statut or ""
        if statut.startswith("Annul") or statut.startswith("Termine"):
            return statut
        start = self.minutes_from_midnight(heure_rdv)
        now = datetime.now()
        now_minutes = now.hour * 60 + now.minute
        if start <= now_minutes < start + self.SERVICE_WINDOW_MINUTES:
            if statut.startswith("Confirm") or statut == "En attente" or statut.startswith("En Service"):
                return "En Service"
        return statut

    def status_priority(self, statut):
        statut = statut or ""
        if statut.startswith("Confirm"):
            return 0
        if statut == "En attente" or statut.startswith("En Service"):
            return 1
        if statut.startswith("Annul") or statut.startswith("Termine"):
            return 2
        return 3

    def time_sort_key(self, heure):
        start = self.minutes_from_midnight(heure)
        now = datetime.now()
        now_minutes = now.hour * 60 + now.minute
        if start >= now_minutes:
            return start - now_minutes
        return 10000 + (now_minutes - start)

    def sort_today_rows(self, rows):
        def sort_key(row):
            display_status = self.effective_status(row["statut"], row["heure_rdv"])
            status_key = self.status_priority(display_status)
            time_key = self.time_sort_key(row["heure_rdv"])
            if self.sort_time_reverse:
                time_key = -time_key
            return (status_key, time_key, row["heure_rdv"])

        return sorted(rows, key=sort_key)

    def toggle_time_sort(self):
        self.sort_time_reverse = not self.sort_time_reverse
        arrow = " ▼" if self.sort_time_reverse else " ▲"
        self.tree.heading("heure", text=f"Heure{arrow}")
        self.render_today_rows()

    def status_tag(self, status):
        if status.startswith("Confirm"):
            return "green", "●"
        if status.startswith("Annul") or status.startswith("Termine"):
            return "red", "●"
        if status.startswith("En"):
            return "blue", "●"
        return "yellow", "●"

    def fetch_today_rows(self):
        return self.db.fetchall(
            """
            SELECT r.id_rdv, r.heure_rdv, r.statut,
                   c.nom || ' ' || c.prenom AS client,
                   s.nom_service AS service,
                   e.nom || ' ' || e.prenom AS employe
            FROM rendez_vous r
            JOIN client c ON c.id_client = r.id_client
            JOIN service s ON s.id_service = r.id_service
            JOIN employe e ON e.id_employe = r.id_employe
            WHERE r.date_rdv = ?
            """,
            (date.today().isoformat(),),
        )

    def render_today_rows(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows = self.sort_today_rows(self.today_rows)
        if not rows:
            self.tree.insert("", tk.END, values=("", "-", "Aucun rendez-vous", "-", "-", "-"))
            return
        for row in rows:
            display_status = self.effective_status(row["statut"], row["heure_rdv"])
            tag, dot = self.status_tag(display_status)
            self.tree.insert(
                "",
                tk.END,
                values=(row["id_rdv"], dot, row["heure_rdv"], row["client"], row["service"], row["employe"], display_status),
                tags=(tag,),
            )

    def refresh(self):
        stats = self.db.dashboard_stats()
        self.vars["clients"].set(str(stats["clients"]))
        self.vars["appointments_today"].set(str(stats["appointments_today"]))
        self.vars["revenue_today"].set(f"{stats['revenue_today']:.2f} MAD")
        self.vars["available_employees"].set(str(stats["available_employees"]))
        self.vars["popular_service"].set(stats["popular_service"])

        self.today_rows = list(self.fetch_today_rows())
        self.tree.heading("heure", text="Heure ▲")
        self.sort_time_reverse = False
        self.render_today_rows()

    def on_double_click(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        if not values:
            return
        try:
            rdv_id = int(values[0])
        except Exception:
            return
        root = self.winfo_toplevel()
        root.show_page("Rendez-vous", lambda: RendezVousFrame(root.content, root.db, root.refresh_dashboard))
        page = root.pages.get("Rendez-vous")
        if page and hasattr(page, "select_rdv"):
            page.select_rdv(rdv_id)
