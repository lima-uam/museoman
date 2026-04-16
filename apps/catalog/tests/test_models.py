import pytest

from apps.catalog.models import Tipo, Vitrina


@pytest.mark.django_db
class TestTipo:
    def test_create(self):
        t = Tipo.objects.create(nombre="Ordenador")
        assert str(t) == "Ordenador"

    def test_nombre_unique(self):
        Tipo.objects.create(nombre="Monitor")
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Tipo.objects.create(nombre="Monitor")


@pytest.mark.django_db
class TestVitrina:
    def test_create(self):
        v = Vitrina.objects.create(numero=1)
        assert str(v) == "Vitrina 1"

    def test_numero_unique(self):
        Vitrina.objects.create(numero=2)
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Vitrina.objects.create(numero=2)
