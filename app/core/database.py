import hashlib
import os
import shutil
import sqlite3
from datetime import date, datetime


class Database:
    """Small SQLite helper used by all application modules."""

    def __init__(self, db_name=None):
        if db_name is None:
            from app.config import DB_PATH, BACKUP_DIR, ensure_data_dirs

            ensure_data_dirs()
            db_name = DB_PATH
            self.backup_dir = BACKUP_DIR
        else:
            self.backup_dir = os.path.join(os.path.dirname(db_name), "backups")
            os.makedirs(self.backup_dir, exist_ok=True)
        self.db_name = db_name
        self.create_tables()
        self.migrate()
        self.seed_services()
        self.seed_users()

    def connect(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def execute(self, query, params=()):
        with self.connect() as conn:
            cur = conn.execute(query, params)
            conn.commit()
            return cur.lastrowid

    def fetchall(self, query, params=()):
        with self.connect() as conn:
            return conn.execute(query, params).fetchall()

    def fetchone(self, query, params=()):
        with self.connect() as conn:
            return conn.execute(query, params).fetchone()

    def create_tables(self):
        statements = [
            """
            CREATE TABLE IF NOT EXISTS client (
                id_client INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                telephone TEXT NOT NULL,
                email TEXT,
                adresse TEXT,
                date_inscription TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS service (
                id_service INTEGER PRIMARY KEY AUTOINCREMENT,
                nom_service TEXT NOT NULL,
                description TEXT,
                prix REAL NOT NULL,
                duree_minutes INTEGER NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS employe (
                id_employe INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                specialite TEXT,
                telephone TEXT,
                salaire REAL DEFAULT 0,
                disponibilite TEXT DEFAULT 'Available'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rendez_vous (
                id_rdv INTEGER PRIMARY KEY AUTOINCREMENT,
                id_client INTEGER NOT NULL,
                id_service INTEGER NOT NULL,
                id_employe INTEGER NOT NULL,
                date_rdv TEXT NOT NULL,
                heure_rdv TEXT NOT NULL,
                statut TEXT NOT NULL,
                FOREIGN KEY (id_client) REFERENCES client(id_client) ON DELETE CASCADE,
                FOREIGN KEY (id_service) REFERENCES service(id_service) ON DELETE CASCADE,
                FOREIGN KEY (id_employe) REFERENCES employe(id_employe) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS paiement (
                id_paiement INTEGER PRIMARY KEY AUTOINCREMENT,
                id_client INTEGER NOT NULL,
                id_rdv INTEGER NOT NULL,
                montant REAL NOT NULL,
                methode_paiement TEXT NOT NULL,
                date_paiement TEXT NOT NULL,
                FOREIGN KEY (id_client) REFERENCES client(id_client) ON DELETE CASCADE,
                FOREIGN KEY (id_rdv) REFERENCES rendez_vous(id_rdv) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
                id_user INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                remember_me INTEGER DEFAULT 0,
                theme TEXT DEFAULT 'dark',
                font_scale REAL DEFAULT 1.0,
                language TEXT DEFAULT 'French'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS paiement_rdv (
                id_paiement INTEGER NOT NULL,
                id_rdv INTEGER NOT NULL,
                PRIMARY KEY (id_paiement, id_rdv),
                FOREIGN KEY (id_paiement) REFERENCES paiement(id_paiement) ON DELETE CASCADE,
                FOREIGN KEY (id_rdv) REFERENCES rendez_vous(id_rdv) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """,
        ]
        with self.connect() as conn:
            for statement in statements:
                conn.execute(statement)
            conn.commit()

    def migrate(self):
        columns = [row["name"] for row in self.fetchall("PRAGMA table_info(employe)")]
        if "disponibilite" not in columns:
            self.execute("ALTER TABLE employe ADD COLUMN disponibilite TEXT DEFAULT 'Available'")
        user_columns = [row["name"] for row in self.fetchall("PRAGMA table_info(users)")]
        for name, ddl in {
            "theme": "ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'dark'",
            "font_scale": "ALTER TABLE users ADD COLUMN font_scale REAL DEFAULT 1.0",
            "language": "ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'French'",
        }.items():
            if name not in user_columns:
                self.execute(ddl)
        defaults = {
            "spa_name": "Gestion Spa",
            "spa_address": "Centre ville",
            "spa_phone": "0600000000",
            "spa_email": "contact@gestionspa.local",
            "spa_footer": "Merci pour votre visite",
            "opening_hour": "09:00",
            "closing_hour": "19:00",
            "work_days": "Lundi,Mardi,Mercredi,Jeudi,Vendredi,Samedi",
            "holidays": "",
            "salary_rules": "Salaire fixe mensuel",
            "default_duration": "60",
            "conflict_rules": "Bloquer les rendez-vous pour le meme employe au meme horaire",
            "appointment_alerts": "1",
            "payment_notifications": "1",
            "availability_alerts": "1",
        }
        for key, value in defaults.items():
            self.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)", (key, value))
        if not self.fetchone("SELECT name FROM sqlite_master WHERE type='table' AND name='paiement_rdv'"):
            self.execute(
                """
                CREATE TABLE paiement_rdv (
                    id_paiement INTEGER NOT NULL,
                    id_rdv INTEGER NOT NULL,
                    PRIMARY KEY (id_paiement, id_rdv),
                    FOREIGN KEY (id_paiement) REFERENCES paiement(id_paiement) ON DELETE CASCADE,
                    FOREIGN KEY (id_rdv) REFERENCES rendez_vous(id_rdv) ON DELETE CASCADE
                )
                """
            )
        existing_links = self.fetchone("SELECT COUNT(*) AS total FROM paiement_rdv")["total"]
        if not existing_links:
            for row in self.fetchall("SELECT id_paiement, id_rdv FROM paiement"):
                self.execute(
                    "INSERT OR IGNORE INTO paiement_rdv (id_paiement, id_rdv) VALUES (?, ?)",
                    (row["id_paiement"], row["id_rdv"]),
                )

    def seed_services(self):
        count = self.fetchone("SELECT COUNT(*) AS total FROM service")["total"]
        if count:
            return
        services = [
            ("Massage", "Massage relaxant complet", 350, 60),
            ("Sauna", "Seance sauna bien-etre", 150, 30),
            ("Hammam", "Hammam traditionnel", 200, 45),
            ("Facial", "Soin visage hydratant", 300, 50),
            ("Pedicure", "Soin pedicure professionnel", 180, 40),
        ]
        for service in services:
            self.execute(
                "INSERT INTO service (nom_service, description, prix, duree_minutes) VALUES (?, ?, ?, ?)",
                service,
            )

    def hash_password(self, password):
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def seed_users(self):
        count = self.fetchone("SELECT COUNT(*) AS total FROM users")["total"]
        if count:
            return
        users = [
            ("admin", self.hash_password("admin"), "Admin", 0, "dark", 1.0, "French"),
            ("reception", self.hash_password("reception"), "Receptionist", 0, "dark", 1.0, "French"),
        ]
        for user in users:
            self.execute(
                "INSERT INTO users (username, password, role, remember_me, theme, font_scale, language) VALUES (?, ?, ?, ?, ?, ?, ?)",
                user,
            )

    def authenticate(self, username, password, remember=False):
        user = self.fetchone("SELECT * FROM users WHERE username=?", (username,))
        if not user or user["password"] != self.hash_password(password):
            return None
        self.execute("UPDATE users SET remember_me=0")
        if remember:
            self.execute("UPDATE users SET remember_me=1 WHERE id_user=?", (user["id_user"],))
        return dict(user)

    def create_user(self, username, password, role):
        username = username.strip()
        role = role.strip()
        if self.fetchone("SELECT id_user FROM users WHERE username=?", (username,)):
            return False, "Ce nom d'utilisateur existe deja."
        self.execute(
            "INSERT INTO users (username, password, role, remember_me) VALUES (?, ?, ?, 0)",
            (username, self.hash_password(password), role),
        )
        return True, "Compte cree avec succes."

    def list_users(self):
        return self.fetchall("SELECT id_user, username, role, theme, font_scale, language FROM users ORDER BY username")

    def update_user_role(self, user_id, role):
        self.execute("UPDATE users SET role=? WHERE id_user=?", (role, user_id))

    def reset_user_password(self, user_id, password):
        self.execute("UPDATE users SET password=? WHERE id_user=?", (self.hash_password(password), user_id))

    def delete_user(self, user_id):
        count = self.fetchone("SELECT COUNT(*) AS total FROM users")["total"]
        if count <= 1:
            return False, "Impossible de supprimer le dernier utilisateur."
        self.execute("DELETE FROM users WHERE id_user=?", (user_id,))
        return True, "Utilisateur supprime."

    def change_username(self, user_id, old_password, new_username):
        user = self.fetchone("SELECT password FROM users WHERE id_user=?", (user_id,))
        if not user or user["password"] != self.hash_password(old_password):
            return False, "Ancien mot de passe incorrect."
        if self.fetchone("SELECT id_user FROM users WHERE username=? AND id_user<>?", (new_username, user_id)):
            return False, "Ce nom d'utilisateur existe deja."
        self.execute("UPDATE users SET username=? WHERE id_user=?", (new_username, user_id))
        return True, "Nom d'utilisateur modifie."

    def change_password(self, user_id, old_password, new_password):
        user = self.fetchone("SELECT password FROM users WHERE id_user=?", (user_id,))
        if not user or user["password"] != self.hash_password(old_password):
            return False, "Ancien mot de passe incorrect."
        self.execute("UPDATE users SET password=? WHERE id_user=?", (self.hash_password(new_password), user_id))
        return True, "Mot de passe modifie."

    def update_user_preferences(self, user_id, theme=None, font_scale=None, language=None):
        if theme is not None:
            self.execute("UPDATE users SET theme=? WHERE id_user=?", (theme, user_id))
        if font_scale is not None:
            self.execute("UPDATE users SET font_scale=? WHERE id_user=?", (font_scale, user_id))
        if language is not None:
            self.execute("UPDATE users SET language=? WHERE id_user=?", (language, user_id))

    def get_user(self, user_id):
        user = self.fetchone("SELECT * FROM users WHERE id_user=?", (user_id,))
        return dict(user) if user else None

    def get_setting(self, key, default=""):
        row = self.fetchone("SELECT value FROM app_settings WHERE key=?", (key,))
        return row["value"] if row else default

    def set_setting(self, key, value):
        self.execute(
            "INSERT INTO app_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value)),
        )

    def all_settings(self):
        return {row["key"]: row["value"] for row in self.fetchall("SELECT key, value FROM app_settings")}

    def backup_database(self, destination):
        os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)
        shutil.copy2(self.db_name, destination)
        return os.path.abspath(destination)

    def create_backup(self, destination=None):
        from app.config import BACKUP_DIR, ensure_data_dirs

        ensure_data_dirs()
        if destination is None:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            destination = os.path.join(BACKUP_DIR, f"spa_backup_{stamp}.db")
        return self.backup_database(destination)

    def list_backups(self):
        from app.config import BACKUP_DIR, ensure_data_dirs

        ensure_data_dirs()
        files = []
        for name in os.listdir(BACKUP_DIR):
            if name.endswith(".db"):
                path = os.path.join(BACKUP_DIR, name)
                files.append((name, path, os.path.getmtime(path)))
        return sorted(files, key=lambda item: item[2], reverse=True)

    def restore_database(self, source):
        if not os.path.isfile(source):
            raise FileNotFoundError(f"Backup introuvable : {source}")
        shutil.copy2(source, self.db_name)
        return os.path.abspath(self.db_name)

    def remembered_user(self):
        user = self.fetchone("SELECT * FROM users WHERE remember_me=1 LIMIT 1")
        return dict(user) if user else None

    def clear_remembered_users(self):
        self.execute("UPDATE users SET remember_me=0")

    def appointment_now_condition(self):
        return date.today().isoformat(), datetime.now().strftime("%H:%M")

    def employee_runtime_status(self, employee_id, manual_status):
        if manual_status == "Not Available":
            return "Not Available"
        today, now = self.appointment_now_condition()
        active_rows = self.fetchall(
            """
            SELECT r.heure_rdv
            FROM rendez_vous r
            WHERE r.id_employe=? AND r.date_rdv=?
              AND r.statut IN ('Confirme', 'Confirmé', 'En attente', 'En Service')
            """,
            (employee_id, today),
        )
        now_minutes = int(now[:2]) * 60 + int(now[3:])
        for row in active_rows:
            start = int(row["heure_rdv"][:2]) * 60 + int(row["heure_rdv"][3:])
            end = start + 180
            if start <= now_minutes < end:
                return "En Service"
        return "Available"

    def employees_with_availability(self, only_available=False):
        rows = self.fetchall("SELECT * FROM employe ORDER BY nom, prenom")
        result = []
        for row in rows:
            item = dict(row)
            status = self.employee_runtime_status(item["id_employe"], item.get("disponibilite") or "Available")
            item["status_runtime"] = status
            item["status_label"] = {
                "Available": "● Available",
                "En Service": "● En Service",
                "Not Available": "● Not Available",
            }.get(status, status)
            if only_available and status != "Available":
                continue
            result.append(item)
        return result

    def available_employee_count(self):
        return len(self.employees_with_availability(only_available=True))

    def most_requested_service(self):
        row = self.fetchone(
            """
            SELECT s.nom_service, COUNT(*) AS total
            FROM rendez_vous r
            JOIN service s ON s.id_service = r.id_service
            GROUP BY s.id_service
            ORDER BY total DESC
            LIMIT 1
            """
        )
        return row["nom_service"] if row else "Aucun"

    def dashboard_stats(self):
        today = date.today().isoformat()
        total_clients = self.fetchone("SELECT COUNT(*) AS total FROM client")["total"]
        total_employees = self.fetchone("SELECT COUNT(*) AS total FROM employe")["total"]
        appointments_today = self.fetchone(
            "SELECT COUNT(*) AS total FROM rendez_vous WHERE date_rdv = ?", (today,)
        )["total"]
        revenue_today = self.fetchone(
            "SELECT COALESCE(SUM(montant), 0) AS total FROM paiement WHERE date_paiement = ?",
            (today,),
        )["total"]
        return {
            "clients": total_clients,
            "employees": total_employees,
            "available_employees": self.available_employee_count(),
            "appointments_today": appointments_today,
            "revenue_today": revenue_today,
            "popular_service": self.most_requested_service(),
        }
