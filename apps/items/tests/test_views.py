import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.items.models import Item
from apps.items.state import State, apply_transition

User = get_user_model()


@pytest.fixture
def client_admin(admin_user):
    c = Client()
    c.force_login(admin_user)
    return c


@pytest.fixture
def client_user(regular_user):
    c = Client()
    c.force_login(regular_user)
    return c


@pytest.mark.django_db
class TestItemListView:
    def test_requires_login(self):
        c = Client()
        resp = c.get(reverse("items:list"))
        assert resp.status_code == 302
        assert "/login/" in resp["Location"]

    def test_admin_can_access(self, client_admin):
        resp = client_admin.get(reverse("items:list"))
        assert resp.status_code == 200

    def test_shows_active_items_by_default(self, client_admin, item):
        resp = client_admin.get(reverse("items:list") + "?activo=1")
        assert item.nombre in resp.content.decode()

    def test_hides_inactive_items_by_default(self, client_admin, item):
        item.activo = False
        item.save()
        resp = client_admin.get(reverse("items:list") + "?activo=1")
        assert item.nombre not in resp.content.decode()

    def test_shows_inactive_with_filter(self, client_admin, item):
        item.activo = False
        item.save()
        resp = client_admin.get(reverse("items:list") + "?activo=0")
        assert item.nombre in resp.content.decode()

    def test_text_search_nombre(self, client_admin, item):
        resp = client_admin.get(reverse("items:list") + f"?q={item.nombre[:5]}&activo=")
        assert item.nombre in resp.content.decode()

    def test_filter_by_estado(self, client_admin, item):
        resp = client_admin.get(reverse("items:list") + "?estado=libre&activo=1")
        assert item.nombre in resp.content.decode()
        resp2 = client_admin.get(reverse("items:list") + "?estado=documentado&activo=1")
        assert item.nombre not in resp2.content.decode()

    def test_filter_by_tipo(self, client_admin, item, tipo, admin_user):
        from apps.catalog.models import Tipo
        other_tipo = Tipo.objects.create(nombre="Monitor")
        other_item = Item.all_objects.create(nombre="Monitor VGA", created_by=admin_user)
        other_item.tipos.add(other_tipo)
        # filter by item's tipo — only item shows
        resp = client_admin.get(reverse("items:list") + f"?tipo={tipo.pk}&activo=1")
        assert item.nombre in resp.content.decode()
        assert other_item.nombre not in resp.content.decode()

    def test_item_can_have_multiple_tipos(self, admin_user):
        from apps.catalog.models import Tipo
        t1 = Tipo.objects.create(nombre="Tipo A")
        t2 = Tipo.objects.create(nombre="Tipo B")
        obj = Item.all_objects.create(nombre="Multi", created_by=admin_user)
        obj.tipos.set([t1, t2])
        obj.refresh_from_db()
        assert obj.tipos.count() == 2

    def test_pagination(self, client_admin, admin_user):
        for i in range(25):
            Item.all_objects.create(nombre=f"Item {i}", created_by=admin_user)
        resp = client_admin.get(reverse("items:list") + "?activo=1")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestItemDetailView:
    def test_requires_login(self, item):
        c = Client()
        resp = c.get(reverse("items:detail", kwargs={"pk": item.pk}))
        assert resp.status_code == 302

    def test_shows_item_details(self, client_admin, item):
        resp = client_admin.get(reverse("items:detail", kwargs={"pk": item.pk}))
        assert resp.status_code == 200
        assert item.nombre in resp.content.decode()
        assert str(item.pk) in resp.content.decode()

    def test_shows_inactive_item(self, client_admin, item):
        item.activo = False
        item.save()
        resp = client_admin.get(reverse("items:detail", kwargs={"pk": item.pk}))
        assert resp.status_code == 200


@pytest.mark.django_db
class TestItemCreateView:
    def test_requires_admin(self, client_user):
        resp = client_user.post(reverse("items:create"), {"nombre": "Test"})
        assert resp.status_code == 403

    def test_admin_can_create(self, client_admin, tipo):
        resp = client_admin.post(reverse("items:create"), {
            "nombre": "Nueva pieza", "tipos": [tipo.pk], "observaciones": ""
        })
        assert resp.status_code == 302
        assert Item.all_objects.filter(nombre="Nueva pieza").exists()


@pytest.mark.django_db
class TestItemTransitionView:
    def test_regular_user_can_assign_to_self(self, client_user, regular_user, item):
        resp = client_user.post(
            reverse("items:transition", kwargs={"pk": item.pk}),
            {"target": State.ASIGNADO},
        )
        assert resp.status_code == 302
        item.refresh_from_db()
        assert item.estado == State.ASIGNADO
        assert item.assigned_user == regular_user

    def test_invalid_transition_shows_error(self, client_user, regular_user, item, admin_user):
        # Try to go to documentado from libre — forbidden
        resp = client_user.post(
            reverse("items:transition", kwargs={"pk": item.pk}),
            {"target": State.DOCUMENTADO},
            follow=True,
        )
        assert resp.status_code == 200
        item.refresh_from_db()
        assert item.estado == State.LIBRE

    def test_admin_can_mark_documentado(self, client_admin, admin_user, regular_user, item):
        apply_transition(item, State.ASIGNADO, regular_user, assign_to=regular_user)
        apply_transition(item, State.EN_REVISION, regular_user, url="https://example.com")
        resp = client_admin.post(
            reverse("items:transition", kwargs={"pk": item.pk}),
            {"target": State.DOCUMENTADO},
        )
        assert resp.status_code == 302
        item.refresh_from_db()
        assert item.estado == State.DOCUMENTADO

    def test_transition_to_en_revision_without_url_fails(self, client_user, regular_user, item):
        apply_transition(item, State.ASIGNADO, regular_user, assign_to=regular_user)
        resp = client_user.post(
            reverse("items:transition", kwargs={"pk": item.pk}),
            {"target": State.EN_REVISION},
            follow=True,
        )
        assert resp.status_code == 200
        item.refresh_from_db()
        assert item.estado == State.ASIGNADO  # not advanced

    def test_transition_to_en_revision_sets_url(self, client_user, regular_user, item):
        apply_transition(item, State.ASIGNADO, regular_user, assign_to=regular_user)
        resp = client_user.post(
            reverse("items:transition", kwargs={"pk": item.pk}),
            {"target": State.EN_REVISION, "url": "https://example.com/pieza"},
        )
        assert resp.status_code == 302
        item.refresh_from_db()
        assert item.estado == State.EN_REVISION
        assert item.url == "https://example.com/pieza"


@pytest.mark.django_db
class TestItemDeactivateView:
    def test_requires_admin(self, client_user, item):
        resp = client_user.post(reverse("items:deactivate", kwargs={"pk": item.pk}))
        assert resp.status_code == 403

    def test_admin_can_deactivate(self, client_admin, item):
        resp = client_admin.post(reverse("items:deactivate", kwargs={"pk": item.pk}))
        assert resp.status_code == 302
        item.refresh_from_db()
        assert item.activo is False

    def test_admin_can_reactivate(self, client_admin, item):
        item.activo = False
        item.save()
        resp = client_admin.post(reverse("items:deactivate", kwargs={"pk": item.pk}))
        assert resp.status_code == 302
        item.refresh_from_db()
        assert item.activo is True
