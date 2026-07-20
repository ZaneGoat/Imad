# Tests — Gestion Spa

## Fichiers de test

| Fichier | Description |
|---------|-------------|
| `test_database.py` | Creation des tables, utilisateur admin, authentification, client, cles etrangeres |
| `test_backup.py` | Creation, restauration et liste des sauvegardes SQLite |
| `test_paiement.py` | Paiement unique lie a plusieurs rendez-vous (`paiement_rdv`) |

## Lancer les tests

Depuis la racine du projet :

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Ou :

```bash
python tests/run_tests.py
```

## Resultat attendu

Tous les tests doivent passer (`OK`) sans erreur.
