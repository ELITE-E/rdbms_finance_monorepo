"""
app/db_core.py

SimpleDB integration layer.

Step 1 responsibilities:
- Open the SimpleDB database from settings.DB_DIR
- Provide a global threading.Lock to serialize DB access
  (important because our DB is file-based and not designed for concurrent writes)
- Provide small helper functions execute()/execute_script() so later code does not
  spread DB access logic everywhere.
"""

from __future__ import annotations

import threading

from simpledb import Database

from . import settings

# One Database instance for the whole process
_DB = Database.open(settings.DB_DIR)

# Serialize DB calls (web servers can handle requests concurrently)
_DB_LOCK = threading.Lock()


def get_db() -> Database:
    """
    Return the global SimpleDB Database instance.

    Returns:
        Database: opened at settings.DB_DIR
    """
    return _DB


def execute(sql: str):
    """
    Execute a single SQL statement with locking.

    Args:
        sql: SQL string containing a single statement.

    Returns:
        CommandOk or QueryResult (from SimpleDB).
    """
    with _DB_LOCK:
        return _DB.execute(sql)


def execute_script(sql: str):
    """
    Execute a semicolon-separated SQL script with locking.

    Args:
        sql: SQL script containing one or more statements separated by ';'.

    Returns:
        List of CommandOk/QueryResult results.
    """
    with _DB_LOCK:
        return _DB.execute_script(sql)