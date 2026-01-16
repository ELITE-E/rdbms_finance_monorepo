"""
app/routes/pages.py

Basic utility pages for the app.

Step 2:
- Keep "/" redirect only.
- Login/register/dashboard now live in dedicated route modules.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/")
def home() -> RedirectResponse:
    """
    Redirect root to dashboard.

    Returns:
        RedirectResponse to /dashboard
    """
    return RedirectResponse(url="/dashboard", status_code=303)