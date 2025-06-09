from ninja import NinjaAPI
from django.contrib.auth import get_user_model
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from datetime import date
from typing import List, Optional
from django.db.models import Q
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Room, Category, Booking
from .shemas import UserSchema, RegisterSchema, LoginSchema, TokenSchema, CategorySchema, RoomSchema, RoomFilterSchema, BookingSchema, CreateBookingSchema, RoomAvailabilitySchema
from .auth import JWTAuth

api = NinjaAPI(auth=JWTAuth())
User = get_user_model()


# ----- Аутентификация -----

@api.post("/auth/register", auth=None, tags=['Авторизация'])
def register(request, data: RegisterSchema):
    if User.objects.filter(username=data.username).exists():
        return {"error": "User already exists"}

    user = User.objects.create_user(
        username=data.username,
        password=data.password,

    )
    return {"message": "User created successfully"}


@api.post("/auth/login", auth=None, tags=['Авторизация'])
def login(request, data: LoginSchema):
    user = authenticate(username=data.username, password=data.password)
    if not user:
        return {"error": "Invalid credentials"}

    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }

# ----- Номера -----

@api.get('/rooms', response=List[RoomSchema], tags=['комнаты'])
def list_rooms(request, start_date: Optional[date] = None, end_date: Optional[date] = None, max_price: Optional[float] = None, min_price: Optional[float] = None, guests: Optional[int] = None):
    qs = Room.objects.filter(is_active=True)
    if min_price is not None:
        qs = qs.filter(price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(price__lte=max_price)
    if guests is not None:
        qs = qs.filter(max_guests__gte=guests)

    if start_date and end_date:
        booked_rooms = Booking.objects.filter(
            Q(start_date__lt=end_date) & Q(end_date__gt=start_date)
        ).values_list('room_id', flat=True)
        qs = qs.exclude(id__in=booked_rooms)
    return qs.select_related('category')

@api.get('/rooms/{room_id}', response=RoomSchema,  tags=['комнаты'])
def room_detail(request, room_id: int):
    room = get_object_or_404(Room, id=room_id)
    return room

@api.get('/categories', response=List[CategorySchema],  tags=['категория'])
def list_categories(request):
    return Category.objects.all()

# ----- Бронирования -----

@api.post('/bookings', response=BookingSchema,  tags=['бронь'])
def create_booking(request, data: CreateBookingSchema):
    user = request.user
    room = get_object_or_404(Room, id=data.room_id)

    if not room.is_active:
        raise HttpError(400, "Room is currently unavailable for booking")

    if data.start_date >= data.end_date:
        raise HttpError(400, "End date must be after start date")

    if data.start_date < date.today():
        raise HttpError(400, "Cannot book in the past")


    conflict_exists = Booking.objects.filter(
        room=room,
        start_date__lt=data.end_date,
        end_date__gt=data.start_date
    ).exists()
    if conflict_exists:
        raise HttpError(400, "Room not available for these dates")
    booking = Booking.objects.create(user=user, room=room, start_date=data.start_date, end_date=data.end_date)
    return booking

@api.get('/bookings', response=List[BookingSchema],  tags=['бронь'])
def user_bookings(request):
    return Booking.objects.filter(user=request.user).select_related('room', 'room__category')

@api.delete('/bookings/{booking_id}',  tags=['бронь'])
def cancel_booking(request, booking_id: int):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    booking.delete()
    return {"msg": "Booking cancelled"}

# ----- Админка -----

def admin_required(request):
    if not request.user.is_authenticated or not request.user.is_admin:
        raise HttpError(403, "Admin access required")

@api.post('/admin/categories', response=CategorySchema, tags=['админ'])
def create_category(request, data: CategorySchema):
    admin_required(request)
    category = Category.objects.create(name=data.name)
    return category

@api.put('/admin/categories/{category_id}', response=CategorySchema, tags=['админ'])
def update_category(request, category_id: int, data: CategorySchema):
    admin_required(request)
    category = get_object_or_404(Category, id=category_id)
    category.name = data.name
    category.save()
    return category

@api.delete('/admin/categories/{category_id}', tags=['админ'])
def delete_category(request, category_id: int):
    admin_required(request)
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    return {"msg": "Category deleted"}

@api.post('/admin/rooms', response=RoomSchema, tags=['админ'])
def create_room(request, data: RoomSchema):
    admin_required(request)
    category = get_object_or_404(Category, id=data.category.id)
    room = Room.objects.create(
        number=data.number,
        price=data.price,
        max_guests=data.max_guests,
        category=category
    )
    return room

@api.put('/admin/rooms/{room_id}', response=RoomSchema, tags=['админ'])
def update_room(request, room_id: int, data: RoomSchema):
    admin_required(request)
    room = get_object_or_404(Room, id=room_id)
    category = get_object_or_404(Category, id=data.category.id)
    room.number = data.number
    room.price = data.price
    room.max_guests = data.max_guests
    room.category = category
    room.save()
    return room

@api.delete('/admin/rooms/{room_id}',  tags=['админ'])
def delete_room(request, room_id: int):
    admin_required(request)
    room = get_object_or_404(Room, id=room_id)
    room.delete()
    return {"msg": "Room deleted"}

# ----- Менеджер -----

def manager_required(request):
    if not request.user.is_authenticated or not (request.user.is_manager or request.user.is_admin):
        raise HttpError(403, "Manager access required")


@api.patch('/manager/rooms/{room_id}/availability', tags=['менеджер'])
def manager_toggle_room_availability(request, room_id: int, data: RoomAvailabilitySchema):
    manager_required(request)
    room = get_object_or_404(Room, id=room_id)
    room.is_active = data.is_active
    room.save()
    return {"msg": f"Room availability set to {room.is_active}"}


@api.get('/manager/bookings', response=List[BookingSchema], tags=['менеджер'])
def get_bookings_by_date(request, start_date: Optional[date] = None, end_date: Optional[date] = None):
    manager_required(request)

    bookings = Booking.objects.select_related('user', 'room__category')

    if start_date and end_date:
        bookings = bookings.filter(
            start_date__lt=end_date,
            end_date__gt=start_date
        )

    return bookings

@api.get('/manager/bookings/{booking_id}', response=BookingSchema, tags=['менеджер'])
def get_booking_by_id(request, booking_id: int):
    manager_required(request)

    booking = get_object_or_404(Booking.objects.select_related('user', 'room__category'), id=booking_id)
    return booking


@api.get('/manager/rooms', response=List[RoomSchema], tags=['менеджер'])
def manager_list_rooms(request, is_active: Optional[bool] = None):
    manager_required(request)
    qs = Room.objects.select_related('category').all()
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs