import discord
from discord import app_commands
from discord.ext import commands
import sys
import asyncio
import signal

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
    
    # Référence au bot depuis l'interaction
    bot = interaction.client
    
    # Prévenir les utilisateurs dans les tickets ouverts
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
        pass  # Ignorer les erreurs de notification
    
    # Envoyer confirmation finale
    embed.description = "✅ Arrêt terminé. Le bot va redémarrer automatiquement."
    embed.color = discord.Color.green()
    try:
        await interaction.followup.send(embed=embed, ephemeral=True)
    except:
        pass
    
    # Attendre un peu pour que les messages soient envoyés
    await asyncio.sleep(2)
    
    # Arrêter le bot
    await bot.close()
    
def setup(bot: commands.Bot):
    # Attacher les gestionnaires de signaux pour Replit
    def signal_handler(signum, frame):
        print("\n⚠️ Signal d'arrêt reçu, arrêt propre en cours...")
        asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
    
    # SIGTERM est envoyé par Replit lors de l'arrêt
    signal.signal(signal.SIGTERM, signal_handler)
    # SIGINT pour Ctrl+C en local
    signal.signal(signal.SIGINT, signal_handler)
    
    bot.tree.add_command(shutdown_cmd)