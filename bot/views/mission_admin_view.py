import discord
from discord.ui import View, button, Modal, TextInput
import random
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
        
        # Get the mission channel
        guild = interaction.guild
        if not guild:
            await interaction.followup.send("❌ Erreur : serveur introuvable", ephemeral=True)
            return
        
        mission_channel = guild.get_channel(MISS_CHANNEL_ID)
        if not isinstance(mission_channel, discord.TextChannel):
            await interaction.followup.send("❌ Erreur : salon des missions introuvable", ephemeral=True)
            return

        # Create mission tracking embed
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

        # Update mission message in mission channel
        missions[self.msg_id]["admin_msg_id"] = admin_msg.id
        mission_msg = await mission_channel.fetch_message(self.msg_id)
        if mission_msg:
            embed = mission_msg.embeds[0]
            embed.color = discord.Color.green()
            embed.set_footer(text="✅ Mission validée")
            await mission_msg.edit(
                embed=embed, 
                view=MissionParticipationView(self.mission_data, self.msg_id)
            )

        # Send DM to client
        try:
            client = await interaction.client.fetch_user(self.client_id)
            if client:
                await client.send(f"✅ Votre demande de mission **{self.mission_data['nom']}** a été acceptée!")
        except:
            pass

    @button(label="❌ Refuser", style=discord.ButtonStyle.danger)
    async def refuse_mission(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Remove mission message
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

        # Update admin message
        embed = discord.Embed(
            title=f"📋 Mission refusée : {self.mission_data['nom']}",
            description=f"Refusée par {interaction.user.mention}",
            color=discord.Color.red()
        )
        await interaction.message.edit(embed=embed, view=None)

        # Send DM to client
        try:
            client = await interaction.client.fetch_user(self.client_id)
            if client:
                await client.send(f"❌ Votre demande de mission **{self.mission_data['nom']}** a été refusée.")
        except:
            pass

        # Clean up mission data
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
        
        # Update admin message
        await self.update_admin_tracking(interaction)

    @button(label="❌ Je ne pourrai pas", style=discord.ButtonStyle.danger)
    async def decline_presence(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        if self.msg_id not in missions:
            await interaction.followup.send("❌ Cette mission n'est plus disponible.", ephemeral=True)
            return
            
        missions[self.msg_id]["agents_confirmed"][interaction.user.id] = False
        await interaction.followup.send("❌ Votre absence a été enregistrée.", ephemeral=True)
        
        # Update admin message
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
            
            # Update presence field
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

        # Generate random radio frequency
        frequency = random.randint(10000, 100000)
        
        # Get present agents
        present_agents = [
            f"<@{agent_id}>" 
            for agent_id, confirmed in missions[self.msg_id]["agents_confirmed"].items() 
            if confirmed
        ]
        
        if not present_agents:
            await interaction.followup.send("❌ Aucun agent n'est inscrit pour cette mission!", ephemeral=True)
            return

        # Update tracking embed
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
        
        # Send radio message
        guild = interaction.guild
        if guild:
            from ..config import RADIO_CHANNEL_ID
            radio_channel = guild.get_channel(RADIO_CHANNEL_ID)
            if isinstance(radio_channel, discord.TextChannel):
                await radio_channel.send(
                    f"📻 **Nouvelle mission en cours**\n"
                    f"Fréquence : `{frequency}`\n"
                    f"Agents assignés : {', '.join(present_agents)}"
                )

        # Update view
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

        # Calculate cost based on present agents
        nb_agents = len(self.present_agents)
        base_cost = 50000
        agent_cost = nb_agents * 15000  # Using highest rate for security
        total_cost = int(1.3 * (base_cost + agent_cost))  # 30% markup

        # Update embed
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.dark_grey()
        embed.set_field_at(
            -2,  # Status field
            name="Status",
            value="🏁 Mission terminée",
            inline=False
        )
        embed.add_field(
            name="Coût total",
            value=f"💰 {total_cost:,} $",
            inline=False
        )

        # Remove view buttons and add feedback view for client
        client_id = int(self.mission_data["id"])
        await interaction.message.edit(
            embed=embed,
            view=None
        )

        # Send cost and feedback request to client
        try:
            client = await interaction.client.fetch_user(client_id)
            if client:
                feedback_embed = discord.Embed(
                    title="🎯 Mission terminée",
                    description=(
                        f"Votre mission **{self.mission_data['nom']}** est terminée.\n\n"
                        f"💰 **Montant à régler :** {total_cost:,} $\n"
                        f"📱 **Numéro pour virement :** 555-0234\n\n"
                        "Merci de nous donner votre feedback ci-dessous !"
                    ),
                    color=discord.Color.blue()
                )
                await client.send(
                    embed=feedback_embed,
                    view=MissionFeedbackView(self.mission_data, self.msg_id)
                )
        except:
            pass

        # Clean up mission data
        missions.pop(self.msg_id, None)

class MissionFeedbackView(View):
    def __init__(self, mission_data: Dict[str, Any], msg_id: int):
        super().__init__(timeout=None)
        self.mission_data = mission_data
        self.msg_id = msg_id
        self.feedback_text = None
        self.rating = 0

    def create_star_buttons(self):
        """Removes existing star buttons and adds new ones based on current rating"""
        # Remove old star buttons
        self.clear_items()
        
        # Add new star buttons
        for i in range(1, 6):
            btn = discord.ui.Button(
                label="★" if i <= self.rating else "☆",
                custom_id=f"star_{i}",
                style=discord.ButtonStyle.primary if i <= self.rating else discord.ButtonStyle.secondary
            )
            btn.callback = self.create_star_callback(i)
            self.add_item(btn)
            
        # Add feedback and submit buttons
        feedback_btn = discord.ui.Button(
            label="💬 Ajouter un commentaire",
            custom_id="feedback",
            style=discord.ButtonStyle.success
        )
        feedback_btn.callback = self.feedback_callback
        self.add_item(feedback_btn)
        
        if self.rating > 0:  # Only show submit if at least 1 star
            submit_btn = discord.ui.Button(
                label="✅ Envoyer le feedback",
                custom_id="submit",
                style=discord.ButtonStyle.primary
            )
            submit_btn.callback = self.submit_callback
            self.add_item(submit_btn)

    def create_star_callback(self, rating: int):
        async def callback(interaction: discord.Interaction):
            self.rating = rating
            await interaction.response.defer()
            
            # Update buttons
            self.create_star_buttons()
            await interaction.message.edit(view=self)
            
            # Send confirmation
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
        
        # Create feedback embed
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
            
        # Send to admin channel
        guild = interaction.guild
        if guild:
            admin_channel = guild.get_channel(MISSADMIN_CHANNEL_ID)
            if isinstance(admin_channel, discord.TextChannel):
                await admin_channel.send(embed=embed)
        
        # Update message
        await interaction.message.edit(
            content="✅ Merci pour votre feedback!",
            embed=None,
            view=None
        )

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