import datetime
import discord
from discord.ui import View, button
from bot.config import ROLE_AGENTS_ID
from bot.utils.missions_data import missions, save_missions
from bot.agents import agents_manager

class MissionValidationView(View):
    def __init__(self, nom: str, user_id: str, lieu: str, nb_agents: int, date: datetime.datetime):
        super().__init__(timeout=None)
        self.nom = nom
        self.user_id = user_id
        self.lieu = lieu
        self.nb_agents = nb_agents
        self.date = date

    @button(label="Oui, je serai présent", style=discord.ButtonStyle.primary)
    async def oui_agent(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if interaction.message is None:
            await interaction.followup.send("Erreur interne (message introuvable).", ephemeral=True)
            return
        mission_msg_id = interaction.message.id
        missions.setdefault(mission_msg_id, {})
        missions[mission_msg_id].setdefault("agents_confirmed", {})
        missions[mission_msg_id]["agents_confirmed"][interaction.user.id] = True
        save_missions()
        agents_manager.increment_missions(str(interaction.user.id))
        await interaction.followup.send("✅ Ta présence a été enregistrée.", ephemeral=True)

    @button(label="Non, je ne pourrai pas", style=discord.ButtonStyle.secondary)
    async def non_agent(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if interaction.message is None:
            await interaction.followup.send("Erreur interne (message introuvable).", ephemeral=True)
            return
        mission_msg_id = interaction.message.id
        missions.setdefault(mission_msg_id, {})
        missions[mission_msg_id].setdefault("agents_confirmed", {})
        missions[mission_msg_id]["agents_confirmed"][interaction.user.id] = False
        save_missions()
        agents_manager.increment_absence(str(interaction.user.id))
        await interaction.followup.send("❌ Ta non-présence a été enregistrée.", ephemeral=True)

    async def handle_mission(self, msg_id: int, bot: discord.Client):
        mission = missions.get(msg_id)
        if not mission:
            return

        reminder_time = mission.get("date") - datetime.timedelta(minutes=30) if mission.get("date") else None
        now = datetime.datetime.now()

        if reminder_time and now < reminder_time:
            await discord.utils.sleep_until(reminder_time)
            channel_raw = mission.get("channel")
            channel_id = None
            if channel_raw is None:
                channel_id = None
            elif isinstance(channel_raw, int):
                channel_id = channel_raw
            else:
                try:
                    channel_id = int(str(channel_raw))
                except (TypeError, ValueError):
                    channel_id = None
            channel = bot.get_channel(channel_id) if channel_id is not None else None
            if isinstance(channel, discord.TextChannel):
                role = channel.guild.get_role(ROLE_AGENTS_ID)
                mention = role.mention if role else ""
                present = [f"<@{uid}>" for uid, ok in mission.get("agents_confirmed", {}).items() if ok]
                msg_text = f"⏰ Rappel : Mission pour **{mission.get('nom','')}** dans **30 min** au {mission.get('lieu','')}. {mention}\n"
                if present:
                    msg_text += f"✅ Présents : {', '.join(present)}"
                await channel.send(msg_text)
            mission["reminder_sent"] = True
            save_missions()

        if mission.get("date") and now < mission["date"]:
            await discord.utils.sleep_until(mission["date"])

        nb_agents = mission.get("nb_agents", 0)
        tarif = nb_agents * 15000
        channel_raw = mission.get("channel")
        channel_id = None
        if channel_raw is None:
            channel_id = None
        elif isinstance(channel_raw, int):
            channel_id = channel_raw
        else:
            try:
                channel_id = int(str(channel_raw))
            except (TypeError, ValueError):
                channel_id = None
        channel = bot.get_channel(channel_id) if channel_id is not None else None
        if isinstance(channel, discord.TextChannel):
            await channel.send(
                f"✅ Mission terminée pour {mission.get('nom','')} ({mission.get('id')}).\nTarif dû : **{tarif:,} $**"
            )
        missions.pop(msg_id, None)
        save_missions()
