import gc
import os
import tempfile
import unittest

from app.core.database import Database


class PaiementTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(os.path.join(self.temp_dir.name, "spa.db"))
        self.client_id = self.db.execute(
            "INSERT INTO client (nom, prenom, telephone, email, adresse, date_inscription) VALUES (?, ?, ?, ?, ?, ?)",
            ("Ali", "Ben", "0611111111", "", "", "2026-05-21"),
        )
        self.service_id = self.db.fetchone("SELECT id_service FROM service LIMIT 1")["id_service"]
        self.employee_id = self.db.execute(
            "INSERT INTO employe (nom, prenom, specialite, telephone, salaire, disponibilite) VALUES (?, ?, ?, ?, ?, ?)",
            ("Sara", "Spa", "Massage", "0622222222", 5000, "Available"),
        )

    def tearDown(self):
        del self.db
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except PermissionError:
            pass

    def _create_rdv(self, hour):
        return self.db.execute(
            "INSERT INTO rendez_vous (id_client, id_service, id_employe, date_rdv, heure_rdv, statut) VALUES (?, ?, ?, ?, ?, ?)",
            (self.client_id, self.service_id, self.employee_id, "2026-05-21", hour, "Confirme"),
        )

    def test_single_payment_multiple_rdv_links(self):
        rdv1 = self._create_rdv("10:00")
        rdv2 = self._create_rdv("11:00")
        paiement_id = self.db.execute(
            "INSERT INTO paiement (id_client, id_rdv, montant, methode_paiement, date_paiement) VALUES (?, ?, ?, ?, ?)",
            (self.client_id, rdv1, 700.0, "Cash", "2026-05-21"),
        )
        self.db.execute("INSERT INTO paiement_rdv (id_paiement, id_rdv) VALUES (?, ?)", (paiement_id, rdv1))
        self.db.execute("INSERT INTO paiement_rdv (id_paiement, id_rdv) VALUES (?, ?)", (paiement_id, rdv2))
        links = self.db.fetchall("SELECT id_rdv FROM paiement_rdv WHERE id_paiement=?", (paiement_id,))
        self.assertEqual(len(links), 2)


if __name__ == "__main__":
    unittest.main()
