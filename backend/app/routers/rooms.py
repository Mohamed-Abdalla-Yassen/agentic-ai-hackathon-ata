"""Room-level owner operations: read one, edit one.

Creation lives under the parent space (`POST /spaces/{id}/rooms`) because a room
cannot exist without one. Once created a room has its own identity, so editing
it is addressed directly rather than through the space.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.db import decode_amenities, encode_amenities, execute, photos_by_room, query_one
from app.deps import db_conn, require_owner
from app.schemas import RoomOut, RoomUpdate

router = APIRouter(prefix="/rooms", tags=["rooms"])


def _owned_room(conn: sqlite3.Connection, room_id: int, owner_id: int) -> dict:
    room = query_one(
        conn,
        "SELECT r.*, s.owner_id FROM rooms r JOIN spaces s ON s.id = r.space_id WHERE r.id = ?",
        (room_id,),
    )
    if room is None:
        raise HTTPException(status_code=404, detail="room not found")
    if room["owner_id"] != owner_id:
        raise HTTPException(status_code=403, detail="you do not own this room")
    return room


def _to_out(conn: sqlite3.Connection, room: dict) -> RoomOut:
    return RoomOut(
        id=room["id"],
        space_id=room["space_id"],
        name=room["name"],
        capacity=room["capacity"],
        price=room["price"],
        price_unit=room["price_unit"],
        amenities=decode_amenities(room["amenities"]),
        notes=room["notes"],
        photos=photos_by_room(conn, [room["id"]])[room["id"]],
    )


@router.get("/{room_id}", response_model=RoomOut)
def get_room(
    room_id: int,
    owner: dict = Depends(require_owner),
    conn: sqlite3.Connection = Depends(db_conn),
):
    """The owner's view of one room — what the edit form loads.

    Separate from `GET /listings/{id}`, which is the booker's view: that one
    requires a booker role and exposes the public listing shape, not the
    editable fields.
    """
    return _to_out(conn, _owned_room(conn, room_id, owner["id"]))


@router.patch("/{room_id}", response_model=RoomOut)
def update_room(
    room_id: int,
    body: RoomUpdate,
    owner: dict = Depends(require_owner),
    conn: sqlite3.Connection = Depends(db_conn),
):
    """Update any subset of a room's fields.

    PATCH rather than PUT so a client can send only what changed, and so adding
    a field later does not silently blank it for older clients. Omitted fields
    keep their stored value; `notes` can be cleared by sending an empty string,
    which is why "omitted" and "empty" have to stay distinguishable.
    """
    room = _owned_room(conn, room_id, owner["id"])

    changes = body.model_dump(exclude_unset=True)
    if not changes:
        # Nothing to do, but not an error — a no-op save should be harmless.
        return _to_out(conn, room)

    if "amenities" in changes:
        changes["amenities"] = encode_amenities(changes["amenities"])

    assignments = ", ".join(f"{column} = ?" for column in changes)
    execute(
        conn,
        f"UPDATE rooms SET {assignments} WHERE id = ?",
        (*changes.values(), room_id),
    )

    return _to_out(conn, _owned_room(conn, room_id, owner["id"]))
