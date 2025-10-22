import discord
from discord.ext import commands
from bot.config import TOKEN, GUILD_ID
from bot.events import setup_events
from bot.commands.menu import menu_cmd
from bot.commands.annonces import annonces_cmd
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
    # Register member join handler to send welcome messages
    setup_join(bot)
    # Load contacts extension to send menu view
    await contacts.setup(bot)


if TOKEN is None:
    raise RuntimeError("TOKEN n'est pas défini dans le fichier .env")

bot.run(TOKEN)
