import discord
from ..config import LOC_CHANNEL_ID

MESSAGE_IDENTIFIER = "📍 Localisation"

async def send_localisation_image(bot: discord.Client, image_url: str, alt_text: str = "Localisation"):
    try:
        from ..utils.auto_messages import clean_and_send
    except ImportError:
        print("⚠️ Impossible d'importer clean_and_send")
        return

    channel = bot.get_channel(LOC_CHANNEL_ID)
    if channel is None and LOC_CHANNEL_ID:
        try:
            channel = await bot.fetch_channel(LOC_CHANNEL_ID)
        except Exception:
            channel = None
    if channel is None or not isinstance(channel, discord.TextChannel):
        print(f"⚠️ Salon de localisation introuvable : {LOC_CHANNEL_ID}")
        return

    embed = discord.Embed(title=MESSAGE_IDENTIFIER, description=alt_text, color=discord.Color.blue())
    if image_url:
        embed.set_image(url=image_url)
    
    # Nettoie les anciens messages et envoie le nouveau
    await clean_and_send(channel, embed=embed, bot_filter=MESSAGE_IDENTIFIER)
