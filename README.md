# Gestion Spa

Application de bureau pour la gestion d'un spa : clients, services, employes, rendez-vous, paiements et rapports. Interface graphique **Tkinter**, donnees stockees dans **SQLite**.

## Introduction

Gestion Spa permet a l'equipe d'accueil et a l'administrateur de suivre l'activite quotidienne du centre : reservations, encaissements, disponibilite du personnel et statistiques mensuelles. L'application fonctionne en local, sans serveur web.

## Lancer l'application

1. Installer **Python 3.10+** (avec support **tkinter** sur Windows).
2. (Optionnel) Creer un environnement virtuel et installer les dependances de test :

```bash
pip install -r requirements.txt
```

3. Depuis la racine du projet :

```bash
python main.py
```

## Compte administrateur par defaut

| Champ | Valeur |
|-------|--------|
| Utilisateur | `admin` |
| Mot de passe | `admin` |

Un compte reception est aussi cree : `reception` / `reception`.

## Sauvegarde et restauration (Admin → Parametres)

La base SQLite est dans `data/database/spa.db`.

- **Creer une sauvegarde** : copie automatique dans `data/backups/` (nom horodate `spa_backup_AAAAMMJJ_HHMMSS.db`).
- **Restaurer** : selectionner un fichier `.db` ; la base active est remplacee puis l'application se recharge.

Les sauvegardes protègent contre la perte de donnees avant une mise a jour ou une manipulation importante.

## Base SQLite — relations principales

```
client (1) ──< rendez_vous >── (1) service
                │
                ├── employe
                │
paiement (1) ──< paiement_rdv >── (N) rendez_vous
     │
     └── client
```

| Table | Role |
|-------|------|
| `client` | Fiches clients |
| `service` | Catalogue (prix, duree) |
| `employe` | Personnel et disponibilite |
| `rendez_vous` | Reservations (date, heure, statut) |
| `paiement` | Encaissement (montant, methode, date) |
| `paiement_rdv` | Lien plusieurs RDV → un paiement |
| `users` | Comptes Admin / Receptionist |
| `app_settings` | Parametres spa (nom, horaires, etc.) |

## Architecture

```
gp/
├── main.py                 # Point d'entree Tkinter
├── requirements.txt
├── README.md
├── app/
│   ├── config.py           # Chemins data/, backups/, pdf/
│   ├── core/
│   │   └── database.py     # SQLite, migrations, sauvegarde
│   ├── ui/                 # Ecrans (auth, dashboard, CRUD, rapports, parametres)
│   └── utils/
│       └── pdf_utils.py    # Generation PDF (recus, rapports)
├── data/
│   ├── database/spa.db
│   ├── backups/
│   └── pdf/
└── tests/
    ├── test_database.py
    ├── test_backup.py
    ├── test_paiement.py
    ├── run_tests.py
    └── TESTS.md
```

- **Presentation** : `app/ui/*` (frames Tkinter + `ui_utils`)
- **Metier / donnees** : `app/core/database.py`
- **Transverse** : `app/config.py`, `app/utils/pdf_utils.py`

## Tests

Voir `tests/TESTS.md` pour la liste detaillee.

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Roles

| Role | Acces |
|------|--------|
| **Admin** | Toutes les pages + rapports + sauvegarde |
| **Receptionist** | Dashboard, clients, rendez-vous, paiements, profil |
