"""FastAPI dependencies: DB connection per request, current user, role guards."""

import sqlite3
from typing import Iterator

import jwt
from fastapi import Depends, HTTPException, Request

from app.db import get_connection, query_one
from app.security import decode_token


def db_conn() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def get_current_user(request: Request, conn: sqlite3.Connection = Depends(db_conn)) -> dict:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or invalid authorization header")

    token = auth_header.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid or expired token")

    user = query_one(conn, "SELECT id, name, email, role FROM users WHERE id = ?", (payload["sub"],))
    if user is None:
        raise HTTPException(status_code=401, detail="user no longer exists")
    return user


def require_owner(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "owner":
        raise HTTPException(status_code=403, detail="owner role required")
    return user


def require_booker(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "booker":
        raise HTTPException(status_code=403, detail="booker role required")
    return user
