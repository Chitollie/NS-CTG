import discord
from discord import app_commands
from discord.ext import commands
from bot.config import GUILD_ID
from bot.views.menu_view import MenuView

class MenuCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="menu",
        description="Affiche le menu principal"
    )
    async def menu(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Bienvenue chez Nova Sécurité",
            description="Choisissez une option ci-dessous :",
            color=discord.Color.dark_blue(),
        )
        await interaction.response.send_message(embed=embed, view=MenuView())

    @commands.Cog.listener()
    async def on_ready(self):
        guild = discord.Object(id=GUILD_ID)
        self.bot.tree.copy_global_to(guild=guild)
        synced = await self.bot.tree.sync(guild=guild)
        print(f"[Nova Sécurité] Slash commands synchronisées : {len(synced)}")

async def setup(bot: commands.Bot):
    cog = MenuCog(bot)
    await bot.add_cog(cog)

    bot.tree.add_command(cog.menu)
