"""
app/routes/dashboard.py

Step 10 update:
- Use require_user() helper to reduce repeated code.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request

from ..deps import require_user
from ..services.dashboard_service import compute_dashboard, format_cents

router = APIRouter()


@router.get("/dashboard")
def dashboard(request: Request):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    data = compute_dashboard(int(user["id"]))  # type: ignore[index]

    spending_rows = [{"category_name": row["category_name"], "expense_cents": int(row["expense_cents"])} for row in data.spending_by_category]
    chart_labels = [r["category_name"] for r in spending_rows]
    chart_values = [round(r["expense_cents"] / 100.0, 2) for r in spending_rows]

    ctx = {
        "request": request,
        "user": user,
        "ym": data.ym,
        "balance": format_cents(data.balance_cents),
        "month_income": format_cents(data.month_income_cents),
        "month_expense": format_cents(data.month_expense_cents),
        "spending_by_category": [{"category_name": r["category_name"], "expense": format_cents(r["expense_cents"])} for r in spending_rows],
        "recent_transactions": [
            {
                **t,
                "amount_display": format_cents(-int(t["amount_cents"]) if t["type"] == "expense" else int(t["amount_cents"])),
            }
            for t in data.recent_transactions
        ],
        "chart_labels_json": json.dumps(chart_labels),
        "chart_values_json": json.dumps(chart_values),
    }

    templates = request.app.state.templates
    return templates.TemplateResponse("dashboard.html", ctx)