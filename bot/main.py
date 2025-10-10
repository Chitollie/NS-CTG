import discord
from discord.ext import commands
from bot.config import TOKEN, GUILD_ID
from bot.events import setup_events
from bot.commands.menu import menu_cmd
from bot.web_server import keep_alive

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def setup():
    bot.tree.add_command(menu_cmd, guild=discord.Object(id=GUILD_ID))
    await setup_events(bot)

keep_alive()

import asyncio
asyncio.run(setup())
bot.run(TOKEN)