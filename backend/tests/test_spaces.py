from tests.conftest import auth_header


def create_space(client, owner_auth, **overrides):
    body = {
        "name": "Test Space",
        "address": "1 Test St",
        "contact_info": "test@example.com",
        "description": "A space",
        **overrides,
    }
    return client.post("/api/spaces", json=body, headers=auth_header(owner_auth["token"]))


def test_create_space(client, owner_auth):
    resp = create_space(client, owner_auth)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["owner_id"] == owner_auth["user"]["id"]
    assert data["name"] == "Test Space"


def test_create_space_requires_owner_role(client, booker_auth):
    resp = create_space(client, booker_auth)
    assert resp.status_code == 403
    assert "error" in resp.json()


def test_list_my_spaces_nests_rooms(client, owner_auth):
    space = create_space(client, owner_auth).json()
    client.post(
        f"/api/spaces/{space['id']}/rooms",
        json={
            "name": "Room A",
            "capacity": 4,
            "price": 20,
            "price_unit": "hour",
            "amenities": ["wifi", "projector"],
            "notes": "nice room",
        },
        headers=auth_header(owner_auth["token"]),
    )

    resp = client.get("/api/spaces/mine", headers=auth_header(owner_auth["token"]))
    assert resp.status_code == 200
    spaces = resp.json()
    assert len(spaces) == 1
    assert len(spaces[0]["rooms"]) == 1
    assert spaces[0]["rooms"][0]["amenities"] == ["wifi", "projector"]


def test_create_room_under_nonexistent_space(client, owner_auth):
    resp = client.post(
        "/api/spaces/999999/rooms",
        json={"name": "R", "capacity": 2, "price": 10, "price_unit": "hour", "amenities": [], "notes": ""},
        headers=auth_header(owner_auth["token"]),
    )
    assert resp.status_code == 404
    assert "error" in resp.json()


def test_create_room_under_another_owners_space(client, owner_auth, booker_auth):
    space = create_space(client, owner_auth).json()

    # Register a second owner and try to add a room to the first owner's space.
    resp = client.post(
        "/api/auth/register",
        json={"name": "Other Owner", "email": "other-owner@example.com", "password": "pw12345", "role": "owner"},
    )
    other_token = resp.json()["token"]

    resp = client.post(
        f"/api/spaces/{space['id']}/rooms",
        json={"name": "R", "capacity": 2, "price": 10, "price_unit": "hour", "amenities": [], "notes": ""},
        headers=auth_header(other_token),
    )
    assert resp.status_code == 403
    assert "error" in resp.json()


def test_create_room_unknown_amenity(client, owner_auth):
    space = create_space(client, owner_auth).json()
    resp = client.post(
        f"/api/spaces/{space['id']}/rooms",
        json={
            "name": "R",
            "capacity": 2,
            "price": 10,
            "price_unit": "hour",
            "amenities": ["hot_tub"],
            "notes": "",
        },
        headers=auth_header(owner_auth["token"]),
    )
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_create_room_bad_price_unit(client, owner_auth):
    space = create_space(client, owner_auth).json()
    resp = client.post(
        f"/api/spaces/{space['id']}/rooms",
        json={
            "name": "R",
            "capacity": 2,
            "price": 10,
            "price_unit": "month",
            "amenities": [],
            "notes": "",
        },
        headers=auth_header(owner_auth["token"]),
    )
    assert resp.status_code == 400
    assert "error" in resp.json()
