"""
app/services/dashboard_service.py

Dashboard computations for Step 8.

Responsibilities:
- Aggregate transactions in Python (because SimpleDB has no SUM/GROUP BY)
- Compute:
    - all-time balance
    - current month income + expense totals
    - current month spending by category
    - recent transactions list

Design notes:
- We store amount in cents.
- Expenses are subtracted from balance; income added.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..repos.transactions_repo import list_transactions_for_user


@dataclass(frozen=True)
class DashboardData:
    """
    Container for computed dashboard metrics.
    """
    balance_cents: int
    month_income_cents: int
    month_expense_cents: int
    spending_by_category: list[dict[str, Any]]  # [{category_name, expense_cents}]
    recent_transactions: list[dict[str, Any]]
    ym: str  # current month key 'YYYY-MM'


def compute_dashboard(user_id: int, *, now: datetime | None = None) -> DashboardData:
    """
    Compute dashboard metrics for a user.

    Args:
        user_id: Owner user id.
        now: Optional datetime override for testing.

    Returns:
        DashboardData with computed metrics.
    """
    if now is None:
        now = datetime.now()

    ym = now.strftime("%Y-%m")

    # All transactions for balance (could be large; fine for demo).
    all_txs = list_transactions_for_user(user_id, ym=None)

    balance = 0
    for t in all_txs:
        amt = int(t["amount_cents"])
        if t["type"] == "income":
            balance += amt
        else:
            balance -= amt

    # Current month transactions (cheap filter because we use ym equality)
    month_txs = list_transactions_for_user(user_id, ym=ym)

    month_income = 0
    month_expense = 0
    spend_map: dict[str, int] = {}

    for t in month_txs:
        amt = int(t["amount_cents"])
        if t["type"] == "income":
            month_income += amt
        else:
            month_expense += amt
            cname = t["category_name"] or "Uncategorized"
            spend_map[cname] = spend_map.get(cname, 0) + amt

    spending_by_category = [
        {"category_name": k, "expense_cents": v}
        for k, v in spend_map.items()
    ]
    spending_by_category.sort(key=lambda x: x["expense_cents"], reverse=True)

    # Recent transactions: take first N from all_txs (already sorted desc by repo)
    recent = all_txs[:10]

    return DashboardData(
        balance_cents=balance,
        month_income_cents=month_income,
        month_expense_cents=month_expense,
        spending_by_category=spending_by_category,
        recent_transactions=recent,
        ym=ym,
    )


def format_cents(cents: int) -> str:
    """
    Format cents as a currency-like string.

    Args:
        cents: Integer cents.

    Returns:
        String "123.45" (with negative sign if needed).
    """
    sign = "-" if cents < 0 else ""
    cents = abs(int(cents))
    return f"{sign}{cents // 100}.{cents % 100:02d}"