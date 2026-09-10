"""Room photo upload, serving and deletion."""

import sqlite3

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import max_photos_per_room
from app.db import execute, query_all, query_one
from app.deps import db_conn, rate_limit_upload, require_owner
from app.photos import PhotoRejected, delete_file, path_for, public_url, save_upload
from app.schemas import PhotoOut

router = APIRouter(tags=["photos"])


def _owned_room(conn: sqlite3.Connection, room_id: int, owner_id: int) -> dict:
    """Fetch a room, or fail with the same 404/403 rules the rest of the API uses."""
    room = query_one(
        conn,
        "SELECT r.id, s.owner_id FROM rooms r JOIN spaces s ON s.id = r.space_id WHERE r.id = ?",
        (room_id,),
    )
    if room is None:
        raise HTTPException(status_code=404, detail="room not found")
    if room["owner_id"] != owner_id:
        raise HTTPException(status_code=403, detail="you do not own this room")
    return room


@router.post("/rooms/{room_id}/photos", response_model=PhotoOut, status_code=201)
def upload_photo(
    room_id: int,
    file: UploadFile = File(...),
    owner: dict = Depends(require_owner),
    conn: sqlite3.Connection = Depends(db_conn),
    _: None = Depends(rate_limit_upload),
):
    """Attach one photo to a room the caller owns.

    One file per request rather than a batch: it keeps a single bad image from
    failing a whole upload, and lets the UI show per-file progress.
    """
    _owned_room(conn, room_id, owner["id"])

    existing = query_one(
        conn, "SELECT COUNT(*) AS n FROM room_photos WHERE room_id = ?", (room_id,)
    )
    cap = max_photos_per_room()
    if existing["n"] >= cap:
        raise HTTPException(status_code=400, detail=f"this room already has {cap} photos")

    try:
        stored_name, content_type, size = save_upload(file.file.read, file.content_type)
    except PhotoRejected as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        photo_id = execute(
            conn,
            "INSERT INTO room_photos (room_id, stored_name, content_type, size_bytes) "
            "VALUES (?, ?, ?, ?)",
            (room_id, stored_name, content_type, size),
        )
    except Exception:
        # The row is what makes the file reachable, so an orphaned file is just
        # wasted disk — clean it up rather than leaving it behind.
        delete_file(stored_name)
        raise

    return PhotoOut(id=photo_id, url=public_url(photo_id), content_type=content_type, size=size)


@router.get("/rooms/{room_id}/photos", response_model=list[PhotoOut])
def list_photos(room_id: int, conn: sqlite3.Connection = Depends(db_conn)):
    rows = query_all(
        conn,
        "SELECT id, content_type, size_bytes FROM room_photos WHERE room_id = ? ORDER BY id",
        (room_id,),
    )
    return [
        PhotoOut(
            id=row["id"],
            url=public_url(row["id"]),
            content_type=row["content_type"],
            size=row["size_bytes"],
        )
        for row in rows
    ]


@router.get("/photos/{photo_id}")
def get_photo(photo_id: int, conn: sqlite3.Connection = Depends(db_conn)):
    """Serve the image bytes.

    Deliberately unauthenticated: a browser loading <img src> sends no
    Authorization header, and listing photos are public information anyway —
    the listings they belong to are readable by any signed-in booker. Ids are
    sequential, so this exposes no more than the listing pages already do.
    """
    row = query_one(
        conn, "SELECT stored_name, content_type FROM room_photos WHERE id = ?", (photo_id,)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="photo not found")

    try:
        path = path_for(row["stored_name"])
    except PhotoRejected:
        raise HTTPException(status_code=404, detail="photo not found")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="photo not found")

    return FileResponse(
        path,
        media_type=row["content_type"],
        headers={
            # Immutable: a photo id always maps to the same bytes, since editing
            # means uploading a new one.
            "Cache-Control": "public, max-age=31536000, immutable",
            # The bytes were sniffed on upload, but say so again at serve time so
            # a browser never content-sniffs its way to executing them.
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete("/photos/{photo_id}", status_code=204)
def delete_photo(
    photo_id: int,
    owner: dict = Depends(require_owner),
    conn: sqlite3.Connection = Depends(db_conn),
):
    row = query_one(
        conn,
        "SELECT p.id, p.stored_name, s.owner_id FROM room_photos p "
        "JOIN rooms r ON r.id = p.room_id JOIN spaces s ON s.id = r.space_id "
        "WHERE p.id = ?",
        (photo_id,),
    )
    if row is None:
        raise HTTPException(status_code=404, detail="photo not found")
    if row["owner_id"] != owner["id"]:
        raise HTTPException(status_code=403, detail="you do not own this photo")

    # Row first: a missing file behind a live row is a broken image, while a
    # live file behind no row is merely unreferenced.
    execute(conn, "DELETE FROM room_photos WHERE id = ?", (photo_id,))
    delete_file(row["stored_name"])
    return None
