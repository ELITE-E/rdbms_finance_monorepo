"""
app/main.py

Step 3 update:
- Adds categories routes (GET/POST /categories)
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from starlette.templating import Jinja2Templates

from .db_core import get_db
from .db_init import init_db
from .auth.auth import router as auth_router
from .routes.categories import router as categories_router
from .routes.dashboard import router as dashboard_router
from .routes.pages import router as pages_router
from .routes.transactions import router as  transactions_router


def create_app() -> FastAPI:
    app = FastAPI(title="Simple Finance Tracker")

    base_dir = Path(__file__).resolve().parent
    templates_dir = base_dir / "templates"

    app.state.templates = Jinja2Templates(directory=str(templates_dir))

    app.include_router(pages_router)
    app.include_router(auth_router)
    app.include_router(dashboard_router)
    app.include_router(categories_router)
    app.include_router(transactions_router)
    @app.on_event("startup")
    def _startup() -> None:
        db = get_db()
        init_db(db)

    return app


app = create_app()