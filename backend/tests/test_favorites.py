"""Saved rooms."""

from tests.conftest import auth_header, register


def setup_room(client, owner_token, name="Room A"):
    space = client.post(
        "/api/spaces",
        json={"name": "S", "address": "1 Str, Berlin", "contact_info": "c", "description": ""},
        headers=auth_header(owner_token),
    ).json()
    return client.post(
        f"/api/spaces/{space['id']}/rooms",
        json={"name": name, "capacity": 4, "price": 10, "price_unit": "hour", "amenities": [], "notes": ""},
        headers=auth_header(owner_token),
    ).json()


def test_booker_can_save_and_list_a_room(client, owner_auth, booker_auth):
    room = setup_room(client, owner_auth["token"])
    headers = auth_header(booker_auth["token"])

    assert client.put(f"/api/rooms/{room['id']}/favorite", headers=headers).status_code == 204

    favorites = client.get("/api/favorites", headers=headers).json()
    assert [f["roomId"] for f in favorites] == [room["id"]]
    assert favorites[0]["favorite"] is True


def test_saving_twice_is_a_no_op(client, owner_auth, booker_auth):
    room = setup_room(client, owner_auth["token"])
    headers = auth_header(booker_auth["token"])

    client.put(f"/api/rooms/{room['id']}/favorite", headers=headers)
    client.put(f"/api/rooms/{room['id']}/favorite", headers=headers)

    assert len(client.get("/api/favorites", headers=headers).json()) == 1


def test_unsaving_works_and_is_also_idempotent(client, owner_auth, booker_auth):
    room = setup_room(client, owner_auth["token"])
    headers = auth_header(booker_auth["token"])

    client.put(f"/api/rooms/{room['id']}/favorite", headers=headers)
    assert client.delete(f"/api/rooms/{room['id']}/favorite", headers=headers).status_code == 204
    assert client.get("/api/favorites", headers=headers).json() == []

    # Removing again is fine.
    assert client.delete(f"/api/rooms/{room['id']}/favorite", headers=headers).status_code == 204


def test_search_and_listing_report_whether_a_room_is_saved(client, owner_auth, booker_auth):
    room = setup_room(client, owner_auth["token"])
    headers = auth_header(booker_auth["token"])

    assert client.get("/api/search", headers=headers).json()["results"][0]["favorite"] is False
    assert client.get(f"/api/listings/{room['id']}", headers=headers).json()["favorite"] is False

    client.put(f"/api/rooms/{room['id']}/favorite", headers=headers)

    assert client.get("/api/search", headers=headers).json()["results"][0]["favorite"] is True
    assert client.get(f"/api/listings/{room['id']}", headers=headers).json()["favorite"] is True


def test_favorites_are_private_to_each_booker(client, owner_auth, booker_auth):
    room = setup_room(client, owner_auth["token"])
    client.put(f"/api/rooms/{room['id']}/favorite", headers=auth_header(booker_auth["token"]))

    other = register(client, "booker", "other@example.com")["token"]
    assert client.get("/api/favorites", headers=auth_header(other)).json() == []
    assert client.get("/api/search", headers=auth_header(other)).json()["results"][0]["favorite"] is False


def test_owners_cannot_use_favorites(client, owner_auth):
    room = setup_room(client, owner_auth["token"])
    headers = auth_header(owner_auth["token"])

    assert client.put(f"/api/rooms/{room['id']}/favorite", headers=headers).status_code == 403
    assert client.get("/api/favorites", headers=headers).status_code == 403


def test_saving_a_missing_room_is_404(client, booker_auth):
    assert client.put("/api/rooms/9999/favorite", headers=auth_header(booker_auth["token"])).status_code == 404


def test_favorites_carry_photos_and_room_detail(client, owner_auth, booker_auth):
    import io

    room = setup_room(client, owner_auth["token"], name="Photogenic")
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    client.post(
        f"/api/rooms/{room['id']}/photos",
        files={"file": ("a.png", io.BytesIO(png), "image/png")},
        headers=auth_header(owner_auth["token"]),
    )
    client.put(f"/api/rooms/{room['id']}/favorite", headers=auth_header(booker_auth["token"]))

    saved = client.get("/api/favorites", headers=auth_header(booker_auth["token"])).json()[0]
    assert saved["roomName"] == "Photogenic"
    assert len(saved["photos"]) == 1
    assert saved["address"] == "1 Str, Berlin"


def test_favorites_are_newest_first(client, owner_auth, booker_auth):
    first = setup_room(client, owner_auth["token"], name="First")
    second = setup_room(client, owner_auth["token"], name="Second")
    headers = auth_header(booker_auth["token"])

    client.put(f"/api/rooms/{first['id']}/favorite", headers=headers)
    client.put(f"/api/rooms/{second['id']}/favorite", headers=headers)

    names = [f["roomName"] for f in client.get("/api/favorites", headers=headers).json()]
    assert names[0] == "Second"
