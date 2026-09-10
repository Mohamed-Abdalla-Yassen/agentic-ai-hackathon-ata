import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.db import (
    decode_amenities,
    encode_amenities,
    execute,
    photos_by_room,
    query_all,
    query_one,
)
from app.deps import db_conn, require_owner
from app.schemas import RoomCreate, RoomOut, SpaceCreate, SpaceOut, SpaceWithRooms

router = APIRouter(prefix="/spaces", tags=["spaces"])


@router.post("", response_model=SpaceOut, status_code=201)
def create_space(
    body: SpaceCreate,
    owner: dict = Depends(require_owner),
    conn: sqlite3.Connection = Depends(db_conn),
):
    space_id = execute(
        conn,
        "INSERT INTO spaces (owner_id, name, address, contact_info, description) "
        "VALUES (?, ?, ?, ?, ?)",
        (owner["id"], body.name, body.address, body.contact_info, body.description),
    )
    return SpaceOut(
        id=space_id,
        owner_id=owner["id"],
        name=body.name,
        address=body.address,
        contact_info=body.contact_info,
        description=body.description,
    )


@router.get("/mine", response_model=list[SpaceWithRooms])
def list_my_spaces(
    owner: dict = Depends(require_owner),
    conn: sqlite3.Connection = Depends(db_conn),
):
    spaces = query_all(conn, "SELECT * FROM spaces WHERE owner_id = ? ORDER BY id", (owner["id"],))
    if not spaces:
        return []

    space_ids = [s["id"] for s in spaces]
    placeholders = ",".join("?" * len(space_ids))
    rooms = query_all(
        conn,
        f"SELECT * FROM rooms WHERE space_id IN ({placeholders}) ORDER BY id",
        space_ids,
    )

    photos = photos_by_room(conn, [room["id"] for room in rooms])

    rooms_by_space: dict[int, list[dict]] = {sid: [] for sid in space_ids}
    for room in rooms:
        rooms_by_space[room["space_id"]].append(room)

    return [
        SpaceWithRooms(
            **space,
            rooms=[
                RoomOut(
                    **{
                        **room,
                        "amenities": decode_amenities(room["amenities"]),
                        "photos": photos.get(room["id"], []),
                    }
                )
                for room in rooms_by_space[space["id"]]
            ],
        )
        for space in spaces
    ]


@router.post("/{space_id}/rooms", response_model=RoomOut, status_code=201)
def create_room(
    space_id: int,
    body: RoomCreate,
    owner: dict = Depends(require_owner),
    conn: sqlite3.Connection = Depends(db_conn),
):
    space = query_one(conn, "SELECT * FROM spaces WHERE id = ?", (space_id,))
    if space is None:
        raise HTTPException(status_code=404, detail="space not found")
    if space["owner_id"] != owner["id"]:
        raise HTTPException(status_code=403, detail="you do not own this space")

    room_id = execute(
        conn,
        "INSERT INTO rooms (space_id, name, capacity, price, price_unit, amenities, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            space_id,
            body.name,
            body.capacity,
            body.price,
            body.price_unit,
            encode_amenities(body.amenities),
            body.notes,
        ),
    )
    return RoomOut(
        id=room_id,
        space_id=space_id,
        name=body.name,
        capacity=body.capacity,
        price=body.price,
        price_unit=body.price_unit,
        amenities=body.amenities,
        notes=body.notes,
    )
