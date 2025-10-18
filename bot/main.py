import discord
from discord.ext import commands
from bot.config import TOKEN, GUILD_ID
from bot.events import setup_events
from bot.commands.menu import menu_cmd
from bot.web_server import keep_alive
from bot.commands.annonces import annonces_cmd

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def setup_hook():
    bot.tree.add_command(menu_cmd, guild=discord.Object(id=GUILD_ID))
    bot.tree.add_command(annonces_cmd, guild=discord.Object(id=GUILD_ID))
    await setup_events(bot)


keep_alive()

import asyncio

asyncio.run(setup())

if TOKEN is None:
    raise RuntimeError("TOKEN n'est pas défini dans le fichier .env")

bot.run(TOKEN)
