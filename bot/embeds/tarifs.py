import discord
from ..config import TARIF_CHANNEL_ID

MESSAGE_IDENTIFIER = "Nos Tarifs"

async def send_tarifs(client: discord.Client):
    try:
        from ..utils.auto_messages import clean_and_send
    except ImportError:
        print("⚠️ Impossible d'importer clean_and_send")
        return

    channel = client.get_channel(TARIF_CHANNEL_ID)
    if not channel or not isinstance(channel, discord.TextChannel):
        return

    embed = discord.Embed(
        title=MESSAGE_IDENTIFIER,
        description=
        "Voici un aperçu des tarifs de base. Utilisez la simulation pour obtenir une estimation précise.",
        color=discord.Color.gold())
    embed.add_field(name="Frais de base",
                    value="50 000 $ (coûts de services)",
                    inline=False)
    embed.add_field(name="Recrue", value="10 000 $ / 30 minutes", inline=True)
    embed.add_field(name="Agent confirmé",
                    value="12 500 $ / 30 minutes",
                    inline=True)
    embed.add_field(name="Responsable",
                    value="15 000 $ / 30 minutes",
                    inline=True)
    embed.set_footer(text="Simulation disponible via le /menu")

    # Nettoie les anciens messages et envoie le nouveau
    await clean_and_send(channel, embed=embed, bot_filter=MESSAGE_IDENTIFIER)