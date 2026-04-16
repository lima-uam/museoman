import pytest

from apps.items.models import Item
from apps.items.state import State


@pytest.mark.django_db
class TestItemModel:
    def test_create(self, item):
        assert item.estado == State.LIBRE
        assert item.activo is True
        assert item.identificador == "PC-001"

    def test_default_manager_excludes_inactive(self, item):
        item.activo = False
        item.save()
        assert Item.objects.filter(pk=item.pk).count() == 0
        assert Item.all_objects.filter(pk=item.pk).count() == 1

    def test_all_objects_includes_inactive(self, item):
        assert Item.all_objects.filter(pk=item.pk).exists()

    def test_str(self, item):
        assert "PC-001" in str(item)
        assert "IBM PC XT" in str(item)

    def test_identificador_unique(self, item, tipo, admin_user):
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Item.all_objects.create(nombre="Otro", identificador="PC-001", tipo=tipo, created_by=admin_user)
