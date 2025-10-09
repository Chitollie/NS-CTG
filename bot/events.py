import discord
from .config import GUILD_ID, IDENT_CHANNEL_ID
from .views.identification_view import IdentificationButtonView

async def setup_events(bot: discord.Client):
    @bot.event
    async def on_ready():
        print(f"✅ Connecté en tant que {bot.user}")
        try:
            synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
            print(f"Commandes slash synchronisées : {len(synced)}")
        except Exception as e:
            print(e)

        channel = bot.get_channel(IDENT_CHANNEL_ID)
        if isinstance(channel, discord.TextChannel):
            async for msg in channel.history(limit=50):
                if msg.author == bot.user and msg.components:
                    break
            else:
                await channel.send("Clique sur le bouton pour t'identifier :", view=IdentificationButtonView())
