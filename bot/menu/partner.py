import discord
from discord.ui import Modal, TextInput, View, Button, Select
from .tickets import create_ticket_channel, clean_and_send
import os
from dotenv import load_dotenv

load_dotenv()
PARTNER_FCHANNEL_ID = int(os.getenv("PARTNER_FCHANNEL_ID", 0))
PARTNERS_DATA_CHANNEL_ID = int(os.getenv("PARTNERS_DATA_CHANNEL_ID", 0))

PARTNER_REQUESTS = {}  # ticket_id -> dict des infos et status

# ---------------- MODALS ----------------
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
            "company_type": self.company_type.value.strip(),
            "status": "pending",
            "info_submitted": {"direction": False, "pdg": False},
            "offers": {"direction": None, "pdg": None},
            "signed": {"direction": False, "pdg": False}
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

            PARTNER_REQUESTS[ticket_channel.id] = {"data": result, "embed_msg_id": msg.id}

        await interaction.followup.send("✅ Votre demande a été postée dans le ticket.", ephemeral=True)

# ---------------- VIEWS ----------------
class PartnershipDecisionView(View):
    def __init__(self, ticket_channel_id: int, request_data: dict):
        super().__init__(timeout=None)
        self.ticket_channel_id = ticket_channel_id
        self.request_data = request_data

        self.add_item(Button(style=discord.ButtonStyle.success, label="Accepter", custom_id="accept"))
        self.add_item(Button(style=discord.ButtonStyle.danger, label="Refuser", custom_id="refuse"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True  # ici tu peux restreindre aux membres de la direction

    @discord.ui.button(label="Accepter", style=discord.ButtonStyle.success)
    async def accept_callback(self, interaction: discord.Interaction, button: Button):
        PARTNER_REQUESTS[self.ticket_channel_id]["data"]["status"] = "accepted"

        # Envoie embed "Non envoyé" avec statut de chaque partie
        ticket_channel = interaction.channel
        embed = discord.Embed(
            title=f"Informations complémentaires — {self.request_data['company_name']}",
            description=f"Préparez le lien permanent et remplissez les infos ci-dessous",
            color=discord.Color.orange()
        )
        embed.add_field(name="Statut", value=f"❌ Direction : non envoyé\n❌ PDG : non envoyé")
        msg = await ticket_channel.send(embed=embed, view=PartnerInfoView(self.ticket_channel_id))

        PARTNER_REQUESTS[self.ticket_channel_id]["info_embed_msg_id"] = msg.id

        await interaction.response.send_message("✅ Informations complémentaires demandées aux deux parties.", ephemeral=False)

    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.danger)
    async def refuse_callback(self, interaction: discord.Interaction, button: Button):
        PARTNER_REQUESTS[self.ticket_channel_id]["data"]["status"] = "refused"
        await interaction.response.send_message("❌ Partenariat refusé.", ephemeral=False)

class PartnerInfoView(View):
    def __init__(self, ticket_channel_id: int):
        super().__init__(timeout=None)
        self.ticket_channel_id = ticket_channel_id
        self.add_item(Button(label="Envoyer mes informations", style=discord.ButtonStyle.primary, custom_id="send_info"))

    @discord.ui.button(label="Envoyer mes informations", style=discord.ButtonStyle.primary)
    async def send_info_callback(self, interaction: discord.Interaction, button: Button):
        """Ouvre un modal pour remplir nom, description, lien discord, offre, infos sup"""
        await interaction.response.send_modal(PartnerInfoModal(self.ticket_channel_id, interaction.user))

class PartnerInfoModal(Modal):
    def __init__(self, ticket_channel_id: int, user: discord.User):
        super().__init__(title="Informations complémentaires")
        self.ticket_channel_id = ticket_channel_id
        self.user = user

        self.company_name = TextInput(label="Nom de l'entreprise", required=True)
        self.presentation = TextInput(label="Présentation courte", required=True)
        self.discord_link = TextInput(label="Lien Discord", required=True)
        self.offer = TextInput(label="Offre proposée", required=True)
        self.extra_info = TextInput(label="Infos supplémentaires (facultatif)", required=False)

        self.add_item(self.company_name)
        self.add_item(self.presentation)
        self.add_item(self.discord_link)
        self.add_item(self.offer)
        self.add_item(self.extra_info)

    async def on_submit(self, interaction: discord.Interaction):
        ticket_data = PARTNER_REQUESTS[self.ticket_channel_id]["data"]
        side = "direction" if self.user.id == ticket_data.get("requester_id") else "pdg"

        ticket_data["info_submitted"][side] = True
        ticket_data[f"{side}_info"] = {
            "company_name": self.company_name.value,
            "presentation": self.presentation.value,
            "discord_link": self.discord_link.value,
            "offer": self.offer.value,
            "extra_info": self.extra_info.value
        }

        # Met à jour l'embed avec le statut des deux parties
        ticket_channel = interaction.channel
        msg_id = PARTNER_REQUESTS[self.ticket_channel_id]["info_embed_msg_id"]
        try:
            msg = await ticket_channel.fetch_message(msg_id)
            status_lines = [
                f"{'✅' if ticket_data['info_submitted']['direction'] else '❌'} Direction",
                f"{'✅' if ticket_data['info_submitted']['pdg'] else '❌'} PDG"
            ]
            embed = msg.embeds[0]
            embed.set_field_at(0, name="Statut", value="\n".join(status_lines))
            await msg.edit(embed=embed)
        except Exception as e:
            print(f"Erreur update embed statut: {e}")

        await interaction.response.send_message("✅ Informations enregistrées.", ephemeral=True)

# ---------------- FONCTION DEPLOY ----------------
async def deploy_partnership_menu(bot: commands.Bot):
    """Déploie le menu initial dans le channel de contact."""
    from bot.config import CONTACTS_CHANNEL_ID

    channel = bot.get_channel(CONTACTS_CHANNEL_ID)
    if channel is None:
        channel = await bot.fetch_channel(CONTACTS_CHANNEL_ID)

    embed = discord.Embed(
        title="Nous contacter",
        description="Choisissez une option ci-dessous :",
        color=discord.Color.blurple()
    )
    view = PartnershipDecisionView(0, {})  # id et data fictifs pour menu initial
    await clean_and_send(channel, embed=embed, view=view)
