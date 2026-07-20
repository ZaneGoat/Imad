import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app.config import BACKUP_DIR


class AccordionSection(ttk.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, style="App.TFrame")
        self.title = title
        self.opened = tk.BooleanVar(value=False)
        self.header = ttk.Button(self, text=f"> {title}", style="Ghost.TButton", command=self.toggle)
        self.header.pack(fill="x", pady=(0, 6))
        self.body = ttk.Frame(self, style="Card.TFrame", padding=16)

    def toggle(self):
        self.opened.set(not self.opened.get())
        self.header.configure(text=f"{'v' if self.opened.get() else '>'} {self.title}")
        if self.opened.get():
            self.body.pack(fill="x", pady=(0, 12))
        else:
            self.body.pack_forget()


class SettingsFrame(ttk.Frame):
    def __init__(self, parent, db, current_user, apply_preferences, restart_after_restore=None):
        super().__init__(parent, padding=22, style="App.TFrame")
        self.db = db
        self.current_user = current_user
        self.apply_preferences = apply_preferences
        self.restart_after_restore = restart_after_restore
        self.user_tree = None
        self.setting_vars = {key: tk.StringVar(value=value) for key, value in self.db.all_settings().items()}
        self.theme_var = tk.StringVar(value=current_user.get("theme", "dark"))
        self.build()

    def build(self):
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text="Parametres", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            self,
            text=f"Connecte : {self.current_user['username']} ({self.current_user['role']})",
            style="Subtle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 18))

        content = ttk.Frame(self, style="App.TFrame")
        content.grid(row=2, column=0, sticky="nsew")
        self.rowconfigure(2, weight=1)

        if self.current_user["role"] == "Admin":
            self.user_management(self.add_section(content, "User Management"))
            self.database_backup(self.add_section(content, "Sauvegarde base de donnees"))
            self.spa_information(self.add_section(content, "Spa Informations"))
            self.working_hours(self.add_section(content, "Working Hours"))
            self.appearance(self.add_section(content, "Apparence"))
        else:
            self.profile_security(self.add_section(content, "Profile & Security"))
            self.appearance(self.add_section(content, "Apparence"))

    def add_section(self, parent, title):
        section = AccordionSection(parent, title)
        section.pack(fill="x", pady=5)
        return section.body

    def labeled_entry(self, parent, label, var, row, width=38, show=None):
        ttk.Label(parent, text=label, style="CardLabel.TLabel").grid(row=row, column=0, sticky="w", pady=5)
        entry = ttk.Entry(parent, textvariable=var, width=width, show=show)
        entry.grid(row=row, column=1, sticky="ew", pady=5, padx=(12, 0))
        parent.columnconfigure(1, weight=1)
        return entry

    def user_management(self, parent):
        parent.columnconfigure(0, weight=1)
        form = ttk.Frame(parent, style="Card.TFrame")
        form.grid(row=0, column=0, sticky="ew")
        username = tk.StringVar()
        password = tk.StringVar()
        role = tk.StringVar(value="Receptionist")
        self.labeled_entry(form, "Nouvel utilisateur", username, 0)
        self.labeled_entry(form, "Mot de passe", password, 1, show="*")
        ttk.Label(form, text="Role", style="CardLabel.TLabel").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Combobox(form, textvariable=role, values=("Admin", "Receptionist"), state="readonly").grid(row=2, column=1, sticky="ew", pady=5, padx=(12, 0))
        ttk.Button(form, text="+ Creer le compte", command=lambda: self.create_user(username, password, role)).grid(row=3, column=1, sticky="e", pady=8)

        self.user_tree = ttk.Treeview(parent, columns=("id", "username", "role"), show="headings", height=5)
        for col, title, width in (("id", "ID", 50), ("username", "Utilisateur", 180), ("role", "Role", 140)):
            self.user_tree.heading(col, text=title)
            self.user_tree.column(col, width=width)
        self.user_tree.grid(row=1, column=0, sticky="ew", pady=12)
        actions = ttk.Frame(parent, style="Card.TFrame")
        actions.grid(row=2, column=0, sticky="ew")
        ttk.Button(actions, text="Admin", command=lambda: self.change_selected_role("Admin")).pack(side="left", padx=4)
        ttk.Button(actions, text="Receptionist", command=lambda: self.change_selected_role("Receptionist")).pack(side="left", padx=4)
        ttk.Button(actions, text="Reset password", command=self.reset_selected_password).pack(side="left", padx=4)
        ttk.Button(actions, text="Supprimer", command=self.delete_selected_user).pack(side="left", padx=4)
        self.load_users()

    def selected_user_id(self):
        selected = self.user_tree.selection()
        return self.user_tree.item(selected[0], "values")[0] if selected else None

    def load_users(self):
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        for row in self.db.list_users():
            self.user_tree.insert("", tk.END, values=(row["id_user"], row["username"], row["role"]))

    def create_user(self, username, password, role):
        if not username.get().strip() or not password.get().strip():
            messagebox.showwarning("Validation", "Nom d'utilisateur et mot de passe obligatoires.")
            return
        ok, msg = self.db.create_user(username.get(), password.get(), role.get())
        messagebox.showinfo("Utilisateur", msg) if ok else messagebox.showwarning("Utilisateur", msg)
        if ok:
            username.set("")
            password.set("")
            self.load_users()

    def change_selected_role(self, role):
        user_id = self.selected_user_id()
        if user_id:
            self.db.update_user_role(user_id, role)
            self.load_users()

    def reset_selected_password(self):
        user_id = self.selected_user_id()
        if user_id:
            self.db.reset_user_password(user_id, "1234")
            messagebox.showinfo("Password", "Mot de passe reinitialise a 1234.")

    def delete_selected_user(self):
        user_id = self.selected_user_id()
        if user_id and messagebox.askyesno("Confirmation", "Supprimer cet utilisateur ?"):
            ok, msg = self.db.delete_user(user_id)
            messagebox.showinfo("Utilisateur", msg) if ok else messagebox.showwarning("Utilisateur", msg)
            self.load_users()

    def database_backup(self, parent):
        parent.columnconfigure(0, weight=1)
        ttk.Label(
            parent,
            text="Copie SQLite dans data/backups/. La restauration remplace la base active.",
            style="CardLabel.TLabel",
            wraplength=520,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        actions = ttk.Frame(parent, style="Card.TFrame")
        actions.grid(row=1, column=0, columnspan=2, sticky="ew")
        ttk.Button(actions, text="Creer une sauvegarde", command=self.create_backup).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Choisir emplacement...", command=self.create_backup_custom).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Restaurer une sauvegarde", command=self.restore_backup).pack(side="left")
        self.backup_list = ttk.Treeview(parent, columns=("name", "path"), show="headings", height=4)
        self.backup_list.heading("name", text="Fichier")
        self.backup_list.heading("path", text="Chemin")
        self.backup_list.column("name", width=220)
        self.backup_list.column("path", width=320)
        self.backup_list.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self.load_backup_list()

    def load_backup_list(self):
        if not self.backup_list:
            return
        for item in self.backup_list.get_children():
            self.backup_list.delete(item)
        for name, path, _mtime in self.db.list_backups():
            self.backup_list.insert("", tk.END, values=(name, path))

    def create_backup(self):
        try:
            path = self.db.create_backup()
            self.load_backup_list()
            messagebox.showinfo("Sauvegarde", f"Sauvegarde creee :\n{path}")
        except OSError as exc:
            messagebox.showerror("Sauvegarde", f"Impossible de creer la sauvegarde.\n{exc}")

    def create_backup_custom(self):
        path = filedialog.asksaveasfilename(
            title="Enregistrer la sauvegarde",
            defaultextension=".db",
            initialdir=BACKUP_DIR,
            filetypes=[("SQLite", "*.db"), ("Tous les fichiers", "*.*")],
        )
        if not path:
            return
        try:
            saved = self.db.backup_database(path)
            self.load_backup_list()
            messagebox.showinfo("Sauvegarde", f"Sauvegarde creee :\n{saved}")
        except OSError as exc:
            messagebox.showerror("Sauvegarde", f"Impossible de creer la sauvegarde.\n{exc}")

    def restore_backup(self):
        selected = self.backup_list.selection()
        initial = BACKUP_DIR
        path = None
        if selected:
            path = self.backup_list.item(selected[0], "values")[1]
        if not path:
            path = filedialog.askopenfilename(
                title="Restaurer une sauvegarde",
                initialdir=BACKUP_DIR,
                filetypes=[("SQLite", "*.db"), ("Tous les fichiers", "*.*")],
            )
        if not path or not os.path.isfile(path):
            return
        if not messagebox.askyesno(
            "Restauration",
            "Cette action remplace la base actuelle.\nContinuer ?",
        ):
            return
        try:
            self.db.restore_database(path)
            messagebox.showinfo("Restauration", "Base restauree. L'application va se recharger.")
            if self.restart_after_restore:
                self.restart_after_restore()
        except OSError as exc:
            messagebox.showerror("Restauration", f"Echec de la restauration.\n{exc}")

    def spa_information(self, parent):
        keys = [("spa_name", "Nom du spa"), ("spa_address", "Adresse"), ("spa_phone", "Telephone"), ("spa_email", "Email"), ("spa_footer", "Texte recu")]
        for row, (key, label) in enumerate(keys):
            self.labeled_entry(parent, label, self.setting_vars[key], row)
        ttk.Button(parent, text="Sauvegarder", command=lambda: self.save_settings([key for key, _ in keys])).grid(row=len(keys), column=1, sticky="e", pady=10)

    def working_hours(self, parent):
        keys = [("opening_hour", "Ouverture"), ("closing_hour", "Fermeture"), ("work_days", "Jours de travail"), ("holidays", "Vacances")]
        for row, (key, label) in enumerate(keys):
            self.labeled_entry(parent, label, self.setting_vars[key], row)
        ttk.Button(parent, text="Sauvegarder", command=lambda: self.save_settings([key for key, _ in keys])).grid(row=len(keys), column=1, sticky="e", pady=10)

    def appearance(self, parent):
        ttk.Label(parent, text="Mode", style="CardLabel.TLabel").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Combobox(parent, textvariable=self.theme_var, values=("dark", "light"), state="readonly").grid(row=0, column=1, sticky="ew", padx=(12, 0))
        parent.columnconfigure(1, weight=1)
        ttk.Button(parent, text="Appliquer", command=lambda: self.apply_preferences(theme=self.theme_var.get())).grid(row=1, column=1, sticky="e", pady=10)

    def profile_security(self, parent):
        old_user_pw = tk.StringVar()
        new_username = tk.StringVar()
        old_pw = tk.StringVar()
        new_pw = tk.StringVar()
        confirm = tk.StringVar()
        self.labeled_entry(parent, "Ancien mot de passe", old_user_pw, 0, show="*")
        self.labeled_entry(parent, "Nouveau username", new_username, 1)
        ttk.Button(parent, text="Changer username", command=lambda: self.change_username(old_user_pw, new_username)).grid(row=2, column=1, sticky="e", pady=8)
        self.labeled_entry(parent, "Ancien mot de passe", old_pw, 3, show="*")
        self.labeled_entry(parent, "Nouveau mot de passe", new_pw, 4, show="*")
        self.labeled_entry(parent, "Confirmer", confirm, 5, show="*")
        ttk.Button(parent, text="Changer password", command=lambda: self.change_password(old_pw, new_pw, confirm)).grid(row=6, column=1, sticky="e", pady=8)

    def save_settings(self, keys):
        for key in keys:
            self.db.set_setting(key, self.setting_vars[key].get())
        messagebox.showinfo("Parametres", "Parametres sauvegardes.")

    def change_username(self, old_password, new_username):
        ok, msg = self.db.change_username(self.current_user["id_user"], old_password.get(), new_username.get())
        messagebox.showinfo("Profil", msg) if ok else messagebox.showwarning("Profil", msg)
        if ok:
            self.apply_preferences()

    def change_password(self, old_pw, new_pw, confirm):
        if new_pw.get() != confirm.get():
            messagebox.showwarning("Profil", "Les mots de passe ne correspondent pas.")
            return
        ok, msg = self.db.change_password(self.current_user["id_user"], old_pw.get(), new_pw.get())
        messagebox.showinfo("Profil", msg) if ok else messagebox.showwarning("Profil", msg)
