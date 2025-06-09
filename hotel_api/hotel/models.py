from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_client = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Room(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='комнаты')
    number = models.CharField(max_length=10, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    max_guests = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'Room {self.number} ({self.category.name})'

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='бронь')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='бронь')
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'start_date', 'end_date')