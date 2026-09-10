"""SQLite connection and query helpers (raw sqlite3, no ORM)."""

import sqlite3
from typing import Any, Iterable

from app.config import database_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('owner', 'booker'))
);

CREATE TABLE IF NOT EXISTS spaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    contact_info TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    space_id INTEGER NOT NULL REFERENCES spaces(id),
    name TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    price REAL NOT NULL,
    price_unit TEXT NOT NULL CHECK (price_unit IN ('hour', 'day')),
    amenities TEXT NOT NULL DEFAULT ',',
    notes TEXT NOT NULL DEFAULT ''
);

-- Uploaded room photos. The image bytes live on disk (see app/photos.py); only
-- the metadata is stored here. `stored_name` is a generated filename, never
-- anything the uploader chose. ON DELETE CASCADE keeps rows from outliving the
-- room, though the files themselves still need an explicit unlink.
CREATE TABLE IF NOT EXISTS room_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    stored_name TEXT NOT NULL UNIQUE,
    content_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_room_photos_room ON room_photos(room_id);

-- A booker's saved rooms. The composite primary key makes favouriting the same
-- room twice a no-op instead of a duplicate row, so the endpoint can be
-- idempotent without a read-then-write race.
CREATE TABLE IF NOT EXISTS favorites (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, room_id)
);

CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
"""


def get_connection() -> sqlite3.Connection:
    """Open a fresh connection to the configured database file.

    Called once per request via a FastAPI dependency (see app.deps), and once
    by seed.py / test fixtures — never shared across threads.
    """
    conn = sqlite3.connect(database_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def query_all(conn: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[dict]:
    rows = conn.execute(sql, tuple(params)).fetchall()
    return [dict(row) for row in rows]


def query_one(conn: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> dict | None:
    row = conn.execute(sql, tuple(params)).fetchone()
    return dict(row) if row is not None else None


def execute(conn: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> int:
    """Run an INSERT/UPDATE/DELETE, commit, and return lastrowid."""
    cursor = conn.execute(sql, tuple(params))
    conn.commit()
    return cursor.lastrowid


# --- Amenities encoding -----------------------------------------------------
#
# Amenities are stored as a comma-delimited string with sentinel commas on
# both ends, e.g. ",wifi,projector,". That lets the search hard-filter check
# "does this room have amenity X" with a plain `LIKE '%,wifi,%'` clause per
# required amenity, with no join table. These two helpers are the only place
# that encoding should ever be touched.


def encode_amenities(amenities: list[str]) -> str:
    if not amenities:
        return ","
    return "," + ",".join(amenities) + ","


def decode_amenities(encoded: str) -> list[str]:
    return [a for a in encoded.split(",") if a]


# --- Photos -----------------------------------------------------------------


def photos_by_room(conn: sqlite3.Connection, room_ids: Iterable[int]) -> dict[int, list[dict]]:
    """Map room id -> photo records, in one query rather than one query per room.

    Owners need the id (to delete a photo); bookers only ever need the url.
    """
    ids = list(room_ids)
    if not ids:
        return {}

    from app.photos import public_url

    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT id, room_id, content_type, size_bytes FROM room_photos "
        f"WHERE room_id IN ({placeholders}) ORDER BY id",
        tuple(ids),
    ).fetchall()

    by_room: dict[int, list[dict]] = {room_id: [] for room_id in ids}
    for row in rows:
        by_room[row["room_id"]].append(
            {
                "id": row["id"],
                "url": public_url(row["id"]),
                "content_type": row["content_type"],
                "size": row["size_bytes"],
            }
        )
    return by_room


def photo_urls_by_room(conn: sqlite3.Connection, room_ids: Iterable[int]) -> dict[int, list[str]]:
    """Map room id -> photo URLs. What the booker-facing payloads carry."""
    return {
        room_id: [photo["url"] for photo in photos]
        for room_id, photos in photos_by_room(conn, room_ids).items()
    }


# --- Favorites ---------------------------------------------------------------


def favorite_room_ids(conn: sqlite3.Connection, user_id: int, room_ids: Iterable[int]) -> set[int]:
    """Which of these rooms the user has favourited.

    Scoped to the rooms actually being rendered rather than fetching the user's
    whole favourites list, so a long-standing user does not pay for their
    history on every search.
    """
    ids = list(room_ids)
    if not ids:
        return set()

    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT room_id FROM favorites WHERE user_id = ? AND room_id IN ({placeholders})",
        (user_id, *ids),
    ).fetchall()
    return {row["room_id"] for row in rows}
