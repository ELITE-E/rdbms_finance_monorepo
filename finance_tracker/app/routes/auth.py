"""
app/routes/auth.py

Step 10 update:
- Set cookie max_age to align with token expiry.
"""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from starlette.responses import Response

from .. import settings
from ..repos.users_repo import create_user, get_user_by_email, get_user_by_username
from ..security import create_access_token, hash_password, verify_password

router = APIRouter()


def _set_auth_cookie(resp: Response, token: str) -> None:
    """
    Attach JWT to response as HttpOnly cookie.

    Args:
        resp: Response to mutate.
        token: JWT string.
    """
    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    resp.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        httponly=settings.COOKIE_HTTPONLY,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        max_age=max_age,
        path="/",
    )


@router.get("/register")
def register_form(request: Request):
    templates = request.app.state.templates
    return templates.TemplateResponse("register.html", {"request": request, "error": None, "user": None})


@router.post("/register")
def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
):
    templates = request.app.state.templates

    username = username.strip()
    email = email.strip().lower()

    if not username or not email or not password:
        return templates.TemplateResponse("register.html", {"request": request, "error": "All fields are required.", "user": None})

    if password != password2:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Passwords do not match.", "user": None})

    if get_user_by_username(username) is not None:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already taken.", "user": None})

    if get_user_by_email(email) is not None:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email already registered.", "user": None})

    pw_hash = hash_password(password)
    user_id = create_user(username=username, email=email, password_hash=pw_hash)

    token = create_access_token(user_id=user_id, email=email)
    resp = RedirectResponse(url="/dashboard", status_code=303)
    _set_auth_cookie(resp, token)
    return resp


@router.get("/login")
def login_form(request: Request):
    templates = request.app.state.templates
    return templates.TemplateResponse("login.html", {"request": request, "error": None, "user": None})


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    templates = request.app.state.templates

    email = email.strip().lower()
    user = get_user_by_email(email)

    if user is None or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email or password.", "user": None})

    token = create_access_token(user_id=int(user["id"]), email=user["email"])
    resp = RedirectResponse(url="/dashboard", status_code=303)
    _set_auth_cookie(resp, token)
    return resp


@router.post("/logout")
def logout() -> Response:
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie(settings.AUTH_COOKIE_NAME, path="/")
    return resp