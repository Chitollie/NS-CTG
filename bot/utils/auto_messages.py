import discord
from typing import Optional
import json
from pathlib import Path

# Emplacement du fichier de stockage des derniers messages envoyés par channel
STORAGE_PATH = Path(__file__).resolve().parents[2] / "data" / "auto_messages.json"
STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_store() -> dict:
    try:
        if STORAGE_PATH.exists():
            return json.loads(STORAGE_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_store(d: dict):
    try:
        STORAGE_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


async def clean_and_send(
    channel: discord.TextChannel,
    content: Optional[str] = None,
    *,
    embed: Optional[discord.Embed] = None,
    view: Optional[discord.ui.View] = None,
    bot_filter: str = None
) -> Optional[discord.Message]:
    """
    Met à jour le dernier message envoyé par le bot dans le canal s’il existe,
    sinon envoie un nouveau message.
    """
    bot_id = None
    try:
        if channel.guild and channel.guild.me:
            bot_id = channel.guild.me.id
        else:
            bot_id = getattr(getattr(channel, "_state", None), "user", None)
            if hasattr(bot_id, "id"):
                bot_id = bot_id.id
    except Exception:
        bot_id = None

    store = _load_store()
    last_id = store.get(str(channel.id))
    msg = None

    # Essayer de récupérer et modifier le message précédent
    if last_id:
        try:
            prev = await channel.fetch_message(int(last_id))
            if prev and getattr(prev
