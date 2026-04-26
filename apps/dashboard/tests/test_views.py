from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

_FAKE_WIDGET = {
    "name": "LIMA Discord",
    "presence_count": 7,
    "instant_invite": "https://discord.gg/test",
    "channels": [{"id": "1", "name": "General", "position": 0}],
    "members": [
        {"id": "u1", "username": "Ana", "status": "online", "avatar_url": None},
        {"id": "u2", "username": "Pedro", "status": "idle", "avatar_url": None},
    ],
}


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
class TestAboutAssignmentLimit:
    def test_limit_sentence_shown(self, settings):
        settings.ITEM_ASSIGNMENT_LIMIT = 5
        with patch("apps.dashboard.views.get_discord_widget", return_value=None):
            c = Client()
            resp = c.get(reverse("about"))
        assert b"5 piezas pendientes" in resp.content

    def test_unlimited_sentence_shown(self, settings):
        settings.ITEM_ASSIGNMENT_LIMIT = 0
        with patch("apps.dashboard.views.get_discord_widget", return_value=None):
            c = Client()
            resp = c.get(reverse("about"))
        assert b"No hay l" in resp.content  # "No hay límite..."


@pytest.mark.django_db
class TestAboutView:
    def test_accessible_without_login(self):
        with patch("apps.dashboard.views.get_discord_widget", return_value=None):
            c = Client()
            resp = c.get(reverse("about"))
        assert resp.status_code == 200

    def test_shows_stats(self, item):
        with patch("apps.dashboard.views.get_discord_widget", return_value=None):
            c = Client()
            resp = c.get(reverse("about"))
        assert resp.status_code == 200
        assert b"Total piezas activas" in resp.content

    def test_contains_discord_iframe_as_fallback(self):
        with patch("apps.dashboard.views.get_discord_widget", return_value=None):
            c = Client()
            resp = c.get(reverse("about"))
        assert b"discord.com/widget" in resp.content

    def test_contains_project_info(self):
        with patch("apps.dashboard.views.get_discord_widget", return_value=None):
            c = Client()
            resp = c.get(reverse("about"))
        assert b"Museoman" in resp.content
        assert b"LIMA" in resp.content

    def test_renders_discord_card_when_widget_available(self):
        with patch("apps.dashboard.views.get_discord_widget", return_value=_FAKE_WIDGET):
            c = Client()
            resp = c.get(reverse("about"))
        content = resp.content.decode()
        assert "LIMA Discord" in content
        assert "7" in content
        assert "Unirse al servidor" in content
        assert "Ana" in content
        assert "discord.com/widget" not in content

    def test_falls_back_to_iframe_on_widget_failure(self):
        with patch("apps.dashboard.views.get_discord_widget", return_value=None):
            c = Client()
            resp = c.get(reverse("about"))
        assert b"discord.com/widget" in resp.content
        assert b"discord-card" not in resp.content
