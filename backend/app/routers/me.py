"""The signed-in user's own profile."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.db import execute, query_one
from app.deps import db_conn, get_current_user
from app.schemas import ProfileUpdate, UserOut
from app.security import hash_password, verify_password

router = APIRouter(prefix="/me", tags=["profile"])


@router.get("", response_model=UserOut)
def get_profile(user: dict = Depends(get_current_user)):
    """Who the current token belongs to.

    The contract originally had no such route, so clients cached the user object
    from login. This lets a client confirm the server's view instead, which
    matters once the profile can change.
    """
    return UserOut(**user)


@router.patch("", response_model=UserOut)
def update_profile(
    body: ProfileUpdate,
    user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(db_conn),
):
    """Update name, email or password.

    Email and password are account-takeover material, so changing either
    requires the current password: a stolen or borrowed session alone must not
    be enough to lock the real owner out of their account. Renaming is harmless
    by comparison and needs no re-authentication.

    The role is deliberately not editable — switching between owner and booker
    would change what the account can reach, and the existing spaces and
    favourites would be left attached to the wrong kind of user.
    """
    changes = body.model_dump(exclude_unset=True)
    changes.pop("current_password", None)
    if not changes:
        return UserOut(**user)

    sensitive = {"email", "password"} & changes.keys()
    if sensitive:
        if not body.current_password:
            raise HTTPException(
                status_code=400,
                detail="your current password is required to change your email or password",
            )
        row = query_one(conn, "SELECT password_hash FROM users WHERE id = ?", (user["id"],))
        if row is None or not verify_password(body.current_password, row["password_hash"]):
            raise HTTPException(status_code=400, detail="current password is incorrect")

    if "email" in changes:
        # COLLATE NOCASE on the column means this also catches case variants.
        taken = query_one(
            conn,
            "SELECT id FROM users WHERE email = ? AND id != ?",
            (changes["email"], user["id"]),
        )
        if taken is not None:
            raise HTTPException(status_code=400, detail="email is already registered")

    columns = {}
    if "name" in changes:
        columns["name"] = changes["name"]
    if "email" in changes:
        columns["email"] = changes["email"]
    if "password" in changes:
        columns["password_hash"] = hash_password(changes["password"])

    assignments = ", ".join(f"{column} = ?" for column in columns)
    execute(
        conn,
        f"UPDATE users SET {assignments} WHERE id = ?",
        (*columns.values(), user["id"]),
    )

    updated = query_one(
        conn, "SELECT id, name, email, role FROM users WHERE id = ?", (user["id"],)
    )
    return UserOut(**updated)
