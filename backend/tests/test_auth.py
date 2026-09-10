from tests.conftest import auth_header, register


def test_register_owner_and_booker(client):
    owner = register(client, "owner", "owner1@example.com")
    booker = register(client, "booker", "booker1@example.com")
    assert owner["user"]["role"] == "owner"
    assert booker["user"]["role"] == "booker"
    assert "password" not in owner["user"]
    assert "token" in owner


def test_register_duplicate_email(client):
    register(client, "owner", "dupe@example.com")
    resp = client.post(
        "/api/auth/register",
        json={"name": "Again", "email": "dupe@example.com", "password": "pw12345", "role": "booker"},
    )
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_register_bad_role(client):
    resp = client.post(
        "/api/auth/register",
        json={"name": "X", "email": "x@example.com", "password": "pw12345", "role": "admin"},
    )
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_login_success(client):
    register(client, "booker", "login@example.com", password="secretpw")
    resp = client.post("/api/auth/login", json={"email": "login@example.com", "password": "secretpw"})
    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == "login@example.com"


def test_login_wrong_password(client):
    register(client, "booker", "wrongpw@example.com", password="secretpw")
    resp = client.post("/api/auth/login", json={"email": "wrongpw@example.com", "password": "nope"})
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_login_unknown_email(client):
    resp = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "whatever"})
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_missing_token_is_401(client):
    resp = client.get("/api/spaces/mine")
    assert resp.status_code == 401
    assert "error" in resp.json()


def test_garbage_token_is_401(client):
    resp = client.get("/api/spaces/mine", headers=auth_header("not-a-real-token"))
    assert resp.status_code == 401
    assert "error" in resp.json()
