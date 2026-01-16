"""
app/routes/transactions.py

Step 10 update:
- Use require_user() helper for cleaner protected routes.
- No functional changes beyond refactor for maintainability.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from ..deps import require_user
from ..repos.categories_repo import get_category_by_id_for_user, list_categories_for_user
from ..repos.transactions_repo import (
    create_transaction,
    delete_transaction_for_user,
    get_transaction_by_id_for_user,
    list_transactions_for_user,
    update_transaction_for_user,
)

router = APIRouter()


def _parse_amount_to_cents(amount_str: str) -> int:
    s = amount_str.strip()
    if not s:
        raise ValueError("Amount is required.")
    if "." in s:
        left, right = s.split(".", 1)
        if not left:
            left = "0"
        if not (left.isdigit() and right.isdigit()):
            raise ValueError("Amount must be a number.")
        if len(right) > 2:
            raise ValueError("Amount can have at most 2 decimal places.")
        right = right.ljust(2, "0")
        cents = int(left) * 100 + int(right[:2])
    else:
        if not s.isdigit():
            raise ValueError("Amount must be a number.")
        cents = int(s) * 100
    if cents <= 0:
        raise ValueError("Amount must be greater than 0.")
    return cents


def _validate_date(date_str: str) -> tuple[str, str]:
    s = date_str.strip()
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format.")
    return s, dt.strftime("%Y-%m")


def _format_cents(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(int(cents))
    return f"{sign}{cents // 100}.{cents % 100:02d}"


@router.get("/transactions")
def transactions_list(request: Request):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    ym = request.query_params.get("ym")
    txs = list_transactions_for_user(int(user["id"]), ym=ym)  # type: ignore[index]

    for t in txs:
        amt = int(t["amount_cents"])
        if t["type"] == "expense":
            amt = -amt
        t["amount_display"] = _format_cents(amt)

    templates = request.app.state.templates
    return templates.TemplateResponse("transactions.html", {"request": request, "user": user, "transactions": txs, "ym": ym or ""})


@router.get("/transactions/new")
def transaction_new_form(request: Request):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    categories = list_categories_for_user(int(user["id"]))  # type: ignore[index]
    templates = request.app.state.templates
    return templates.TemplateResponse("transaction_new.html", {"request": request, "user": user, "categories": categories, "error": None})


@router.post("/transactions/new")
def transaction_new_submit(
    request: Request,
    amount: str = Form(...),
    tx_type: str = Form(...),
    category_id: int = Form(...),
    date: str = Form(...),
    description: str = Form(""),
):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    templates = request.app.state.templates
    categories = list_categories_for_user(int(user["id"]))  # type: ignore[index]

    tx_type = tx_type.strip().lower()
    if tx_type not in ("income", "expense"):
        return templates.TemplateResponse("transaction_new.html", {"request": request, "user": user, "categories": categories, "error": "Type must be 'income' or 'expense'."})

    cat = get_category_by_id_for_user(int(category_id), int(user["id"]))  # type: ignore[index]
    if cat is None:
        return templates.TemplateResponse("transaction_new.html", {"request": request, "user": user, "categories": categories, "error": "Invalid category selection."})

    try:
        amount_cents = _parse_amount_to_cents(amount)
        date_iso, ym = _validate_date(date)
    except ValueError as e:
        return templates.TemplateResponse("transaction_new.html", {"request": request, "user": user, "categories": categories, "error": str(e)})

    desc = description.strip() or None

    create_transaction(
        user_id=int(user["id"]),  # type: ignore[index]
        category_id=int(category_id),
        amount_cents=amount_cents,
        tx_type=tx_type,
        description=desc,
        date=date_iso,
        ym=ym,
    )
    return RedirectResponse(url="/transactions", status_code=303)


@router.get("/transactions/{tx_id}/edit")
def transaction_edit_form(request: Request, tx_id: int):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    tx = get_transaction_by_id_for_user(int(tx_id), int(user["id"]))  # type: ignore[index]
    if tx is None:
        return RedirectResponse(url="/transactions", status_code=303)

    categories = list_categories_for_user(int(user["id"]))  # type: ignore[index]
    amount_cents = int(tx["amount_cents"])
    amount_str = f"{amount_cents // 100}.{amount_cents % 100:02d}"

    templates = request.app.state.templates
    return templates.TemplateResponse("transaction_edit.html", {"request": request, "user": user, "tx": tx, "categories": categories, "amount_str": amount_str, "error": None})


@router.post("/transactions/{tx_id}/edit")
def transaction_edit_submit(
    request: Request,
    tx_id: int,
    amount: str = Form(...),
    tx_type: str = Form(...),
    category_id: int = Form(...),
    date: str = Form(...),
    description: str = Form(""),
):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    templates = request.app.state.templates
    categories = list_categories_for_user(int(user["id"]))  # type: ignore[index]

    tx = get_transaction_by_id_for_user(int(tx_id), int(user["id"]))  # type: ignore[index]
    if tx is None:
        return RedirectResponse(url="/transactions", status_code=303)

    tx_type = tx_type.strip().lower()
    if tx_type not in ("income", "expense"):
        return templates.TemplateResponse("transaction_edit.html", {"request": request, "user": user, "tx": tx, "categories": categories, "amount_str": amount, "error": "Invalid type."})

    cat = get_category_by_id_for_user(int(category_id), int(user["id"]))  # type: ignore[index]
    if cat is None:
        return templates.TemplateResponse("transaction_edit.html", {"request": request, "user": user, "tx": tx, "categories": categories, "amount_str": amount, "error": "Invalid category."})

    try:
        amount_cents = _parse_amount_to_cents(amount)
        date_iso, ym = _validate_date(date)
    except ValueError as e:
        return templates.TemplateResponse("transaction_edit.html", {"request": request, "user": user, "tx": tx, "categories": categories, "amount_str": amount, "error": str(e)})

    desc = description.strip() or None

    try:
        update_transaction_for_user(
            tx_id=int(tx_id),
            user_id=int(user["id"]),  # type: ignore[index]
            category_id=int(category_id),
            amount_cents=amount_cents,
            tx_type=tx_type,
            description=desc,
            date=date_iso,
            ym=ym,
        )
    except ValueError as e:
        return templates.TemplateResponse("transaction_edit.html", {"request": request, "user": user, "tx": tx, "categories": categories, "amount_str": amount, "error": str(e)})

    return RedirectResponse(url="/transactions", status_code=303)


@router.post("/transactions/{tx_id}/delete")
def transaction_delete(request: Request, tx_id: int):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    try:
        delete_transaction_for_user(tx_id=int(tx_id), user_id=int(user["id"]))  # type: ignore[index]
    except ValueError:
        pass

    return RedirectResponse(url="/transactions", status_code=303)