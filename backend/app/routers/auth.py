import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.db import execute, query_one
from app.deps import db_conn, rate_limit_auth
from app.schemas import AuthResponse, LoginRequest, RegisterRequest, UserOut
from app.security import create_token, hash_password, verify_password

# Every auth endpoint is unauthenticated and therefore only identifiable by
# IP, so the limit is declared once on the router rather than per route.
router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(rate_limit_auth)])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest, conn: sqlite3.Connection = Depends(db_conn)):
    existing = query_one(conn, "SELECT id FROM users WHERE email = ?", (body.email,))
    if existing is not None:
        raise HTTPException(status_code=400, detail="email is already registered")

    user_id = execute(
        conn,
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        (body.name, body.email, hash_password(body.password), body.role),
    )
    token = create_token(user_id, body.role)
    user = UserOut(id=user_id, name=body.name, email=body.email, role=body.role)
    return AuthResponse(token=token, user=user)


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, conn: sqlite3.Connection = Depends(db_conn)):
    row = query_one(conn, "SELECT * FROM users WHERE email = ?", (body.email,))
    if row is None or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=400, detail="invalid email or password")

    token = create_token(row["id"], row["role"])
    user = UserOut(id=row["id"], name=row["name"], email=row["email"], role=row["role"])
    return AuthResponse(token=token, user=user)
