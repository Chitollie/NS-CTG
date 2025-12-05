import discord
from discord.ui import View, button
from typing import Dict, Any
from bot.config import ROLE_AGENTS_ID, MISS_CHANNEL_ID, MISSADMIN_CHANNEL_ID
from bot.utils.missions_data import missions, save_missions
from bot.commands.agents import agents_manager

# ============ FEEDBACK SYSTEM ============
feedback_states = {}

class FeedbackState:
    def __init__(self, user_id: int, mission_data: Dict[str, Any], msg_id: int):
        self.user_id = user_id
        self.mission_data = mission_data
        self.msg_id = msg_id
        self.step = 0
        self.note = None
        self.comment = None

async def send_note_request(user: discord.User):
    embed = discord.Embed(
        title="⭐ Noter la mission",
        description="Veuillez envoyer une note entre 1 et 5 (1=très mauvais, 5=excellent).\nSi vous ne souhaitez pas donner de retour, répondez 'non'."
    )
    await user.send(embed=embed)
    if user.id in feedback_states:
        feedback_states[user.id].step = 1

async def send_comment_request(user: discord.User):
    embed = discord.Embed(
        title="💬 Commentaire sur la mission",
        description="Vous pouvez maintenant écrire un commentaire sur la mission.\nRépondez 'non' si vous ne souhaitez pas commenter."
    )
    await user.send(embed=embed)
    if user.id in feedback_states:
        feedback_states[user.id].step = 2

async def send_recap(user: discord.User):
    state = feedback_states.get(user.id)
    if not state:
        return
    stars = "".join(["⭐" if i < (state.note or 0) else "☆" for i in range(5)]) if state.note else ""
    embed = discord.Embed(
        title="📝 Récapitulatif de votre feedback",
        description=f"Note : {stars}\nCommentaire : {state.comment if state.comment else 'Aucun'}"
    )
    embed.set_footer(text="Répondez 'envoyer' pour transmettre votre feedback, ou 'modifier' pour le changer.")
    await user.send(embed=embed)
    state.step = 3

async def send_modify_choice(user: discord.User):
    embed = discord.Embed(
        title="✏️ Modifier votre feedback",
        description="Que souhaitez-vous modifier ? Répondez 'note' ou 'commentaire'."
    )
    await user.send(embed=embed)
    if user.id in feedback_states:
        feedback_states[user.id].step = 4

async def start_feedback_dm(user: discord.User, mission_data: Dict[str, Any], msg_id: int, bot: discord.Client):
    state = FeedbackState(user.id, mission_data, msg_id)
    feedback_states[user.id] = state
    intro_embed = discord.Embed(
        title="⭐ Nous aimerions votre avis !",
        description="Merci d'avoir fait appel à nous. Nous serions ravis d'avoir votre retour sur la mission."
    )
    await user.send(embed=intro_embed)
    await send_note_request(user)

# ============ MISSION VIEWS ============

class MissionAdminView(View):
    def __init__(self, mission_data: Dict[str, Any], msg_id: int):
        super().__init__(timeout=None)
        self.mission_data = mission_data
        self.msg_id = msg_id

    @button(label="✅ Accepter", style=discord.ButtonStyle.success)
    async def accept_mission(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        admin_channel = interaction.guild.get_channel(MISSADMIN_CHANNEL_ID) if interaction.guild else None
        if not isinstance(admin_channel, discord.TextChannel):
            await interaction.followup.send("Canal admin introuvable.", ephemeral=True)
            return

        track_embed = discord.Embed(title=f"Suivi - {self.mission_data.get('nom','')}", color=discord.Color.blue())
        track_embed.add_field(name="Client", value=self.mission_data.get("id", "N/A"), inline=False)
        track_embed.add_field(name="Lieu", value=self.mission_data.get("lieu", "N/A"), inline=False)
        track_view = MissionTrackingView(self.mission_data, self.msg_id)
        admin_msg = await admin_channel.send(embed=track_embed, view=track_view)

        missions.setdefault(self.msg_id, self.mission_data)
        missions[self.msg_id]["admin_msg_id"] = admin_msg.id
        missions[self.msg_id]["admin_channel"] = admin_channel.id
        missions[self.msg_id]["validated"] = True
        save_missions()

        # Edit mission message: remove validation text and attach participation view
        mission_ch_id = self.mission_data.get("channel")
        try:
            if mission_ch_id:
                ch = interaction.client.get_channel(int(mission_ch_id))
                if isinstance(ch, discord.TextChannel):
                    mission_msg = await ch.fetch_message(self.msg_id)
                    if mission_msg and mission_msg.embeds:
                        embed = mission_msg.embeds[0]
                        if embed.description:
                            embed.description = embed.description.replace("⏳ En cours de validation par un haut gradé", "").strip()
                        embed.color = discord.Color.green()
                        embed.set_footer(text="✅ Mission validée")
                        await mission_msg.edit(embed=embed, view=MissionParticipationView(self.mission_data, self.msg_id))
        except Exception:
            pass

        await interaction.followup.send("Mission acceptée et message admin créé.", ephemeral=True)

    @button(label="❌ Refuser", style=discord.ButtonStyle.danger)
    async def refuse_mission(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if self.msg_id in missions:
            missions.pop(self.msg_id, None)
            save_missions()
        await interaction.followup.send("Mission refusée et supprimée.", ephemeral=True)

class MissionParticipationView(View):
    def __init__(self, mission_data: Dict[str, Any], msg_id: int):
        super().__init__(timeout=None)
        self.mission_data = mission_data
        self.msg_id = msg_id

    @button(label="✅ Je serai présent", style=discord.ButtonStyle.success)
    async def confirm_presence(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        mission_msg_id = interaction.message.id
        missions.setdefault(mission_msg_id, self.mission_data)
        missions[mission_msg_id].setdefault("agents_confirmed", {})
        missions[mission_msg_id]["agents_confirmed"][interaction.user.id] = True
        save_missions()
        agents_manager.increment_missions(str(interaction.user.id))
        await interaction.followup.send("✅ Votre présence a été enregistrée!", ephemeral=True)
        await self.update_admin_tracking(interaction)

    @button(label="❌ Je ne pourrai pas", style=discord.ButtonStyle.danger)
    async def decline_presence(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        mission_msg_id = interaction.message.id
        missions.setdefault(mission_msg_id, self.mission_data)
        missions[mission_msg_id].setdefault("agents_confirmed", {})
        missions[mission_msg_id]["agents_confirmed"][interaction.user.id] = False
        save_missions()
        agents_manager.increment_absence(str(interaction.user.id))
        await interaction.followup.send("❌ Votre absence a été enregistrée.", ephemeral=True)
        await self.update_admin_tracking(interaction)

    async def update_admin_tracking(self, interaction: discord.Interaction):
        data = missions.get(self.msg_id)
        if not data:
            return
        admin_channel_id = data.get("admin_channel") or MISSADMIN_CHANNEL_ID
        admin_ch = interaction.client.get_channel(admin_channel_id)
        if not isinstance(admin_ch, discord.TextChannel):
            return
        admin_msg_id = data.get("admin_msg_id")
        if not admin_msg_id:
            return
        try:
            admin_msg = await admin_ch.fetch_message(int(admin_msg_id))
            present = [f"<@{uid}>" for uid, ok in data.get("agents_confirmed", {}).items() if ok]
            absent = [f"<@{uid}>" for uid, ok in data.get("agents_confirmed", {}).items() if not ok]
            embed = discord.Embed(title=f"Suivi - {data.get('nom','')}", color=discord.Color.orange())
            embed.add_field(name="Présents", value=", ".join(present) if present else "Aucun", inline=False)
            embed.add_field(name="Absents", value=", ".join(absent) if absent else "Aucun", inline=False)
            await admin_msg.edit(embed=embed)
        except Exception:
            pass

class MissionTrackingView(View):
    def __init__(self, mission_data: Dict[str, Any], msg_id: int):
        super().__init__(timeout=None)
        self.mission_data = mission_data
        self.msg_id = msg_id

    @button(label="🚀 Débuter la mission", style=discord.ButtonStyle.primary)
    async def start_mission(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if self.msg_id in missions:
            missions[self.msg_id]["started"] = True
            save_missions()
        try:
            admin_ch_id = missions[self.msg_id].get("admin_channel") or MISSADMIN_CHANNEL_ID
            admin_ch = interaction.client.get_channel(admin_ch_id)
            if isinstance(admin_ch, discord.TextChannel):
                admin_msg = await admin_ch.fetch_message(int(missions[self.msg_id]["admin_msg_id"]))
                embed = discord.Embed(title=f"Suivi - {self.mission_data.get('nom','')}", color=discord.Color.gold())
                embed.add_field(name="Status", value="En cours", inline=False)
                await admin_msg.edit(embed=embed)
        except Exception:
            pass
        await interaction.followup.send("Mission démarrée.", ephemeral=True)

class MissionEndingView(View):
    def __init__(self, mission_data: Dict[str, Any], msg_id: int, present_agents: list):
        super().__init__(timeout=None)
        self.mission_data = mission_data
        self.msg_id = msg_id
        self.present_agents = present_agents

    @button(label="🏁 Terminer la mission", style=discord.ButtonStyle.danger)
    async def end_mission(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        missions.pop(self.msg_id, None)
        save_missions()
        await interaction.followup.send("Mission terminée et supprimée.", ephemeral=True)

