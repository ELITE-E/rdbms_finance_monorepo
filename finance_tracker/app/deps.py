"""
app/deps.py

Auth helpers.

Step 10 updates:
- Add require_user() helper to standardize redirect pattern.
- Add helper to clear invalid auth cookie (optional hardening).
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.responses import Response

from . import settings
from .repos.users_repo import get_user_by_id
from .security import decode_access_token


def get_current_user(request: Request) -> dict | None:
    """
    Read JWT cookie, validate it, and load the user.

    Args:
        request: FastAPI request

    Returns:
        User dict if authenticated, otherwise None.
    """
    token = request.cookies.get(settings.AUTH_COOKIE_NAME)
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    sub = payload.get("sub")
    if not sub:
        return None

    try:
        user_id = int(sub)
    except ValueError:
        return None

    return get_user_by_id(user_id)


def clear_auth_cookie(resp: Response) -> None:
    """
    Remove auth cookie from client.

    Args:
        resp: Response to modify.
    """
    resp.delete_cookie(settings.AUTH_COOKIE_NAME, path="/")


def require_user(request: Request) -> tuple[dict | None, Response | None]:
    """
    Standardize "protected route" behavior.

    Args:
        request: FastAPI request.

    Returns:
        (user, redirect_response)
        - If authenticated: (user_dict, None)
        - If not: (None, RedirectResponse to /login)

    Notes:
        Callers use:
          user, redirect = require_user(request)
          if redirect: return redirect
    """
    user = get_current_user(request)
    if user:
        return user, None
    return None, RedirectResponse(url="/login", status_code=303)