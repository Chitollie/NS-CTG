import discord
from ..config import TARIF_CHANNEL_ID


async def send_tarifs(client: discord.Client):
    embed = discord.Embed(
        title="Nos Tarifs",
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

    channel = client.get_channel(TARIF_CHANNEL_ID)
    if not channel:
        return

    # Vérifie si un embed similaire a déjà été envoyé récemment
    async for message in channel.history(limit=50):
        if message.author == client.user and message.embeds:
            if message.embeds[0].title == embed.title:
                return

    await channel.send(embed=embed)