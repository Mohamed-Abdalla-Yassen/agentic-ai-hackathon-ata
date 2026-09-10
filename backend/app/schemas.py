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


class ProfileUpdate(BaseModel):
    """Partial update of the signed-in user's own profile.

    `role` is intentionally absent — see routers/me.py. `current_password` is
    not a field being changed; it is the re-authentication that changing email
    or password requires.
    """

    name: Optional[str] = Field(default=None, min_length=1)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=8)
    current_password: Optional[str] = None


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


class RoomUpdate(BaseModel):
    """Partial update of a room. Unset fields are left alone; the validators
    mirror RoomCreate so an edit cannot put a room into a state that creation
    would have refused."""

    name: Optional[str] = Field(default=None, min_length=1)
    capacity: Optional[int] = Field(default=None, gt=0)
    price: Optional[float] = Field(default=None, gt=0)
    price_unit: Optional[str] = None
    amenities: Optional[list[str]] = None
    notes: Optional[str] = None

    @field_validator("price_unit")
    @classmethod
    def validate_price_unit(cls, v: str | None) -> str | None:
        if v is not None and v not in PRICE_UNITS:
            raise ValueError(f"price_unit must be one of {PRICE_UNITS}")
        return v

    @field_validator("amenities")
    @classmethod
    def validate_amenities(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        unknown = [a for a in v if a not in ROOM_AMENITIES]
        if unknown:
            raise ValueError(f"unknown amenities: {unknown}. Allowed: {ROOM_AMENITIES}")
        return v


class PhotoOut(BaseModel):
    id: int
    url: str
    content_type: str
    size: int


class RoomOut(BaseModel):
    id: int
    space_id: int
    name: str
    capacity: int
    price: float
    price_unit: str
    amenities: list[str]
    notes: str
    # Full records, not just urls: the owner dashboard needs ids to delete with.
    photos: list[PhotoOut] = Field(default_factory=list)


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
    # Photo URLs, first one being what a result card shows as its thumbnail.
    photos: list[str] = Field(default_factory=list)
    favorite: bool = False
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
    photos: list[str] = Field(default_factory=list)
    favorite: bool = False
