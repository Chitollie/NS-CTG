import discord
from discord.ext import commands
from bot import config


def setup_join(bot: commands.Bot):

    WELCOME_CHANNEL_ID = getattr(config, "JOIN_CHANNEL_ID", None)
    CHANNEL_ID_IDENTITE = getattr(config, "IDENT_CHANNEL_ID", None)

    @bot.event
    async def on_member_join(member):
        welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID) if WELCOME_CHANNEL_ID else None
        identite_channel = bot.get_channel(CHANNEL_ID_IDENTITE) if CHANNEL_ID_IDENTITE else None

        if not welcome_channel or not identite_channel:
            print("⚠️ Impossible de trouver le salon de bienvenue ou d'identité.")
            return

        embed = discord.Embed(
            title="🎉 Bienvenue sur Nova Security !",
            description=(
                f"Bienvenue à toi {member.mention} 💜\n\n"
                f"Nous sommes ravis de t'accueillir parmi nous !\n"
                f"➡️ Pense à t'enregistrer dans {getattr(identite_channel, 'mention', '#salon-identite')} pour valider ton arrivée ✨"
            ),
            color=discord.Color.purple()
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Un nouveau citoyen vient d'arriver 🌆")

        if isinstance(welcome_channel, discord.TextChannel):
            await welcome_channel.send(embed=embed)
        print(f"👋 Nouveau membre détecté : {member.name}")
