import pytest

from apps.items.models import Item


@pytest.mark.django_db
class TestItemModel:
    def test_default_manager_excludes_inactive(self, item):
        item.activo = False
        item.save()
        assert Item.objects.filter(pk=item.pk).count() == 0
        assert Item.all_objects.filter(pk=item.pk).count() == 1

    def test_all_objects_includes_inactive(self, item):
        assert Item.all_objects.filter(pk=item.pk).exists()

    def test_str(self, item):
        assert "IBM PC XT" in str(item)
