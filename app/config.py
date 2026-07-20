import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
DB_DIR = os.path.join(DATA_DIR, "database")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
PDF_DIR = os.path.join(DATA_DIR, "pdf")
DB_PATH = os.path.join(DB_DIR, "spa.db")


def ensure_data_dirs():
    for folder in (DB_DIR, BACKUP_DIR, PDF_DIR):
        os.makedirs(folder, exist_ok=True)
