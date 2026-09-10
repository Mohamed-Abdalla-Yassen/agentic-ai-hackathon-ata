"""FastAPI dependencies: DB connection per request, current user, role guards,
rate limits."""

import math
import sqlite3
from typing import Iterator

import jwt
from fastapi import Depends, HTTPException, Request

from app.config import (
    rate_limit_ai_global_per_day,
    rate_limit_ai_per_day,
    rate_limit_ai_per_hour,
    rate_limit_auth_per_hour,
    rate_limit_read_per_minute,
    rate_limit_upload_per_hour,
    trust_proxy_headers,
)
from app.db import get_connection, query_one
from app.ratelimit import Limit, limiter
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


# --- Rate limiting ---------------------------------------------------------


def client_ip(request: Request) -> str:
    """Best available identifier for an unauthenticated caller.

    X-Forwarded-For is only consulted when the deployment says it sits behind a
    proxy (see config.trust_proxy_headers) — the leftmost entry is the original
    client. Read unconditionally it would be a rate-limit bypass, since the
    caller writes it.
    """
    if trust_proxy_headers():
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _enforce(bucket: str, identity: str, limit: Limit, message: str) -> None:
    retry_after = limiter.check(bucket, identity, limit)
    if retry_after is None:
        return
    # Retry-After is whole seconds, and rounding down would invite a retry that
    # is still inside the window.
    raise HTTPException(
        status_code=429,
        detail=message,
        headers={"Retry-After": str(max(1, math.ceil(retry_after)))},
    )


def rate_limit_auth(request: Request) -> None:
    """Per-IP cap on login/register.

    Slows credential stuffing, and — because registration is the cheap way to
    get around a per-user quota — throttles the supply of fresh accounts an
    attacker could point at the AI search endpoint.
    """
    _enforce(
        "auth",
        client_ip(request),
        Limit(rate_limit_auth_per_hour(), 3600),
        "too many authentication attempts, please try again later",
    )


def rate_limit_read(user: dict = Depends(get_current_user)) -> dict:
    """Loose per-user cap on endpoints that cost nothing but database time."""
    _enforce(
        "read",
        str(user["id"]),
        Limit(rate_limit_read_per_minute(), 60),
        "too many requests, please slow down",
    )
    return user


def rate_limit_upload(user: dict = Depends(get_current_user)) -> None:
    """Per-owner cap on photo uploads — each one costs disk, not tokens."""
    _enforce(
        "upload",
        str(user["id"]),
        Limit(rate_limit_upload_per_hour(), 3600),
        "too many photo uploads, please try again later",
    )


def consume_ai_quota(user: dict) -> None:
    """Charge one AI-backed search against every applicable budget.

    Called from the search route rather than declared as a dependency, because
    only searches that carry a note reach the model — quota must be spent on the
    requests that actually cost tokens, not on every search.

    The global budget is checked last so that a single user hitting their own
    ceiling doesn't consume a slot from the shared daily pool.
    """
    identity = str(user["id"])
    _enforce(
        "ai_hour",
        identity,
        Limit(rate_limit_ai_per_hour(), 3600),
        "AI search limit reached for this hour, please try again later",
    )
    _enforce(
        "ai_day",
        identity,
        Limit(rate_limit_ai_per_day(), 86_400),
        "AI search limit reached for today, please try again tomorrow",
    )
    _enforce(
        "ai_global",
        "all",
        Limit(rate_limit_ai_global_per_day(), 86_400),
        "AI search is temporarily unavailable due to high demand, please try again later",
    )


# --- Role guards -----------------------------------------------------------
#
# Both guards resolve the user through rate_limit_read, so every authenticated
# endpoint carries the cheap per-user throttle without each router opting in.


def require_owner(user: dict = Depends(rate_limit_read)) -> dict:
    if user["role"] != "owner":
        raise HTTPException(status_code=403, detail="owner role required")
    return user


def require_booker(user: dict = Depends(rate_limit_read)) -> dict:
    if user["role"] != "booker":
        raise HTTPException(status_code=403, detail="booker role required")
    return user
