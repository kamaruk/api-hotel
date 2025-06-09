from ninja import Schema
from typing import Optional
from datetime import date


class UserSchema(Schema):
    id: int
    username: str
    is_admin: bool

class RegisterSchema(Schema):
    username: str
    password: str

class LoginSchema(Schema):
    username: str
    password: str

class TokenSchema(Schema):
    access: str
    refresh: str

class CategorySchema(Schema):
    id: int
    name: str

    class Config:
        orm_mode = True

class RoomCategorySchema(Schema):
    id: int
    name: str

    class Config:
        orm_mode = True

class RoomSchema(Schema):
    id: int
    number: str
    price: float
    max_guests: int
    category: RoomCategorySchema

    class Config:
        orm_mode = True

class RoomFilterSchema(Schema):
    start_date: Optional[date]
    end_date: Optional[date]
    max_price: Optional[float]
    min_price: Optional[float]
    guests: Optional[int]

class BookingUserSchema(Schema):
    id: int
    username: str

    class Config:
        orm_mode = True

class BookingSchema(Schema):
    id: int
    user: BookingUserSchema
    room: RoomSchema
    start_date: date
    end_date: date

    class Config:
        orm_mode = True

class CreateBookingSchema(Schema):
    room_id: int
    start_date: date
    end_date: date

class RoomAvailabilitySchema(Schema):
    is_active: bool