import discord
from discord.ext import commands
from .config import GUILD_ID, IDENT_CHANNEL_ID
from .views.identification_view import IdentificationButtonView
from .views.askmiss_view import AskMissView
from .config import ASKMISS_CHANNEL_ID
from .config import LOC_CHANNEL_ID
from .embeds.localisation import send_localisation_image
from .embeds.tarifs import tarifs_embed
from .views.tarifs_view import TarifsModal


async def setup_events(bot: commands.Bot):
    @bot.event
    async def on_ready():
        print(f"✅ Connecté en tant que {bot.user}")
        try:
            # sync application commands for the specific guild
            synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
            print(f"Commandes slash synchronisées : {len(synced)}")
        except Exception as e:
            print(e)

        # Try to get the identification channel and send the identification view if missing
        channel = bot.get_channel(IDENT_CHANNEL_ID)
        if isinstance(channel, discord.TextChannel):
            async for msg in channel.history(limit=50):
                if msg.author == bot.user and getattr(msg, "components", None):
                    break
            else:
                await channel.send("Clique sur le bouton pour t'identifier :", view=IdentificationButtonView())

        # Also ensure there's a persistent message in the ask-mission channel
        ask_channel = bot.get_channel(ASKMISS_CHANNEL_ID)
        if isinstance(ask_channel, discord.TextChannel):
            async for msg in ask_channel.history(limit=50):
                if msg.author == bot.user and getattr(msg, "components", None):
                    break
            else:
                embed = discord.Embed(
                    title="📢 Demandes d'agents",
                    description="Clique sur le bouton ci-dessous pour créer une demande d'agents.",
                    color=discord.Color.green(),
                )
                await ask_channel.send(embed=embed, view=AskMissView())

        # Send localisation image if provided (checks for LOC_CHANNEL_ID existence)
        loc_channel = bot.get_channel(LOC_CHANNEL_ID)
        if isinstance(loc_channel, discord.TextChannel):
            # If you want to use an environment-specified image url, attempt to read it
            import os
            image_url = os.getenv("LOC_IMAGE_URL")
            if image_url:
                await send_localisation_image(bot, image_url, alt_text="Localisation de nos équipes")

        # Optionally send tarifs embed to the same ask channel or a tarifs channel (reuse ask_channel)
        try:
            tarifs_msg_embed = tarifs_embed()
            if isinstance(ask_channel, discord.TextChannel):
                await ask_channel.send(embed=tarifs_msg_embed)
        except Exception:
            pass
