import pytest
from django.test import Client
from django.urls import reverse

from apps.audit.models import AuditLog
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


@pytest.mark.django_db
class TestVitrinaListPieceCount:
    def test_item_count_shown(self, admin_user, item, vitrina):
        from apps.items.models import Item

        item.vitrina = vitrina
        item.save()
        # Create an inactive item in the same vitrina — should not count
        Item.all_objects.create(nombre="Inactivo", created_by=admin_user, vitrina=vitrina, activo=False)

        c = Client()
        c.force_login(admin_user)
        resp = c.get(reverse("catalog:vitrina_list"))
        assert resp.status_code == 200
        row = next(v for v in resp.context["vitrinas"] if v.pk == vitrina.pk)
        assert row.item_count == 1  # only the active item

    def test_zero_count_for_empty_vitrina(self, admin_user, vitrina):
        c = Client()
        c.force_login(admin_user)
        resp = c.get(reverse("catalog:vitrina_list"))
        row = next(v for v in resp.context["vitrinas"] if v.pk == vitrina.pk)
        assert row.item_count == 0


@pytest.mark.django_db
class TestVitrinaUpdateView:
    def _client(self, user):
        c = Client()
        c.force_login(user)
        return c

    def test_update_nombre_emits_field_audit(self, admin_user, vitrina):
        old_nombre = vitrina.nombre
        c = self._client(admin_user)
        resp = c.post(
            reverse("catalog:vitrina_update", kwargs={"pk": vitrina.pk}),
            {"nombre": "Sala nueva", "url": vitrina.url or ""},
        )
        assert resp.status_code == 302
        log = AuditLog.objects.filter(vitrina=vitrina, action=AuditLog.ACTION_VITRINA_UPDATED, field="nombre").first()
        assert log is not None
        assert log.from_state == old_nombre
        assert log.to_state == "Sala nueva"

    def test_update_no_changes_emits_no_entries(self, admin_user, vitrina):
        c = self._client(admin_user)
        resp = c.post(
            reverse("catalog:vitrina_update", kwargs={"pk": vitrina.pk}),
            {"nombre": vitrina.nombre or "", "url": vitrina.url or ""},
        )
        assert resp.status_code == 302
        assert AuditLog.objects.filter(vitrina=vitrina, action=AuditLog.ACTION_VITRINA_UPDATED).count() == 0

    def test_update_url_emits_field_audit(self, admin_user, vitrina):
        c = self._client(admin_user)
        resp = c.post(
            reverse("catalog:vitrina_update", kwargs={"pk": vitrina.pk}),
            {"nombre": vitrina.nombre or "", "url": "https://new.example.com"},
        )
        assert resp.status_code == 302
        log = AuditLog.objects.filter(vitrina=vitrina, action=AuditLog.ACTION_VITRINA_UPDATED, field="url").first()
        assert log is not None
        assert log.to_state == "https://new.example.com"
