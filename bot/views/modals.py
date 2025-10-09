import discord
from discord.ui import Modal, TextInput
from ..config import ROLE_IDENTIFIE_ID, ROLE_LSPD_ID, ROLE_SAMS_ID, VERIFROLE_CHANNEL_ID
from .verif_view import VerificationRoleView

class IdentificationModal(Modal, title="Identification"):
    nom_prenom = TextInput(label="Nom / Prénom")
    user_id = TextInput(label="ID")
    grade_specifique = TextInput(
        label="Grade spécifique (optionnel)",
        placeholder="Ex : LSPD / SAMS",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Impossible de changer ton pseudo ici.", ephemeral=True)
            return

        new_nick = f"{self.nom_prenom.value} | {self.user_id.value}"

        # Récupère le grade demandé
        grade = (self.grade_specifique.value or "").strip().lower()

        if grade in ["lspd", "sams"]:
            # On envoie la demande dans le salon de vérif
            verif_channel = guild.get_channel(VERIFROLE_CHANNEL_ID)
            if not isinstance(verif_channel, discord.TextChannel):
                await interaction.response.send_message("⚠️ Salon de vérification introuvable.", ephemeral=True)
                return

            embed = discord.Embed(
                title="📋 Nouvelle demande de rôle spécifique",
                color=discord.Color.orange()
            )
            embed.add_field(name="Nom / Prénom", value=self.nom_prenom.value, inline=False)
            embed.add_field(name="ID", value=self.user_id.value, inline=False)
            embed.add_field(name="Grade demandé", value=grade.upper(), inline=False)
            embed.add_field(name="Utilisateur", value=f"{interaction.user.mention}", inline=False)

            view = VerificationRoleView(
                user_id=interaction.user.id,
                grade=grade,
                nick=new_nick
            )

            await verif_channel.send(embed=embed, view=view)
            await interaction.response.send_message(
                "📨 Ta demande de rôle spécifique a été envoyée pour vérification.", ephemeral=True
            )

        else:
            # Cas standard → changement de pseudo + ajout du rôle citoyen
            try:
                if isinstance(interaction.user, discord.Member):
                    await interaction.user.edit(nick=new_nick)
                    base_role = guild.get_role(ROLE_IDENTIFIE_ID)
                    if base_role:
                        await interaction.user.add_roles(base_role)

                await interaction.response.send_message(
                    f"✅ Ton pseudo a été changé en **{new_nick}** et le rôle citoyen t’a été attribué.",
                    ephemeral=True
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ Je n'ai pas la permission de changer ton pseudo ou d'ajouter le rôle.",
                    ephemeral=True
                )
            except discord.HTTPException:
                await interaction.response.send_message("❌ Une erreur est survenue.", ephemeral=True)
