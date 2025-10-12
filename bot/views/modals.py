import discord
from discord.ui import Modal, TextInput
from ..config import ROLE_IDENTIFIE_ID, ROLE_LSPD_ID, ROLE_SAMS_ID, VERIFROLE_CHANNEL_ID, MISS_CHANNEL_ID
from .verif_view import VerificationRoleView
import datetime


class IdentificationModal(Modal, title="Identification"):
    nom_prenom = TextInput(label="Nom / Prénom", placeholder="Ex : Jean Dupont")
    user_id = TextInput(label="ID", placeholder="Ex : 59669")
    grade_specifique = TextInput(
        label="Grade spécifique (optionnel)",
        placeholder="Ex : LSPD / SAMS",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "Impossible de changer ton pseudo ici.", ephemeral=True)
            return

        new_nick = f"{self.nom_prenom.value} | {self.user_id.value}"

        # Récupère le grade demandé
        grade = (self.grade_specifique.value or "").strip().lower()

        if grade in ["lspd", "sams"]:
            # On envoie la demande dans le salon de vérif
            verif_channel = guild.get_channel(VERIFROLE_CHANNEL_ID)
            if not isinstance(verif_channel, discord.TextChannel):
                await interaction.response.send_message(
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
            await interaction.response.send_message(
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

                await interaction.response.send_message(
                    f"✅ Ton pseudo a été changé en **{new_nick}** et le rôle citoyen t’a été attribué.",
                    ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ Je n'ai pas la permission de changer ton pseudo ou d'ajouter le rôle.",
                    ephemeral=True)
            except discord.HTTPException:
                await interaction.response.send_message(
                    "❌ Une erreur est survenue.", ephemeral=True)

class DemandeAgentsModal(Modal, title="Demande d'agents"):
    nom_mission = TextInput(label="Nom de la mission")
    lieu = TextInput(label="Lieu de la mission")
    nb_agents = TextInput(label="Nombre d'agents nécessaires", placeholder="Ex : 3")
    date_heure = TextInput(
        label="Date et heure de la mission",
        placeholder="Format : JJ/MM/AAAA HH:MM",
        style=discord.TextStyle.short
    )
    notes = TextInput(
        label="Notes additionnelles (optionnel)",
        required=False,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        from ..utils.missions_data import missions
        from .mission_view import MissionValidationView

        try:
            nb_agents = int(self.nb_agents.value)
            if nb_agents <= 0:
                await interaction.response.send_message("❌ Le nombre d'agents doit être positif.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ Le nombre d'agents doit être un nombre valide.", ephemeral=True)
            return

        try:
            date_mission = datetime.datetime.strptime(self.date_heure.value.strip(), "%d/%m/%Y %H:%M")
        except ValueError:
            await interaction.response.send_message(
                "❌ Format de date invalide. Utilise : JJ/MM/AAAA HH:MM (ex: 25/12/2024 14:30)",
                ephemeral=True
            )
            return

        if date_mission < datetime.datetime.now():
            await interaction.response.send_message("❌ La date de mission doit être dans le futur.", ephemeral=True)
            return

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("❌ Erreur : serveur introuvable.", ephemeral=True)
            return

        mission_channel = guild.get_channel(MISS_CHANNEL_ID)
        if not isinstance(mission_channel, discord.TextChannel):
            await interaction.response.send_message("❌ Salon de missions introuvable.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📋 Nouvelle mission : {self.nom_mission.value}",
            description=f"Demande par {interaction.user.mention}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Lieu", value=self.lieu.value, inline=False)
        embed.add_field(name="Agents requis", value=str(nb_agents), inline=True)
        embed.add_field(name="Date et heure", value=self.date_heure.value, inline=True)
        if self.notes.value:
            embed.add_field(name="Notes", value=self.notes.value, inline=False)

        view = MissionValidationView(
            nom=self.nom_mission.value,
            user_id=str(interaction.user.id),
            lieu=self.lieu.value,
            nb_agents=nb_agents,
            date=date_mission
        )

        msg = await mission_channel.send(embed=embed, view=view)

        missions[msg.id] = {
            "nom": self.nom_mission.value,
            "id": str(interaction.user.id),
            "lieu": self.lieu.value,
            "nb_agents": nb_agents,
            "date": date_mission,
            "channel": mission_channel.id,
            "agents_confirmed": {},
            "reminder_sent": False
        }

        await interaction.response.send_message(
            f"✅ Ta demande de mission a été envoyée dans {mission_channel.mention}.",
            ephemeral=True
        )
