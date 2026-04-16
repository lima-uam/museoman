import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        u = User.objects.create_user(email="test@example.com", name="Test User", password="pass")
        assert u.email == "test@example.com"
        assert u.name == "Test User"
        assert not u.is_staff
        assert u.is_active
        assert u.check_password("pass")

    def test_create_superuser(self):
        u = User.objects.create_superuser(email="admin@example.com", name="Admin", password="pass")
        assert u.is_staff
        assert u.is_superuser
        assert u.is_admin  # property alias

    def test_email_is_username_field(self):
        assert User.USERNAME_FIELD == "email"

    def test_str(self):
        u = User(email="a@b.com", name="Alice")
        assert "Alice" in str(u)
        assert "a@b.com" in str(u)

    def test_create_user_no_email_raises(self):
        with pytest.raises(ValueError):
            User.objects.create_user(email="", name="X", password="p")

    def test_email_is_unique(self):
        User.objects.create_user(email="dup@example.com", name="A", password="p")
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            User.objects.create_user(email="dup@example.com", name="B", password="p")
