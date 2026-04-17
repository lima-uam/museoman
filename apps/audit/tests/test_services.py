import pytest
import responses as responses_lib
from unittest.mock import patch

from apps.audit.models import AuditLog
from apps.audit.services import record


class _SyncThread:
    """Runs target immediately on start() — makes Discord calls synchronous in tests."""
    def __init__(self, target, args=(), daemon=False, **kwargs):
        self._target = target
        self._args = args
    def start(self):
        self._target(*self._args)


@pytest.mark.django_db
class TestAuditRecord:
    def test_creates_log_entry(self, item, admin_user):
        log = record(AuditLog.ACTION_STATE_CHANGE, item, admin_user, from_state="libre", to_state="asignado")
        assert log.pk is not None
        assert log.action == AuditLog.ACTION_STATE_CHANGE
        assert log.from_state == "libre"
        assert log.to_state == "asignado"
        assert log.actor == admin_user
        assert log.item == item

    def test_discord_not_called_when_url_empty(self, item, admin_user, settings):
        settings.DISCORD_WEBHOOK_URL = ""
        # Should not raise even without mocking HTTP
        record(AuditLog.ACTION_DEACTIVATED, item, admin_user)

    @responses_lib.activate
    def test_discord_called_when_url_set(self, item, admin_user, settings):
        url = "https://discord.com/api/webhooks/test/token"
        settings.DISCORD_WEBHOOK_URL = url
        responses_lib.add(responses_lib.POST, url, json={}, status=200)

        with patch("apps.audit.services.threading.Thread", _SyncThread):
            record(AuditLog.ACTION_STATE_CHANGE, item, admin_user, from_state="libre", to_state="asignado")

        assert len(responses_lib.calls) == 1
        assert b"Museoman" in responses_lib.calls[0].request.body

    @responses_lib.activate
    def test_discord_failure_does_not_raise(self, item, admin_user, settings):
        url = "https://discord.com/api/webhooks/test/token"
        settings.DISCORD_WEBHOOK_URL = url
        responses_lib.add(responses_lib.POST, url, body=Exception("network error"))

        with patch("apps.audit.services.threading.Thread", _SyncThread):
            record(AuditLog.ACTION_DEACTIVATED, item, admin_user)
