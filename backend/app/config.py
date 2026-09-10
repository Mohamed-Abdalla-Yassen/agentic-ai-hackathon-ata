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


# --- Rate limiting ---------------------------------------------------------
#
# Unlike the secrets above, these have defaults: a missing limit should mean
# "the safe built-in value", never "no limit at all". Deployments tune them by
# setting the env var; forgetting to set one still leaves the app protected.


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        raise RuntimeError(f"Environment variable {name} must be an integer, got {raw!r}")
    if value < 1:
        raise RuntimeError(f"Environment variable {name} must be at least 1, got {value}")
    return value


def rate_limit_auth_per_hour() -> int:
    """Login/register attempts allowed per client IP per hour."""
    return _env_int("RATE_LIMIT_AUTH_PER_HOUR", 30)


def rate_limit_read_per_minute() -> int:
    """Free (non-AI) authenticated requests allowed per user per minute."""
    return _env_int("RATE_LIMIT_READ_PER_MINUTE", 60)


def rate_limit_ai_per_hour() -> int:
    """AI-backed searches allowed per booker per hour."""
    return _env_int("RATE_LIMIT_AI_PER_HOUR", 20)


def rate_limit_ai_per_day() -> int:
    """AI-backed searches allowed per booker per day."""
    return _env_int("RATE_LIMIT_AI_PER_DAY", 100)


def rate_limit_ai_global_per_day() -> int:
    """Total AI-backed searches served per day, across every user.

    The hard ceiling on daily Anthropic spend. Per-user quotas cannot provide
    this on their own while anyone can register a fresh account for free.
    """
    return _env_int("RATE_LIMIT_AI_GLOBAL_PER_DAY", 500)


def trust_proxy_headers() -> bool:
    """Whether to read the client IP from X-Forwarded-For.

    Off by default: the header is caller-controlled, so trusting it when the app
    is directly reachable lets an attacker forge a new identity per request and
    erase every per-IP limit. Turn it on only behind a proxy that overwrites it.
    """
    return os.environ.get("TRUST_PROXY_HEADERS", "").strip().lower() in {"1", "true", "yes"}
