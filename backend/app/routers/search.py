import logging
import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.ai import rank_rooms
from app.config import SEARCH_CANDIDATE_LIMIT
from app.db import decode_amenities, photo_urls_by_room, query_all, query_one
from app.deps import consume_ai_quota, db_conn, require_booker
from app.schemas import ListingOut, SearchResponse, SearchResult

router = APIRouter(tags=["search"])
logger = logging.getLogger(__name__)


@router.get("/search", response_model=SearchResponse)
def search(
    location: Optional[str] = None,
    capacity: Optional[int] = None,
    priceMax: Optional[float] = None,
    amenities: Optional[str] = None,
    note: Optional[str] = None,
    booker: dict = Depends(require_booker),
    conn: sqlite3.Connection = Depends(db_conn),
):
    required_amenities = [a.strip() for a in amenities.split(",") if a.strip()] if amenities else []

    clauses = ["1=1"]
    params: list = []

    if location:
        clauses.append("s.address LIKE ?")
        params.append(f"%{location}%")
    if capacity is not None:
        clauses.append("r.capacity >= ?")
        params.append(capacity)
    if priceMax is not None:
        clauses.append("r.price <= ?")
        params.append(priceMax)
    for amenity in required_amenities:
        clauses.append("r.amenities LIKE ?")
        params.append(f"%,{amenity},%")

    sql = f"""
        SELECT r.id AS room_id, r.name AS room_name, r.capacity, r.price,
               r.price_unit, r.amenities, r.notes,
               s.name AS space_name, s.address
        FROM rooms r
        JOIN spaces s ON s.id = r.space_id
        WHERE {' AND '.join(clauses)}
        ORDER BY r.id
        LIMIT ?
    """
    params.append(SEARCH_CANDIDATE_LIMIT)

    rows = query_all(conn, sql, params)
    for row in rows:
        row["amenities"] = decode_amenities(row["amenities"])

    photos = photo_urls_by_room(conn, [row["room_id"] for row in rows])

    if not note:
        results = [
            SearchResult(
                roomId=row["room_id"],
                spaceName=row["space_name"],
                roomName=row["room_name"],
                address=row["address"],
                capacity=row["capacity"],
                price=row["price"],
                price_unit=row["price_unit"],
                amenities=row["amenities"],
                photos=photos.get(row["room_id"], []),
                reason=None,
            )
            for row in rows
        ]
        return SearchResponse(results=results)

    # Past this point the request costs Anthropic tokens, so it is charged
    # against the AI budgets. Raises 429 before any spend if a quota is out.
    consume_ai_quota(booker)

    rows_by_id = {row["room_id"]: row for row in rows}
    reason_by_id: dict[int, str] = {}
    order: list[int] = list(rows_by_id.keys())

    try:
        candidates = [
            {
                "room_id": row["room_id"],
                "room_name": row["room_name"],
                "space_name": row["space_name"],
                "capacity": row["capacity"],
                "price": row["price"],
                "price_unit": row["price_unit"],
                "amenities": row["amenities"],
                "notes": row["notes"],
            }
            for row in rows
        ]
        ranked = rank_rooms(note, candidates)

        seen = set()
        new_order = []
        for entry in ranked:
            room_id = entry.get("room_id")
            if room_id in rows_by_id and room_id not in seen:
                new_order.append(room_id)
                seen.add(room_id)
                reason_by_id[room_id] = entry.get("reason")
        # Any candidate the model dropped is appended at the end, unranked.
        for room_id in order:
            if room_id not in seen:
                new_order.append(room_id)
        order = new_order
    except Exception:
        logger.exception("AI ranking failed; falling back to SQL order")
        # order/reason_by_id already reflect the unranked SQL fallback

    results = [
        SearchResult(
            roomId=room_id,
            spaceName=rows_by_id[room_id]["space_name"],
            roomName=rows_by_id[room_id]["room_name"],
            address=rows_by_id[room_id]["address"],
            capacity=rows_by_id[room_id]["capacity"],
            price=rows_by_id[room_id]["price"],
            price_unit=rows_by_id[room_id]["price_unit"],
            amenities=rows_by_id[room_id]["amenities"],
            photos=photos.get(room_id, []),
            reason=reason_by_id.get(room_id),
        )
        for room_id in order
    ]
    return SearchResponse(results=results)


@router.get("/listings/{room_id}", response_model=ListingOut)
def get_listing(
    room_id: int,
    booker: dict = Depends(require_booker),
    conn: sqlite3.Connection = Depends(db_conn),
):
    row = query_one(
        conn,
        """
        SELECT r.id AS room_id, r.name AS room_name, r.capacity, r.price,
               r.price_unit, r.amenities, r.notes,
               s.id AS space_id, s.name AS space_name, s.address,
               s.contact_info, s.description
        FROM rooms r
        JOIN spaces s ON s.id = r.space_id
        WHERE r.id = ?
        """,
        (room_id,),
    )
    if row is None:
        raise HTTPException(status_code=404, detail="listing not found")

    return ListingOut(
        photos=photo_urls_by_room(conn, [row["room_id"]])[row["room_id"]],
        roomId=row["room_id"],
        roomName=row["room_name"],
        capacity=row["capacity"],
        price=row["price"],
        price_unit=row["price_unit"],
        amenities=decode_amenities(row["amenities"]),
        notes=row["notes"],
        spaceId=row["space_id"],
        spaceName=row["space_name"],
        address=row["address"],
        contact_info=row["contact_info"],
        description=row["description"],
    )
