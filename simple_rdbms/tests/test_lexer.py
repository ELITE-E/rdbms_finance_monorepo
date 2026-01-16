import pytest

from simpledb.lexer import TokenType, tokenize
from simpledb.errors import SqlSyntaxError


def test_tokenize_create_table_smoke():
    sql = "CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(255) UNIQUE);"
    tokens = tokenize(sql)
    types = [t.typ for t in tokens]

    assert TokenType.CREATE in types
    assert TokenType.TABLE in types
    assert TokenType.IDENT in types  # users, id, INTEGER, email, VARCHAR, etc.
    assert TokenType.LPAREN in types
    assert TokenType.RPAREN in types
    assert TokenType.SEMI in types
    assert types[-1] == TokenType.EOF


def test_tokenize_select_join_where_and():
    sql = """
    SELECT * FROM t1
    JOIN t2 ON t1.id = t2.t1_id
    WHERE t1.id = 1 AND t2.ok = true;
    """
    tokens = tokenize(sql)
    types = [t.typ for t in tokens]

    assert TokenType.SELECT in types
    assert TokenType.JOIN in types
    assert TokenType.ON in types
    assert TokenType.WHERE in types
    assert TokenType.AND in types
    assert TokenType.INT in types
    assert TokenType.BOOL in types


def test_unterminated_string_raises():
    with pytest.raises(SqlSyntaxError):
        tokenize("INSERT INTO t (name) VALUES ('oops);")