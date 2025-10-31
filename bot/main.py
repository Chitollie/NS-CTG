import discord
from discord.ext import commands
from bot.config import TOKEN, GUILD_ID
from bot.events import setup_events
from bot.commands.menu import menu_cmd
from bot.commands.annonces import annonces_cmd
from bot.commands import admin
from bot.utils.join import setup_join
from bot.embeds import contacts

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def setup_hook():
    bot.tree.add_command(menu_cmd, guild=discord.Object(id=GUILD_ID))
    bot.tree.add_command(annonces_cmd, guild=discord.Object(id=GUILD_ID))
    await setup_events(bot)
    # Register admin commands (including shutdown)
    await admin.setup(bot)
    # Register member join handler to send welcome messages
    setup_join(bot)
    # Load contacts extension to send menu view
    await contacts.setup(bot)


@bot.event
async def on_disconnect():
    print("⚠️ Déconnecté de Discord. Tentative de reconnexion...")

@bot.event
async def on_shutdown():
    """Appelé juste avant l'arrêt du bot."""
    print("🔌 Arrêt propre du bot en cours...")
    # Sauvegarder ici les données importantes si nécessaire

if TOKEN is None:
    raise RuntimeError("TOKEN n'est pas défini dans le fichier .env")

try:
    bot.run(TOKEN)
except KeyboardInterrupt:
    print("\n⌨️ Arrêt par Ctrl+C")
except Exception as e:
    print(f"❌ Erreur fatale : {e}")
finally:
    print("🔄 Bot arrêté. Il redémarrera automatiquement sur Replit.")
