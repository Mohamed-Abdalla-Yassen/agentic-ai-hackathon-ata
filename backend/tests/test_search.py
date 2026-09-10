from tests.conftest import auth_header


def setup_listing(client, owner_auth, **room_overrides):
    space = client.post(
        "/api/spaces",
        json={"name": "Berlin Space", "address": "5 Berlin Str, Berlin", "contact_info": "c", "description": ""},
        headers=auth_header(owner_auth["token"]),
    ).json()

    room_body = {
        "name": "Room A",
        "capacity": 6,
        "price": 50,
        "price_unit": "hour",
        "amenities": ["wifi", "projector"],
        "notes": "quiet room with natural light",
        **room_overrides,
    }
    room = client.post(
        f"/api/spaces/{space['id']}/rooms", json=room_body, headers=auth_header(owner_auth["token"])
    ).json()
    return space, room


def test_search_requires_booker_role(client, owner_auth):
    resp = client.get("/api/search", headers=auth_header(owner_auth["token"]))
    assert resp.status_code == 403
    assert "error" in resp.json()


def test_search_filters_by_location(client, owner_auth, booker_auth):
    setup_listing(client, owner_auth)
    resp = client.get("/api/search?location=Berlin", headers=auth_header(booker_auth["token"]))
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 1

    resp = client.get("/api/search?location=Hamburg", headers=auth_header(booker_auth["token"]))
    assert resp.json()["results"] == []


def test_search_filters_by_capacity(client, owner_auth, booker_auth):
    setup_listing(client, owner_auth, capacity=6)
    resp = client.get("/api/search?capacity=10", headers=auth_header(booker_auth["token"]))
    assert resp.json()["results"] == []

    resp = client.get("/api/search?capacity=4", headers=auth_header(booker_auth["token"]))
    assert len(resp.json()["results"]) == 1


def test_search_filters_by_price_max(client, owner_auth, booker_auth):
    setup_listing(client, owner_auth, price=50)
    resp = client.get("/api/search?priceMax=20", headers=auth_header(booker_auth["token"]))
    assert resp.json()["results"] == []

    resp = client.get("/api/search?priceMax=100", headers=auth_header(booker_auth["token"]))
    assert len(resp.json()["results"]) == 1


def test_search_filters_by_amenities(client, owner_auth, booker_auth):
    setup_listing(client, owner_auth, amenities=["wifi"])
    resp = client.get("/api/search?amenities=wifi,projector", headers=auth_header(booker_auth["token"]))
    assert resp.json()["results"] == []

    resp = client.get("/api/search?amenities=wifi", headers=auth_header(booker_auth["token"]))
    assert len(resp.json()["results"]) == 1


def test_search_without_note_skips_ai_and_returns_sql_order(client, owner_auth, booker_auth, monkeypatch):
    _, room1 = setup_listing(client, owner_auth)
    _, room2 = setup_listing(client, owner_auth)

    called = []
    monkeypatch.setattr("app.routers.search.rank_rooms", lambda note, candidates: called.append(1) or [])

    resp = client.get("/api/search", headers=auth_header(booker_auth["token"]))
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert [r["roomId"] for r in results] == [room1["id"], room2["id"]]
    assert all(r["reason"] is None for r in results)
    assert called == []  # AI must not be called when note is empty


def test_search_with_note_reorders_and_attaches_reasons(client, owner_auth, booker_auth, monkeypatch):
    _, room1 = setup_listing(client, owner_auth)
    _, room2 = setup_listing(client, owner_auth)

    def fake_rank(note, candidates):
        return [
            {"room_id": room2["id"], "reason": "Better fit"},
            {"room_id": room1["id"], "reason": "Also fine"},
        ]

    monkeypatch.setattr("app.routers.search.rank_rooms", fake_rank)

    resp = client.get("/api/search?note=quiet+focused+work", headers=auth_header(booker_auth["token"]))
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert [r["roomId"] for r in results] == [room2["id"], room1["id"]]
    assert results[0]["reason"] == "Better fit"
    assert results[1]["reason"] == "Also fine"


def test_search_falls_back_when_ai_raises(client, owner_auth, booker_auth, monkeypatch):
    _, room1 = setup_listing(client, owner_auth)

    def fake_rank(note, candidates):
        raise RuntimeError("simulated API failure")

    monkeypatch.setattr("app.routers.search.rank_rooms", fake_rank)

    resp = client.get("/api/search?note=anything", headers=auth_header(booker_auth["token"]))
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert [r["roomId"] for r in results] == [room1["id"]]
    assert results[0]["reason"] is None


def test_search_appends_candidates_the_model_omitted(client, owner_auth, booker_auth, monkeypatch):
    _, room1 = setup_listing(client, owner_auth)
    _, room2 = setup_listing(client, owner_auth)

    def fake_rank(note, candidates):
        # Only ranks room1, "forgetting" room2.
        return [{"room_id": room1["id"], "reason": "Great fit"}]

    monkeypatch.setattr("app.routers.search.rank_rooms", fake_rank)

    resp = client.get("/api/search?note=something", headers=auth_header(booker_auth["token"]))
    results = resp.json()["results"]
    assert {r["roomId"] for r in results} == {room1["id"], room2["id"]}
    assert [r["roomId"] for r in results][0] == room1["id"]
    omitted = [r for r in results if r["roomId"] == room2["id"]][0]
    assert omitted["reason"] is None


def test_get_listing(client, owner_auth, booker_auth):
    _, room = setup_listing(client, owner_auth)
    resp = client.get(f"/api/listings/{room['id']}", headers=auth_header(booker_auth["token"]))
    assert resp.status_code == 200
    data = resp.json()
    assert data["roomId"] == room["id"]
    assert "reason" not in data


def test_get_listing_not_found(client, booker_auth):
    resp = client.get("/api/listings/999999", headers=auth_header(booker_auth["token"]))
    assert resp.status_code == 404
    assert "error" in resp.json()
