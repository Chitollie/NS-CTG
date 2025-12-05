import json
import os
from typing import Dict, Any
import discord
from discord.ext import commands

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
                json.dump({"agents": self.agents, "embed_msg_id": self.embed_msg_id}, f, ensure_ascii=False, indent=2)
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

    def increment_absence(self, user_id: str):
        user_id = str(user_id)
        ag = self.ensure_agent(user_id)
        ag["absences"] = ag.get("absences", 0) + 1
        self.save()

    def increment_missions(self, user_id: str):
        user_id = str(user_id)
        ag = self.ensure_agent(user_id)
        ag["missions_done"] = ag.get("missions_done", 0) + 1
        self.save()

    def rank_up(self, user_id: str, new_rank: str):
        user_id = str(user_id)
        ag = self.ensure_agent(user_id)
        ag["rank"] = new_rank
        self.save()

    def rank_down(self, user_id: str, new_rank: str):
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
            absences = data.get("absences", 0)
            spec = data.get("specialty") or "-"
            permits = ", ".join(data.get("permits", [])) or "-"
            missions_done = data.get("missions_done", 0)
            emb.add_field(
                name=f"{name} ({uid})",
                value=f"**Rang:** {rank}\n**Absences:** {absences}\n**Spécialité:** {spec}\n**Permis:** {permits}\n**Missions:** {missions_done}",
                inline=False
            )
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

class AgentsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await agents_manager.restore_embed(self.bot)

    @commands.command()
    @commands.is_owner()
    async def agent_rank(self, ctx: commands.Context, user: discord.User, *, rank: str):
        """Change le rang d'un agent"""
        agents_manager.rank_up(str(user.id), rank)
        await ctx.send(f"✅ Rang de {user.mention} changé à {rank}")

    @commands.command()
    @commands.is_owner()
    async def agent_specialty(self, ctx: commands.Context, user: discord.User, *, specialty: str = None):
        """Change la spécialité d'un agent"""
        agents_manager.set_specialty(str(user.id), specialty)
        await ctx.send(f"✅ Spécialité de {user.mention} changée à {specialty or 'Aucune'}")

    @commands.command()
    @commands.is_owner()
    async def agent_permit(self, ctx: commands.Context, user: discord.User, action: str, *, permit: str):
        """Ajoute ou retire un permis"""
        if action.lower() == "add":
            agents_manager.add_permit(str(user.id), permit)
            await ctx.send(f"✅ Permis {permit} ajouté à {user.mention}")
        elif action.lower() == "remove":
            agents_manager.remove_permit(str(user.id), permit)
            await ctx.send(f"✅ Permis {permit} retiré à {user.mention}")
        else:
            await ctx.send("❌ Action invalide (add/remove)")

async def setup(bot: commands.Bot):
    await bot.add_cog(AgentsCog(bot))
    await agents_manager.restore_embed(bot)
