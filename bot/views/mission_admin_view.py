import discord
from discord.ui import View, button, Modal, TextInput
import random
import os
import asyncio
from typing import Optional, Dict, Any
from ..config import ROLE_AGENTS_ID, MISS_CHANNEL_ID, MISSADMIN_CHANNEL_ID
from ..utils.missions_data import missions

class MissionAdminView(View):
    def __init__(self, mission_data: Dict[str, Any], msg_id: int):
        super().__init__(timeout=None)
        self.mission_data = mission_data
        self.msg_id = msg_id
        self.client_id = int(mission_data["id"])

    @button(label="✅ Accepter", style=discord.ButtonStyle.success)
    async def accept_mission(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        guild = interaction.guild
        if not guild:
            await interaction.followup.send("❌ Erreur : serveur introuvable", ephemeral=True)
            return
        
        mission_channel = guild.get_channel(MISS_CHANNEL_ID)
        if not isinstance(mission_channel, discord.TextChannel):
            await interaction.followup.send("❌ Erreur : salon des missions introuvable", ephemeral=True)
            return

        track_embed = discord.Embed(
            title=f"📋 Suivi mission : {self.mission_data['nom']}",
            description=f"**Lieu :** {self.mission_data['lieu']}\n**Agents requis :** {self.mission_data['nb_agents']}",
            color=discord.Color.blue()
        )
        track_embed.add_field(name="Présence des agents", value="*Aucun agent inscrit*", inline=False)
        track_view = MissionTrackingView(self.mission_data, self.msg_id)
        
        admin_msg = await interaction.message.edit(
            embed=track_embed,
            view=track_view
        )

        missions[self.msg_id]["admin_msg_id"] = admin_msg.id
        try:
            mission_msg = await mission_channel.fetch_message(self.msg_id)
            if mission_msg:
                embed = mission_msg.embeds[0]
                embed.color = discord.Color.green()
                embed.set_footer(text="✅ Mission validée")
                await mission_msg.edit(
                    embed=embed, 
                    view=MissionParticipationView(self.mission_data, self.msg_id)
                )
        except Exception:
            pass

        try:
            client = await interaction.client.fetch_user(self.client_id)
            if client:
                await client.send(f"✅ Votre demande de mission **{self.mission_data['nom']}** a été acceptée!")
        except:
            pass

    @button(label="❌ Refuser", style=discord.ButtonStyle.danger)
    async def refuse_mission(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        guild = interaction.guild
        if not guild:
            return
            
        mission_channel = guild.get_channel(MISS_CHANNEL_ID)
        if isinstance(mission_channel, discord.TextChannel):
            try:
                mission_msg = await mission_channel.fetch_message(self.msg_id)
                await mission_msg.delete()
            except:
                pass

        embed = discord.Embed(
            title=f"📋 Mission refusée : {self.mission_data['nom']}",
            description=f"Refusée par {interaction.user.mention}",
            color=discord.Color.red()
        )
        await interaction.message.edit(embed=embed, view=None)

        try:
            client = await interaction.client.fetch_user(self.client_id)
            if client:
                await client.send(f"❌ Votre demande de mission **{self.mission_data['nom']}** a été refusée.")
        except:
            pass

        missions.pop(self.msg_id, None)

class MissionParticipationView(View):
    def __init__(self, mission_data: Dict[str, Any], msg_id: int):
        super().__init__(timeout=None)
        self.mission_data = mission_data
        self.msg_id = msg_id

    @button(label="✅ Je serai présent", style=discord.ButtonStyle.success)
    async def confirm_presence(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        if self.msg_id not in missions:
            await interaction.followup.send("❌ Cette mission n'est plus disponible.", ephemeral=True)
            return
            
        missions[self.msg_id]["agents_confirmed"][interaction.user.id] = True
        await interaction.followup.send("✅ Votre présence a été enregistrée!", ephemeral=True)
        
        await self.update_admin_tracking(interaction)

    @button(label="❌ Je ne pourrai pas", style=discord.ButtonStyle.danger)
    async def decline_presence(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        if self.msg_id not in missions:
            await interaction.followup.send("❌ Cette mission n'est plus disponible.", ephemeral=True)
            return
            
        missions[self.msg_id]["agents_confirmed"][interaction.user.id] = False
        await interaction.followup.send("❌ Votre absence a été enregistrée.", ephemeral=True)
        
        await self.update_admin_tracking(interaction)

    async def update_admin_tracking(self, interaction: discord.Interaction):
        if not interaction.guild:
            return
            
        admin_channel = interaction.guild.get_channel(MISSADMIN_CHANNEL_ID)
        if not isinstance(admin_channel, discord.TextChannel):
            return
            
        admin_msg_id = missions[self.msg_id].get("admin_msg_id")
        if not admin_msg_id:
            return
            
        try:
            admin_msg = await admin_channel.fetch_message(admin_msg_id)
            if not admin_msg:
                return
                
            embed = admin_msg.embeds[0]
            
            present_agents = [
                f"<@{agent_id}>" 
                for agent_id, confirmed in missions[self.msg_id]["agents_confirmed"].items() 
                if confirmed
            ]
            
            if present_agents:
                embed.set_field_at(
                    0, 
                    name="Présence des agents",
                    value="\n".join(f"• {agent}" for agent in present_agents),
                    inline=False
                )
            else:
                embed.set_field_at(
                    0,
                    name="Présence des agents",
                    value="*Aucun agent inscrit*",
                    inline=False
                )
            
            await admin_msg.edit(embed=embed)
            
        except Exception as e:
            print(f"Error updating admin message: {e}")

class MissionTrackingView(View):
    def __init__(self, mission_data: Dict[str, Any], msg_id: int):
        super().__init__(timeout=None)
        self.mission_data = mission_data
        self.msg_id = msg_id

    @button(label="🚀 Débuter la mission", style=discord.ButtonStyle.primary)
    async def start_mission(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        if self.msg_id not in missions:
            await interaction.followup.send("❌ Cette mission n'existe plus.", ephemeral=True)
            return

        frequency = random.randint(10000, 100000)
        
        present_agents = [
            str(agent_id)
            for agent_id, confirmed in missions[self.msg_id]["agents_confirmed"].items() 
            if confirmed
        ]
        
        if not present_agents:
            await interaction.followup.send("❌ Aucun agent n'est inscrit pour cette mission!", ephemeral=True)
            return

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.add_field(
            name="Status",
            value="✅ Mission en cours",
            inline=False
        )
        embed.add_field(
            name="Fréquence radio",
            value=f"📻 {frequency}",
            inline=False
        )
        
        guild = interaction.guild
        if guild:
            from ..config import RADIO_CHANNEL_ID
            radio_channel = guild.get_channel(RADIO_CHANNEL_ID)
            if isinstance(radio_channel, discord.TextChannel):
                await radio_channel.send(
                    f"📻 **Nouvelle mission en cours**\n"
                    f"Fréquence : `{frequency}`\n"
                    f"Agents assignés : {', '.join(f'<@{a}>' for a in present_agents)}"
                )

        await interaction.message.edit(
            embed=embed,
            view=MissionEndingView(self.mission_data, self.msg_id, present_agents)
        )

class MissionEndingView(View):
    def __init__(self, mission_data: Dict[str, Any], msg_id: int, present_agents: list):
        super().__init__(timeout=None)
        self.mission_data = mission_data
        self.msg_id = msg_id
        self.present_agents = present_agents

    @button(label="🏁 Terminer la mission", style=discord.ButtonStyle.danger)
    async def end_mission(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        if self.msg_id not in missions:
            await interaction.followup.send("❌ Cette mission n'existe plus.", ephemeral=True)
            return

        # Récupération des grades et salaires depuis le .env
        GRADE_DR = [x.strip() for x in os.getenv("GRADE_DR", "").split(",") if x.strip()]
        GRADE_AGTCONF = [x.strip() for x in os.getenv("GRADE_AGTCONF", "").split(",") if x.strip()]
        GRADE_RCR = [x.strip() for x in os.getenv("GRADE_RCR", "").split(",") if x.strip()]

        SALAIRES = {
            "DR": 15000,
            "AGTCONF": 12500,
            "RCR": 10000,
        }

        # Calcul dynamique du coût total
        base_cost = 20000
        total_salaires = 0

        for agent_id in self.present_agents:
            # agent_id est une string d'ID (ex: "7653067...")
            if agent_id in GRADE_DR:
                total_salaires += SALAIRES["DR"]
            elif agent_id in GRADE_AGTCONF:
                total_salaires += SALAIRES["AGTCONF"]
            elif agent_id in GRADE_RCR:
                total_salaires += SALAIRES["RCR"]
            else:
                # Option: définir un salaire par défaut au lieu de 0
                print(f"[!] ID {agent_id} n'a pas de grade défini.")

        total_cost = int(1.3 * (base_cost + total_salaires))  # 30% markup

        # Mise à jour de l’embed
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.dark_grey()
        try:
            embed.set_field_at(
                -2,
                name="Status",
                value="🏁 Mission terminée",
                inline=False
            )
        except Exception:
            # si l'index -2 n'existe pas, ajouter un field Status
            embed.add_field(name="Status", value="🏁 Mission terminée", inline=False)

        embed.add_field(
            name="Coût total",
            value=f"💰 {total_cost:,} $",
            inline=False
        )

        client_id = int(self.mission_data["id"])
        await interaction.message.edit(embed=embed, view=None)

        # Envoi DM au client et démarrage du feedback DM
        try:
            client = await interaction.client.fetch_user(client_id)
            if client:
                cost_embed = discord.Embed(
                    title="🎯 Mission terminée",
                    description=(
                        f"Votre mission **{self.mission_data['nom']}** est terminée.\n\n"
                        f"💰 **Montant à régler :** {total_cost:,} $\n"
                        f"📱 **Numéro pour virement :** 59669-70941"
                    ),
                    color=discord.Color.blue()
                )
                await client.send(embed=cost_embed)
                # Démarrer le process de feedback DM
                await start_feedback_dm(client, self.mission_data, self.msg_id, interaction.client)
        except Exception as e:
            print(f"Error sending DM to client: {e}")

        # Clean up mission data
        missions.pop(self.msg_id, None)

# --- Feedback DM system ---
feedback_states = {}  # user_id: FeedbackState

class FeedbackState:
    def __init__(self, user_id, mission_data, msg_id):
        self.user_id = user_id
        self.mission_data = mission_data
        self.msg_id = msg_id
        self.step = 0  # 0: intro, 1: note, 2: commentaire, 3: recap, 4: choix envoyer/modifier
        self.note = None
        self.comment = None

async def start_feedback_dm(user, mission_data, msg_id, bot):
    state = FeedbackState(user.id, mission_data, msg_id)
    feedback_states[user.id] = state
    # 1. Intro
    intro_embed = discord.Embed(
        title="⭐ Nous aimerions votre avis !",
        description="Merci d'avoir fait appel à nous. Nous serions ravis d'avoir votre retour sur la mission."
    )
    await user.send(embed=intro_embed)
    # 2. Demande de note
    await send_note_request(user)

async def send_note_request(user):
    embed = discord.Embed(
        title="⭐ Noter la mission",
        description="Veuillez envoyer une note entre 1 et 5 (1=très mauvais, 5=excellent).\nSi vous ne souhaitez pas donner de retour, répondez 'non'."
    )
    await user.send(embed=embed)
    feedback_states[user.id].step = 1

async def send_comment_request(user):
    embed = discord.Embed(
        title="💬 Commentaire sur la mission",
        description="Vous pouvez maintenant écrire un commentaire sur la mission.\nRépondez 'non' si vous ne souhaitez pas commenter."
    )
    await user.send(embed=embed)
    feedback_states[user.id].step = 2

async def send_recap(user):
    state = feedback_states[user.id]
    stars = "".join(["⭐" if i < state.note else "☆" for i in range(5)]) if state.note else ""
    embed = discord.Embed(
        title="📝 Récapitulatif de votre feedback",
        description=f"Note : {stars}\nCommentaire : {state.comment if state.comment else 'Aucun'}"
    )
    embed.set_footer(text="Répondez 'envoyer' pour transmettre votre feedback, ou 'modifier' pour le changer.")
    await user.send(embed=embed)
    state.step = 3

async def send_modify_choice(user):
    embed = discord.Embed(
        title="✏️ Modifier votre feedback",
        description="Que souhaitez-vous modifier ? Répondez 'note' ou 'commentaire'."
    )
    await user.send(embed=embed)
    feedback_states[user.id].step = 4

# Optionnel: gérer les messages DM entrants pour avancer le flow (à brancher dans ton on_message / event)
# Exemple minimal à placer dans ton bot event listener (hors de ce fichier) :
# @bot.event
# async def on_message(message):
#     if message.author.bot: return
#     if message.author.id in feedback_states:
#         state = feedback_states[message.author.id]
#         content = message.content.strip().lower()
#         if state.step == 1:
#             if content == "non":
#                 state.note = None
#                 await send_recap(message.author)
#             elif content.isdigit() and 1 <= int(content) <= 5:
#                 state.note = int(content)
#                 await send_comment_request(message.author)
#             else:
#                 await message.channel.send("Veuillez répondre par un nombre entre 1 et 5, ou 'non'.")
#         elif state.step == 2:
#             if content == "non":
#                 state.comment = None
#                 await send_recap(message.author)
#             else:
#                 state.comment = message.content
#                 await send_recap(message.author)
#         elif state.step == 3:
#             if content == "envoyer":
#                 # envoyer feedback au channel admin
#                 guild = bot.get_guild(YOUR_GUILD_ID)  # adapte si besoin
#                 admin_channel = guild.get_channel(MISSADMIN_CHANNEL_ID)
#                 embed = discord.Embed(title=f"📊 Feedback - {state.mission_data['nom']}", color=discord.Color.green())
#                 stars = "★" * state.note + "☆" * (5 - state.note) if state.note else "Aucun"
#                 embed.add_field(name="Note", value=stars, inline=False)
#                 embed.add_field(name="Commentaire", value=state.comment or "Aucun", inline=False)
#                 if isinstance(admin_channel, discord.TextChannel):
#                     await admin_channel.send(embed=embed)
#                 await message.channel.send("Merci ! Votre feedback a bien été envoyé.")
#                 feedback_states.pop(message.author.id, None)
#             elif content == "modifier":
#                 await send_modify_choice(message.author)
#             else:
#                 await message.channel.send("Répondez 'envoyer' ou 'modifier'.")
#         elif state.step == 4:
#             if content == "note":
#                 await send_note_request(message.author)
#             elif content == "commentaire":
#                 await send_comment_request(message.author)
#             else:
#                 await message.channel.send("Répondez 'note' ou 'commentaire'.")

class MissionFeedbackView(View):
    def __init__(self, mission_data: Dict[str, Any], msg_id: int):
        super().__init__(timeout=None)
        self.mission_data = mission_data
        self.msg_id = msg_id
        self.feedback_text = None
        self.rating = 0

    def create_star_buttons(self):
        """Removes existing star buttons and adds new ones based on current rating"""
        self.clear_items()
        
        star_row = []
        for i in range(1, 6):
            btn = discord.ui.Button(
                emoji="⭐" if i <= self.rating else "✩",
                custom_id=f"star_{i}",
                style=discord.ButtonStyle.primary if i <= self.rating else discord.ButtonStyle.secondary,
                row=0
            )
            btn.callback = self.create_star_callback(i)
            star_row.append(btn)
            
        for btn in star_row:
            self.add_item(btn)
            
        feedback_btn = discord.ui.Button(
            label="📝 Ajouter un commentaire",
            custom_id="feedback",
            style=discord.ButtonStyle.success,
            row=1
        )
        feedback_btn.callback = self.feedback_callback
        self.add_item(feedback_btn)
        
        if self.rating > 0:
            submit_btn = discord.ui.Button(
                label="✅ Envoyer le feedback",
                custom_id="submit",
                style=discord.ButtonStyle.primary,
                row=1
            )
            submit_btn.callback = self.submit_callback
            self.add_item(submit_btn)

    def create_star_callback(self, rating: int):
        async def callback(interaction: discord.Interaction):
            self.rating = rating
            await interaction.response.defer()
            self.create_star_buttons()
            try:
                await interaction.message.edit(view=self)
            except Exception:
                pass
            await interaction.followup.send(
                f"⭐ Vous avez noté la mission {rating} étoile{'s' if rating > 1 else ''}!",
                ephemeral=True
            )
        return callback

    async def feedback_callback(self, interaction: discord.Interaction):
        modal = FeedbackModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        if modal.feedback:
            self.feedback_text = modal.feedback
            await interaction.followup.send(
                "✅ Votre commentaire a été enregistré! Cliquez sur 'Envoyer le feedback' quand vous avez terminé.",
                ephemeral=True
            )

    async def submit_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title=f"📊 Feedback - {self.mission_data['nom']}",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Note",
            value="★" * self.rating + "☆" * (5 - self.rating),
            inline=False
        )
        if self.feedback_text:
            embed.add_field(
                name="Commentaire",
                value=self.feedback_text,
                inline=False
            )
            
        guild = interaction.guild
        if guild:
            admin_channel = guild.get_channel(MISSADMIN_CHANNEL_ID)
            if isinstance(admin_channel, discord.TextChannel):
                await admin_channel.send(embed=embed)
        
        completion_embed = discord.Embed(
            title="✨ Feedback envoyé",
            description="Merci d'avoir pris le temps de nous donner votre avis !\nAu plaisir de vous revoir pour une prochaine mission.",
            color=discord.Color.green()
        )
        try:
            await interaction.message.edit(
                embed=completion_embed,
                view=None
            )
        except Exception:
            pass

class FeedbackModal(Modal):
    def __init__(self):
        super().__init__(title="Commentaire sur la mission")
        self.feedback = None
        
    feedback_text = TextInput(
        label="Votre commentaire",
        style=discord.TextStyle.paragraph,
        placeholder="Comment s'est passée la mission? Des suggestions?",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.feedback = self.feedback_text.value
