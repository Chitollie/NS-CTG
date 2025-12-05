import discord
from discord import app_commands
from discord.ext import commands
import sys
import asyncio
import signal

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="sync", description="Synchronise les commandes slash")
    @app_commands.checks.has_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction):
        """Synchronise les commandes slash"""
        try:
            synced = await self.bot.tree.sync()
            await interaction.response.send_message(f"✅ {len(synced)} commandes synchronisées", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)

    @app_commands.command(name="shutdown", description="Éteint le bot")
    @app_commands.checks.has_permissions(administrator=True)
    async def shutdown(self, interaction: discord.Interaction):
        """Éteint le bot"""
        await interaction.response.send_message("👋 Bot arrêté")
        await self.bot.close()

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))