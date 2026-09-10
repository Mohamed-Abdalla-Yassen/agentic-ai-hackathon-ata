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
