import pytest

from simpledb.ast import CreateIndex, CreateTable, Delete, Insert, Select, Update
from simpledb.errors import SqlSyntaxError
from simpledb.parser import parse_sql


def test_parse_create_table():
    stmt = parse_sql(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL);"
    )
    assert isinstance(stmt, CreateTable)
    assert stmt.table_name == "users"
    assert stmt.columns[0].name == "id"
    assert stmt.columns[0].typ.name == "INTEGER"
    assert stmt.columns[0].primary_key is True
    assert stmt.columns[1].name == "email"
    assert stmt.columns[1].typ.name == "VARCHAR"
    assert stmt.columns[1].typ.params == [255]
    assert stmt.columns[1].unique is True
    assert stmt.columns[1].not_null is True


def test_parse_create_index():
    stmt = parse_sql("CREATE INDEX idx_email ON users(email);")
    assert isinstance(stmt, CreateIndex)
    assert stmt.index_name == "idx_email"
    assert stmt.table_name == "users"
    assert stmt.column_name == "email"
import pytest

from simpledb.ast import CreateIndex, CreateTable, Delete, Insert, Select, Update
from simpledb.errors import SqlSyntaxError
from simpledb.parser import parse_sql


def test_parse_create_table():
    stmt = parse_sql(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL);"
    )
    assert isinstance(stmt, CreateTable)
    assert stmt.table_name == "users"
    assert stmt.columns[0].name == "id"
    assert stmt.columns[0].typ.name == "INTEGER"
    assert stmt.columns[0].primary_key is True
    assert stmt.columns[1].name == "email"
    assert stmt.columns[1].typ.name == "VARCHAR"
    assert stmt.columns[1].typ.params == [255]
    assert stmt.columns[1].unique is True
    assert stmt.columns[1].not_null is True


def test_parse_create_index():
    stmt = parse_sql("CREATE INDEX idx_email ON users(email);")
    assert isinstance(stmt, CreateIndex)
    assert stmt.index_name == "idx_email"
    assert stmt.table_name == "users"
    assert stmt.column_name == "email"


def test_parse_insert():
    stmt = parse_sql("INSERT INTO users (id, email) VALUES (1, 'a@b.com');")
    assert isinstance(stmt, Insert)
    assert stmt.table_name == "users"
    assert stmt.columns == ["id", "email"]
    assert stmt.values == [1, "a@b.com"]


def test_parse_select_join_where():
    stmt = parse_sql(
        "SELECT transactions.id, categories.name "
        "FROM transactions "
        "JOIN categories ON transactions.category_id = categories.id "
        "WHERE transactions.user_id = 1 AND categories.name = 'Groceries';"
    )
    assert isinstance(stmt, Select)
    assert stmt.columns is not None
    assert stmt.from_table == "transactions"
    assert len(stmt.joins) == 1
    assert stmt.where is not None
    assert len(stmt.where.conditions) == 2


def test_parse_update():
    stmt = parse_sql("UPDATE users SET email = 'x@y.com' WHERE id = 1;")
    assert isinstance(stmt, Update)
    assert stmt.table_name == "users"
    assert stmt.assignments[0].column == "email"
    assert stmt.assignments[0].value == "x@y.com"
    assert stmt.where is not None


def test_parse_delete():
    stmt = parse_sql("DELETE FROM users WHERE id = 1;")
    assert isinstance(stmt, Delete)
    assert stmt.table_name == "users"
    assert stmt.where is not None


def test_parse_errors_on_missing_paren():
    with pytest.raises(SqlSyntaxError):
        parse_sql("CREATE TABLE t (id INTEGER;")

def test_parse_insert():
    stmt = parse_sql("INSERT INTO users (id, email) VALUES (1, 'a@b.com');")
    assert isinstance(stmt, Insert)
    assert stmt.table_name == "users"
    assert stmt.columns == ["id", "email"]
    assert stmt.values == [1, "a@b.com"]


def test_parse_select_join_where():
    stmt = parse_sql(
        "SELECT transactions.id, categories.name "
        "FROM transactions "
        "JOIN categories ON transactions.category_id = categories.id "
        "WHERE transactions.user_id = 1 AND categories.name = 'Groceries';"
    )
    assert isinstance(stmt, Select)
    assert stmt.columns is not None
    assert stmt.from_table == "transactions"
    assert len(stmt.joins) == 1
    assert stmt.where is not None
    assert len(stmt.where.conditions) == 2


def test_parse_update():
    stmt = parse_sql("UPDATE users SET email = 'x@y.com' WHERE id = 1;")
    assert isinstance(stmt, Update)
    assert stmt.table_name == "users"
    assert stmt.assignments[0].column == "email"
    assert stmt.assignments[0].value == "x@y.com"
    assert stmt.where is not None


def test_parse_delete():
    stmt = parse_sql("DELETE FROM users WHERE id = 1;")
    assert isinstance(stmt, Delete)
    assert stmt.table_name == "users"
    assert stmt.where is not None


def test_parse_errors_on_missing_paren():
    with pytest.raises(SqlSyntaxError):
        parse_sql("CREATE TABLE t (id INTEGER;")