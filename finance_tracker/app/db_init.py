"""
app/db_init.py

Database schema initialization.

Step 1 responsibilities:
- Ensure required tables exist (users, categories, transactions)
- Ensure basic indexes exist to support later steps
- Be idempotent: safe to call on every startup

We rely on db.catalog checks so we don't crash on re-runs.
"""

from __future__ import annotations

from simpledb import Database

from .db_core import execute


def init_db(db: Database) -> None:
    """
    Initialize database schema (idempotent).

    Args:
        db: SimpleDB Database instance (used to inspect catalog state).
    """
    # ---- Tables ----
    # Note: We create all tables now as part of "foundation".
    # This does NOT implement features yet; it just prepares storage.

    if "users" not in db.catalog.tables:
        execute(
            """
            CREATE TABLE users (
              id INTEGER PRIMARY KEY,
              username VARCHAR(32) UNIQUE NOT NULL,
              email VARCHAR(255) UNIQUE NOT NULL,
              password_hash TEXT NOT NULL
            );
            """.strip()
        )

    if "categories" not in db.catalog.tables:
        execute(
            """
            CREATE TABLE categories (
              id INTEGER PRIMARY KEY,
              user_id INTEGER NOT NULL,
              name VARCHAR(50) NOT NULL
            );
            """.strip()
        )

    if "transactions" not in db.catalog.tables:
        execute(
            """
            CREATE TABLE transactions (
              id INTEGER PRIMARY KEY,
              user_id INTEGER NOT NULL,
              category_id INTEGER NOT NULL,
              amount_cents INTEGER NOT NULL,
              type VARCHAR(7) NOT NULL,
              description TEXT,
              date DATE NOT NULL,
              ym VARCHAR(7) NOT NULL
            );
            """.strip()
        )

    # ---- Indexes ----
    # SimpleDB supports single-column indexes. These help common equality lookups.

    indexes = db.catalog.indexes

    if "idx_users_email" not in indexes:
        execute("CREATE INDEX idx_users_email ON users(email);")

    if "idx_users_username" not in indexes:
        execute("CREATE INDEX idx_users_username ON users(username);")

    if "idx_categories_user" not in indexes:
        execute("CREATE INDEX idx_categories_user ON categories(user_id);")

    if "idx_tx_user" not in indexes:
        execute("CREATE INDEX idx_tx_user ON transactions(user_id);")

    if "idx_tx_ym" not in indexes:
        execute("CREATE INDEX idx_tx_ym ON transactions(ym);")

    if "idx_tx_category" not in indexes:
        execute("CREATE INDEX idx_tx_category ON transactions(category_id);")