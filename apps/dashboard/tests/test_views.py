import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
class TestDashboardView:
    def test_requires_login(self):
        c = Client()
        resp = c.get(reverse("dashboard:index"))
        assert resp.status_code == 302

    def test_accessible_to_user(self, regular_user):
        c = Client()
        c.force_login(regular_user)
        resp = c.get(reverse("dashboard:index"))
        assert resp.status_code == 200

    def test_shows_state_counts(self, admin_user, item):
        c = Client()
        c.force_login(admin_user)
        resp = c.get(reverse("dashboard:index"))
        assert resp.status_code == 200
        assert b"1" in resp.content  # at least 1 item in some state


@pytest.mark.django_db
class TestAboutView:
    def test_accessible_without_login(self):
        c = Client()
        resp = c.get(reverse("about"))
        assert resp.status_code == 200

    def test_shows_stats(self, item):
        c = Client()
        resp = c.get(reverse("about"))
        assert resp.status_code == 200
        assert b"Total piezas activas" in resp.content

    def test_contains_discord_iframe(self):
        c = Client()
        resp = c.get(reverse("about"))
        assert b"discord.com/widget" in resp.content

    def test_contains_project_info(self):
        c = Client()
        resp = c.get(reverse("about"))
        assert b"Museoman" in resp.content
        assert b"LIMA" in resp.content
