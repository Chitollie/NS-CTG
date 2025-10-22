import discord

# --- Configuration (par défaut, changez l'ID ou appelez la fonction avec un channel spécifique) ---
DEFAULT_CHANNEL_ID = 1424405632001376378
MESSAGE_IDENTIFIER = "📜 Règlement du Serveur"


async def send_rules(bot: discord.Client, channel_id: int = DEFAULT_CHANNEL_ID):
    channel = bot.get_channel(channel_id)
    if channel is None or not isinstance(channel, discord.TextChannel):
        return

    # --- Vérifie s'il existe déjà un embed avec ce titre ---
    async for message in channel.history(limit=50):
        if message.author == bot.user and message.embeds:
            embed = message.embeds[0]
            if embed.title == MESSAGE_IDENTIFIER:
                return

    # --- Crée l'embed ---
    embed = discord.Embed(
        title=MESSAGE_IDENTIFIER,
        description=(
            "Bienvenue sur le serveur ! Merci de lire attentivement ce règlement 💜\n\n"
            "1️⃣ **Respect** – Aucune insulte, moquerie ou comportement toxique.\n"
            "2️⃣ **Spam** – Évitez les messages inutiles, le flood ou les majuscules excessives.\n"
            "3️⃣ **Contenu** – Pas de contenu NSFW, raciste, homophobe ou offensant.\n"
            "4️⃣ **Publicité** – Interdite sans l’accord du staff.\n"
            "5️⃣ **Canaux** – Respectez les thèmes de chaque salon.\n\n"
            "⚠️ Tout manquement à ces règles peut entraîner une sanction."
        ),
        color=discord.Color.purple()
    )
    embed.set_footer(text="Merci de respecter ces règles ❤️")
    embed.set_thumbnail(url="")
    embed.set_author(name="", icon_url="")

    await channel.send(embed=embed)
