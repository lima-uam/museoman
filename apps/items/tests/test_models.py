import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

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


@pytest.mark.django_db
class TestVitrinaSlot:
    def test_slot_blank_by_default(self, item):
        assert item.vitrina_slot == ""

    def test_valid_slot_digits(self, item, vitrina):
        item.vitrina = vitrina
        item.vitrina_slot = "5"
        item.full_clean()  # no error

    def test_valid_slot_hex_letters(self, item, vitrina):
        item.vitrina = vitrina
        item.vitrina_slot = "A"
        item.full_clean()  # no error

    def test_invalid_slot_lowercase(self, item, vitrina):
        item.vitrina = vitrina
        item.vitrina_slot = "a"
        with pytest.raises(ValidationError):
            item.full_clean()

    def test_invalid_slot_non_hex(self, item, vitrina):
        item.vitrina = vitrina
        item.vitrina_slot = "G"
        with pytest.raises(ValidationError):
            item.full_clean()

    def test_unique_slot_within_vitrina(self, item, vitrina, admin_user):
        item.vitrina = vitrina
        item.vitrina_slot = "3"
        item.save()
        with pytest.raises(IntegrityError):
            Item.all_objects.create(nombre="Otro", created_by=admin_user, vitrina=vitrina, vitrina_slot="3")

    def test_same_slot_allowed_in_different_vitrinas(self, item, vitrina, admin_user):
        from apps.catalog.models import Vitrina

        v2 = Vitrina.objects.create(nombre="Otra vitrina")
        item.vitrina = vitrina
        item.vitrina_slot = "A"
        item.save()
        other = Item.all_objects.create(nombre="Otro", created_by=admin_user, vitrina=v2, vitrina_slot="A")
        other.save()  # should not raise

    def test_null_vitrina_allows_empty_slot(self, item):
        item.vitrina = None
        item.vitrina_slot = ""
        item.full_clean()  # no error


@pytest.mark.django_db
class TestVitrinaSlotForm:
    def _post_form(self, client, item, data):
        from django.urls import reverse

        return client.post(reverse("items:update", kwargs={"pk": item.pk}), data)

    def test_slot_cleared_when_vitrina_changes(self, client, admin_user, item, vitrina):
        from apps.catalog.models import Vitrina
        from django.urls import reverse

        client.force_login(admin_user)
        v2 = Vitrina.objects.create(nombre="Otra")
        item.vitrina = vitrina
        item.vitrina_slot = "B"
        item.save()

        client.post(
            reverse("items:update", kwargs={"pk": item.pk}),
            {
                "nombre": item.nombre,
                "tipos": [],
                "vitrina": v2.pk,
                "vitrina_slot": "B",  # user tries to keep slot, but vitrina changed
                "url": "",
                "observaciones": "",
            },
        )
        item.refresh_from_db()
        assert item.vitrina == v2
        assert item.vitrina_slot == ""

    def test_duplicate_slot_rejected(self, client, admin_user, item, vitrina):
        from django.urls import reverse

        client.force_login(admin_user)
        # Create another item with slot "C" in the same vitrina
        Item.all_objects.create(nombre="Otro", created_by=admin_user, vitrina=vitrina, vitrina_slot="C")
        item.vitrina = vitrina
        item.save()

        resp = client.post(
            reverse("items:update", kwargs={"pk": item.pk}),
            {
                "nombre": item.nombre,
                "tipos": [],
                "vitrina": vitrina.pk,
                "vitrina_slot": "C",
                "url": "",
                "observaciones": "",
            },
        )
        assert resp.status_code == 200  # form re-rendered with error
        item.refresh_from_db()
        assert item.vitrina_slot != "C"  # not saved

    def test_slot_uppercased_by_form(self, client, admin_user, item, vitrina):
        from django.urls import reverse

        client.force_login(admin_user)
        client.post(
            reverse("items:update", kwargs={"pk": item.pk}),
            {
                "nombre": item.nombre,
                "tipos": [],
                "vitrina": vitrina.pk,
                "vitrina_slot": "a",  # lowercase — form should uppercase → "A"
                "url": "",
                "observaciones": "",
            },
        )
        item.refresh_from_db()
        assert item.vitrina_slot == "A"
