import gc
import os
import tempfile
import unittest

from app.core.database import Database


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "spa.db")
        self.db = Database(self.db_path)
        self.db.execute(
            "INSERT INTO client (nom, prenom, telephone, email, adresse, date_inscription) VALUES (?, ?, ?, ?, ?, ?)",
            ("Backup", "User", "0600000001", "", "", "2026-05-21"),
        )

    def tearDown(self):
        del self.db
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except PermissionError:
            pass

    def test_create_and_restore_backup(self):
        backup_path = self.db.create_backup(os.path.join(self.temp_dir.name, "backup.db"))
        self.assertTrue(os.path.isfile(backup_path))

        self.db.execute("DELETE FROM client")
        self.assertEqual(self.db.fetchone("SELECT COUNT(*) AS total FROM client")["total"], 0)

        self.db.restore_database(backup_path)
        self.assertEqual(self.db.fetchone("SELECT COUNT(*) AS total FROM client")["total"], 1)

    def test_list_backups_in_data_folder(self):
        from app.config import ensure_data_dirs

        ensure_data_dirs()
        before = len(self.db.list_backups())
        path = self.db.create_backup()
        self.assertTrue(os.path.isfile(path))
        self.assertEqual(len(self.db.list_backups()), before + 1)


if __name__ == "__main__":
    unittest.main()
