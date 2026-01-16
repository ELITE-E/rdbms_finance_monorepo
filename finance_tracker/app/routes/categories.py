"""
app/routes/categories.py

Step 10 update:
- Use require_user() helper for cleaner protected routes.
"""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from ..deps import require_user
from ..repos.categories_repo import create_category, delete_category, list_categories_for_user, rename_category

router = APIRouter()


def _render_categories(request: Request, user: dict, error: str | None):
    templates = request.app.state.templates
    categories = list_categories_for_user(int(user["id"]))
    return templates.TemplateResponse(
        "categories.html",
        {"request": request, "user": user, "categories": categories, "error": error},
    )


@router.get("/categories")
def categories_page(request: Request):
    user, redirect = require_user(request)
    if redirect:
        return redirect
    return _render_categories(request, user, error=None)  # type: ignore[arg-type]


@router.post("/categories")
def categories_create(request: Request, name: str = Form(...)):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    name = name.strip()
    if not name:
        return _render_categories(request, user, error="Category name cannot be empty.")  # type: ignore[arg-type]

    try:
        create_category(user_id=int(user["id"]), name=name)  # type: ignore[index]
    except ValueError as e:
        return _render_categories(request, user, error=str(e))  # type: ignore[arg-type]

    return RedirectResponse(url="/categories", status_code=303)


@router.post("/categories/{category_id}/rename")
def categories_rename(request: Request, category_id: int, new_name: str = Form(...)):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    new_name = new_name.strip()
    if not new_name:
        return _render_categories(request, user, error="New category name cannot be empty.")  # type: ignore[arg-type]

    try:
        rename_category(category_id=int(category_id), user_id=int(user["id"]), new_name=new_name)  # type: ignore[index]
    except ValueError as e:
        return _render_categories(request, user, error=str(e))  # type: ignore[arg-type]

    return RedirectResponse(url="/categories", status_code=303)


@router.post("/categories/{category_id}/delete")
def categories_delete(request: Request, category_id: int):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    try:
        delete_category(category_id=int(category_id), user_id=int(user["id"]))  # type: ignore[index]
    except ValueError as e:
        return _render_categories(request, user, error=str(e))  # type: ignore[arg-type]

    return RedirectResponse(url="/categories", status_code=303)