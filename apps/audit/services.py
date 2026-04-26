import logging
import threading

from django.conf import settings

from .models import AuditLog

logger = logging.getLogger(__name__)

STATE_LABELS = {
    "libre": "Libre",
    "asignado": "Asignado",
    "en_revision": "En revisión",
    "documentado": "Documentado",
}


def _truncate(value: str, n: int = 255) -> str:
    if len(value) <= n:
        return value
    return value[: n - 3] + "..."


def record(
    action: str,
    item,
    actor,
    *,
    field: str = "",
    from_state: str = "",
    to_state: str = "",
    payload: dict | None = None,
):
    """Create an AuditLog entry for an item and post to Discord (best-effort)."""
    log = AuditLog.objects.create(
        item=item,
        actor=actor,
        action=action,
        field=field,
        from_state=_truncate(from_state),
        to_state=_truncate(to_state),
        payload=payload or {},
    )
    _post_discord(log)
    return log


def record_vitrina(
    action: str,
    vitrina,
    actor,
    *,
    field: str = "",
    from_state: str = "",
    to_state: str = "",
    payload: dict | None = None,
):
    """Create an AuditLog entry for a vitrina and post to Discord (best-effort)."""
    log = AuditLog.objects.create(
        vitrina=vitrina,
        actor=actor,
        action=action,
        field=field,
        from_state=_truncate(from_state),
        to_state=_truncate(to_state),
        payload=payload or {},
    )
    _post_discord(log)
    return log


def record_field_changes(item, actor, old: dict, new: dict):
    """Emit one AuditLog(ACTION_UPDATED) per changed field."""
    for key in old:
        old_val = old[key]
        new_val = new.get(key, "")
        if old_val != new_val:
            record(AuditLog.ACTION_UPDATED, item, actor, field=key, from_state=old_val, to_state=new_val)


def record_vitrina_field_changes(vitrina, actor, old: dict, new: dict):
    """Emit one AuditLog(ACTION_VITRINA_UPDATED) per changed field."""
    for key in old:
        old_val = old[key]
        new_val = new.get(key, "")
        if old_val != new_val:
            record_vitrina(
                AuditLog.ACTION_VITRINA_UPDATED, vitrina, actor, field=key, from_state=old_val, to_state=new_val
            )


# ── Discord ────────────────────────────────────────────────────────────────

_DISCORD_COLORS = {
    AuditLog.ACTION_STATE_CHANGE: 0x0D6EFD,
    AuditLog.ACTION_ASSIGNED: 0x6F42C1,
    AuditLog.ACTION_CREATED: 0x198754,
    AuditLog.ACTION_UPDATED: 0xD4A017,
    AuditLog.ACTION_DEACTIVATED: 0xDC3545,
    AuditLog.ACTION_ACTIVATED: 0x198754,
    AuditLog.ACTION_PHOTO_ADDED: 0x0DCAF0,
    AuditLog.ACTION_PHOTO_DELETED: 0xFD7E14,
    AuditLog.ACTION_VITRINA_CREATED: 0x198754,
    AuditLog.ACTION_VITRINA_UPDATED: 0xD4A017,
    AuditLog.ACTION_VITRINA_DELETED: 0xDC3545,
}


def _build_discord_embed(log: AuditLog) -> dict:
    actor_name = log.actor.name if log.actor else "Sistema"
    color = _DISCORD_COLORS.get(log.action, 0x6C757D)

    if log.vitrina is not None:
        title = f"Vitrina #{log.vitrina.pk}: {log.vitrina.nombre or '(sin nombre)'}"
    else:
        title = f"Pieza #{log.item_id}: {log.item.nombre if log.item else '?'}"

    fields = [
        {"name": "Accion", "value": log.get_action_display(), "inline": True},
        {"name": "Por", "value": actor_name, "inline": True},
    ]

    if log.field:
        fields.append({"name": "Campo", "value": log.field, "inline": False})
    if log.from_state:
        fields.append({"name": "Antes", "value": log.from_state, "inline": True})
    if log.to_state:
        fields.append({"name": "Despues", "value": log.to_state, "inline": True})

    return {
        "title": title,
        "color": color,
        "fields": fields,
        "timestamp": log.created_at.isoformat(),
    }


def _post_discord(log: AuditLog):
    url = getattr(settings, "DISCORD_WEBHOOK_URL", "")
    if not url:
        return

    threading.Thread(target=_send_discord, args=(url, log), daemon=True).start()


def _send_discord(url: str, log: AuditLog):
    import requests

    try:
        embed = _build_discord_embed(log)
        resp = requests.post(url, json={"embeds": [embed]}, timeout=5)
        if not resp.ok:
            logger.warning("Discord webhook respondio %s: %s", resp.status_code, resp.text[:200])
    except Exception:
        logger.exception("Error al enviar webhook a Discord")
