"""Pydantic request/response models."""

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.config import PRICE_UNITS, ROOM_AMENITIES

Role = Literal["owner", "booker"]


# --- Auth --------------------------------------------------------------


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=1)
    role: Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: Role


class AuthResponse(BaseModel):
    token: str
    user: UserOut


# --- Spaces / Rooms ------------------------------------------------------


class SpaceCreate(BaseModel):
    name: str = Field(min_length=1)
    address: str = Field(min_length=1)
    contact_info: str = Field(min_length=1)
    description: str = ""


class SpaceOut(BaseModel):
    id: int
    owner_id: int
    name: str
    address: str
    contact_info: str
    description: str


class RoomCreate(BaseModel):
    name: str = Field(min_length=1)
    capacity: int = Field(gt=0)
    price: float = Field(gt=0)
    price_unit: str
    amenities: list[str] = Field(default_factory=list)
    notes: str = ""

    @field_validator("price_unit")
    @classmethod
    def validate_price_unit(cls, v: str) -> str:
        if v not in PRICE_UNITS:
            raise ValueError(f"price_unit must be one of {PRICE_UNITS}")
        return v

    @field_validator("amenities")
    @classmethod
    def validate_amenities(cls, v: list[str]) -> list[str]:
        unknown = [a for a in v if a not in ROOM_AMENITIES]
        if unknown:
            raise ValueError(f"unknown amenities: {unknown}. Allowed: {ROOM_AMENITIES}")
        return v


class RoomOut(BaseModel):
    id: int
    space_id: int
    name: str
    capacity: int
    price: float
    price_unit: str
    amenities: list[str]
    notes: str


class SpaceWithRooms(SpaceOut):
    rooms: list[RoomOut]


# --- Search / Listings ---------------------------------------------------


class SearchResult(BaseModel):
    roomId: int
    spaceName: str
    roomName: str
    address: str
    capacity: int
    price: float
    price_unit: str
    amenities: list[str]
    reason: Optional[str] = None


class SearchResponse(BaseModel):
    results: list[SearchResult]


class ListingOut(BaseModel):
    roomId: int
    roomName: str
    capacity: int
    price: float
    price_unit: str
    amenities: list[str]
    notes: str
    spaceId: int
    spaceName: str
    address: str
    contact_info: str
    description: str
