import discord
from discord import app_commands
from ..config import GUILD_ID
from ..views.menu_view import MenuView

@app_commands.command(name="menu", description="Ouvrir le menu")
async def menu_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(
        title="Bienvenue chez Nova Sécurité",
        description="Choisissez une option ci-dessous :",
        color=discord.Color.dark_blue(),
    )
    await interaction.followup.send(embed=embed, view=MenuView(), ephemeral=True)
