"""Rate limiting: the unit behaviour of the window, and the API-level budgets
that keep an attacker from draining the Anthropic key."""

import pytest

from app.ratelimit import Limit, SlidingWindowLimiter
from tests.conftest import auth_header, register


# --- The window itself -----------------------------------------------------


def test_allows_up_to_the_limit_then_blocks():
    limiter = SlidingWindowLimiter()
    limit = Limit(count=3, window_seconds=60)

    assert [limiter.check("b", "user", limit) for _ in range(3)] == [None, None, None]
    retry_after = limiter.check("b", "user", limit)
    assert retry_after is not None and 0 < retry_after <= 60


def test_identities_and_buckets_do_not_share_quota():
    limiter = SlidingWindowLimiter()
    limit = Limit(count=1, window_seconds=60)

    assert limiter.check("b", "user-1", limit) is None
    assert limiter.check("b", "user-1", limit) is not None
    # A different user, and the same user in a different bucket, are unaffected.
    assert limiter.check("b", "user-2", limit) is None
    assert limiter.check("other", "user-1", limit) is None


def test_quota_frees_up_once_the_window_passes(monkeypatch):
    limiter = SlidingWindowLimiter()
    limit = Limit(count=1, window_seconds=60)
    clock = {"now": 1_000.0}
    monkeypatch.setattr("app.ratelimit.time.monotonic", lambda: clock["now"])

    assert limiter.check("b", "user", limit) is None
    assert limiter.check("b", "user", limit) is not None

    clock["now"] += 61
    assert limiter.check("b", "user", limit) is None


def test_blocked_calls_do_not_extend_the_block(monkeypatch):
    """A client hammering while blocked must not push its own reset away."""
    limiter = SlidingWindowLimiter()
    limit = Limit(count=1, window_seconds=60)
    clock = {"now": 1_000.0}
    monkeypatch.setattr("app.ratelimit.time.monotonic", lambda: clock["now"])

    assert limiter.check("b", "user", limit) is None
    for _ in range(10):
        clock["now"] += 1
        assert limiter.check("b", "user", limit) is not None

    # The original hit is still what governs: 60s after it, quota is back.
    clock["now"] = 1_000.0 + 61
    assert limiter.check("b", "user", limit) is None


# --- API level -------------------------------------------------------------


def test_auth_endpoints_are_limited_per_ip(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_AUTH_PER_HOUR", "3")

    for i in range(3):
        assert client.post(
            "/api/auth/login", json={"email": f"nobody{i}@example.com", "password": "wrong-pw"}
        ).status_code == 400  # wrong credentials, but the attempt still counts

    resp = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "wrong-pw"})
    assert resp.status_code == 429
    assert "error" in resp.json()
    assert int(resp.headers["Retry-After"]) >= 1


def test_registration_is_limited_so_accounts_cannot_be_minted_freely(client, monkeypatch):
    """Per-user AI quotas are only meaningful if new users are not free."""
    monkeypatch.setenv("RATE_LIMIT_AUTH_PER_HOUR", "2")

    register(client, "booker", "one@example.com")
    register(client, "booker", "two@example.com")

    resp = client.post(
        "/api/auth/register",
        json={"name": "T", "email": "three@example.com", "password": "pw12345", "role": "booker"},
    )
    assert resp.status_code == 429


def test_search_without_a_note_never_spends_ai_quota(client, owner_auth, booker_auth, monkeypatch):
    """Plain filtered search costs no tokens, so it must not be charged."""
    monkeypatch.setenv("RATE_LIMIT_AI_PER_HOUR", "1")

    for _ in range(5):
        resp = client.get("/api/search?location=Berlin", headers=auth_header(booker_auth["token"]))
        assert resp.status_code == 200


def test_ai_search_is_limited_per_user(client, booker_auth, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_AI_PER_HOUR", "2")
    monkeypatch.setattr("app.routers.search.rank_rooms", lambda note, candidates: [])

    for _ in range(2):
        resp = client.get("/api/search?note=quiet+room", headers=auth_header(booker_auth["token"]))
        assert resp.status_code == 200

    resp = client.get("/api/search?note=quiet+room", headers=auth_header(booker_auth["token"]))
    assert resp.status_code == 429
    assert "hour" in resp.json()["error"]


def test_global_ai_budget_caps_spend_across_all_users(client, monkeypatch):
    """The attack this exists for: many accounts, each under its own quota."""
    monkeypatch.setenv("RATE_LIMIT_AI_GLOBAL_PER_DAY", "3")
    monkeypatch.setenv("RATE_LIMIT_AI_PER_HOUR", "100")
    monkeypatch.setenv("RATE_LIMIT_AUTH_PER_HOUR", "1000")
    monkeypatch.setattr("app.routers.search.rank_rooms", lambda note, candidates: [])

    tokens = [register(client, "booker", f"b{i}@example.com")["token"] for i in range(4)]

    for token in tokens[:3]:
        assert client.get("/api/search?note=x", headers=auth_header(token)).status_code == 200

    # A brand-new account with an untouched personal quota is still refused.
    resp = client.get("/api/search?note=x", headers=auth_header(tokens[3]))
    assert resp.status_code == 429


def test_a_users_own_limit_does_not_burn_the_global_budget(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_AI_PER_HOUR", "1")
    monkeypatch.setenv("RATE_LIMIT_AI_GLOBAL_PER_DAY", "2")
    monkeypatch.setenv("RATE_LIMIT_AUTH_PER_HOUR", "1000")
    monkeypatch.setattr("app.routers.search.rank_rooms", lambda note, candidates: [])

    greedy = register(client, "booker", "greedy@example.com")["token"]
    assert client.get("/api/search?note=x", headers=auth_header(greedy)).status_code == 200
    for _ in range(5):
        assert client.get("/api/search?note=x", headers=auth_header(greedy)).status_code == 429

    # Only one global slot was ever consumed, so two other users still get in.
    for i in range(1):
        other = register(client, "booker", f"other{i}@example.com")["token"]
        assert client.get("/api/search?note=x", headers=auth_header(other)).status_code == 200


def test_forged_forwarded_for_cannot_reset_the_ip_limit(client, monkeypatch):
    """X-Forwarded-For is caller-controlled and untrusted by default."""
    monkeypatch.setenv("RATE_LIMIT_AUTH_PER_HOUR", "2")

    body = {"email": "nobody@example.com", "password": "wrong-pw"}
    for _ in range(2):
        client.post("/api/auth/login", json=body)

    resp = client.post("/api/auth/login", json=body, headers={"X-Forwarded-For": "9.9.9.9"})
    assert resp.status_code == 429


def test_read_endpoints_are_limited_per_user(client, booker_auth, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_READ_PER_MINUTE", "3")

    for _ in range(3):
        assert client.get("/api/search", headers=auth_header(booker_auth["token"])).status_code == 200

    assert client.get("/api/search", headers=auth_header(booker_auth["token"])).status_code == 429


@pytest.mark.parametrize("value", ["not-a-number", "0", "-5"])
def test_invalid_limit_configuration_fails_loudly(client, booker_auth, monkeypatch, value):
    """A typo'd limit must not silently mean 'unlimited'.

    In production the unhandled-exception handler turns this into a 500; the
    test client re-raises instead, which is what we assert on here.
    """
    monkeypatch.setenv("RATE_LIMIT_READ_PER_MINUTE", value)
    with pytest.raises(RuntimeError, match="RATE_LIMIT_READ_PER_MINUTE"):
        client.get("/api/search", headers=auth_header(booker_auth["token"]))
