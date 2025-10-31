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
    Nettoie les anciens messages du bot dans le canal et envoie un nouveau message.
    
    Args:
        channel: Le canal où nettoyer/envoyer
        content: Le contenu du message à envoyer (optionnel)
        embed: L'embed à envoyer (optionnel)
        view: La vue à attacher (optionnel)
        bot_filter: Texte à rechercher dans les anciens messages pour les identifier
                   Si None, supprime tous les messages du bot
    """
    # Tentative 1: suppression ciblée à partir du dernier message connu (stocké)
    store = _load_store()
    last_id = store.get(str(channel.id))
    if last_id:
        try:
            try:
                prev = await channel.fetch_message(int(last_id))
            except Exception:
                prev = None
            if prev and prev.author == channel.guild.me:
                try:
                    await prev.delete()
                except discord.Forbidden:
                    print(f"⚠️ Impossible de supprimer le message {last_id} dans {channel.name} (permission manquante). Continuer sans nettoyage.")
                except discord.HTTPException:
                    pass
        except Exception:
            # Ne pas bloquer l'envoi si fetch/delete échoue
            pass

    # Tentative 2: suppression par lecture d'historique si disponible
    try:
        async for message in channel.history(limit=100):
            if message.author == channel.guild.me:  # Si c'est un message du bot
                if bot_filter is None or (message.content and bot_filter in message.content):
                    try:
                        await message.delete()
                    except discord.Forbidden:
                        # Pas la permission de supprimer ; on arrête la boucle de suppression
                        print(f"⚠️ Impossible de supprimer les messages dans {channel.name} (permission manquante). Continuer sans nettoyage.")
                        break
                    except discord.HTTPException:
                        # Erreur lors de la suppression d'un message individuel, on continue
                        continue
    except discord.Forbidden:
        # Pas la permission de lire l'historique — on loggue et on continue pour envoyer le message
        print(f"⚠️ Impossible de lire l'historique du canal {channel.name} (permission manquante). Envoi sans nettoyage.")
    except discord.HTTPException as e:
        print(f"❌ Erreur HTTP lors de la lecture de l'historique du canal {channel.name}: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue lors de la lecture de l'historique du canal {channel.name}: {e}")

    # Tenter d'envoyer le message même si le nettoyage a échoué
    try:
        if any([content, embed, view]):
            msg = await channel.send(content=content, embed=embed, view=view)
            # Enregistrer l'ID du message envoyé pour futur nettoyage ciblé
            try:
                store = _load_store()
                store[str(channel.id)] = msg.id
                _save_store(store)
            except Exception:
                pass
            return msg
    except discord.Forbidden:
        print(f"❌ Permissions manquantes pour envoyer un message dans le canal {channel.name}")
    except discord.HTTPException as e:
        print(f"❌ Erreur HTTP lors de l'envoi dans le canal {channel.name}: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue lors de l'envoi dans le canal {channel.name}: {e}")

    return None