import discord
from discord import app_commands
from discord.ext import commands
from ..config import GUILD_ID
from ..views.menu_view import MenuView

class MenuCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def menu(self, ctx: commands.Context):
        """Affiche le menu principal"""
        embed = discord.Embed(
            title="Bienvenue chez Nova Sécurité",
            description="Choisissez une option ci-dessous :",
            color=discord.Color.dark_blue(),
        )
        await ctx.send(embed=embed, view=MenuView())

async def setup(bot: commands.Bot):
    await bot.add_cog(MenuCog(bot))
