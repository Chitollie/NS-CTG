import discord
from discord.ext import commands
from discord.ui import View, button, Modal, TextInput
from ..config import ROLE_IDENTIFIE_ID, VERIFROLE_CHANNEL_ID
from .verif_view import VerificationRoleView
import datetime


class IdentificationModal(Modal, title="Identification"):
    nom_prenom = TextInput(label="Prénom / Nom", placeholder="Ex : Jean Dupont")
    user_id = TextInput(label="ID", placeholder="Ex : 59669")
    grade_specifique = TextInput(
        label="Grade spécifique (optionnel)",
        placeholder="Ex : LSPD / SAMS",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Déferer la réponse immédiatement pour éviter le timeout de 3s si le traitement prend du temps
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            # Si defer échoue (très rare), on continue quand même
            pass

        guild = interaction.guild
        if guild is None:
            await interaction.followup.send(
                "Impossible de changer ton pseudo ici.", ephemeral=True)
            return

        new_nick = f"{self.nom_prenom.value} | {self.user_id.value}"

        # Récupère le grade demandé
        grade = (self.grade_specifique.value or "").strip().lower()

        if grade in ["lspd", "sams"]:
            # On envoie la demande dans le salon de vérif
            verif_channel = guild.get_channel(VERIFROLE_CHANNEL_ID)
            if not isinstance(verif_channel, discord.TextChannel):
                await interaction.followup.send(
                    "⚠️ Salon de vérification introuvable.", ephemeral=True)
                return

            embed = discord.Embed(
                title="📋 Nouvelle demande de rôle spécifique",
                color=discord.Color.orange())
            embed.add_field(name="Nom / Prénom",
                            value=self.nom_prenom.value,
                            inline=False)
            embed.add_field(name="ID", value=self.user_id.value, inline=False)
            embed.add_field(name="Grade demandé",
                            value=grade.upper(),
                            inline=False)
            embed.add_field(name="Utilisateur",
                            value=f"{interaction.user.mention}",
                            inline=False)

            view = VerificationRoleView(user_id=interaction.user.id,
                                        grade=grade,
                                        nick=new_nick)

            await verif_channel.send(embed=embed, view=view)
            await interaction.followup.send(
                "📨 Ta demande de rôle spécifique a été envoyée pour vérification.",
                ephemeral=True)

        else:
            # Cas standard → changement de pseudo + ajout du rôle citoyen
            try:
                if isinstance(interaction.user, discord.Member):
                    await interaction.user.edit(nick=new_nick)
                    base_role = guild.get_role(ROLE_IDENTIFIE_ID)
                    if base_role:
                        await interaction.user.add_roles(base_role)
                await interaction.followup.send(
                    f"✅ Ton pseudo a été changé en **{new_nick}** et le rôle citoyen t’a été attribué.",
                    ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send(
                    "❌ Je n'ai pas la permission de changer ton pseudo ou d'ajouter le rôle.",
                    ephemeral=True)
            except discord.HTTPException:
                await interaction.followup.send(
                    "❌ Une erreur est survenue.", ephemeral=True)


class IdentificationButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="S'identifier", style=discord.ButtonStyle.primary, custom_id="ident_button")
    async def ident_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(IdentificationModal())


async def setup(bot: commands.Bot):
    """Envoie le message d'identification dans le channel configuré en utilisant clean_and_send.

    Ce setup fait un fetch si nécessaire et planifie l'envoi si le bot n'est pas encore prêt.
    """
    try:
        from .. import config
        from ..utils.auto_messages import clean_and_send
    except Exception as e:
        print(f"⚠️ Erreur d'import dans identification.setup : {e}")
        return

    ident_channel_id = getattr(config, "IDENT_CHANNEL_ID", None)
    if ident_channel_id is None:
        print("⚠️ IDENT_CHANNEL_ID n'est pas défini")
        return

    async def send_ident():
        channel = bot.get_channel(ident_channel_id)
        if channel is None:
            try:
                channel = await bot.fetch_channel(ident_channel_id)
            except Exception:
                channel = None
        if not channel or not isinstance(channel, discord.TextChannel):
            print(f"⚠️ Salon d'identification introuvable : {ident_channel_id}")
            return

        await clean_and_send(
            channel,
            content="Clique sur le bouton pour t'identifier :",
            view=IdentificationButtonView(),
            bot_filter="Clique sur le bouton pour t'identifier"
        )

    # Planifier l'envoi via la boucle (sûr depuis setup_hook)
    try:
        bot.loop.create_task(send_ident())
    except Exception as e:
        print(f"⚠️ Erreur lors de l'initialisation du message d'identification : {e}")
