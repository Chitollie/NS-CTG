import json
import os
from typing import Dict, Any
import discord
from discord.ext import commands
from discord import app_commands, Interaction, User

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_PATH = os.path.normpath(os.path.join(DATA_DIR, "agents.json"))

class AgentsManager:
    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.embed_msg_id: int | None = None
        self._ensure_data_dir()
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
        self._ensure_data_dir()
        try:
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(
                    {"agents": self.agents, "embed_msg_id": self.embed_msg_id},
                    f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            print(f"Error saving agents file: {e}")

    def _ensure_data_dir(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)

    def ensure_agent(self, user_id: str, name: str = None):
        user_id = str(user_id)
        if user_id not in self.agents:
            self.agents[user_id] = self.get_default(user_id, name)
            self.save()
        return self.agents[user_id]

    def rank_up(self, user_id: str, new_rank: str):
        user_id = str(user_id)
        ag = self.ensure_agent(user_id)
        ag["rank"] = new_rank
        self.save()

    def set_specialty(self, user_id: str, specialty: str = None):
        user_id = str(user_id)
        ag = self.ensure_agent(user_id)
        ag["specialty"] = specialty
        self.save()

    def add_permit(self, user_id: str, permit: str):
        user_id = str(user_id)
        ag = self.ensure_agent(user_id)
        permits = ag.get("permits", [])
        if permit not in permits:
            permits.append(permit)
        ag["permits"] = permits
        self.save()

    def remove_permit(self, user_id: str, permit: str):
        user_id = str(user_id)
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
            missions_done = data.get("missions_done", 0)
            absences = data.get("absences", 0)
            emb.add_field(
                name=f"{name} ({uid})",
                value=f"**Rang:** {rank}\n**Missions:** {missions_done}\n**Absences:** {absences}",
                inline=False
            )
        return emb

    async def build_agent_profile(self, user_id: str):
        ag = self.ensure_agent(user_id)
        emb = discord.Embed(title=f"📋 Profil de {ag.get('name')}", color=discord.Color.blurple())
        emb.add_field(name="Rang", value=ag.get("rank", "Recrue"), inline=True)
        emb.add_field(name="Missions", value=ag.get("missions_done", 0), inline=True)
        emb.add_field(name="Absences", value=ag.get("absences", 0), inline=True)
        emb.add_field(name="Spécialité", value=ag.get("specialty") or "-", inline=False)
        emb.add_field(name="Permis", value=", ".join(ag.get("permits", [])) or "-", inline=False)
        return emb

    async def restore_embed(self, bot: commands.Bot):
        try:
            from bot.config import AGENTS_CHANNEL_ID
        except Exception:
            return
        if AGENTS_CHANNEL_ID == 0:
            return
        channel = bot.get_channel(AGENTS_CHANNEL_ID)
        if channel is None:
            try:
                channel = await bot.fetch_channel(AGENTS_CHANNEL_ID)
            except Exception:
                return
        if not isinstance(channel, discord.TextChannel):
            return
        emb = await self.build_embed()
        if self.embed_msg_id:
            try:
                msg = await channel.fetch_message(int(self.embed_msg_id))
                await msg.edit(embed=emb)
                return
            except Exception:
                pass
        try:
            m = await channel.send(embed=emb)
            self.embed_msg_id = m.id
            self.save()
        except Exception as e:
            print(f"Error sending agents embed: {e}")

agents_manager = AgentsManager()


# ----------------- COG -----------------
class AgentsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await agents_manager.restore_embed(self.bot)

    @app_commands.command(
        name="agent",
        description="Gérer un agent"
    )
    @app_commands.describe(
        user="Utilisateur à gérer",
        type="Type de gestion",
        action="Action (pour rank ou permits)",
        value="Valeur à appliquer (nouveau rang, specialty, permis)"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="rank", value="rank"),
        app_commands.Choice(name="specialty", value="specialty"),
        app_commands.Choice(name="permits", value="permits"),
        app_commands.Choice(name="profile", value="profile")
    ])
    async def agent(self, interaction: Interaction, user: User, type: app_commands.Choice[str], action: str = None, value: str = None):
        uid = str(user.id)

        if type.value == "profile":
            emb = await agents_manager.build_agent_profile(uid)
            await interaction.response.send_message(embed=emb)
            return

        if type.value == "rank":
            if action not in ["up", "down"]:
                return await interaction.response.send_message("❌ Action invalide (up/down).", ephemeral=True)
            new_rank = value or "Recrue"
            agents_manager.rank_up(uid, new_rank)
            await agents_manager.restore_embed(self.bot)
            await interaction.response.send_message(f"✅ Rang de {user.mention} → {new_rank}")

        elif type.value == "specialty":
            agents_manager.set_specialty(uid, value)
            await agents_manager.restore_embed(self.bot)
            await interaction.response.send_message(f"✅ Spécialité mise à jour : {value or 'Aucune'}")

        elif type.value == "permits":
            if action not in ["add", "remove"]:
                return await interaction.response.send_message("❌ Action invalide (add/remove).", ephemeral=True)
            if action == "add":
                agents_manager.add_permit(uid, value)
                msg = f"✅ Permis {value} ajouté"
            else:
                agents_manager.remove_permit(uid, value)
                msg = f"🚫 Permis {value} retiré"
            await agents_manager.restore_embed(self.bot)
            await interaction.response.send_message(f"{msg} à {user.mention}")


async def setup(bot: commands.Bot):
    cog = AgentsCog(bot)
    await bot.add_cog(cog)

    bot.tree.add_command(cog.agent)
    try:
        from bot.config import GUILD_ID
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
        else:
            await bot.tree.sync()
    except Exception as e:
        print(f"[Slash Sync Error] {e}")
