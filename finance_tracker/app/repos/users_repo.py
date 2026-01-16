"""
app/repos/users_repo.py

User repository: DB access for users table.

Step 2 responsibilities:
- Create user records (registration)
- Lookup users for authentication (login)
- Generate new user ids (SimpleDB doesn't auto-increment)

Implementation notes:
- Because our DB access is serialized by a global lock, max(id)+1 is safe enough
  for this demo app.
"""

from __future__ import annotations

from typing import Any

from simpledb import QueryResult

from ..db_core import execute
from ..sql import sql_literal


def _row_to_user(row: list[Any]) -> dict[str, Any]:
    """
    Convert a SimpleDB row to a user dict.

    Expected order: id, username, email, password_hash
    """
    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "password_hash": row[3],
    }


def get_user_by_email(email: str) -> dict[str, Any] | None:
    """
    Fetch user by email.

    Args:
        email: Email.

    Returns:
        User dict or None.
    """
    res = execute(
        "SELECT id, username, email, password_hash FROM users "
        f"WHERE email = {sql_literal(email)};"
    )
    assert isinstance(res, QueryResult)
    if not res.rows:
        return None
    return _row_to_user(res.rows[0])


def get_user_by_username(username: str) -> dict[str, Any] | None:
    """
    Fetch user by username.

    Args:
        username: Username.

    Returns:
        User dict or None.
    """
    res = execute(
        "SELECT id, username, email, password_hash FROM users "
        f"WHERE username = {sql_literal(username)};"
    )
    assert isinstance(res, QueryResult)
    if not res.rows:
        return None
    return _row_to_user(res.rows[0])


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    """
    Fetch user by id.

    Args:
        user_id: Integer user id.

    Returns:
        User dict or None.
    """
    res = execute(
        "SELECT id, username, email, password_hash FROM users "
        f"WHERE id = {sql_literal(int(user_id))};"
    )
    assert isinstance(res, QueryResult)
    if not res.rows:
        return None
    return _row_to_user(res.rows[0])


def next_user_id() -> int:
    """
    Compute next user id as max(id)+1.

    Returns:
        Next id.
    """
    res = execute("SELECT id FROM users;")
    assert isinstance(res, QueryResult)
    max_id = 0
    for row in res.rows:
        if row and isinstance(row[0], int):
            max_id = max(max_id, row[0])
    return max_id + 1


def create_user(*, username: str, email: str, password_hash: str) -> int:
    """
    Create a new user.

    Args:
        username: Unique username.
        email: Unique email.
        password_hash: Hashed password.

    Returns:
        New user id.
    """
    user_id = next_user_id()
    execute(
        "INSERT INTO users (id, username, email, password_hash) VALUES "
        f"({sql_literal(user_id)}, {sql_literal(username)}, {sql_literal(email)}, {sql_literal(password_hash)});"
    )
    return user_id