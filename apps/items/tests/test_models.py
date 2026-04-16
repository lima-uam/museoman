import pytest

from apps.items.models import Item


@pytest.mark.django_db
class TestItemModel:
    def test_create_auto_assigns_identificador(self, item):
        item.refresh_from_db()
        assert item.identificador == f"PIEZA-{item.pk:04d}"

    def test_identificador_format(self, item):
        item.refresh_from_db()
        assert item.identificador.startswith("PIEZA-")

    def test_explicit_identificador_preserved(self, tipo, admin_user):
        obj = Item.all_objects.create(
            nombre="Manual", identificador="CUSTOM-001", tipo=tipo, created_by=admin_user
        )
        obj.refresh_from_db()
        assert obj.identificador == "CUSTOM-001"

    def test_default_manager_excludes_inactive(self, item):
        item.activo = False
        item.save()
        assert Item.objects.filter(pk=item.pk).count() == 0
        assert Item.all_objects.filter(pk=item.pk).count() == 1

    def test_all_objects_includes_inactive(self, item):
        assert Item.all_objects.filter(pk=item.pk).exists()

    def test_str(self, item):
        item.refresh_from_db()
        assert item.identificador in str(item)
        assert "IBM PC XT" in str(item)

    def test_identificador_unique(self, item, tipo, admin_user):
        item.refresh_from_db()
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Item.all_objects.create(
                nombre="Otro", identificador=item.identificador, tipo=tipo, created_by=admin_user
            )
