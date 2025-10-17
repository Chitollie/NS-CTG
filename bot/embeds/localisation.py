import discord
from ..config import LOC_CHANNEL_ID

async def send_localisation_image(bot: discord.Client, image_url: str, alt_text: str = "Localisation"):
    channel = bot.get_channel(LOC_CHANNEL_ID)
    if channel is None or not isinstance(channel, discord.TextChannel):
        return

    embed = discord.Embed(title="📍 Localisation", description=alt_text, color=discord.Color.blue())
    if image_url:
        embed.set_image(url=image_url)
    await channel.send(embed=embed)
