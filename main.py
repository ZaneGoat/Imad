import tkinter as tk
from tkinter import ttk

from app.core.database import Database
from app.ui.auth import LoginFrame
from app.ui.client import ClientFrame
from app.ui.dashboard import DashboardFrame
from app.ui.employe import EmployeFrame
from app.ui.paiement import PaiementFrame
from app.ui.rendezvous import RendezVousFrame
from app.ui.reports import ReportsFrame
from app.ui.service import ServiceFrame
from app.ui.settings import SettingsFrame


class SpaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestion Spa")
        self.geometry("1260x760")
        self.minsize(1100, 650)
        self.db = Database()
        self.current_user = None
        self.pages = {}
        self.nav_buttons = {}
        self.theme = "dark"
        self.font_scale = 1.0
        self.palette = {}
        self.configure_style("dark", 1.0)
        remembered = self.db.remembered_user()
        self.show_app(remembered) if remembered else self.show_login()

    def colors(self, theme):
        if theme == "light":
            return {
                "bg": "#F1F5F9", "sidebar": "#FFFFFF", "card": "#FFFFFF", "panel": "#CBD5E1",
                "text": "#0F172A", "muted": "#64748B", "heading": "#0F172A",
                "accent": "#2563EB", "accent2": "#0284C7", "button_hover": "#1D4ED8",
                "entry": "#FFFFFF", "entry_text": "#0F172A", "tree": "#FFFFFF",
                "tree_alt": "#F8FAFC", "tree_head": "#DBEAFE", "danger": "#DC2626",
            }
        return {
            "bg": "#0F172A", "sidebar": "#111827", "card": "#1E293B", "panel": "#334155",
            "text": "#E5E7EB", "muted": "#94A3B8", "heading": "#F8FAFC",
            "accent": "#2563EB", "accent2": "#38BDF8", "button_hover": "#1D4ED8",
            "entry": "#E2E8F0", "entry_text": "#0F172A", "tree": "#1E293B",
            "tree_alt": "#172033", "tree_head": "#334155", "danger": "#FCA5A5",
        }

    def font(self, size, weight="normal"):
        return ("Segoe UI", max(8, int(size * self.font_scale)), weight)

    def configure_style(self, theme="dark", font_scale=1.0):
        self.theme = theme
        self.font_scale = float(font_scale or 1.0)
        self.palette = self.colors(theme)
        c = self.palette
        style = ttk.Style(self)
        style.theme_use("clam")
        self.configure(bg=c["bg"])

        style.configure(".", font=self.font(10), background=c["bg"], foreground=c["text"])
        style.configure("App.TFrame", background=c["bg"])
        style.configure("Sidebar.TFrame", background=c["sidebar"])
        style.configure("Card.TFrame", background=c["card"], relief="flat", borderwidth=0)
        style.configure("TFrame", background=c["bg"])
        style.configure("Panel.TLabelframe", background=c["bg"], foreground=c["text"], bordercolor=c["panel"], lightcolor=c["panel"], darkcolor=c["panel"])
        style.configure("Panel.TLabelframe.Label", background=c["bg"], foreground=c["text"], font=self.font(11, "bold"))
        style.configure("TLabel", background=c["bg"], foreground=c["text"])
        style.configure("PageTitle.TLabel", font=self.font(22, "bold"), foreground=c["heading"], background=c["bg"])
        style.configure("Title.TLabel", font=self.font(17, "bold"), foreground=c["heading"], background=c["bg"])
        style.configure("Hero.TLabel", font=self.font(26, "bold"), foreground=c["heading"], background=c["sidebar"])
        style.configure("Subtle.TLabel", foreground=c["muted"], background=c["bg"])
        style.configure("Muted.TLabel", foreground=c["muted"], background=c["bg"])
        style.configure("CardLabel.TLabel", foreground=c["muted"], background=c["card"])
        style.configure("Metric.TLabel", font=self.font(18, "bold"), foreground=c["accent2"], background=c["card"])

        style.configure("TEntry", fieldbackground=c["entry"], foreground=c["entry_text"], padding=8, bordercolor=c["panel"], lightcolor=c["panel"], darkcolor=c["panel"])
        style.configure("TCombobox", fieldbackground=c["entry"], foreground=c["entry_text"], padding=6, bordercolor=c["panel"])
        style.configure("TCheckbutton", background=c["bg"], foreground=c["text"])
        style.configure("Dark.TEntry", fieldbackground=c["entry"], foreground=c["entry_text"], padding=10, bordercolor=c["panel"])
        style.configure("Dark.TCheckbutton", background=c["card"], foreground=c["text"])

        style.configure("Primary.TButton", padding=(15, 10), font=self.font(10, "bold"), background=c["accent"], foreground="#FFFFFF", borderwidth=0, focusthickness=0)
        style.configure("TButton", padding=(11, 8), background=c["accent"], foreground="#FFFFFF", borderwidth=0, focusthickness=0)
        style.configure("Ghost.TButton", background=c["panel"], foreground=c["text"], padding=(10, 8), borderwidth=0)
        style.configure("Nav.TButton", anchor="w", padding=(16, 12), background=c["sidebar"], foreground=c["muted"], borderwidth=0, focusthickness=0)
        style.configure("NavActive.TButton", anchor="w", padding=(16, 12), background=c["accent"], foreground="#FFFFFF", borderwidth=0, focusthickness=0)
        style.map("TButton", background=[("active", c["button_hover"])], foreground=[("active", "#FFFFFF")])
        style.map("Nav.TButton", background=[("active", c["panel"])], foreground=[("active", c["heading"])])

        style.configure("Treeview", rowheight=31, background=c["tree"], fieldbackground=c["tree"], foreground=c["text"], borderwidth=0)
        style.configure("Treeview.Heading", font=self.font(10, "bold"), background=c["tree_head"], foreground=c["heading"], borderwidth=0)
        style.map("Treeview", background=[("selected", c["accent"])], foreground=[("selected", "#FFFFFF")])

        style.configure(
            "Vertical.TScrollbar",
            troughcolor=c["card"],
            background=c["accent2"],
            arrowcolor=c["heading"],
            bordercolor=c["panel"],
            relief="flat",
            width=10,
            gripcount=0,
        )
        style.configure(
            "Horizontal.TScrollbar",
            troughcolor=c["card"],
            background=c["accent2"],
            arrowcolor=c["heading"],
            bordercolor=c["panel"],
            relief="flat",
            width=10,
            gripcount=0,
        )
        style.map("Vertical.TScrollbar", background=[("active", c["accent"]), ("pressed", c["button_hover"])])
        style.map("Horizontal.TScrollbar", background=[("active", c["accent"]), ("pressed", c["button_hover"])])

        style.configure("LoginBg.TFrame", background=c["bg"])
        style.configure("LoginCard.TFrame", background=c["card"])
        style.configure("Logo.TLabel", font=self.font(32, "bold"), foreground=c["accent2"], background=c["card"])
        style.configure("LoginTitle.TLabel", font=self.font(23, "bold"), foreground=c["heading"], background=c["card"])
        style.configure("LoginMuted.TLabel", foreground=c["muted"], background=c["card"])
        style.configure("LoginLabel.TLabel", foreground=c["text"], background=c["card"])
        style.configure("Error.TLabel", foreground=c["danger"], background=c["card"])

    def clear_root(self):
        for child in self.winfo_children():
            child.destroy()

    def show_login(self):
        self.clear_root()
        LoginFrame(self, self.db, self.show_app).pack(fill="both", expand=True)

    def show_app(self, user):
        self.current_user = user
        self.configure_style(user.get("theme", "dark"), user.get("font_scale", 1.0))
        self.clear_root()
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(self, style="Sidebar.TFrame", padding=(16, 20))
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.columnconfigure(0, weight=1)
        ttk.Label(sidebar, text="Gestion Spa", style="Hero.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(sidebar, text=f"{user['role']} - {user['username']}", foreground=self.palette["muted"], background=self.palette["sidebar"]).grid(row=1, column=0, sticky="w", pady=(0, 18))

        self.content = ttk.Frame(self, style="App.TFrame")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

        allowed = self.allowed_pages(user["role"])
        nav = [
            ("Dashboard", "[D] Dashboard", lambda: DashboardFrame(self.content, self.db, self.quick_actions())),
            ("Clients", "[C] Clients", lambda: ClientFrame(self.content, self.db, self.refresh_dashboard)),
            ("Services", "[S] Services", lambda: ServiceFrame(self.content, self.db, self.refresh_dashboard)),
            ("Employes", "[E] Employes", lambda: EmployeFrame(self.content, self.db, self.refresh_dashboard)),
            ("Rendez-vous", "[R] Rendez-vous", lambda: RendezVousFrame(self.content, self.db, self.refresh_dashboard)),
            ("Paiements", "[P] Paiements", lambda: PaiementFrame(self.content, self.db, self.refresh_dashboard)),
            ("Rapports", "[A] Rapports", lambda: ReportsFrame(self.content, self.db)),
            ("Parametres", "[*] Parametres", lambda: SettingsFrame(self.content, self.db, self.current_user, self.apply_user_preferences, self.restart_after_restore)),
        ]
        factories = {key: factory for key, _label, factory in nav}

        row = 2
        for key, label, factory in nav:
            if key not in allowed:
                continue
            btn = ttk.Button(sidebar, text=label, style="Nav.TButton", command=lambda k=key, f=factory: self.show_page(k, f))
            btn.grid(row=row, column=0, sticky="ew", pady=3)
            self.nav_buttons[key] = btn
            row += 1
        ttk.Separator(sidebar).grid(row=row, column=0, sticky="ew", pady=16)
        ttk.Button(sidebar, text="[X] Deconnexion", style="Nav.TButton", command=self.logout).grid(row=row + 1, column=0, sticky="ew")
        self.show_page("Dashboard", factories["Dashboard"])

    def allowed_pages(self, role):
        if role == "Receptionist":
            return {"Dashboard", "Clients", "Rendez-vous", "Paiements", "Parametres"}
        return {"Dashboard", "Clients", "Services", "Employes", "Rendez-vous", "Paiements", "Rapports", "Parametres"}

    def quick_actions(self):
        actions = {"rdv": self.new_appointment, "client": self.new_client}
        if "Paiements" in self.allowed_pages(self.current_user["role"]):
            actions["paiement"] = self.new_payment
        return actions

    def show_page(self, key, factory=None):
        for button_key, button in self.nav_buttons.items():
            button.configure(style="NavActive.TButton" if button_key == key else "Nav.TButton")
        for child in self.content.winfo_children():
            child.grid_forget()
        if key not in self.pages:
            self.pages[key] = factory()
            self.pages[key].grid(row=0, column=0, sticky="nsew")
        else:
            self.pages[key].grid(row=0, column=0, sticky="nsew")
        page = self.pages[key]
        if hasattr(page, "load"):
            page.load()
        if hasattr(page, "refresh"):
            page.refresh()
        if hasattr(page, "generate") and key == "Rapports":
            page.generate()

    def refresh_dashboard(self):
        page = self.pages.get("Dashboard")
        if page and hasattr(page, "refresh"):
            page.refresh()

    def restart_after_restore(self):
        user = self.current_user
        self.db = Database()
        self.pages = {}
        self.nav_buttons = {}
        if user:
            self.current_user = self.db.get_user(user["id_user"]) or user
            self.show_app(self.current_user)
        else:
            self.show_login()

    def apply_user_preferences(self, theme=None, font_scale=None, language=None):
        self.db.update_user_preferences(self.current_user["id_user"], theme=theme, font_scale=font_scale, language=language)
        self.current_user = self.db.get_user(self.current_user["id_user"])
        self.pages = {}
        self.nav_buttons = {}
        self.show_app(self.current_user)

    def new_client(self):
        self.show_page("Clients", lambda: ClientFrame(self.content, self.db, self.refresh_dashboard))
        self.pages["Clients"].clear()

    def new_appointment(self):
        self.show_page("Rendez-vous", lambda: RendezVousFrame(self.content, self.db, self.refresh_dashboard))
        self.pages["Rendez-vous"].clear()

    def new_payment(self):
        self.show_page("Paiements", lambda: PaiementFrame(self.content, self.db, self.refresh_dashboard))
        self.pages["Paiements"].clear()

    def logout(self):
        self.db.clear_remembered_users()
        self.current_user = None
        self.pages = {}
        self.nav_buttons = {}
        self.show_login()


if __name__ == "__main__":
    app = SpaApp()
    app.mainloop()
