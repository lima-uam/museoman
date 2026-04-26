import logging

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

_WIDGET_URL = "https://discord.com/api/guilds/{id}/widget.json"
_GUILD_URL = "https://discord.com/api/guilds/{id}?with_counts=true"
_TTL = 60


def get_discord_widget() -> dict | None:
    cached = cache.get("discord:widget")
    if cached is not None:
        return cached

    guild_id = settings.DISCORD_GUILD_ID
    try:
        resp = requests.get(_WIDGET_URL.format(id=guild_id), timeout=3)
        if resp.status_code != 200:
            logger.warning("Discord widget returned %s", resp.status_code)
            return None
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Discord widget fetch failed: %s", exc)
        return None

    if settings.DISCORD_BOT_TOKEN:
        try:
            bot_resp = requests.get(
                _GUILD_URL.format(id=guild_id),
                headers={"Authorization": f"Bot {settings.DISCORD_BOT_TOKEN}"},
                timeout=3,
            )
            if bot_resp.status_code == 200:
                guild = bot_resp.json()
                data["member_count"] = guild.get("approximate_member_count")
        except requests.RequestException as exc:
            logger.warning("Discord guild fetch failed: %s", exc)

    cache.set("discord:widget", data, _TTL)
    return data
