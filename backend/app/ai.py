"""The single Claude API call that re-ranks search candidates.

Per spec: one call, strict JSON output, ranked room ids + a one-line reason
each. The model id comes from the environment (app.config.ranking_model) —
never hardcoded here.
"""

import json
import logging

import anthropic

from app.config import anthropic_api_key, ranking_model

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


def rank_rooms(note: str, candidates: list[dict]) -> list[dict]:
    """Returns a list of {"room_id": int, "reason": str}, best match first.

    Raises on any API failure or malformed response — callers are expected to
    catch and fall back to the SQL-filtered order (see routers/search.py).
    """
    client = anthropic.Anthropic(api_key=anthropic_api_key())

    response = client.messages.create(
        model=ranking_model(),
        max_tokens=2000,
        output_config={
            "effort": "low",
            "format": {"type": "json_schema", "schema": RANKING_SCHEMA},
        },
        system=RANKING_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": json.dumps({"note": note, "candidates": candidates}),
            }
        ],
    )

    text = next(block.text for block in response.content if block.type == "text")
    data = json.loads(text)
    return data["ranked"]
