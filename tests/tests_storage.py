import pytest

from simpledb import Database
from simpledb.errors import ExecutionError
from simpledb.result import QueryResult


def test_insert_and_select_star(tmp_path):
    db = Database.open(tmp_path)
    db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(255));")

    db.execute("INSERT INTO users (id, email) VALUES (1, 'a@b.com');")
    db.execute("INSERT INTO users (id, email) VALUES (2, 'c@d.com');")

    res = db.execute("SELECT * FROM users;")
    assert isinstance(res, QueryResult)
    assert res.columns == ["id", "email"]
    assert res.rows == [
        [1, "a@b.com"],
        [2, "c@d.com"],
    ]


def test_select_where_and(tmp_path):
    db = Database.open(tmp_path)
    db.execute("CREATE TABLE t (a INTEGER, b BOOLEAN, name VARCHAR(10));")

    db.execute("INSERT INTO t (a, b, name) VALUES (1, true, 'x');")
    db.execute("INSERT INTO t (a, b, name) VALUES (1, false, 'y');")
    db.execute("INSERT INTO t (a, b, name) VALUES (2, true, 'z');")

    res = db.execute("SELECT name FROM t WHERE a = 1 AND b = true;")
    assert res.columns == ["name"]
    assert res.rows == [["x"]]


def test_insert_unknown_column_errors(tmp_path):
    db = Database.open(tmp_path)
    db.execute("CREATE TABLE users (id INTEGER, email VARCHAR(255));")
    with pytest.raises(ExecutionError):
        db.execute("INSERT INTO users (id, nope) VALUES (1, 'x');")


def test_select_unknown_column_errors(tmp_path):
    db = Database.open(tmp_path)
    db.execute("CREATE TABLE users (id INTEGER, email VARCHAR(255));")
    with pytest.raises(ExecutionError):
        db.execute("SELECT nope FROM users;")


def test_basic_type_validation_integer(tmp_path):
    db = Database.open(tmp_path)
    db.execute("CREATE TABLE t (a INTEGER);")
    with pytest.raises(ExecutionError):
        db.execute("INSERT INTO t (a) VALUES ('not-int');")