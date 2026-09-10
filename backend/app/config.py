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

# Supported providers for the search ranking call. "anthropic" talks to the
# Claude Messages API; "openai" talks to any OpenAI-compatible /chat/completions
# endpoint (OpenAI itself, SovereignEG, Ollama, vLLM, OpenRouter, ...).
AI_PROVIDERS = ["anthropic", "openai"]
DEFAULT_AI_PROVIDER = "anthropic"


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Required environment variable {name} is not set. "
            f"Copy backend/.env.example to backend/.env and fill it in."
        )
    return value


def _optional_env(name: str) -> str | None:
    value = os.environ.get(name)
    return value.strip() or None if value else None


# Read lazily (as functions, not module-level constants) so tests can set
# environment variables before first use and so a missing var only breaks the
# code path that actually needs it, not import time.
def database_path() -> str:
    return _require_env("DATABASE_PATH")


def jwt_secret() -> str:
    return _require_env("JWT_SECRET")


# --- AI provider selection -------------------------------------------------


def ai_provider() -> str:
    """Which backend the search ranking call talks to.

    Defaults to Anthropic so an existing .env keeps working untouched; set
    AI_PROVIDER=openai to use any OpenAI-compatible endpoint instead.
    """
    value = (os.environ.get("AI_PROVIDER") or DEFAULT_AI_PROVIDER).strip().lower()
    if value not in AI_PROVIDERS:
        raise RuntimeError(
            f"AI_PROVIDER must be one of {', '.join(AI_PROVIDERS)} — got {value!r}."
        )
    return value


def anthropic_credentials() -> tuple[str, str]:
    """Returns (kind, value) where kind is "api_key" or "auth_token".

    A key is sent as `x-api-key`, a token as `Authorization: Bearer` — the two
    are different auth schemes, so we track which one we were given. The key
    wins if both are set.
    """
    api_key = _optional_env("ANTHROPIC_API_KEY")
    if api_key:
        return ("api_key", api_key)
    auth_token = _optional_env("ANTHROPIC_AUTH_TOKEN")
    if auth_token:
        return ("auth_token", auth_token)
    raise RuntimeError(
        "Set either ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN for "
        "AI_PROVIDER=anthropic. Copy backend/.env.example to backend/.env "
        "and fill it in."
    )


def anthropic_model() -> str:
    return _require_env("ANTHROPIC_MODEL")


def anthropic_base_url() -> str | None:
    """Overrides the Anthropic API endpoint (e.g. a compatible gateway)."""
    return _optional_env("ANTHROPIC_BASE_URL")


def openai_api_key() -> str:
    return _require_env("OPENAI_API_KEY")


def openai_model() -> str:
    return _require_env("OPENAI_MODEL")


def openai_base_url() -> str | None:
    """Endpoint for the OpenAI-compatible provider.

    Unset means api.openai.com. Point it at a compatible gateway to use another
    model host — e.g. https://backend.sovereigneg.com/v1 for SovereignEG.
    """
    return _optional_env("OPENAI_BASE_URL")


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
        raise RuntimeError(
            f"Environment variable {name} must be an integer, got {raw!r}"
        )
    if value < 1:
        raise RuntimeError(
            f"Environment variable {name} must be at least 1, got {value}"
        )
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


# --- Photo uploads ---------------------------------------------------------

# What an owner is allowed to upload. Deliberately a short allowlist of formats
# browsers render natively: anything else (SVG especially, which can carry
# script) is refused rather than sanitised.
ALLOWED_PHOTO_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

# Leading bytes that identify each allowed format. The browser-supplied
# Content-Type is a claim, not evidence, so the file is identified by its own
# contents before anything is written to disk.
PHOTO_MAGIC_BYTES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    # WebP is "RIFF....WEBP" — the size field sits between the two markers.
    "image/webp": [b"RIFF"],
}


def upload_dir() -> str:
    """Directory holding uploaded photo files. Created on first write."""
    return os.environ.get("UPLOAD_DIR", "").strip() or "./data/uploads"


def max_photo_bytes() -> int:
    """Largest accepted upload. Default 5 MB."""
    return _env_int("MAX_PHOTO_BYTES", 5 * 1024 * 1024)


def max_photos_per_room() -> int:
    """Cap per room, so one owner cannot fill the disk."""
    return _env_int("MAX_PHOTOS_PER_ROOM", 8)


def rate_limit_upload_per_hour() -> int:
    """Photo uploads allowed per owner per hour."""
    return _env_int("RATE_LIMIT_UPLOAD_PER_HOUR", 60)


def trust_proxy_headers() -> bool:
    """Whether to read the client IP from X-Forwarded-For.

    Off by default: the header is caller-controlled, so trusting it when the app
    is directly reachable lets an attacker forge a new identity per request and
    erase every per-IP limit. Turn it on only behind a proxy that overwrites it.
    """
    return os.environ.get("TRUST_PROXY_HEADERS", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
