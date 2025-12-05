import json
import os
from typing import Dict, Any
import discord
from discord import app_commands
from discord.ext import commands

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_PATH = os.path.normpath(os.path.join(DATA_DIR, "agents.json"))

grades = [
    "Recrue",   # 0
    "Agent",    # 1
    "Agent supérieur", # 2
    "Responsable",  # 3
    "Chef d'unité", # 4
    "Manager",  # 5
]

ANNONCES_CHANNEL_ID = 1424408550918066266

class AgentsManager:
    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.embed_msg_id: int | None = None
        _ensure_data_dir()
        self.load()

    def get_default(self, user_id: str, name: str = None):
        return {
            "id": user_id,
            "name": name or f"<@{user_id}>",
            "rank": "Recrue",
            "absences": 0,
            "specialty": None,
            "permits": [],
            "missions_done": 0,
        }

    def load(self):
        if not os.path.exists(DATA_PATH):
            self.agents = {}
            return
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.agents = raw.get("agents", {})
            self.embed_msg_id = raw.get("embed_msg_id")
        except Exception:
            self.agents = {}
            self.embed_msg_id = None

    def save(self):
        _ensure_data_dir()
        try:
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump({"agents": self.agents, "embed_msg_id": self.embed_msg_id}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving agents file: {e}")

    def ensure_agent(self, user_id: str, name: str = None):
        if user_id not in self.agents:
            self.agents[user_id] = self.get_default(user_id, name)
            self.save()
        return self.agents[user_id]

    def increment_absence(self, user_id: str):
        ag = self.ensure_agent(user_id)
        ag["absences"] = ag.get("absences", 0) + 1
        self.save()

    def increment_missions(self, user_id: str):
        ag = self.ensure_agent(user_id)
        ag["missions_done"] = ag.get("missions_done", 0) + 1
        self.save()

    def rank_up(self, user_id: str, new_rank: str):
        ag = self.ensure_agent(user_id)
        ag["rank"] = new_rank
        self.save()

    def set_specialty(self, user_id: str, specialty: str | None):
        ag = self.ensure_agent(user_id)
        ag["specialty"] = specialty
        self.save()

    def add_permit(self, user_id: str, permit: str):
        ag = self.ensure_agent(user_id)
        permits = ag.get("permits", [])
        if permit not in permits:
            permits.append(permit)
        ag["permits"] = permits
        self.save()

    def remove_permit(self, user_id: str, permit: str):
        ag = self.ensure_agent(user_id)
        permits = ag.get("permits", [])
        if permit in permits:
            permits.remove(permit)
        ag["permits"] = permits
        self.save()

    async def build_embed(self):
        emb = discord.Embed(title="📋 Liste des agents", color=discord.Color.blurple())
        if not self.agents:
            emb.description = "Aucun agent enregistré"
            return emb
        for uid, data in sorted(self.agents.items(), key=lambda kv: kv[1].get("rank", "")):
            name = data.get("name", f"<@{uid}>")
            rank = data.get("rank", "N/A")
            absences = data.get("absences", 0)
            spec = data.get("specialty") or "-"
            permits = ", ".join(data.get("permits", [])) or "-"
            missions_done = data.get("missions_done", 0)
            emb.add_field(
                name=f"{name} ({uid})",
                value=f"Rank: {rank}\nAbsences: {absences}\nSpec: {spec}\nPermits: {permits}\nMissions: {missions_done}",
                inline=False
            )
        return emb

    async def restore_embed(self, bot: commands.Bot):
        try:
            from bot.config import AGENTS_CHANNEL_ID
        except Exception:
            return
        channel = bot.get_channel(AGENTS_CHANNEL_ID)
        if channel is None:
            try:
                channel = await bot.fetch_channel(AGENTS_CHANNEL_ID)
            except Exception:
                return
        emb = await self.build_embed()
        if self.embed_msg_id:
            try:
                msg = await channel.fetch_message(int(self.embed_msg_id))
                await msg.edit(embed=emb)
                return
            except Exception:
                pass
        m = await channel.send(embed=emb)
        self.embed_msg_id = m.id
        self.save()

def _ensure_data_dir():
    folder = os.path.dirname(DATA_PATH)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

agents_manager = AgentsManager()

class AgentsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await agents_manager.restore_embed(self.bot)

    @app_commands.command(name="agents", description="Gestionnaire des agents.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        agent="L'agent à gérer",
        type="Type d'action (ex : Rank)",
        action="Action si type = Rank : up ou down"
    )
    async def agents_cmd(self, interaction: discord.Interaction, agent: discord.Member, type: str, action: str = None):
        await interaction.response.defer(ephemeral=True)

        type = type.lower()
        if type not in ["up", "down"]:
            return await interaction.followup.send("Type invalide. Utilise `up` ou `down`.")

        guild_roles = {role.name: role for role in interaction.guild.roles}

        current_index = None
        for i, grade in enumerate(grades):
            if grade in guild_roles and guild_roles[grade] in agent.roles:
                current_index = i
                break

        annonces_channel = interaction.guild.get_channel(ANNONCES_CHANNEL_ID)
        if annonces_channel is None:
            return await interaction.followup.send("Channel d'annonces introuvable !")

        if type == "rank":
            if action is None:
                return await interaction.followup.send("Précise une action : `up` ou `down`.")
            action = action.lower()
            if action not in ["up", "down"]:
                return await interaction.followup.send("Action invalide. Utilise `up` ou `down`.")
            type = action

        # --- UP ---
        if type == "up":
            if current_index is None:
                new_grade = grades[0]
                await agent.add_roles(guild_roles[new_grade])
                await annonces_channel.send(f"📈 **{agent.mention} est maintenant {new_grade} !** 👏")
                return await interaction.followup.send(f"Grade ajouté : {new_grade}")

            if current_index == len(grades) - 1:
                return await interaction.followup.send("Impossible de UP, il est déjà au grade maximal.")

            old_role = guild_roles[grades[current_index]]
            new_role = guild_roles[grades[current_index + 1]]

            await agent.remove_roles(old_role)
            await agent.add_roles(new_role)

            await annonces_channel.send(f"📈 **{agent.mention} est passé de {old_role.name} à {new_role.name} !** 🚀")
            return await interaction.followup.send(f"UP effectué : {old_role.name} → {new_role.name}")

        # --- DOWN ---
        if type == "down":
            if current_index is None:
                return await interaction.followup.send("Cet agent n'a aucun grade.")

            if current_index == 0:
                old_role = guild_roles[grades[0]]
                await agent.remove_roles(old_role)

                await annonces_channel.send(f"📉 **{agent.mention} a été retiré de Recrue. Il ne fait plus partie des agents.**")
                try:
                    await agent.send("❌ Vous avez été **licencié** et retiré de l'équipe des agents.")
                except:
                    pass

                return await interaction.followup.send("Recrue retirée et agent licencié.")

            old_role = guild_roles[grades[current_index]]
            new_role = guild_roles[grades[current_index - 1]]

            await agent.remove_roles(old_role)
            await agent.add_roles(new_role)

            await annonces_channel.send(f"📉 **{agent.mention} est descendu de {old_role.name} à {new_role.name}.**")
            return await interaction.followup.send(f"DOWN effectué : {old_role.name} → {new_role.name}")

async def setup(bot: commands.Bot):
    await bot.add_cog(AgentsCog(bot))
    # restore embed once at setup
    await agents_manager.restore_embed(bot)
