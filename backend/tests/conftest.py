import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    """Point config at a throwaway DB/secret for every test, so the app never
    touches real environment values or a real provider key.

    Provider vars for both backends are cleared first — a developer's own .env
    is already loaded by app.config at import time, and a stray AI_PROVIDER or
    base URL there would otherwise change what these tests exercise.
    """
    for name in (
        "AI_PROVIDER",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "OPENAI_BASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-openai-model")
    # Uploads too: any test that posts a photo must write into a throwaway
    # directory, never the real one. This lives here rather than in the photo
    # tests because several other suites upload a file incidentally, and each
    # one that forgot would quietly litter the developer's data directory.
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Rate-limit counters live in module state, so they would otherwise leak
    between tests and fail whichever test happened to run after a burst."""
    from app.ratelimit import limiter

    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def client(env):
    from app.db import get_connection, init_schema

    conn = get_connection()
    init_schema(conn)
    conn.close()

    from app.main import app

    return TestClient(app)


def register(
    client: TestClient,
    role: str,
    email: str,
    name: str = "Test User",
    password: str = "pw12345",
) -> dict:
    resp = client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password, "role": role},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def owner_auth(client):
    data = register(client, "owner", "owner@example.com")
    return {"token": data["token"], "user": data["user"]}


@pytest.fixture
def booker_auth(client):
    data = register(client, "booker", "booker@example.com")
    return {"token": data["token"], "user": data["user"]}


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
