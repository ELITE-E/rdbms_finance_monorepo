import json

import pytest

from simpledb import Database
from simpledb.errors import ExecutionError


def test_create_table_persists_catalog(tmp_path):
    db = Database.open(tmp_path)

    db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL);")

    catalog_path = tmp_path / "catalog.json"
    assert catalog_path.exists()

    raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert "users" in raw["tables"]
    assert raw["tables"]["users"]["columns"][0]["name"] == "id"


def test_create_index_requires_table(tmp_path):
    db = Database.open(tmp_path)
    with pytest.raises(ExecutionError):
        db.execute("CREATE INDEX idx_email ON users(email);")


def test_create_index_requires_column(tmp_path):
    db = Database.open(tmp_path)
    db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(255));")
    with pytest.raises(ExecutionError):
        db.execute("CREATE INDEX idx_x ON users(nope);")


def test_duplicate_table_name_errors(tmp_path):
    db = Database.open(tmp_path)
    db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY);")
    with pytest.raises(ExecutionError):
        db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY);")


def test_only_one_primary_key_supported(tmp_path):
    db = Database.open(tmp_path)
    with pytest.raises(ExecutionError):
        db.execute("CREATE TABLE t (a INTEGER PRIMARY KEY, b INTEGER PRIMARY KEY);")