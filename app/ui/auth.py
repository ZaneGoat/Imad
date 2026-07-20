import tkinter as tk
from tkinter import ttk


class LoginFrame(ttk.Frame):
    def __init__(self, parent, db, on_login):
        super().__init__(parent, style="LoginBg.TFrame")
        self.db = db
        self.on_login = on_login
        self.show_password = tk.BooleanVar(value=False)
        self.remember = tk.BooleanVar(value=True)
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.new_username = tk.StringVar()
        self.new_password = tk.StringVar()
        self.confirm_password = tk.StringVar()
        self.new_role = tk.StringVar(value="Receptionist")
        self.error = tk.StringVar()
        self.create_message = tk.StringVar()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.card = None
        self.show_login_page()

    def clear_card(self):
        if self.card is not None:
            self.card.destroy()
        self.card = ttk.Frame(self, style="LoginCard.TFrame", padding=34)
        self.card.grid(row=0, column=0)
        self.card.columnconfigure(0, weight=1)

    def show_login_page(self):
        self.clear_card()
        card = self.card
        self.error.set("")

        ttk.Label(card, text="SPA", style="Logo.TLabel").grid(row=0, column=0)
        ttk.Label(card, text="Gestion Spa", style="LoginTitle.TLabel").grid(row=1, column=0, pady=(4, 4))
        ttk.Label(card, text="Connectez-vous a votre espace de gestion", style="LoginMuted.TLabel").grid(row=2, column=0, pady=(0, 22))

        ttk.Label(card, text="Nom d'utilisateur", style="LoginLabel.TLabel").grid(row=3, column=0, sticky="w")
        ttk.Entry(card, textvariable=self.username, style="Dark.TEntry", width=34).grid(row=4, column=0, sticky="ew", pady=(5, 14))

        ttk.Label(card, text="Mot de passe", style="LoginLabel.TLabel").grid(row=5, column=0, sticky="w")
        pass_row = ttk.Frame(card, style="LoginCard.TFrame")
        pass_row.grid(row=6, column=0, sticky="ew", pady=(5, 12))
        pass_row.columnconfigure(0, weight=1)
        self.password_entry = ttk.Entry(pass_row, textvariable=self.password, show="*", style="Dark.TEntry")
        self.password_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(pass_row, text="Voir", width=6, style="Ghost.TButton", command=self.toggle_password).grid(row=0, column=1, padx=(8, 0))

        ttk.Checkbutton(card, text="Remember Me", variable=self.remember, style="Dark.TCheckbutton").grid(row=7, column=0, sticky="w", pady=(0, 12))
        ttk.Label(card, textvariable=self.error, style="Error.TLabel", wraplength=300).grid(row=8, column=0, sticky="w")
        ttk.Button(card, text="Se connecter", style="Primary.TButton", command=self.login).grid(row=9, column=0, sticky="ew", pady=(16, 0))
        ttk.Button(card, text="Creer un compte", style="Ghost.TButton", command=self.show_create_page).grid(row=10, column=0, sticky="ew", pady=(10, 0))

        self.password_entry.bind("<Return>", lambda _event: self.login())

    def show_create_page(self):
        self.clear_card()
        card = self.card
        self.create_message.set("")

        ttk.Label(card, text="SPA", style="Logo.TLabel").grid(row=0, column=0)
        ttk.Label(card, text="Creer un compte", style="LoginTitle.TLabel").grid(row=1, column=0, pady=(4, 4))
        ttk.Label(card, text="Ajoutez un nouvel utilisateur de l'application", style="LoginMuted.TLabel").grid(row=2, column=0, pady=(0, 22))

        ttk.Label(card, text="Nom d'utilisateur", style="LoginLabel.TLabel").grid(row=3, column=0, sticky="w")
        ttk.Entry(card, textvariable=self.new_username, style="Dark.TEntry", width=34).grid(row=4, column=0, sticky="ew", pady=(5, 12))

        ttk.Label(card, text="Mot de passe", style="LoginLabel.TLabel").grid(row=5, column=0, sticky="w")
        ttk.Entry(card, textvariable=self.new_password, show="*", style="Dark.TEntry").grid(row=6, column=0, sticky="ew", pady=(5, 12))

        ttk.Label(card, text="Confirmer le mot de passe", style="LoginLabel.TLabel").grid(row=7, column=0, sticky="w")
        ttk.Entry(card, textvariable=self.confirm_password, show="*", style="Dark.TEntry").grid(row=8, column=0, sticky="ew", pady=(5, 12))

        ttk.Label(card, text="Le compte cree aura le role Receptionist.", style="LoginMuted.TLabel").grid(row=9, column=0, sticky="w", pady=(0, 10))
        ttk.Label(card, textvariable=self.create_message, style="LoginMuted.TLabel", wraplength=300).grid(row=10, column=0, sticky="w")
        ttk.Button(card, text="Creer le compte", style="Primary.TButton", command=self.create_account).grid(row=11, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(card, text="Retour", style="Ghost.TButton", command=self.show_login_page).grid(row=12, column=0, sticky="ew", pady=(10, 0))

    def toggle_password(self):
        self.show_password.set(not self.show_password.get())
        self.password_entry.configure(show="" if self.show_password.get() else "*")

    def login(self):
        username = self.username.get().strip()
        password = self.password.get().strip()
        if not username or not password:
            self.error.set("Veuillez remplir le nom d'utilisateur et le mot de passe.")
            return
        user = self.db.authenticate(username, password, self.remember.get())
        if not user:
            self.error.set("Nom d'utilisateur ou mot de passe incorrect.")
            return
        self.error.set("")
        self.on_login(user)

    def create_account(self):
        username = self.new_username.get().strip()
        password = self.new_password.get().strip()
        confirm = self.confirm_password.get().strip()
        role = "Receptionist"

        if not username or not password or not confirm:
            self.create_message.set("Remplissez tous les champs du nouveau compte.")
            return
        if len(password) < 4:
            self.create_message.set("Le mot de passe doit contenir au moins 4 caracteres.")
            return
        if password != confirm:
            self.create_message.set("Les mots de passe ne correspondent pas.")
            return

        ok, message = self.db.create_user(username, password, role)
        if not ok:
            self.create_message.set(message)
            return

        self.username.set(username)
        self.password.set("")
        self.new_username.set("")
        self.new_password.set("")
        self.confirm_password.set("")
        self.create_message.set(f"{message} Retournez a la page de connexion.")
