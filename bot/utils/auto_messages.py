import discord
from typing import Optional

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
    # Tentative de suppression des anciens messages — non bloquante si permissions manquantes
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
            return await channel.send(content=content, embed=embed, view=view)
    except discord.Forbidden:
        print(f"❌ Permissions manquantes pour envoyer un message dans le canal {channel.name}")
    except discord.HTTPException as e:
        print(f"❌ Erreur HTTP lors de l'envoi dans le canal {channel.name}: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue lors de l'envoi dans le canal {channel.name}: {e}")

    return None