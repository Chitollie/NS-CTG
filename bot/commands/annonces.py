import discord
from discord import app_commands
from discord.ext import commands
from ..config import ANNOUNCEMENT_CHANNEL_ID


class AnnounceConfirmView(discord.ui.View):
    def __init__(self, content: str, author_id: int, everyone: bool = False):
        super().__init__(timeout=60)
        self.content = content
        self.author_id = author_id
        self.everyone = everyone
        self.value = None

    def _is_author_or_admin(self, interaction: discord.Interaction) -> bool:
        # Prefer Member permissions when available
        user = interaction.user
        if isinstance(user, discord.Member):
            return user.id == self.author_id or user.guild_permissions.administrator
        # fallback: allow only the original author id
        return user.id == self.author_id

    @discord.ui.button(label="Confirmer", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_author_or_admin(interaction):
            await interaction.response.send_message("Tu n'as pas la permission de confirmer cette annonce.", ephemeral=True)
            return
        guild = interaction.guild
        if guild is None:
            await interaction.response.edit_message(content="❌ Erreur : serveur introuvable.", view=None)
            return
        channel = guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        if channel and isinstance(channel, discord.TextChannel):
            if self.everyone:
                await channel.send(self.content, allowed_mentions=discord.AllowedMentions(everyone=True))
            else:
                await channel.send(self.content)
            await interaction.response.edit_message(content="✅ Annonce envoyée.", view=None)
        else:
            await interaction.response.edit_message(content="❌ Salon d'annonces introuvable.", view=None)
        self.value = True
        self.stop()

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_author_or_admin(interaction):
            await interaction.response.send_message("Tu n'as pas la permission d'annuler cette annonce.", ephemeral=True)
            return
        await interaction.response.edit_message(content="❌ Envoi annulé.", view=None)
        self.value = False
        self.stop()


@app_commands.command(name="annonces", description="Envoyer une annonce (administrateurs uniquement)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(message="Le message d'annonce à envoyer")
async def annonces_cmd(interaction: discord.Interaction, message: str, everyone: bool = False):
    # Show preview and confirm
    embed = discord.Embed(title="📣 Aperçu de l'annonce", description=message, color=discord.Color.blue())
    view = AnnounceConfirmView(content=message, author_id=interaction.user.id, everyone=everyone)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
