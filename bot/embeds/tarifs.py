import discord

def tarifs_embed():
    embed = discord.Embed(
        title="💰 Tarifs - Nova Sécurité",
        description="Voici un aperçu des tarifs de base. Utilisez la simulation pour obtenir une estimation précise.",
        color=discord.Color.gold()
    )
    embed.add_field(name="Frais de base", value="50 000 $ (coûts de services)", inline=False)
    embed.add_field(name="Recrue", value="10 000 $ / agent", inline=True)
    embed.add_field(name="Agent confirmé", value="12 500 $ / agent", inline=True)
    embed.add_field(name="Responsable", value="15 000 $ / agent", inline=True)
    embed.set_footer(text="Simulation disponible via le /menu")
    return embed
