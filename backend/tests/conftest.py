import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    """Point config at a throwaway DB/secret for every test, so the app never
    touches real environment values or a real Anthropic key."""
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "test-model")


@pytest.fixture
def client(env):
    from app.db import get_connection, init_schema

    conn = get_connection()
    init_schema(conn)
    conn.close()

    from app.main import app

    return TestClient(app)


def register(client: TestClient, role: str, email: str, name: str = "Test User", password: str = "pw12345") -> dict:
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
