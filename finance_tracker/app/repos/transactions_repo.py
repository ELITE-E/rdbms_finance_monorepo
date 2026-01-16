"""
app/repos/transactions_repo.py

Transaction repository: DB access for transactions table.

Step 7 adds:
- get_transaction_by_id_for_user()
- update_transaction_for_user()
- delete_transaction_for_user()

Notes:
- Ownership enforced by WHERE user_id = current_user
- Amount stored as integer cents; date stored as 'YYYY-MM-DD'; ym is 'YYYY-MM'
"""

from __future__ import annotations

from typing import Any

from simpledb import QueryResult

from ..db_core import execute
from ..sql import sql_literal


def next_transaction_id() -> int:
    res = execute("SELECT id FROM transactions;")
    assert isinstance(res, QueryResult)
    max_id = 0
    for row in res.rows:
        if row and isinstance(row[0], int):
            max_id = max(max_id, row[0])
    return max_id + 1


def create_transaction(
    *,
    user_id: int,
    category_id: int,
    amount_cents: int,
    tx_type: str,
    description: str | None,
    date: str,
    ym: str,
) -> int:
    tx_id = next_transaction_id()
    execute(
        "INSERT INTO transactions (id, user_id, category_id, amount_cents, type, description, date, ym) VALUES "
        f"({sql_literal(tx_id)}, {sql_literal(int(user_id))}, {sql_literal(int(category_id))}, "
        f"{sql_literal(int(amount_cents))}, {sql_literal(tx_type)}, {sql_literal(description)}, "
        f"{sql_literal(date)}, {sql_literal(ym)});"
    )
    return tx_id


def list_transactions_for_user(user_id: int, ym: str | None = None) -> list[dict[str, Any]]:
    if ym is None or ym.strip() == "":
        where = f"WHERE transactions.user_id = {sql_literal(int(user_id))}"
    else:
        where = (
            f"WHERE transactions.user_id = {sql_literal(int(user_id))} "
            f"AND transactions.ym = {sql_literal(ym)}"
        )

    sql = (
        "SELECT transactions.id, transactions.date, transactions.ym, transactions.type, "
        "transactions.amount_cents, transactions.description, "
        "transactions.category_id, categories.name "
        "FROM transactions "
        "JOIN categories ON transactions.category_id = categories.id "
        f"{where};"
    )

    res = execute(sql)
    assert isinstance(res, QueryResult)

    out: list[dict[str, Any]] = []
    for r in res.rows:
        out.append(
            {
                "id": r[0],
                "date": r[1],
                "ym": r[2],
                "type": r[3],
                "amount_cents": r[4],
                "description": r[5],
                "category_id": r[6],
                "category_name": r[7],
            }
        )

    out.sort(key=lambda x: (x["date"] or "", x["id"] or 0), reverse=True)
    return out


def get_transaction_by_id_for_user(tx_id: int, user_id: int) -> dict[str, Any] | None:
    """
    Fetch a transaction by id only if it belongs to the user.

    Args:
        tx_id: Transaction id.
        user_id: Owner user id.

    Returns:
        Transaction dict or None.
    """
    res = execute(
        "SELECT id, user_id, category_id, amount_cents, type, description, date, ym "
        "FROM transactions "
        f"WHERE id = {sql_literal(int(tx_id))} AND user_id = {sql_literal(int(user_id))};"
    )
    assert isinstance(res, QueryResult)
    if not res.rows:
        return None

    r = res.rows[0]
    return {
        "id": r[0],
        "user_id": r[1],
        "category_id": r[2],
        "amount_cents": r[3],
        "type": r[4],
        "description": r[5],
        "date": r[6],
        "ym": r[7],
    }


def update_transaction_for_user(
    *,
    tx_id: int,
    user_id: int,
    category_id: int,
    amount_cents: int,
    tx_type: str,
    description: str | None,
    date: str,
    ym: str,
) -> None:
    """
    Update a transaction owned by the user.

    Args:
        tx_id: Transaction id.
        user_id: Owner user id (ownership enforcement).
        category_id: New category id.
        amount_cents: New amount in cents.
        tx_type: 'income' or 'expense'
        description: Optional description.
        date: 'YYYY-MM-DD'
        ym: 'YYYY-MM'

    Raises:
        ValueError if transaction not found.
    """
    existing = get_transaction_by_id_for_user(tx_id, user_id)
    if existing is None:
        raise ValueError("Transaction not found.")

    execute(
        "UPDATE transactions SET "
        f"category_id = {sql_literal(int(category_id))}, "
        f"amount_cents = {sql_literal(int(amount_cents))}, "
        f"type = {sql_literal(tx_type)}, "
        f"description = {sql_literal(description)}, "
        f"date = {sql_literal(date)}, "
        f"ym = {sql_literal(ym)} "
        f"WHERE id = {sql_literal(int(tx_id))};"
    )


def delete_transaction_for_user(*, tx_id: int, user_id: int) -> None:
    """
    Delete a transaction owned by the user.

    Args:
        tx_id: Transaction id.
        user_id: Owner user id.

    Raises:
        ValueError if not found.
    """
    existing = get_transaction_by_id_for_user(tx_id, user_id)
    if existing is None:
        raise ValueError("Transaction not found.")

    execute(f"DELETE FROM transactions WHERE id = {sql_literal(int(tx_id))};")