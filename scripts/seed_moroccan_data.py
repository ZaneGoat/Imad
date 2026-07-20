from random import choice, randint, randrange
from datetime import datetime, timedelta
import os

from app.core.database import Database


def random_moroccan_phone():
    # Moroccan mobile numbers typically start with 06 or 07 followed by 8 digits
    prefix = choice(["06", "07"])
    return prefix + "".join(str(randint(0, 9)) for _ in range(8))


def random_date_within(days_back=365):
    past = datetime.now() - timedelta(days=days_back)
    delta = datetime.now() - past
    rand_days = randrange(delta.days + 1)
    dt = past + timedelta(days=rand_days)
    return dt.date().isoformat()


def random_time_slot():
    hour = randint(9, 18)
    minute = choice(["00", "15", "30", "45"])
    return f"{hour:02d}:{minute}"


def seed(db: Database, n_clients=50, n_employees=10, n_appointments=120, payment_rate=0.65):
    # Minimal offline name lists to avoid external dependencies
    first_names = [
        "Mohamed", "Youssef", "Hicham", "Ilyas", "Ahmed", "Rachid", "Said", "Yassine", "Karim", "Nabil",
        "Fatima", "Khadija", "Aicha", "Imane", "Najat", "Sana", "Salma", "Laila",
    ]
    last_names = [
        "El Idrissi", "Ben Ali", "Khoury", "El Amrani", "Rami", "Bouazizi", "Aziz", "Othmani", "Bensalem",
        "Ziani",
    ]
    # Cities commonly used in Morocco
    cities = ["Casablanca", "Rabat", "Marrakech", "Fes", "Tanger", "Agadir"]

    print("Seeding clients...")
    client_ids = []
    for _ in range(n_clients):
        prenom = choice(first_names)
        nom = choice(last_names)
        telephone = random_moroccan_phone()
        email = f"{prenom.lower()}.{nom.lower().replace(' ', '')}{randint(1,99)}@example.com"
        adresse = f"{randint(1,200)} Rue Principale, {choice(cities)}"
        date_inscription = random_date_within(800)
        cid = db.execute(
            "INSERT INTO client (nom, prenom, telephone, email, adresse, date_inscription) VALUES (?, ?, ?, ?, ?, ?)",
            (nom, prenom, telephone, email, adresse, date_inscription),
        )
        client_ids.append(cid)

    print("Seeding employees...")
    specialities = ["Massage", "Hammam", "Esthetique", "Therapie", "Reception"]
    employee_ids = []
    for _ in range(n_employees):
        prenom = choice(first_names)
        nom = choice(last_names)
        specialite = choice(specialities)
        telephone = random_moroccan_phone()
        salaire = round(randint(3000, 15000) + randint(0, 99) / 100.0, 2)
        disponibilite = choice(["Available", "Not Available"])
        eid = db.execute(
            "INSERT INTO employe (nom, prenom, specialite, telephone, salaire, disponibilite) VALUES (?, ?, ?, ?, ?, ?)",
            (nom, prenom, specialite, telephone, salaire, disponibilite),
        )
        employee_ids.append(eid)

    services = [row["id_service"] for row in db.fetchall("SELECT id_service FROM service")]
    if not services:
        raise RuntimeError("No services found — ensure the DB has services seeded.")

    print("Seeding appointments and payments...")
    appointment_ids = []
    statuses = ["Confirme", "En attente", "Annule"]
    payment_methods = ["Espèces", "Carte Bancaire", "Virement"]
    for _ in range(n_appointments):
        cid = choice(client_ids)
        sid = choice(services)
        eid = choice(employee_ids)
        # allow some appointments in the future and some in the past
        date_rdv = (datetime.now() + timedelta(days=randint(-30, 30))).date().isoformat()
        heure_rdv = random_time_slot()
        statut = choice(statuses)
        rdv_id = db.execute(
            "INSERT INTO rendez_vous (id_client, id_service, id_employe, date_rdv, heure_rdv, statut) VALUES (?, ?, ?, ?, ?, ?)",
            (cid, sid, eid, date_rdv, heure_rdv, statut),
        )
        appointment_ids.append(rdv_id)

        # maybe create a payment
        if (randint(0, 100) / 100.0) <= payment_rate:
            # get service price to determine payment amount
            row = db.fetchone("SELECT prix FROM service WHERE id_service=?", (sid,))
            montant = float(row["prix"]) if row else round(randint(100, 800), 2)
            methode = choice(payment_methods)
            date_paiement = date_rdv if randint(0, 1) else random_date_within(30)
            pid = db.execute(
                "INSERT INTO paiement (id_client, id_rdv, montant, methode_paiement, date_paiement) VALUES (?, ?, ?, ?, ?)",
                (cid, rdv_id, montant, methode, date_paiement),
            )
            # keep paiement_rdv mapping consistent
            db.execute("INSERT OR IGNORE INTO paiement_rdv (id_paiement, id_rdv) VALUES (?, ?)", (pid, rdv_id))

    print(f"Done: {len(client_ids)} clients, {len(employee_ids)} employees, {len(appointment_ids)} appointments seeded.")


if __name__ == "__main__":
    # Use the app's default DB
    db = Database()
    seed(db)
