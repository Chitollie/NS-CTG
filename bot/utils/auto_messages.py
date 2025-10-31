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
    try:
        # Supprimer les anciens messages du bot
        async for message in channel.history(limit=100):
            if message.author == channel.guild.me:  # Si c'est un message du bot
                if bot_filter is None or (message.content and bot_filter in message.content):
                    try:
                        await message.delete()
                    except discord.HTTPException:
                        continue  # Ignore les erreurs de suppression
        
        # Envoyer le nouveau message
        if any([content, embed, view]):
            return await channel.send(content=content, embed=embed, view=view)
        
    except discord.Forbidden:
        print(f"❌ Permissions manquantes dans le canal {channel.name}")
    except discord.HTTPException as e:
        print(f"❌ Erreur HTTP dans le canal {channel.name}: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue dans le canal {channel.name}: {e}")
    
    return None