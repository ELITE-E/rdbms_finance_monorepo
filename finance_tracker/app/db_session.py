import os
import threading
from pathlib import Path
from simpledb import Database

# 1. Look for the path set in the Dockerfile, otherwise default to local 'db' folder
db_path_env = os.getenv("DB_PATH", "./db")
DB_DIR = Path(db_path_env)

_db = None
db_lock = threading.Lock()

def get_db():
    global _db
    if _db is None:
        # Create the directory if it's missing (important for the first run)
        DB_DIR.mkdir(parents=True, exist_ok=True)
        _db = Database.open(DB_DIR)
    return _db