import gc
import os
import tempfile
import unittest

from app.core.database import Database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_spa.db")
        self.db = Database(self.db_path)

    def tearDown(self):
        del self.db
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except PermissionError:
            pass

    def test_tables_created(self):
        tables = {row[0] for row in self.db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")}
        expected = {"client", "service", "employe", "rendez_vous", "paiement", "users", "app_settings", "paiement_rdv"}
        self.assertTrue(expected.issubset(tables))

    def test_seed_admin_user(self):
        user = self.db.fetchone("SELECT username, role FROM users WHERE username='admin'")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "Admin")

    def test_authenticate_admin(self):
        user = self.db.authenticate("admin", "admin", remember=False)
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "admin")

    def test_create_client(self):
        client_id = self.db.execute(
            "INSERT INTO client (nom, prenom, telephone, email, adresse, date_inscription) VALUES (?, ?, ?, ?, ?, ?)",
            ("Test", "Client", "0612345678", "test@spa.local", "Adresse", "2026-05-21"),
        )
        row = self.db.fetchone("SELECT nom FROM client WHERE id_client=?", (client_id,))
        self.assertEqual(row["nom"], "Test")

    def test_foreign_keys_enabled(self):
        with self.assertRaises(Exception):
            self.db.execute(
                "INSERT INTO rendez_vous (id_client, id_service, id_employe, date_rdv, heure_rdv, statut) VALUES (?, ?, ?, ?, ?, ?)",
                (9999, 1, 1, "2026-05-21", "10:00", "Confirme"),
            )


if __name__ == "__main__":
    unittest.main()
