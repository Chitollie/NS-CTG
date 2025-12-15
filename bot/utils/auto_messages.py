import discord
from typing import Optional
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
STORAGE_PATH = BASE_DIR / "data" / "auto_messages.json"

def _load_store() -> dict:
    try:
        if STORAGE_PATH.exists():
            return json.loads(STORAGE_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_store(d: dict):
    try:
        STORAGE_PATH.write_text(
            json.dumps(d, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        pass


async def clean_and_send(
    channel: discord.TextChannel,
    content: Optional[str] = None,
    *,
    embed: Optional[discord.Embed] = None,
    view: Optional[discord.ui.View] = None,
    bot_filter: str = None
)   -> Optional[discord.Message]:


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

    if last_id:
        try:
            prev = await channel.fetch_message(int(last_id))
            if prev and getattr(prev.author, "id", None) == bot_id:
                await prev.edit(content=content, embed=embed, view=view)
                msg = prev
        except discord.NotFound:
            pass
        except discord.Forbidden:
            print(f"⚠️ Pas les permissions pour modifier le message {last_id} dans {channel.name}")
        except discord.HTTPException:
            pass

    if msg is None:
        try:
            msg = await channel.send(content=content, embed=embed, view=view)

            store[str(channel.id)] = str(msg.id)
            _save_store(store)

        except discord.Forbidden:
            print(f"❌ Permissions manquantes pour envoyer un message dans le canal {channel.name}")
        except discord.HTTPException as e:
            print(f"❌ Erreur HTTP lors de l’envoi dans le canal {channel.name}: {e}")
        except Exception as e:
            print(f"❌ Erreur inattendue lors de l’envoi dans le canal {channel.name}: {e}")

    return msg
