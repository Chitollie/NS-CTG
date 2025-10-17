import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

# --- Charger le token depuis le .env ---
load_dotenv()
TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    raise RuntimeError("TOKEN n'est pas défini dans le .env")

# --- Configuration ---
WELCOME_CHANNEL_ID = 1424405724884369600
CHANNEL_ID_IDENTITE = 1423426602485678155

# --- Intents ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = False

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

@bot.event
async def on_member_join(member):
    """Envoie un embed de bienvenue à l'arrivée d'un nouveau membre."""
    welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)
    identite_channel = bot.get_channel(CHANNEL_ID_IDENTITE)

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
    embed.set_footer(text="Un nouveau citoyen vient d’arriver 🌆")

    # send only to text channels (safety for categories/forum/DMs)
    if isinstance(welcome_channel, discord.TextChannel):
        await welcome_channel.send(embed=embed)
    print(f"👋 Nouveau membre détecté : {member.name}")

bot.run(TOKEN)
