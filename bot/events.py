import discord
from discord.ext import commands
from bot.config import (
    GUILD_ID,
    IDENT_CHANNEL_ID,
    ASKMISS_CHANNEL_ID,
    LOC_CHANNEL_ID,
)
from bot.views.identification_view import IdentificationButtonView
from bot.views.askmiss_view import AskMissView
from bot.embeds.localisation import send_localisation_image
from bot.embeds.tarifs import send_tarifs
from bot.views.tarifs_view import TarifsModal


async def setup_events(bot: commands.Bot):

    @bot.event
    async def on_ready():
        print(f"✅ Connecté en tant que {bot.user}")
        try:
            # Synchronisation des commandes slash
            synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
            print(f"Commandes slash synchronisées : {len(synced)}")
        except Exception as e:
            print(e)

        # Identification
        channel = bot.get_channel(IDENT_CHANNEL_ID)
        if isinstance(channel, discord.TextChannel):
            async for msg in channel.history(limit=50):
                if msg.author == bot.user and getattr(msg, "components", None):
                    break
            else:
                await channel.send(
                    "Clique sur le bouton pour t'identifier :",
                    view=IdentificationButtonView()
                )

        # Demande d'agents
        ask_channel = bot.get_channel(ASKMISS_CHANNEL_ID)
        if isinstance(ask_channel, discord.TextChannel):
            async for msg in ask_channel.history(limit=50):
                if msg.author == bot.user and getattr(msg, "components", None):
                    break
            else:
                embed = discord.Embed(
                    title="📢 Demandes d'agents",
                    description="Clique sur le bouton ci-dessous pour demander une sécurisation.",
                    color=discord.Color.green(),
                )
                await ask_channel.send(embed=embed, view=AskMissView())

        # Localisation
        loc_channel = bot.get_channel(LOC_CHANNEL_ID)
        if isinstance(loc_channel, discord.TextChannel):
            import os
            image_url = os.getenv("LOC_IMAGE_URL")
            if image_url:
                await send_localisation_image(
                    bot, image_url, alt_text="Localisation de nos équipes"
                )

        # 💰 Tarifs (embed de base envoyé dans le channel configuré)
        try:
            await send_tarifs(bot)
            print("🪙 Embed des tarifs envoyé avec succès.")
        except Exception as e:
            print(f"⚠️ Erreur lors de l’envoi des tarifs : {e}")