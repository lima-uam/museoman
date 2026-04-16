from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name="correo electrónico")
    name = models.CharField(max_length=150, verbose_name="nombre")
    is_active = models.BooleanField(default=True, verbose_name="activo")
    is_staff = models.BooleanField(default=False, verbose_name="administrador")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="fecha de alta")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} <{self.email}>"

    @property
    def is_admin(self):
        return self.is_staff
