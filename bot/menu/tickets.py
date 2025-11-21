import discord
import random
import logging
from typing import Optional, Dict
import os
from dotenv import load_dotenv

load_dotenv()

TICKETS_CATEGORY_ID = int(os.getenv("TICKETS_CATEGORY_ID", 0))

logger = logging.getLogger("tickets")
logger.setLevel(logging.INFO)

_last_message: Dict[int, int] = {}

def _short_id() -> str:
    return str(random.randint(1000, 9999))

async def create_ticket_channel(guild: discord.Guild, name: str, requester: discord.Member, overwrites_extra: Optional[Dict[discord.Member, discord.PermissionOverwrite]] = None) -> Optional[discord.TextChannel]:
    """Crée un channel ticket classique"""
    overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False)}
    overwrites[requester] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
    if overwrites_extra:
        overwrites.update(overwrites_extra)

    category = None
    if TICKETS_CATEGORY_ID:
        category = guild.get_channel(TICKETS_CATEGORY_ID)
        if not isinstance(category, discord.CategoryChannel):
            category = None

    try:
        channel_name = f"ticket-{name}-{_short_id()}"
        if category:
            return await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        return await guild.create_text_channel(channel_name, overwrites=overwrites)
    except Exception as e:
        logger.exception(f"Erreur création channel ticket: {e}")
        return None

async def clean_and_send(channel: discord.TextChannel, content: str = None, *, embed: discord.Embed = None, view: discord.ui.View = None):
    msg = None
    last_id = _last_message.get(channel.id)
    if last_id:
        try:
            prev = await channel.fetch_message(last_id)
            await prev.edit(content=content, embed=embed, view=view)
            msg = prev
        except Exception:
            pass
    if msg is None:
        try:
            msg = await channel.send(content=content, embed=embed, view=view)
            _last_message[channel.id] = msg.id
        except Exception as e:
            logger.exception(f"Impossible d'envoyer le message dans le channel {channel.id}: {e}")
    return msg
