"""Owner editing of a room after it is published."""

from tests.conftest import auth_header, register


def setup_room(client, owner_token, **overrides):
    space = client.post(
        "/api/spaces",
        json={"name": "S", "address": "1 Str, Berlin", "contact_info": "c", "description": ""},
        headers=auth_header(owner_token),
    ).json()
    body = {
        "name": "Room A",
        "capacity": 6,
        "price": 50,
        "price_unit": "hour",
        "amenities": ["wifi"],
        "notes": "original notes",
        **overrides,
    }
    room = client.post(
        f"/api/spaces/{space['id']}/rooms", json=body, headers=auth_header(owner_token)
    ).json()
    return space, room


def test_owner_can_read_their_room(client, owner_auth):
    _, room = setup_room(client, owner_auth["token"])
    resp = client.get(f"/api/rooms/{room['id']}", headers=auth_header(owner_auth["token"]))
    assert resp.status_code == 200
    assert resp.json()["name"] == "Room A"


def test_owner_can_edit_every_field(client, owner_auth):
    _, room = setup_room(client, owner_auth["token"])

    resp = client.patch(
        f"/api/rooms/{room['id']}",
        json={
            "name": "Renamed Room",
            "capacity": 12,
            "price": 99.5,
            "price_unit": "day",
            "amenities": ["wifi", "projector"],
            "notes": "updated notes",
        },
        headers=auth_header(owner_auth["token"]),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "Renamed Room"
    assert body["capacity"] == 12
    assert body["price"] == 99.5
    assert body["price_unit"] == "day"
    assert body["amenities"] == ["wifi", "projector"]
    assert body["notes"] == "updated notes"


def test_a_partial_edit_leaves_other_fields_alone(client, owner_auth):
    """The whole point of PATCH — sending one field must not blank the rest."""
    _, room = setup_room(client, owner_auth["token"])

    resp = client.patch(
        f"/api/rooms/{room['id']}",
        json={"price": 75},
        headers=auth_header(owner_auth["token"]),
    )
    body = resp.json()
    assert body["price"] == 75
    assert body["name"] == "Room A"
    assert body["capacity"] == 6
    assert body["amenities"] == ["wifi"]
    assert body["notes"] == "original notes"


def test_notes_can_be_cleared(client, owner_auth):
    """An empty string is a real value, distinct from an omitted field."""
    _, room = setup_room(client, owner_auth["token"])
    resp = client.patch(
        f"/api/rooms/{room['id']}", json={"notes": ""}, headers=auth_header(owner_auth["token"])
    )
    assert resp.json()["notes"] == ""


def test_amenities_can_be_emptied(client, owner_auth):
    _, room = setup_room(client, owner_auth["token"])
    resp = client.patch(
        f"/api/rooms/{room['id']}",
        json={"amenities": []},
        headers=auth_header(owner_auth["token"]),
    )
    assert resp.json()["amenities"] == []


def test_an_empty_patch_is_a_harmless_no_op(client, owner_auth):
    _, room = setup_room(client, owner_auth["token"])
    resp = client.patch(
        f"/api/rooms/{room['id']}", json={}, headers=auth_header(owner_auth["token"])
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Room A"


def test_edits_are_visible_to_bookers(client, owner_auth, booker_auth):
    _, room = setup_room(client, owner_auth["token"])
    client.patch(
        f"/api/rooms/{room['id']}",
        json={"name": "Now Called This", "price": 5},
        headers=auth_header(owner_auth["token"]),
    )

    listing = client.get(f"/api/listings/{room['id']}", headers=auth_header(booker_auth["token"]))
    assert listing.json()["roomName"] == "Now Called This"

    results = client.get("/api/search", headers=auth_header(booker_auth["token"])).json()["results"]
    assert results[0]["roomName"] == "Now Called This"
    assert results[0]["price"] == 5


def test_edited_room_still_respects_search_filters(client, owner_auth, booker_auth):
    """Editing capacity must change who the room shows up for."""
    _, room = setup_room(client, owner_auth["token"], capacity=4)
    assert client.get("/api/search?capacity=10", headers=auth_header(booker_auth["token"])).json()["results"] == []

    client.patch(
        f"/api/rooms/{room['id']}", json={"capacity": 20}, headers=auth_header(owner_auth["token"])
    )
    results = client.get("/api/search?capacity=10", headers=auth_header(booker_auth["token"])).json()["results"]
    assert len(results) == 1


def test_editing_does_not_disturb_photos(client, owner_auth):
    import io

    _, room = setup_room(client, owner_auth["token"])
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    client.post(
        f"/api/rooms/{room['id']}/photos",
        files={"file": ("a.png", io.BytesIO(png), "image/png")},
        headers=auth_header(owner_auth["token"]),
    )

    resp = client.patch(
        f"/api/rooms/{room['id']}", json={"name": "Edited"}, headers=auth_header(owner_auth["token"])
    )
    assert len(resp.json()["photos"]) == 1


# --- Authorisation and validation ------------------------------------------


def test_owners_cannot_edit_someone_elses_room(client, owner_auth):
    _, room = setup_room(client, owner_auth["token"])
    intruder = register(client, "owner", "intruder@example.com")["token"]

    resp = client.patch(
        f"/api/rooms/{room['id']}", json={"name": "Hijacked"}, headers=auth_header(intruder)
    )
    assert resp.status_code == 403

    # And nothing changed.
    check = client.get(f"/api/rooms/{room['id']}", headers=auth_header(owner_auth["token"]))
    assert check.json()["name"] == "Room A"


def test_bookers_cannot_edit_rooms(client, owner_auth, booker_auth):
    _, room = setup_room(client, owner_auth["token"])
    resp = client.patch(
        f"/api/rooms/{room['id']}", json={"name": "x"}, headers=auth_header(booker_auth["token"])
    )
    assert resp.status_code == 403


def test_editing_a_missing_room_is_404(client, owner_auth):
    resp = client.patch("/api/rooms/9999", json={"name": "x"}, headers=auth_header(owner_auth["token"]))
    assert resp.status_code == 404


def test_edit_rejects_what_creation_would_have_rejected(client, owner_auth):
    _, room = setup_room(client, owner_auth["token"])
    headers = auth_header(owner_auth["token"])

    for bad in [
        {"capacity": 0},
        {"capacity": -3},
        {"price": -1},
        {"price_unit": "week"},
        {"amenities": ["helipad"]},
        {"name": ""},
    ]:
        resp = client.patch(f"/api/rooms/{room['id']}", json=bad, headers=headers)
        assert resp.status_code == 400, f"{bad} was accepted"
        assert "error" in resp.json()
