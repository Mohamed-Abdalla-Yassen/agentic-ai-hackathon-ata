"""Room photo upload, serving, deletion — and the abuse cases in between."""

import io

import pytest

from tests.conftest import auth_header, register

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 64


@pytest.fixture(autouse=True)
def uploads_to_tmp(tmp_path, monkeypatch):
    """Never write test images into the real upload directory."""
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))


def make_room(client, owner_token):
    space = client.post(
        "/api/spaces",
        json={"name": "S", "address": "1 Str, Berlin", "contact_info": "c", "description": ""},
        headers=auth_header(owner_token),
    ).json()
    room = client.post(
        f"/api/spaces/{space['id']}/rooms",
        json={"name": "R", "capacity": 4, "price": 10, "price_unit": "hour", "amenities": [], "notes": ""},
        headers=auth_header(owner_token),
    ).json()
    return space, room


def upload(client, token, room_id, content=PNG, filename="photo.png", content_type="image/png"):
    return client.post(
        f"/api/rooms/{room_id}/photos",
        files={"file": (filename, io.BytesIO(content), content_type)},
        headers=auth_header(token),
    )


# --- Happy path ------------------------------------------------------------


@pytest.mark.parametrize("content,name,declared", [(PNG, "a.png", "image/png"), (JPEG, "a.jpg", "image/jpeg"), (WEBP, "a.webp", "image/webp")])
def test_owner_can_upload_each_allowed_format(client, owner_auth, content, name, declared):
    _, room = make_room(client, owner_auth["token"])
    resp = upload(client, owner_auth["token"], room["id"], content, name, declared)
    assert resp.status_code == 201, resp.text
    assert resp.json()["url"] == f"/api/photos/{resp.json()['id']}"


def test_uploaded_photo_is_served_back(client, owner_auth):
    _, room = make_room(client, owner_auth["token"])
    photo = upload(client, owner_auth["token"], room["id"]).json()

    resp = client.get(photo["url"])
    assert resp.status_code == 200
    assert resp.content == PNG
    assert resp.headers["content-type"] == "image/png"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"


def test_photos_appear_on_listing_and_search(client, owner_auth, booker_auth):
    _, room = make_room(client, owner_auth["token"])
    photo = upload(client, owner_auth["token"], room["id"]).json()

    listing = client.get(f"/api/listings/{room['id']}", headers=auth_header(booker_auth["token"]))
    assert listing.json()["photos"] == [photo["url"]]

    results = client.get("/api/search", headers=auth_header(booker_auth["token"])).json()["results"]
    assert results[0]["photos"] == [photo["url"]]


def test_rooms_without_photos_report_an_empty_list(client, owner_auth, booker_auth):
    _, room = make_room(client, owner_auth["token"])
    listing = client.get(f"/api/listings/{room['id']}", headers=auth_header(booker_auth["token"]))
    assert listing.json()["photos"] == []


def test_owner_can_delete_their_photo(client, owner_auth):
    _, room = make_room(client, owner_auth["token"])
    photo = upload(client, owner_auth["token"], room["id"]).json()

    assert client.delete(f"/api/photos/{photo['id']}", headers=auth_header(owner_auth["token"])).status_code == 204
    assert client.get(photo["url"]).status_code == 404


# --- Authorisation ---------------------------------------------------------


def test_bookers_cannot_upload(client, owner_auth, booker_auth):
    _, room = make_room(client, owner_auth["token"])
    assert upload(client, booker_auth["token"], room["id"]).status_code == 403


def test_owners_cannot_upload_to_someone_elses_room(client, owner_auth):
    _, room = make_room(client, owner_auth["token"])
    intruder = register(client, "owner", "intruder@example.com")["token"]
    assert upload(client, intruder, room["id"]).status_code == 403


def test_owners_cannot_delete_someone_elses_photo(client, owner_auth):
    _, room = make_room(client, owner_auth["token"])
    photo = upload(client, owner_auth["token"], room["id"]).json()

    intruder = register(client, "owner", "intruder@example.com")["token"]
    assert client.delete(f"/api/photos/{photo['id']}", headers=auth_header(intruder)).status_code == 403
    # And the photo is untouched.
    assert client.get(photo["url"]).status_code == 200


def test_upload_to_a_missing_room_is_404(client, owner_auth):
    assert upload(client, owner_auth["token"], 9999).status_code == 404


# --- Hostile input ---------------------------------------------------------


def test_a_script_renamed_as_an_image_is_rejected(client, owner_auth):
    """Content-Type is a claim; the file's own bytes decide."""
    _, room = make_room(client, owner_auth["token"])
    resp = upload(client, owner_auth["token"], room["id"], b"<?php system($_GET['c']); ?>", "shell.png", "image/png")
    assert resp.status_code == 400
    assert "unsupported image format" in resp.json()["error"]


def test_svg_is_rejected(client, owner_auth):
    """SVG renders as an image but can carry script, so it is not allowed."""
    _, room = make_room(client, owner_auth["token"])
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    assert upload(client, owner_auth["token"], room["id"], svg, "x.svg", "image/svg+xml").status_code == 400


def test_a_riff_file_that_is_not_webp_is_rejected(client, owner_auth):
    """RIFF alone covers .wav and friends — the WEBP marker is what counts."""
    _, room = make_room(client, owner_auth["token"])
    wav = b"RIFF" + b"\x00\x00\x00\x00" + b"WAVE" + b"\x00" * 32
    assert upload(client, owner_auth["token"], room["id"], wav, "x.webp", "image/webp").status_code == 400


def test_an_empty_file_is_rejected(client, owner_auth):
    _, room = make_room(client, owner_auth["token"])
    assert upload(client, owner_auth["token"], room["id"], b"", "empty.png").status_code == 400


def test_oversized_uploads_are_rejected_and_leave_no_file(client, owner_auth, monkeypatch, tmp_path):
    monkeypatch.setenv("MAX_PHOTO_BYTES", "1024")
    _, room = make_room(client, owner_auth["token"])

    resp = upload(client, owner_auth["token"], room["id"], PNG + b"\x00" * 4096)
    assert resp.status_code == 400
    assert "larger than" in resp.json()["error"]

    uploads = tmp_path / "uploads"
    assert not any(uploads.iterdir()) if uploads.exists() else True


def test_a_traversal_filename_cannot_escape_the_upload_directory(client, owner_auth, tmp_path):
    """The uploader's filename is discarded, so it cannot steer the write."""
    _, room = make_room(client, owner_auth["token"])
    resp = upload(client, owner_auth["token"], room["id"], PNG, "../../../../etc/evil.png")
    assert resp.status_code == 201

    stored = list((tmp_path / "uploads").iterdir())
    assert len(stored) == 1
    assert stored[0].name.endswith(".png")
    assert "evil" not in stored[0].name


def test_photo_count_per_room_is_capped(client, owner_auth, monkeypatch):
    monkeypatch.setenv("MAX_PHOTOS_PER_ROOM", "2")
    _, room = make_room(client, owner_auth["token"])

    assert upload(client, owner_auth["token"], room["id"]).status_code == 201
    assert upload(client, owner_auth["token"], room["id"]).status_code == 201

    resp = upload(client, owner_auth["token"], room["id"])
    assert resp.status_code == 400
    assert "already has 2 photos" in resp.json()["error"]


def test_uploads_are_rate_limited(client, owner_auth, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_UPLOAD_PER_HOUR", "2")
    _, room = make_room(client, owner_auth["token"])

    upload(client, owner_auth["token"], room["id"])
    upload(client, owner_auth["token"], room["id"])
    assert upload(client, owner_auth["token"], room["id"]).status_code == 429


def test_missing_photo_id_is_404(client):
    assert client.get("/api/photos/9999").status_code == 404
