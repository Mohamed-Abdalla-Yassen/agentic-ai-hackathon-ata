"""Environment configuration and shared constants.

Nothing secret or environment-specific (DB path, JWT secret, API key, model id)
is ever hardcoded here — every one of those is read from the environment, and
missing ones fail loudly instead of silently falling back to a default.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# The fixed amenities list. Imported by both room creation and search filtering —
# these two must never drift apart, so this is the single source of truth.
ROOM_AMENITIES = ["wifi", "parking", "whiteboard", "projector", "kitchen", "ac"]

PRICE_UNITS = ["hour", "day"]

# Max candidates handed to the AI ranking step (spec targets 5-15).
SEARCH_CANDIDATE_LIMIT = 15

# Origins allowed by CORS — the Vite dev server.
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Required environment variable {name} is not set. "
            f"Copy backend/.env.example to backend/.env and fill it in."
        )
    return value


# Read lazily (as functions, not module-level constants) so tests can set
# environment variables before first use and so a missing var only breaks the
# code path that actually needs it, not import time.
def database_path() -> str:
    return _require_env("DATABASE_PATH")


def jwt_secret() -> str:
    return _require_env("JWT_SECRET")


def anthropic_api_key() -> str:
    return _require_env("ANTHROPIC_API_KEY")


def ranking_model() -> str:
    return _require_env("ANTHROPIC_MODEL")
