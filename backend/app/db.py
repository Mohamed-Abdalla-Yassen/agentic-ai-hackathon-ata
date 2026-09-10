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
