import discord
from discord.ext import commands
from discord.ui import View, button, Modal, TextInput
import datetime


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
        # Déferer la réponse immédiatement pour éviter le timeout si le traitement prend du temps
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        from ..utils.missions_data import missions
        from .mission_view import MissionValidationView

        try:
            nb_agents = int(self.nb_agents.value)
            if nb_agents <= 0:
                await interaction.followup.send("❌ Le nombre d'agents doit être positif.", ephemeral=True)
                return
        except ValueError:
            await interaction.followup.send("❌ Le nombre d'agents doit être un nombre valide.", ephemeral=True)
            return

        try:
            date_mission = datetime.datetime.strptime(self.date_heure.value.strip(), "%d/%m/%Y %H:%M")
        except ValueError:
            await interaction.followup.send(
                "❌ Format de date invalide. Utilise : JJ/MM/AAAA HH:MM (ex: 25/12/2024 14:30)",
                ephemeral=True
            )
            return

        if date_mission < datetime.datetime.now():
            await interaction.followup.send("❌ La date de mission doit être dans le futur.", ephemeral=True)
            return

        guild = interaction.guild
        if guild is None:
            await interaction.followup.send("❌ Erreur : serveur introuvable.", ephemeral=True)
            return

        from ..config import MISS_CHANNEL_ID
        mission_channel = guild.get_channel(MISS_CHANNEL_ID)
        if not isinstance(mission_channel, discord.TextChannel):
            await interaction.followup.send("❌ Salon de missions introuvable.", ephemeral=True)
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

        await interaction.followup.send(
            f"✅ Ta demande de mission a été envoyée dans {mission_channel.mention}.",
            ephemeral=True
        )


class AskMissView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Faire une demande d'agents", style=discord.ButtonStyle.primary, custom_id="askmiss_button")
    async def askmiss_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DemandeAgentsModal())


async def setup(bot: commands.Bot):
    """Envoie le message de demande d'agents dans le channel configuré.

    Utilise clean_and_send et effectue un fetch si nécessaire. Planifie l'envoi si le bot
    n'est pas encore prêt.
    """
    try:
        from .. import config
        from ..utils.auto_messages import clean_and_send
    except Exception as e:
        print(f"⚠️ Erreur d'import dans askmiss.setup : {e}")
        return

    ask_channel_id = getattr(config, "ASKMISS_CHANNEL_ID", None)
    if ask_channel_id is None:
        print("⚠️ ASKMISS_CHANNEL_ID n'est pas défini")
        return

    async def send_ask():
        channel = bot.get_channel(ask_channel_id)
        if channel is None:
            try:
                channel = await bot.fetch_channel(ask_channel_id)
            except Exception:
                channel = None
        if not channel or not isinstance(channel, discord.TextChannel):
            print(f"⚠️ Salon de demande d'agents introuvable : {ask_channel_id}")
            return

        embed = discord.Embed(
            title="📢 Demandes d'agents",
            description="Clique sur le bouton ci-dessous pour demander une sécurisation.",
            color=discord.Color.green(),
        )
        await clean_and_send(
            channel,
            embed=embed,
            view=AskMissView(),
            bot_filter="📢 Demandes d'agents"
        )

    try:
        bot.loop.create_task(send_ask())
    except Exception as e:
        print(f"⚠️ Erreur lors de l'initialisation du message de demande d'agents : {e}")
