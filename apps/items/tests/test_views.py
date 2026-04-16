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
        item.refresh_from_db()
        item.activo = False
        item.save()
        resp = client_admin.get(reverse("items:list") + "?activo=1")
        assert item.identificador not in resp.content.decode()

    def test_shows_inactive_with_filter(self, client_admin, item):
        item.refresh_from_db()
        item.activo = False
        item.save()
        resp = client_admin.get(reverse("items:list") + "?activo=0")
        assert item.identificador in resp.content.decode()

    def test_text_search_nombre(self, client_admin, item):
        item.refresh_from_db()
        resp = client_admin.get(reverse("items:list") + f"?q={item.nombre[:5]}&activo=")
        assert item.identificador in resp.content.decode()

    def test_text_search_identificador(self, client_admin, item):
        item.refresh_from_db()
        resp = client_admin.get(reverse("items:list") + f"?q={item.identificador}&activo=")
        assert item.nombre in resp.content.decode()

    def test_filter_by_estado(self, client_admin, item):
        item.refresh_from_db()
        resp = client_admin.get(reverse("items:list") + "?estado=libre&activo=1")
        assert item.identificador in resp.content.decode()
        resp2 = client_admin.get(reverse("items:list") + "?estado=documentado&activo=1")
        assert item.identificador not in resp2.content.decode()

    def test_pagination(self, client_admin, tipo, admin_user):
        for i in range(25):
            Item.all_objects.create(nombre=f"Item {i}", tipo=tipo, created_by=admin_user)
        resp = client_admin.get(reverse("items:list") + "?activo=1")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestItemDetailView:
    def test_requires_login(self, item):
        c = Client()
        resp = c.get(reverse("items:detail", kwargs={"pk": item.pk}))
        assert resp.status_code == 302

    def test_shows_item_details(self, client_admin, item):
        item.refresh_from_db()
        resp = client_admin.get(reverse("items:detail", kwargs={"pk": item.pk}))
        assert resp.status_code == 200
        assert item.nombre in resp.content.decode()
        assert item.identificador in resp.content.decode()

    def test_shows_inactive_item(self, client_admin, item):
        item.activo = False
        item.save()
        resp = client_admin.get(reverse("items:detail", kwargs={"pk": item.pk}))
        assert resp.status_code == 200


@pytest.mark.django_db
class TestItemCreateView:
    def test_requires_admin(self, client_user, tipo):
        resp = client_user.post(reverse("items:create"), {"nombre": "Test", "tipo": tipo.pk})
        assert resp.status_code == 403

    def test_admin_can_create(self, client_admin, tipo):
        resp = client_admin.post(reverse("items:create"), {
            "nombre": "Nueva pieza", "tipo": tipo.pk, "observaciones": ""
        })
        assert resp.status_code == 302
        obj = Item.all_objects.filter(nombre="Nueva pieza").first()
        assert obj is not None
        assert obj.identificador.startswith("PIEZA-")


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
        apply_transition(item, State.EN_REVISION, regular_user)
        resp = client_admin.post(
            reverse("items:transition", kwargs={"pk": item.pk}),
            {"target": State.DOCUMENTADO},
        )
        assert resp.status_code == 302
        item.refresh_from_db()
        assert item.estado == State.DOCUMENTADO


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
