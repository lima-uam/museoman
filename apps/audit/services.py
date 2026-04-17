import logging

from django.conf import settings

from .models import AuditLog

logger = logging.getLogger(__name__)

STATE_LABELS = {
    "libre": "Libre",
    "asignado": "Asignado",
    "en_revision": "En revisión",
    "documentado": "Documentado",
}


def record(action: str, item, actor, *, from_state: str = "", to_state: str = "", payload: dict | None = None):
    """Create an AuditLog entry for an item and post to Discord (best-effort)."""
    log = AuditLog.objects.create(
        item=item,
        actor=actor,
        action=action,
        from_state=from_state,
        to_state=to_state,
        payload=payload or {},
    )
    _post_discord(log)
    return log


def record_vitrina(action: str, vitrina, actor, *, payload: dict | None = None):
    """Create an AuditLog entry for a vitrina and post to Discord (best-effort)."""
    log = AuditLog.objects.create(
        vitrina=vitrina,
        actor=actor,
        action=action,
        payload=payload or {},
    )
    _post_discord(log)
    return log


def _build_discord_message(log: AuditLog) -> str:
    actor_name = log.actor.name if log.actor else "Sistema"
    action_label = log.get_action_display()

    if log.vitrina is not None:
        subject = f"**Vitrina #{log.vitrina.pk}** — {log.vitrina.nombre or '(sin nombre)'}"
        return f"[Museoman] {subject} | {action_label} | por {actor_name}"

    item_str = f"**#{log.item.pk}** — {log.item.nombre}"

    if log.action == AuditLog.ACTION_STATE_CHANGE:
        from_label = STATE_LABELS.get(log.from_state, log.from_state)
        to_label = STATE_LABELS.get(log.to_state, log.to_state)
        detail = f"{from_label} → {to_label}"
    else:
        detail = action_label

    return f"[Museoman] {item_str} | {detail} | por {actor_name}"


def _post_discord(log: AuditLog):
    url = getattr(settings, "DISCORD_WEBHOOK_URL", "")
    if not url:
        return

    import requests

    try:
        message = _build_discord_message(log)
        resp = requests.post(url, json={"content": message}, timeout=5)
        if not resp.ok:
            logger.warning("Discord webhook respondió %s: %s", resp.status_code, resp.text[:200])
    except Exception:
        logger.exception("Error al enviar webhook a Discord")
