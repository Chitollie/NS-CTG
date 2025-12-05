import discord
from discord import app_commands
from discord.ext import commands
import sys
import asyncio
import signal

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        """Synchronise les commandes slash"""
        try:
            synced = await self.bot.tree.sync()
            await ctx.send(f"✅ {len(synced)} commandes synchronisées")
        except Exception as e:
            await ctx.send(f"❌ Erreur : {e}")

@app_commands.command(name="shutdown", description="Arrêter le bot proprement (administrateurs uniquement)")
@app_commands.checks.has_permissions(administrator=True)
async def shutdown_cmd(interaction: discord.Interaction):
    """Arrête proprement le bot après avoir sauvegardé l'état si nécessaire."""
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(
        title="🔌 Arrêt du bot",
        description="Arrêt en cours...",
        color=discord.Color.orange()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)
    
    bot = interaction.client

    try:
        for guild in bot.guilds:
            ticket_category = discord.utils.get(guild.categories, name="tickets")
            if ticket_category:
                for channel in ticket_category.channels:
                    try:
                        await channel.send("⚠️ Le bot redémarre pour maintenance. Il sera de retour dans quelques instants.")
                    except:
                        continue
    except:
        pass
    
    embed.description = "✅ Arrêt terminé. Le bot va redémarrer automatiquement."
    embed.color = discord.Color.green()
    try:
        await interaction.followup.send(embed=embed, ephemeral=True)
    except:
        pass
    
    await asyncio.sleep(2)
    
    await bot.close()
    
def setup(bot: commands.Bot):
    def signal_handler(signum, frame):
        print("\n⚠️ Signal d'arrêt reçu, arrêt propre en cours...")
        asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    bot.tree.add_command(shutdown_cmd)

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))