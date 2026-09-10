"""The single AI call that re-ranks search candidates.

Per spec: one call, strict JSON output, ranked room ids + a one-line reason
each. Two providers are supported, selected by AI_PROVIDER:

  anthropic — the Claude Messages API (default).
  openai    — any OpenAI-compatible /chat/completions endpoint. Leaving
              OPENAI_BASE_URL unset targets OpenAI itself; pointing it at a
              compatible gateway (SovereignEG, Ollama, vLLM, OpenRouter, ...)
              targets that host instead.

Both paths return the same shape, so routers/search.py never learns which one
ran. Credentials, model ids and endpoints all come from the environment
(app.config) — never hardcoded here.
"""

import json
import logging

from app.config import (
    ai_provider,
    anthropic_base_url,
    anthropic_credentials,
    anthropic_model,
    openai_api_key,
    openai_base_url,
    openai_model,
)

logger = logging.getLogger(__name__)

RANKING_SYSTEM_PROMPT = """\
You are ranking workspace/venue rooms for a booker based on their free-text \
preference note. You will receive a JSON object with "note" (the booker's \
preference, in their own words) and "candidates" (a list of rooms that \
already satisfy the booker's structured filters).

Rank the candidates by how well each one fits the note, using its name, \
amenities, and free-text notes field. Every candidate must appear exactly \
once in your output, ordered best match first. For each one, write a single \
short sentence explaining why it matches — refer to something concrete \
about that room (its notes, amenities, or setting), don't invent details \
that aren't in the candidate data, and don't just restate the note back."""

RANKING_SCHEMA = {
    "type": "object",
    "properties": {
        "ranked": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "room_id": {"type": "integer"},
                    "reason": {"type": "string"},
                },
                "required": ["room_id", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["ranked"],
    "additionalProperties": False,
}

# Appended to the system prompt on the OpenAI path. Schema-enforced output is
# requested there too, but smaller self-hosted models often ignore or don't
# support response_format — spelling the shape out keeps them on track.
JSON_OUTPUT_INSTRUCTION = """

Reply with nothing but a JSON object of exactly this shape — no prose, no \
markdown fences:
{"ranked": [{"room_id": <integer>, "reason": "<one short sentence>"}, ...]}"""

MAX_OUTPUT_TOKENS = 2000


def rank_rooms(note: str, candidates: list[dict]) -> list[dict]:
    """Returns a list of {"room_id": int, "reason": str}, best match first.

    Raises on any API failure or malformed response — callers are expected to
    catch and fall back to the SQL-filtered order (see routers/search.py).
    """
    provider = ai_provider()
    if provider == "openai":
        return _rank_openai(note, candidates)
    return _rank_anthropic(note, candidates)


def _user_message(note: str, candidates: list[dict]) -> str:
    return json.dumps({"note": note, "candidates": candidates})


def _rank_anthropic(note: str, candidates: list[dict]) -> list[dict]:
    import anthropic

    kind, secret = anthropic_credentials()
    client_kwargs: dict = {
        "api_key": secret if kind == "api_key" else None,
        "auth_token": secret if kind == "auth_token" else None,
    }
    base_url = anthropic_base_url()
    if base_url:
        client_kwargs["base_url"] = base_url

    client = anthropic.Anthropic(**client_kwargs)

    response = client.messages.create(
        model=anthropic_model(),
        max_tokens=MAX_OUTPUT_TOKENS,
        output_config={
            "effort": "low",
            "format": {"type": "json_schema", "schema": RANKING_SCHEMA},
        },
        system=RANKING_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _user_message(note, candidates)}],
    )

    text = next(block.text for block in response.content if block.type == "text")
    return _parse_ranked(text)


def _rank_openai(note: str, candidates: list[dict]) -> list[dict]:
    from openai import OpenAI

    client = OpenAI(api_key=openai_api_key(), base_url=openai_base_url())

    request: dict = {
        "model": openai_model(),
        "max_completion_tokens": MAX_OUTPUT_TOKENS,
        "messages": [
            {"role": "system", "content": RANKING_SYSTEM_PROMPT + JSON_OUTPUT_INSTRUCTION},
            {"role": "user", "content": _user_message(note, candidates)},
        ],
    }
    schema_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "ranked_rooms",
            "strict": True,
            "schema": RANKING_SCHEMA,
        },
    }

    try:
        response = client.chat.completions.create(**request, response_format=schema_format)
    except Exception:
        # Plenty of OpenAI-compatible hosts reject response_format (or its
        # json_schema variant) outright. The prompt already specifies the
        # shape, so retry unconstrained rather than failing the search.
        logger.warning(
            "Provider rejected structured-output request; retrying without response_format",
            exc_info=True,
        )
        response = client.chat.completions.create(**request)

    return _parse_ranked(response.choices[0].message.content)


def _parse_ranked(text: str | None) -> list[dict]:
    """Pulls the ranked list out of a model reply.

    Schema-enforced replies parse directly. Models without that support tend
    to wrap the object in markdown fences or a sentence of preamble, so fall
    back to the outermost {...} span before giving up.
    """
    if not text:
        raise ValueError("model returned an empty response")

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("model response contained no JSON object")
        data = json.loads(text[start : end + 1])

    ranked = data["ranked"]
    if not isinstance(ranked, list):
        raise ValueError('model response field "ranked" was not a list')
    return ranked
