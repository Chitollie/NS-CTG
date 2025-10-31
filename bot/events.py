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

        from .utils.auto_messages import clean_and_send
        # Identification
        channel = bot.get_channel(IDENT_CHANNEL_ID)
        if isinstance(channel, discord.TextChannel):
            await clean_and_send(
                channel,
                content="Clique sur le bouton pour t'identifier :",
                view=IdentificationButtonView(),
                bot_filter="Clique sur le bouton pour t'identifier"
            )

        # Demande d'agents
        ask_channel = bot.get_channel(ASKMISS_CHANNEL_ID)
        if isinstance(ask_channel, discord.TextChannel):
            embed = discord.Embed(
                title="📢 Demandes d'agents",
                description="Clique sur le bouton ci-dessous pour demander une sécurisation.",
                color=discord.Color.green(),
            )
            await clean_and_send(
                ask_channel,
                embed=embed,
                view=AskMissView(),
                bot_filter="📢 Demandes d'agents"
            )

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