import discord
from discord import app_commands
from discord.ext import commands
from bot.config import GUILD_ID
from bot.views.menu_view import MenuView

class MenuCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="menu", description="Affiche le menu principal")
    async def menu(self, interaction: discord.Interaction):
        """Affiche le menu principal"""
        embed = discord.Embed(
            title="Bienvenue chez Nova Sécurité",
            description="Choisissez une option ci-dessous :",
            color=discord.Color.dark_blue(),
        )
        await interaction.response.send_message(embed=embed, view=MenuView())

async def setup(bot: commands.Bot):
    await bot.add_cog(MenuCog(bot))
