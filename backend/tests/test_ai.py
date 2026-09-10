"""Provider dispatch and response parsing for the search ranking call.

Both provider paths are exercised against fake clients — nothing here makes a
network request. The point is that rank_rooms() returns the same shape either
way, so routers/search.py never has to care which provider ran.
"""

import json
from types import SimpleNamespace

import pytest

from app import ai
from app.config import ai_provider

RANKED = [
    {"room_id": 2, "reason": "Quiet corner room"},
    {"room_id": 1, "reason": "Bigger table"},
]
CANDIDATES = [{"room_id": 1, "room_name": "A"}, {"room_id": 2, "room_name": "B"}]


class FakeOpenAI:
    """Stand-in for openai.OpenAI that records what it was constructed with."""

    instances: list["FakeOpenAI"] = []

    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key
        self.base_url = base_url
        self.requests: list[dict] = []
        self.reply = json.dumps({"ranked": RANKED})
        self.reject_response_format = False
        FakeOpenAI.instances.append(self)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        if self.reject_response_format and "response_format" in kwargs:
            raise RuntimeError("this provider does not support response_format")
        message = SimpleNamespace(content=self.reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeAnthropic:
    instances: list["FakeAnthropic"] = []

    def __init__(self, api_key=None, auth_token=None, base_url=None):
        self.api_key = api_key
        self.auth_token = auth_token
        self.base_url = base_url
        self.requests: list[dict] = []
        FakeAnthropic.instances.append(self)
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        block = SimpleNamespace(type="text", text=json.dumps({"ranked": RANKED}))
        return SimpleNamespace(content=[block])


@pytest.fixture
def fake_openai(monkeypatch):
    import openai

    FakeOpenAI.instances = []
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    return FakeOpenAI


@pytest.fixture
def fake_anthropic(monkeypatch):
    import anthropic

    FakeAnthropic.instances = []
    monkeypatch.setattr(anthropic, "Anthropic", FakeAnthropic)
    return FakeAnthropic


# --- provider selection ----------------------------------------------------


def test_provider_defaults_to_anthropic(env):
    assert ai_provider() == "anthropic"


def test_provider_is_case_insensitive(env, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "OpenAI")
    assert ai_provider() == "openai"


def test_unknown_provider_fails_loudly(env, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    with pytest.raises(RuntimeError, match="AI_PROVIDER"):
        ai_provider()


def test_default_provider_routes_to_anthropic(env, fake_anthropic, fake_openai):
    assert ai.rank_rooms("quiet", CANDIDATES) == RANKED
    assert len(fake_anthropic.instances) == 1
    assert fake_openai.instances == []


def test_openai_provider_routes_to_openai(
    env, monkeypatch, fake_anthropic, fake_openai
):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    assert ai.rank_rooms("quiet", CANDIDATES) == RANKED
    assert len(fake_openai.instances) == 1
    assert fake_anthropic.instances == []


# --- anthropic path --------------------------------------------------------


def test_anthropic_sends_api_key_as_key_not_token(env, fake_anthropic):
    ai.rank_rooms("quiet", CANDIDATES)
    client = fake_anthropic.instances[0]
    assert client.api_key == "test-key"
    assert client.auth_token is None


def test_anthropic_auth_token_used_when_no_key(env, monkeypatch, fake_anthropic):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "test-token")
    ai.rank_rooms("quiet", CANDIDATES)
    client = fake_anthropic.instances[0]
    assert client.auth_token == "test-token"
    assert client.api_key is None


def test_anthropic_api_key_wins_over_auth_token(env, monkeypatch, fake_anthropic):
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "test-token")
    ai.rank_rooms("quiet", CANDIDATES)
    client = fake_anthropic.instances[0]
    assert client.api_key == "test-key"
    assert client.auth_token is None


def test_anthropic_missing_credentials_fail_loudly(env, monkeypatch, fake_anthropic):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        ai.rank_rooms("quiet", CANDIDATES)


def test_anthropic_base_url_override_is_passed_through(
    env, monkeypatch, fake_anthropic
):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://gateway.example.com")
    ai.rank_rooms("quiet", CANDIDATES)
    assert fake_anthropic.instances[0].base_url == "https://gateway.example.com"


def test_anthropic_sends_model_and_note(env, fake_anthropic):
    ai.rank_rooms("quiet room", CANDIDATES)
    request = fake_anthropic.instances[0].requests[0]
    assert request["model"] == "test-model"
    assert json.loads(request["messages"][0]["content"]) == {
        "note": "quiet room",
        "candidates": CANDIDATES,
    }


# --- openai path -----------------------------------------------------------


@pytest.fixture
def openai_env(env, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")


def test_openai_uses_configured_key_and_model(openai_env, fake_openai):
    ai.rank_rooms("quiet", CANDIDATES)
    client = fake_openai.instances[0]
    assert client.api_key == "test-openai-key"
    assert client.requests[0]["model"] == "test-openai-model"


def test_openai_base_url_defaults_to_none(openai_env, fake_openai):
    """Unset OPENAI_BASE_URL must reach the SDK as None so it uses OpenAI's
    own endpoint, rather than as an empty string."""
    ai.rank_rooms("quiet", CANDIDATES)
    assert fake_openai.instances[0].base_url is None


def test_openai_base_url_override_is_passed_through(
    openai_env, monkeypatch, fake_openai
):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://backend.sovereigneg.com/v1")
    ai.rank_rooms("quiet", CANDIDATES)
    assert fake_openai.instances[0].base_url == "https://backend.sovereigneg.com/v1"


def test_openai_missing_key_fails_loudly(openai_env, monkeypatch, fake_openai):
    monkeypatch.delenv("OPENAI_API_KEY")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        ai.rank_rooms("quiet", CANDIDATES)


def test_openai_missing_model_fails_loudly(openai_env, monkeypatch, fake_openai):
    monkeypatch.delenv("OPENAI_MODEL")
    with pytest.raises(RuntimeError, match="OPENAI_MODEL"):
        ai.rank_rooms("quiet", CANDIDATES)


def test_openai_sends_note_and_json_instruction(openai_env, fake_openai):
    ai.rank_rooms("quiet room", CANDIDATES)
    request = fake_openai.instances[0].requests[0]
    system, user = request["messages"]
    assert system["role"] == "system" and '"ranked"' in system["content"]
    assert json.loads(user["content"]) == {
        "note": "quiet room",
        "candidates": CANDIDATES,
    }


def test_openai_requests_schema_enforced_output(openai_env, fake_openai):
    ai.rank_rooms("quiet", CANDIDATES)
    request = fake_openai.instances[0].requests[0]
    assert request["response_format"]["json_schema"]["schema"] == ai.RANKING_SCHEMA


def test_openai_propagates_failure_when_retry_also_fails(
    openai_env, fake_openai, monkeypatch
):
    def always_fail(**kwargs):
        raise RuntimeError("provider down")

    ai.rank_rooms("quiet", CANDIDATES)
    client = fake_openai.instances[0]
    client.chat.completions.create = always_fail

    monkeypatch.setattr("openai.OpenAI", lambda **kwargs: client)
    with pytest.raises(RuntimeError, match="provider down"):
        ai.rank_rooms("quiet", CANDIDATES)


# --- response parsing ------------------------------------------------------


def test_parse_plain_json():
    assert ai._parse_ranked(json.dumps({"ranked": RANKED})) == RANKED


def test_parse_strips_markdown_fences():
    text = "```json\n" + json.dumps({"ranked": RANKED}) + "\n```"
    assert ai._parse_ranked(text) == RANKED


def test_parse_strips_surrounding_prose():
    text = (
        "Sure! Here is the ranking:\n"
        + json.dumps({"ranked": RANKED})
        + "\nHope that helps."
    )
    assert ai._parse_ranked(text) == RANKED


def test_parse_rejects_empty_response():
    for text in (None, ""):
        with pytest.raises(ValueError, match="empty"):
            ai._parse_ranked(text)


def test_parse_rejects_response_without_json():
    with pytest.raises(ValueError, match="no JSON object"):
        ai._parse_ranked("I cannot help with that.")


def test_parse_rejects_missing_ranked_key():
    with pytest.raises(KeyError):
        ai._parse_ranked(json.dumps({"results": RANKED}))


def test_parse_rejects_non_list_ranked():
    with pytest.raises(ValueError, match="not a list"):
        ai._parse_ranked(json.dumps({"ranked": "room 2 then room 1"}))


def test_openai_parses_fenced_reply_end_to_end(openai_env, fake_openai):
    ai.rank_rooms("quiet", CANDIDATES)
    client = fake_openai.instances[0]
    client.reply = "```json\n" + json.dumps({"ranked": RANKED}) + "\n```"
    monkeypatched = client

    import openai

    openai.OpenAI = lambda **kwargs: (
        monkeypatched
    )  # restored by fake_openai's monkeypatch
    assert ai.rank_rooms("quiet", CANDIDATES) == RANKED
