from django.contrib.auth.models import AbstractUser
from django.db import models


ROLE_CHOICES = (
    ('user', 'Пользователь'),
    ('moderator', 'Модератор'),
    ('admin', 'Администратор'),
)


class User(AbstractUser):
    """Кастомная модель для пользователей"""
    bio = models.TextField(
        'Биография',
        blank=True,
    )
    role = models.CharField(
        max_length=255,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name='Роль'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Адрес электронной почты'
    )
