
"""
app/repos/categories_repo.py

Category repository: DB access for categories table.

Step 4 adds:
- rename_category()
- delete_category() with "blocked if referenced by any transaction"
- get_category_by_id_for_user() to enforce ownership
- category_is_used() helper
"""

from __future__ import annotations

from typing import Any

from simpledb import QueryResult

from ..db_core import execute
from ..sql import sql_literal


def _row_to_category(row: list[Any]) -> dict[str, Any]:
    """
    Convert SimpleDB row to a category dict.

    Expected SELECT order: id, user_id, name
    """
    return {"id": row[0], "user_id": row[1], "name": row[2]}


def list_categories_for_user(user_id: int) -> list[dict[str, Any]]:
    """
    List categories belonging to a user.

    Args:
        user_id: Owner user id.

    Returns:
        List of categories sorted by name (Python-side sorting).
    """
    res = execute(
        "SELECT id, user_id, name FROM categories "
        f"WHERE user_id = {sql_literal(int(user_id))};"
    )
    assert isinstance(res, QueryResult)

    cats = [_row_to_category(r) for r in res.rows]
    cats.sort(key=lambda c: (c["name"] or "").lower())
    return cats


def get_category_by_id_for_user(category_id: int, user_id: int) -> dict[str, Any] | None:
    """
    Fetch a category by id, but only if it belongs to the given user.

    Args:
        category_id: Category id.
        user_id: Owner user id.

    Returns:
        Category dict or None.
    """
    res = execute(
        "SELECT id, user_id, name FROM categories "
        f"WHERE id = {sql_literal(int(category_id))} AND user_id = {sql_literal(int(user_id))};"
    )
    assert isinstance(res, QueryResult)
    if not res.rows:
        return None
    return _row_to_category(res.rows[0])


def get_category_by_name_for_user(name: str, user_id: int) -> dict[str, Any] | None:
    """
    Check if a category with the same name exists for a user.

    Args:
        name: Category name.
        user_id: Owner user id.

    Returns:
        Category dict or None.
    """
    res = execute(
        "SELECT id, user_id, name FROM categories "
        f"WHERE user_id = {sql_literal(int(user_id))} AND name = {sql_literal(name)};"
    )
    assert isinstance(res, QueryResult)

    if not res.rows:
        return None
    return _row_to_category(res.rows[0])


def next_category_id() -> int:
    """
    Generate next categories.id as max(id)+1.

    Returns:
        Next integer id.
    """
    res = execute("SELECT id FROM categories;")
    assert isinstance(res, QueryResult)

    max_id = 0
    for row in res.rows:
        if row and isinstance(row[0], int):
            max_id = max(max_id, row[0])
    return max_id + 1


def create_category(*, user_id: int, name: str) -> int:
    """
    Create a new category.

    Args:
        user_id: Owner user id.
        name: Category name.

    Returns:
        New category id.

    Raises:
        ValueError: if name already exists for the user.
    """
    existing = get_category_by_name_for_user(name, user_id)
    if existing is not None:
        raise ValueError("Category name already exists.")

    category_id = next_category_id()
    execute(
        "INSERT INTO categories (id, user_id, name) VALUES "
        f"({sql_literal(category_id)}, {sql_literal(int(user_id))}, {sql_literal(name)});"
    )
    return category_id


def rename_category(*, category_id: int, user_id: int, new_name: str) -> None:
    """
    Rename an existing category owned by a user.

    Args:
        category_id: Category id.
        user_id: Owner user id.
        new_name: New category name.

    Raises:
        ValueError: if not found, or name conflicts with another category.
    """
    cat = get_category_by_id_for_user(category_id, user_id)
    if cat is None:
        raise ValueError("Category not found.")

    conflict = get_category_by_name_for_user(new_name, user_id)
    if conflict is not None and int(conflict["id"]) != int(category_id):
        raise ValueError("Another category with that name already exists.")

    execute(
        "UPDATE categories SET name = "
        f"{sql_literal(new_name)} WHERE id = {sql_literal(int(category_id))};"
    )


def category_is_used(category_id: int) -> bool:
    """
    Check whether any transaction references this category.

    Args:
        category_id: Category id.

    Returns:
        True if used, otherwise False.
    """
    res = execute(
        f"SELECT id FROM transactions WHERE category_id = {sql_literal(int(category_id))};"
    )
    assert isinstance(res, QueryResult)
    return len(res.rows) > 0


def delete_category(*, category_id: int, user_id: int) -> None:
    """
    Delete a category owned by a user if it isn't referenced by any transaction.

    Args:
        category_id: Category id.
        user_id: Owner user id.

    Raises:
        ValueError: if not found or if category is used by transactions.
    """
    cat = get_category_by_id_for_user(category_id, user_id)
    if cat is None:
        raise ValueError("Category not found.")

    if category_is_used(category_id):
        raise ValueError("Cannot delete: this category has transactions.")

    execute(f"DELETE FROM categories WHERE id = {sql_literal(int(category_id))};")