import discord
from discord.ext import commands
from discord.ui import View, button, Modal, TextInput
import datetime
from bot.utils.missions_data import missions, save_missions
from bot.views.mission_admin_view import MissionAdminView

class DemandeAgentsModal(Modal, title="Demande d'agents"):
    lieu = TextInput(label="Lieu de la mission")
    nb_agents = TextInput(label="Nombre d'agents nécessaires", placeholder="Ex : 3")
    date_debut = TextInput(
        label="Date de début (JJ/MM à HHhMM)", 
        placeholder="Ex : 05/11 à 14h30"
    )
    date_fin = TextInput(
        label="Date de fin (JJ/MM à HHhMM, JJ/MM optionnel)", 
        placeholder="Ex : 05/11 à 16h00"
    )
    notes = TextInput(
        label="Notes additionnelles (optionnel)", 
        required=False, 
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            nb_agents = int(self.nb_agents.value)
            if nb_agents <= 0:
                await interaction.response.send_message("❌ Le nombre d'agents doit être positif.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ Le nombre d'agents doit être un nombre valide.", ephemeral=True)
            return

        year = datetime.datetime.now().year
        try:
            jour, reste = self.date_debut.value.split("/", 1)
            mois, heure_min = reste.strip().split("à")
            heure, minute = heure_min.strip().split("h")
            date_debut = datetime.datetime(
                year, int(mois), int(jour), int(heure), int(minute)
            )
        except:
            await interaction.response.send_message("❌ La date de début est invalide.", ephemeral=True)
            return
        if date_debut < datetime.datetime.now():
            await interaction.response.send_message("❌ La date de début doit être dans le futur.", ephemeral=True)
            return

        try:
            parts = self.date_fin.value.split("/", 1)
            jour_fin = parts[0] if parts else ""
            reste = parts[1] if len(parts) > 1 else ""
            mois_fin = ""
            heure_min_fin = ""
            if reste:
                mois_fin, heure_min_fin = (reste.strip().split("à") + [""])[:2]
            if not jour_fin:
                jour_fin = str(date_debut.day)
            if not mois_fin:
                mois_fin = str(date_debut.month)
            heure_fin, minute_fin = (heure_min_fin.strip().split("h") + ["", ""])[:2]
            date_fin = datetime.datetime(
                year, int(mois_fin), int(jour_fin), int(heure_fin), int(minute_fin)
            )
        except:
            await interaction.response.send_message("❌ La date de fin est invalide.", ephemeral=True)
            return
        if date_fin <= date_debut:
            await interaction.response.send_message("❌ La date de fin doit être après la date de début.", ephemeral=True)
            return

        from bot.config import MISS_CHANNEL_ID, MISSADMIN_CHANNEL_ID

        guild = interaction.guild
        mission_channel = guild.get_channel(MISS_CHANNEL_ID)
        if not isinstance(mission_channel, discord.TextChannel):
            await interaction.response.send_message("❌ Salon de missions introuvable.", ephemeral=True)
            return

        mission_data = {
            "id": str(interaction.user.id),
            "nom": f"Mission - {self.lieu.value}",
            "lieu": self.lieu.value,
            "nb_agents": nb_agents,
            "date_debut": date_debut,
            "date_fin": date_fin,
            "date": date_debut,
            "channel": mission_channel.id,
            "agents_confirmed": {},
            "reminder_sent": False,
            "validated": False,
            "started": False,
        }

        embed = discord.Embed(
            title=f"📋 Nouvelle mission au : {self.lieu.value}",
            description=f"Demande par {interaction.user.mention}\n\n⏳ *En cours de validation par un haut gradé*",
            color=discord.Color.orange()
        )
        embed.add_field(name="Agents requis", value=str(nb_agents), inline=True)
        embed.add_field(name="Début", value=date_debut.strftime("%d/%m à %Hh%M"), inline=True)
        embed.add_field(name="Fin", value=date_fin.strftime("%d/%m à %Hh%M"), inline=True)
        if self.notes.value:
            embed.add_field(name="Notes", value=self.notes.value, inline=False)

        msg = await mission_channel.send(embed=embed)
        missions[msg.id] = mission_data
        save_missions()

        admin_channel = guild.get_channel(MISSADMIN_CHANNEL_ID)
        if isinstance(admin_channel, discord.TextChannel):
            admin_embed = discord.Embed(
                title="🔍 Nouvelle demande de mission à valider",
                description=f"Demandeur : {interaction.user.mention}",
                color=discord.Color.blue()
            )
            admin_embed.add_field(name="Mission", value=self.lieu.value, inline=False)
            admin_embed.add_field(name="Agents requis", value=str(nb_agents), inline=False)
            admin_embed.add_field(name="Début", value=date_debut.strftime("%d/%m à %Hh%M"), inline=True)
            admin_embed.add_field(name="Fin", value=date_fin.strftime("%d/%m à %Hh%M"), inline=True)
            if self.notes.value:
                admin_embed.add_field(name="Notes", value=self.notes.value, inline=False)

            await admin_channel.send(embed=admin_embed, view=MissionAdminView(mission_data, msg.id))

        await interaction.response.send_message("✅ Ta demande de mission a été envoyée", ephemeral=True)

class AskMissView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Faire une demande d'agents", style=discord.ButtonStyle.primary, custom_id="askmiss_button") 
    async def askmiss_button(self, interaction: discord.Interaction, button: discord.ui.Button): 
        await interaction.response.send_modal(DemandeAgentsModal())

async def setup(bot: commands.Bot):
    from bot.config import ASKMISS_CHANNEL_ID
    from bot.utils.auto_messages import clean_and_send

    ask_channel_id = ASKMISS_CHANNEL_ID

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
            description="Clique sur le bouton ci-dessous pour demander une mission.",
            color=discord.Color.green()
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
