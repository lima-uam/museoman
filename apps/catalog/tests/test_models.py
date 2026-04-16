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
    def test_auto_numero_starts_at_1(self):
        v = Vitrina.objects.create(nombre="Sala principal")
        assert v.numero == 1

    def test_auto_numero_increments(self):
        v1 = Vitrina.objects.create(nombre="Primera")
        v2 = Vitrina.objects.create(nombre="Segunda")
        assert v2.numero == v1.numero + 1

    def test_explicit_numero_preserved(self):
        v = Vitrina.objects.create(numero=42, nombre="Especial")
        assert v.numero == 42

    def test_auto_numero_after_explicit(self):
        Vitrina.objects.create(numero=10, nombre="Décima")
        v = Vitrina.objects.create(nombre="Auto")
        assert v.numero == 11

    def test_str_with_nombre(self):
        v = Vitrina.objects.create(nombre="Sala central")
        assert "Sala central" in str(v)
        assert str(v.numero) in str(v)

    def test_str_without_nombre(self):
        v = Vitrina.objects.create()
        assert str(v) == f"Vitrina {v.numero}"

    def test_numero_unique(self):
        Vitrina.objects.create(numero=2, nombre="A")
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Vitrina.objects.create(numero=2, nombre="B")
