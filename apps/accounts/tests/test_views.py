import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestUserCRUDViews:
    def test_list_requires_admin(self, regular_user):
        c = Client()
        c.force_login(regular_user)
        resp = c.get(reverse("accounts:user_list"))
        assert resp.status_code == 403

    def test_admin_can_list_users(self, admin_user):
        c = Client()
        c.force_login(admin_user)
        resp = c.get(reverse("accounts:user_list"))
        assert resp.status_code == 200

    def test_admin_can_create_user(self, admin_user):
        c = Client()
        c.force_login(admin_user)
        resp = c.post(
            reverse("accounts:user_create"),
            {
                "email": "new@test.com",
                "name": "New User",
                "is_staff": False,
                "password1": "complex-pass-123",
                "password2": "complex-pass-123",
            },
        )
        assert resp.status_code == 302
        assert User.objects.filter(email="new@test.com").exists()

    def test_admin_can_update_user(self, admin_user, regular_user):
        c = Client()
        c.force_login(admin_user)
        resp = c.post(
            reverse("accounts:user_update", kwargs={"pk": regular_user.pk}),
            {
                "email": regular_user.email,
                "name": "Updated Name",
                "is_staff": False,
                "is_active": True,
            },
        )
        assert resp.status_code == 302
        regular_user.refresh_from_db()
        assert regular_user.name == "Updated Name"


@pytest.mark.django_db
class TestPasswordChange:
    def test_requires_login(self):
        c = Client()
        resp = c.get(reverse("password_change"))
        assert resp.status_code == 302
        assert "/login/" in resp.url

    def test_authenticated_can_access(self, regular_user):
        c = Client()
        c.force_login(regular_user)
        resp = c.get(reverse("password_change"))
        assert resp.status_code == 200

    def test_password_changes(self, regular_user):
        c = Client()
        c.force_login(regular_user)
        resp = c.post(
            reverse("password_change"),
            {
                "old_password": "testpass",
                "new_password1": "new-complex-pass-456",
                "new_password2": "new-complex-pass-456",
            },
        )
        assert resp.status_code == 302
        regular_user.refresh_from_db()
        assert regular_user.check_password("new-complex-pass-456")

    def test_done_page(self, regular_user):
        c = Client()
        c.force_login(regular_user)
        resp = c.get(reverse("password_change_done"))
        assert resp.status_code == 200
