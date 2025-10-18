import discord
from ..config import TARIF_CHANNEL_ID


async def send_tarifs(client : discord.Client):
    embed = discord.Embed(
        title="💰 Tarifs - Nova Sécurité",
        description=
        "Voici un aperçu des tarifs de base. Utilisez la simulation pour obtenir une estimation précise.",
        color=discord.Color.gold())
    embed.add_field(name="Frais de base",
                    value="50 000 $ (coûts de services)",
                    inline=False)
    embed.add_field(name="Recrue", value="10 000 $ / agent", inline=True)
    embed.add_field(name="Agent confirmé",
                    value="12 500 $ / agent",
                    inline=True)
    embed.add_field(name="Responsable", value="15 000 $ / agent", inline=True)
    embed.set_footer(text="Simulation disponible via le /menu")

    channel =  client.get_channel(TARIF_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)