import discord
from discord import app_commands
from discord.ext import commands


class AnnounceConfirmView(discord.ui.View):
    def __init__(self, content: str, author_id: int, channel: discord.TextChannel, everyone: bool = False):
        super().__init__(timeout=60)
        self.content = content
        self.author_id = author_id
        self.channel = channel
        self.everyone = everyone
        self.value = None

    def _is_author_or_admin(self, interaction: discord.Interaction) -> bool:
        user = interaction.user
        if isinstance(user, discord.Member):
            return user.id == self.author_id or user.guild_permissions.administrator
        return user.id == self.author_id

    @discord.ui.button(label="Confirmer", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not self._is_author_or_admin(interaction):
            await interaction.followup.send("Tu n'as pas la permission de confirmer cette annonce.", ephemeral=True)
            return

        if self.channel and isinstance(self.channel, discord.TextChannel):
            if self.everyone:
                await self.channel.send(self.content, allowed_mentions=discord.AllowedMentions(everyone=True))
            else:
                await self.channel.send(self.content)
            await interaction.followup.send(f"✅ Annonce envoyée dans {self.channel.mention}.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Salon d'annonces introuvable.", ephemeral=True)

        self.value = True
        self.stop()

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not self._is_author_or_admin(interaction):
            await interaction.followup.send("Tu n'as pas la permission d'annuler cette annonce.", ephemeral=True)
            return

        await interaction.followup.send("❌ Envoi annulé.", ephemeral=True)
        self.value = False
        self.stop()


class AnnoncesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="annonces", description="Envoyer une annonce dans un salon choisi (administrateurs uniquement)")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        message="Le message d'annonce à envoyer",
        channel="Le salon où envoyer l'annonce",
        everyone="Mentionner @everyone dans l'annonce"
    )
    async def annonces_cmd(self, interaction: discord.Interaction, message: str, channel: discord.TextChannel, everyone: bool = False):
        message = message.replace("\\n", "\n")
        embed = discord.Embed(
            title="📣 Aperçu de l'annonce",
            description=message,
            color=discord.Color.blue()
        )
        embed.add_field(name="Salon cible", value=channel.mention)
        if everyone:
            embed.add_field(name="Mention", value="@everyone")

        view = AnnounceConfirmView(content=message, author_id=interaction.user.id, channel=channel, everyone=everyone)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AnnoncesCog(bot))
