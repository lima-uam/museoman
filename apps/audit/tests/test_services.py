import json
from unittest.mock import patch

import pytest
import responses as responses_lib

from apps.audit.models import AuditLog
from apps.audit.services import record, record_field_changes


class _SyncThread:
    """Runs target immediately on start() -- makes Discord calls synchronous in tests."""

    def __init__(self, target, args=(), daemon=False, **kwargs):
        self._target = target
        self._args = args

    def start(self):
        self._target(*self._args)


@pytest.mark.django_db
class TestAuditRecord:
    def test_creates_log_entry(self, item, admin_user):
        log = record(AuditLog.ACTION_STATE_CHANGE, item, admin_user, from_state="Libre", to_state="Asignado")
        assert log.pk is not None
        assert log.action == AuditLog.ACTION_STATE_CHANGE
        assert log.from_state == "Libre"
        assert log.to_state == "Asignado"
        assert log.actor == admin_user
        assert log.item == item

    def test_discord_not_called_when_url_empty(self, item, admin_user, settings):
        settings.DISCORD_WEBHOOK_URL = ""
        record(AuditLog.ACTION_DEACTIVATED, item, admin_user)

    @responses_lib.activate
    def test_discord_called_when_url_set(self, item, admin_user, settings):
        url = "https://discord.com/api/webhooks/test/token"
        settings.DISCORD_WEBHOOK_URL = url
        responses_lib.add(responses_lib.POST, url, json={}, status=200)

        with patch("apps.audit.services.threading.Thread", _SyncThread):
            record(AuditLog.ACTION_STATE_CHANGE, item, admin_user, from_state="Libre", to_state="Asignado")

        assert len(responses_lib.calls) == 1
        body = json.loads(responses_lib.calls[0].request.body)
        assert "embeds" in body
        assert body["embeds"][0]["color"] == 0x0D6EFD

    @responses_lib.activate
    def test_discord_failure_does_not_raise(self, item, admin_user, settings):
        url = "https://discord.com/api/webhooks/test/token"
        settings.DISCORD_WEBHOOK_URL = url
        responses_lib.add(responses_lib.POST, url, body=Exception("network error"))

        with patch("apps.audit.services.threading.Thread", _SyncThread):
            record(AuditLog.ACTION_DEACTIVATED, item, admin_user)

    @responses_lib.activate
    def test_discord_embed_includes_field_and_values(self, item, admin_user, settings):
        url = "https://discord.com/api/webhooks/test/token"
        settings.DISCORD_WEBHOOK_URL = url
        responses_lib.add(responses_lib.POST, url, json={}, status=200)

        with patch("apps.audit.services.threading.Thread", _SyncThread):
            record(AuditLog.ACTION_UPDATED, item, admin_user, field="nombre", from_state="Viejo", to_state="Nuevo")

        body = json.loads(responses_lib.calls[0].request.body)
        embed = body["embeds"][0]
        field_names = [f["name"] for f in embed["fields"]]
        assert "Campo" in field_names
        assert "Antes" in field_names
        assert "Despues" in field_names
        campo = next(f for f in embed["fields"] if f["name"] == "Campo")
        assert campo["value"] == "nombre"

    @responses_lib.activate
    def test_discord_embed_consistent_layout_when_no_field(self, item, admin_user, settings):
        url = "https://discord.com/api/webhooks/test/token"
        settings.DISCORD_WEBHOOK_URL = url
        responses_lib.add(responses_lib.POST, url, json={}, status=200)

        with patch("apps.audit.services.threading.Thread", _SyncThread):
            record(AuditLog.ACTION_STATE_CHANGE, item, admin_user, from_state="Libre", to_state="Asignado")

        body = json.loads(responses_lib.calls[0].request.body)
        embed = body["embeds"][0]
        field_names = [f["name"] for f in embed["fields"] if f["name"] not in ("", "​")]
        assert field_names == ["Accion", "Por", "Campo", "Antes", "Despues"]
        campo = next(f for f in embed["fields"] if f["name"] == "Campo")
        assert campo["value"] == "-"


@pytest.mark.django_db
class TestRecordFieldChanges:
    def test_emits_nothing_when_no_changes(self, item, admin_user):
        values = {"nombre": "Pieza A", "url": ""}
        record_field_changes(item, admin_user, values, values.copy())
        assert AuditLog.objects.filter(item=item, action=AuditLog.ACTION_UPDATED).count() == 0

    def test_emits_one_entry_per_changed_field(self, item, admin_user):
        old = {"nombre": "Viejo", "url": ""}
        new = {"nombre": "Nuevo", "url": "https://example.com"}
        record_field_changes(item, admin_user, old, new)
        logs = list(AuditLog.objects.filter(item=item, action=AuditLog.ACTION_UPDATED).order_by("field"))
        assert len(logs) == 2
        nombre_log = next(entry for entry in logs if entry.field == "nombre")
        assert nombre_log.from_state == "Viejo"
        assert nombre_log.to_state == "Nuevo"

    def test_truncates_long_values(self, item, admin_user):
        long_value = "x" * 300
        old = {"obs": long_value}
        new = {"obs": "corto"}
        record_field_changes(item, admin_user, old, new)
        log = AuditLog.objects.get(item=item, action=AuditLog.ACTION_UPDATED, field="obs")
        assert len(log.from_state) == 255
        assert log.from_state.endswith("...")
