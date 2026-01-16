"""
app/settings.py

Central configuration for the Finance Tracker app.

Step 2 adds:
- JWT settings (secret, algorithm, cookie name, expiration)
- Cookie flags (HttpOnly, SameSite, Secure)
"""

from __future__ import annotations

from pathlib import Path

# finance_tracker/ (project root)
BASE_DIR = Path(__file__).resolve().parent.parent

# SimpleDB database directory (persisted on disk)
DB_DIR = BASE_DIR / "db"

# JWT / Auth
JWT_SECRET = "change-me-in-production"  # For demo. In real use, load from env var.
JWT_ALG = "HS256"
AUTH_COOKIE_NAME = "access_token"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Cookie flags
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = "lax"
COOKIE_SECURE = False  # Set True if using HTTPS