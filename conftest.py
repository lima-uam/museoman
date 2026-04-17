import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def admin_user(db):
    User = get_user_model()
    return User.objects.create_superuser(email="admin@test.com", name="Admin Test", password="testpass")


@pytest.fixture
def regular_user(db):
    User = get_user_model()
    return User.objects.create_user(email="user@test.com", name="Regular Test", password="testpass")


@pytest.fixture
def tipo(db):
    from apps.catalog.models import Tipo
    return Tipo.objects.create(nombre="Ordenador")


@pytest.fixture
def vitrina(db):
    from apps.catalog.models import Vitrina
    return Vitrina.objects.create(nombre="Vitrina de prueba")


@pytest.fixture
def item(db, tipo, admin_user):
    from apps.items.models import Item
    obj = Item.all_objects.create(
        nombre="IBM PC XT",
        created_by=admin_user,
    )
    obj.tipos.add(tipo)
    return obj
