"""
app/sql.py

SQL string helpers for safely building SQL for SimpleDB.

Why needed:
- SimpleDB doesn't support parameterized queries yet.
- Therefore we must escape string literals ourselves to avoid syntax errors and
  reduce risk of basic SQL injection.

Rules we follow:
- User input is only inserted as *literals* (never as table/column identifiers).
- We escape single quotes in strings by doubling them: O'Reilly -> O''Reilly
"""

from __future__ import annotations

from typing import Any


def sql_escape_string(value: str) -> str:
    """
    Escape a Python string for safe inclusion in a SQL single-quoted literal.

    Args:
        value: Raw string.

    Returns:
        Escaped string WITHOUT surrounding quotes.

    Example:
        "O'Reilly" -> "O''Reilly"
    """
    return value.replace("'", "''")


def sql_literal(value: Any) -> str:
    """
    Convert a Python value into a SQL literal string.

    Args:
        value: int | str | bool | None

    Returns:
        SQL literal string, e.g.:
          123
          'hello'
          true
          NULL

    Raises:
        TypeError if unsupported type.
    """
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        return "'" + sql_escape_string(value) + "'"
    raise TypeError(f"Unsupported literal type: {type(value).__name__}")