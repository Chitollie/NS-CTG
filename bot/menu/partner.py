import discord
from discord.ui import Modal, TextInput, View, Button
from .tickets import create_ticket_channel, clean_and_send
import os
from dotenv import load_dotenv

load_dotenv()
PARTNER_FCHANNEL_ID = int(os.getenv("PARTNER_FCHANNEL_ID", 0))
PARTNERS_DATA_CHANNEL_ID = int(os.getenv("PARTNERS_DATA_CHANNEL_ID", 0))

PARTNER_REQUESTS = {}

class PartnershipModal(Modal):
    def __init__(self, ticket_channel_id: int):
        super().__init__(title="Demande de Partenariat")
        self.ticket_channel_id = ticket_channel_id

        self.first_name = TextInput(label="Prénom du PDG", required=True)
        self.last_name = TextInput(label="Nom du PDG", required=True)
        self.pdg_id = TextInput(label="ID Discord du PDG", required=True)
        self.company_name = TextInput(label="Nom de l'entreprise", required=True)
        self.company_type = TextInput(label="Type (bar, boutique...)", required=True)

        self.add_item(self.first_name)
        self.add_item(self.last_name)
        self.add_item(self.pdg_id)
        self.add_item(self.company_name)
        self.add_item(self.company_type)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        result = {
            "first_name": self.first_name.value.strip(),
            "last_name": self.last_name.value.strip(),
            "pdg_id": int(self.pdg_id.value.strip()),
            "company_name": self.company_name.value.strip(),
            "company_type": self.company_type.value.strip()
        }

        ticket_channel = interaction.guild.get_channel(self.ticket_channel_id)
        if ticket_channel:
            embed = discord.Embed(
                title=f"Demande de Partenariat — {result['company_name']}",
                description=f"**Type :** {result['company_type']}",
                color=discord.Color.gold()
            )
            embed.add_field(name="PDG", value=f"{result['first_name']} {result['last_name']} (<@{result['pdg_id']}>)", inline=False)
            embed.set_footer(text=f"Demandé par {interaction.user} • ID {interaction.user.id}")

            view = PartnershipDecisionView(ticket_channel.id, result)
            msg = await ticket_channel.send(embed=embed, view=view)

            PARTNER_REQUESTS[ticket_channel.id] = {
                "requester_id": interaction.user.id,
                "pdg_id": result["pdg_id"],
                "pdg_display": f"{result['first_name']} {result['last_name']}",
                "company_name": result["company_name"],
                "company_type": result["company_type"],
                "request_embed_msg_id": msg.id,
                "status": "pending"
            }

        await interaction.followup.send("✅ Votre demande a été postée dans le ticket.", ephemeral=True)

class PartnershipDecisionView(View):
    def __init__(self, ticket_channel_id: int, request_data: dict):
        super().__init__(timeout=None)
        self.ticket_channel_id = ticket_channel_id
        self.request_data = request_data

        accept_btn = Button(style=discord.ButtonStyle.success, label="Accepter")
        refuse_btn = Button(style=discord.ButtonStyle.danger, label="Refuser")
        accept_btn.callback = self.accept_callback
        refuse_btn.callback = self.refuse_callback
        self.add_item(accept_btn)
        self.add_item(refuse_btn)

    async def accept_callback(self, interaction: discord.Interaction):
        PARTNER_REQUESTS[self.ticket_channel_id]["status"] = "accepted"

        # Poster dans le forum
        forum = interaction.guild.get_channel(PARTNER_FCHANNEL_ID)
        if forum:
            thread = await forum.create_thread(
                name=self.request_data["company_name"],
                type=discord.ChannelType.public_thread
            )
            await thread.send(f"**Description :** {self.request_data['company_type']}\n**Lien Discord :** <@{self.request_data['pdg_id']}>")

        # Envoyer dans database
        db_channel = interaction.guild.get_channel(PARTNERS_DATA_CHANNEL_ID)
        if db_channel:
            embed = discord.Embed(
                title=f"{self.request_data['company_name']} - Partenaire",
                description=f"PDG: {self.request_data['pdg_display']} ({self.request_data['pdg_id']})\nType: {self.request_data['company_type']}",
                color=discord.Color.green()
            )
            await db_channel.send(embed=embed)

        # Envoyer MP au PDG
        pdg = interaction.guild.get_member(self.request_data['pdg_id'])
        if pdg:
            await pdg.send(embed=embed)

        await interaction.response.send_message("✅ Partenariat accepté et posté.", ephemeral=False)

    async def refuse_callback(self, interaction: discord.Interaction):
        PARTNER_REQUESTS[self.ticket_channel_id]["status"] = "refused"
        await interaction.response.send_message("❌ Partenariat refusé.", ephemeral=False)
