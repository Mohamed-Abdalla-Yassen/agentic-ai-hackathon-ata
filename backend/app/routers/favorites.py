"""A booker's saved rooms."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.db import decode_amenities, execute, photo_urls_by_room, query_all, query_one
from app.deps import db_conn, require_booker
from app.schemas import SearchResult

router = APIRouter(tags=["favorites"])


def _existing_room(conn: sqlite3.Connection, room_id: int) -> dict:
    room = query_one(conn, "SELECT id FROM rooms WHERE id = ?", (room_id,))
    if room is None:
        raise HTTPException(status_code=404, detail="room not found")
    return room


@router.put("/rooms/{room_id}/favorite", status_code=204)
def add_favorite(
    room_id: int,
    booker: dict = Depends(require_booker),
    conn: sqlite3.Connection = Depends(db_conn),
):
    """Save a room.

    PUT rather than POST, and INSERT OR IGNORE rather than a check-then-insert:
    favouriting is idempotent, so a double tap or a retried request settles on
    the same state instead of erroring or duplicating.
    """
    _existing_room(conn, room_id)
    execute(
        conn,
        "INSERT OR IGNORE INTO favorites (user_id, room_id) VALUES (?, ?)",
        (booker["id"], room_id),
    )
    return None


@router.delete("/rooms/{room_id}/favorite", status_code=204)
def remove_favorite(
    room_id: int,
    booker: dict = Depends(require_booker),
    conn: sqlite3.Connection = Depends(db_conn),
):
    """Unsave a room. Also idempotent — removing what is not there is fine."""
    execute(
        conn,
        "DELETE FROM favorites WHERE user_id = ? AND room_id = ?",
        (booker["id"], room_id),
    )
    return None


@router.get("/favorites", response_model=list[SearchResult])
def list_favorites(
    booker: dict = Depends(require_booker),
    conn: sqlite3.Connection = Depends(db_conn),
):
    """The saved rooms, newest first.

    Returns the same shape as a search result so the UI can render favourites
    with the existing result card rather than a near-duplicate component.
    """
    rows = query_all(
        conn,
        """
        SELECT r.id AS room_id, r.name AS room_name, r.capacity, r.price,
               r.price_unit, r.amenities,
               s.name AS space_name, s.address
        FROM favorites f
        JOIN rooms r ON r.id = f.room_id
        JOIN spaces s ON s.id = r.space_id
        WHERE f.user_id = ?
        ORDER BY f.created_at DESC, r.id DESC
        """,
        (booker["id"],),
    )

    photos = photo_urls_by_room(conn, [row["room_id"] for row in rows])
    return [
        SearchResult(
            roomId=row["room_id"],
            spaceName=row["space_name"],
            roomName=row["room_name"],
            address=row["address"],
            capacity=row["capacity"],
            price=row["price"],
            price_unit=row["price_unit"],
            amenities=decode_amenities(row["amenities"]),
            photos=photos.get(row["room_id"], []),
            favorite=True,
            reason=None,
        )
        for row in rows
    ]
