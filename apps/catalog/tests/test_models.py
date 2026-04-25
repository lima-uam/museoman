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
    def test_str_with_nombre(self):
        v = Vitrina.objects.create(nombre="Sala central")
        assert str(v) == "Sala central"

    def test_str_without_nombre(self):
        v = Vitrina.objects.create()
        assert str(v) == "Vitrina"

    def test_url_optional(self):
        v = Vitrina.objects.create(nombre="Sala A", url="https://example.com")
        assert v.url == "https://example.com"
