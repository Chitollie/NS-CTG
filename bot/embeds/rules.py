import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

# --- Configuration ---
CHANNEL_ID = 1424405632001376378
MESSAGE_IDENTIFIER = "📜 Règlement du Serveur"

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("⚠️ Salon introuvable, vérifie l’ID du salon.")
        return

    # --- Vérifie s'il existe déjà un embed avec ce titre ---
    async for message in channel.history(limit=50):
        if message.author == bot.user and message.embeds:
            embed = message.embeds[0]
            if embed.title == MESSAGE_IDENTIFIER:
                print("⚠️ Un règlement existe déjà, rien n’a été renvoyé.")
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

    # --- Envoie le message ---
    await channel.send(embed=embed)
    print("📨 Embed du règlement envoyé avec succès !")

bot.run(TOKEN)
