import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_LOGS_ID = int(os.getenv("CHANNEL_LOGS_ID"))
ROLE_AGENTS_ID = int(os.getenv("ROLE_AGENTS_ID"))

# --- BOT ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

missions = {}  # stocke les missions {message_id: {infos}}


class DemandeAgentsModal(discord.ui.Modal, title="Demande d'agents"):
    nom_prenom = discord.ui.TextInput(label="Nom / Prénom")
    user_id = discord.ui.TextInput(label="ID")
    lieu = discord.ui.TextInput(label="Lieu")
    nb_agents = discord.ui.TextInput(label="Nombre d'agents")
    date_heure = discord.ui.TextInput(label="Date & Heure (JJ/MM/AAAA - HHhMM)")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Conversion date
            date_obj = datetime.datetime.strptime(self.date_heure.value, "%d/%m/%Y - %Hh%M")
        except ValueError:
            await interaction.response.send_message(
                "⚠️ Format de date invalide. Utilise JJ/MM/AAAA - HHhMM", ephemeral=True
            )
            return

        embed = discord.Embed(title="📋 Nouvelle demande d'agents", color=discord.Color.blue())
        embed.add_field(name="Nom / Prénom", value=self.nom_prenom.value, inline=False)
        embed.add_field(name="ID", value=self.user_id.value, inline=False)
        embed.add_field(name="Lieu", value=self.lieu.value, inline=False)
        embed.add_field(name="Nombre d'agents", value=self.nb_agents.value, inline=False)
        embed.add_field(name="Date & Heure", value=self.date_heure.value, inline=False)

        await interaction.response.send_message("✅ Demande envoyée avec succès !", ephemeral=True)

        # Envoi dans le salon gestion avec boutons
        channel = interaction.client.get_channel(CHANNEL_LOGS_ID)
        if channel:
            view = MissionValidationView(
                nom=self.nom_prenom.value,
                user_id=self.user_id.value,
                lieu=self.lieu.value,
                nb_agents=int(self.nb_agents.value),
                date=date_obj,
            )
            msg = await channel.send(embed=embed, view=view)
            missions[msg.id] = {
                "nom": self.nom_prenom.value,
                "id": self.user_id.value,
                "lieu": self.lieu.value,
                "nb_agents": int(self.nb_agents.value),
                "date": date_obj,
                "channel": channel.id,
                "reminder_sent": False,
            }


class MissionValidationView(discord.ui.View):
    def __init__(self, nom, user_id, lieu, nb_agents, date):
        super().__init__(timeout=None)
        self.nom = nom
        self.user_id = user_id
        self.lieu = lieu
        self.nb_agents = nb_agents
        self.date = date

    @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.success)
    async def valider(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"Mission validée ✅. Elle prendra fin le {self.date.strftime('%d/%m/%Y à %H:%M')}",
            ephemeral=True,
        )

        # Lance la gestion asynchrone de la mission
        asyncio.create_task(self.handle_mission(interaction.message.id))

    @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
    async def refuser(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.edit(content="❌ Mission refusée.", view=None)
        await interaction.response.send_message("Mission refusée.", ephemeral=True)

    async def handle_mission(self, msg_id: int):
        mission = missions.get(msg_id)
        if not mission:
            return

        date_mission = mission["date"]
        reminder_time = date_mission - datetime.timedelta(minutes=30)

        # Envoi rappel 30 min avant
        now = datetime.datetime.now()
        if now < reminder_time:
            await discord.utils.sleep_until(reminder_time)
            channel = bot.get_channel(mission["channel"])
            if channel:
                role = channel.guild.get_role(ROLE_AGENTS_ID)
                if role:
                    await channel.send(
                        f"⏰ Rappel : La mission pour **{mission['nom']}** commence dans **30 minutes** au {mission['lieu']}. {role.mention}"
                    )
                else:
                    await channel.send(
                        f"⏰ Rappel : La mission pour **{mission['nom']}** commence dans **30 minutes** au {mission['lieu']}."
                    )
            mission["reminder_sent"] = True

        # Attente fin de mission
        now = datetime.datetime.now()
        if now < date_mission:
            await discord.utils.sleep_until(date_mission)

        # Calcul du prix
        nb_agents = mission["nb_agents"]
        heures = max(1, round((date_mission - now).total_seconds() / 3600))
        tarif = nb_agents * 15000 + heures * 10000

        channel = bot.get_channel(mission["channel"])
        if channel:
            await channel.send(
                f"✅ Mission terminée pour {mission['nom']} ({mission['id']}).\n"
                f"Tarif dû : **{tarif:,} $**"
            )

        del missions[msg_id]


class MenuSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Demande d'agents", description="Faire une demande de personnel"),
            discord.SelectOption(label="Infos sur nos services", description="Voir les services proposés"),
            discord.SelectOption(label="Contacter un consultant", description="Être mis en relation"),
        ]
        super().__init__(placeholder="Choisis une option...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Demande d'agents":
            await interaction.response.send_modal(DemandeAgentsModal())
        elif self.values[0] == "Infos sur nos services":
            await interaction.response.send_message(
                "ℹ️ Nos services incluent la sécurité événementielle, la protection rapprochée et plus.",
                ephemeral=True,
            )
        elif self.values[0] == "Contacter un consultant":
            await interaction.response.send_message(
                "👔 Un consultant va te recontacter bientôt.", ephemeral=True
            )


class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MenuSelect())


@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Commandes slash synchronisées : {len(synced)}")
    except Exception as e:
        print(e)


@bot.tree.command(guild=discord.Object(id=GUILD_ID), name="menu", description="Ouvrir le menu de la société de sécurité")
async def menu_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Bienvenue chez Nova Sécurité",
        description="Choisissez une option ci-dessous :",
        color=discord.Color.dark_blue(),
    )
    await interaction.response.send_message(embed=embed, view=MenuView(), ephemeral=True)


bot.run(TOKEN)
