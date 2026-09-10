"""Password hashing and JWT encode/decode."""

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import jwt_secret

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_ALGORITHM = "HS256"
JWT_EXPIRY = timedelta(days=7)


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def create_token(user_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(timezone.utc) + JWT_EXPIRY,
    }
    return jwt.encode(payload, jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Raises jwt.PyJWTError (or a subclass) on any invalid/expired token."""
    return jwt.decode(token, jwt_secret(), algorithms=[JWT_ALGORITHM])
