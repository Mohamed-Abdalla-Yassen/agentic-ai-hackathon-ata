"""Managing your own profile."""

from tests.conftest import auth_header, register

PW = "pw12345"


def test_me_returns_the_signed_in_user(client, booker_auth):
    resp = client.get("/api/me", headers=auth_header(booker_auth["token"]))
    assert resp.status_code == 200
    assert resp.json() == booker_auth["user"]


def test_me_requires_a_token(client):
    assert client.get("/api/me").status_code == 401


def test_name_can_be_changed_without_a_password(client, booker_auth):
    resp = client.patch(
        "/api/me", json={"name": "New Name"}, headers=auth_header(booker_auth["token"])
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_changing_email_requires_the_current_password(client, booker_auth):
    headers = auth_header(booker_auth["token"])

    resp = client.patch("/api/me", json={"email": "new@example.com"}, headers=headers)
    assert resp.status_code == 400
    assert "current password" in resp.json()["error"]

    resp = client.patch(
        "/api/me",
        json={"email": "new@example.com", "current_password": "wrong"},
        headers=headers,
    )
    assert resp.status_code == 400

    resp = client.patch(
        "/api/me",
        json={"email": "new@example.com", "current_password": PW},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "new@example.com"


def test_the_new_email_is_what_you_log_in_with(client, booker_auth):
    client.patch(
        "/api/me",
        json={"email": "moved@example.com", "current_password": PW},
        headers=auth_header(booker_auth["token"]),
    )

    assert client.post("/api/auth/login", json={"email": "moved@example.com", "password": PW}).status_code == 200
    old = booker_auth["user"]["email"]
    assert client.post("/api/auth/login", json={"email": old, "password": PW}).status_code == 400


def test_email_cannot_be_taken_from_another_user(client, booker_auth):
    register(client, "booker", "taken@example.com")
    resp = client.patch(
        "/api/me",
        json={"email": "taken@example.com", "current_password": PW},
        headers=auth_header(booker_auth["token"]),
    )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["error"]


def test_keeping_your_own_email_is_not_a_conflict(client, booker_auth):
    """Re-submitting an unchanged email must not collide with yourself."""
    resp = client.patch(
        "/api/me",
        json={"email": booker_auth["user"]["email"], "current_password": PW},
        headers=auth_header(booker_auth["token"]),
    )
    assert resp.status_code == 200


def test_password_change_requires_the_current_one_and_takes_effect(client, booker_auth):
    headers = auth_header(booker_auth["token"])
    email = booker_auth["user"]["email"]

    assert client.patch("/api/me", json={"password": "brandnewpw"}, headers=headers).status_code == 400
    assert client.patch(
        "/api/me", json={"password": "brandnewpw", "current_password": "nope"}, headers=headers
    ).status_code == 400

    resp = client.patch(
        "/api/me", json={"password": "brandnewpw", "current_password": PW}, headers=headers
    )
    assert resp.status_code == 200

    assert client.post("/api/auth/login", json={"email": email, "password": "brandnewpw"}).status_code == 200
    assert client.post("/api/auth/login", json={"email": email, "password": PW}).status_code == 400


def test_short_passwords_are_rejected(client, booker_auth):
    resp = client.patch(
        "/api/me",
        json={"password": "short", "current_password": PW},
        headers=auth_header(booker_auth["token"]),
    )
    assert resp.status_code == 400


def test_role_cannot_be_changed_through_the_profile(client, booker_auth):
    """A booker promoting themselves to owner would be a privilege escalation."""
    resp = client.patch(
        "/api/me",
        json={"role": "owner", "current_password": PW},
        headers=auth_header(booker_auth["token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "booker"
    assert client.get("/api/me", headers=auth_header(booker_auth["token"])).json()["role"] == "booker"


def test_an_empty_update_is_a_no_op(client, booker_auth):
    resp = client.patch("/api/me", json={}, headers=auth_header(booker_auth["token"]))
    assert resp.status_code == 200
    assert resp.json() == booker_auth["user"]


def test_owners_can_manage_their_profile_too(client, owner_auth):
    resp = client.patch(
        "/api/me", json={"name": "Owner Renamed"}, headers=auth_header(owner_auth["token"])
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Owner Renamed"


def test_you_cannot_edit_another_users_profile(client, booker_auth):
    """There is no route that takes a user id — the token is the only subject."""
    other = register(client, "booker", "other@example.com")
    client.patch("/api/me", json={"name": "Changed"}, headers=auth_header(booker_auth["token"]))

    assert client.get("/api/me", headers=auth_header(other["token"])).json()["name"] == "Test User"
