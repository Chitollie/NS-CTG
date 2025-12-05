import discord
from discord.ui import Modal, TextInput, View, Button
from .tickets import create_ticket_channel, clean_and_send
import os
from dotenv import load_dotenv

load_dotenv()
PARTNER_FCHANNEL_ID = int(os.getenv("PARTNER_FCHANNEL_ID", 0))
PARTNERS_DATA_CHANNEL_ID = int(os.getenv("PARTNERS_DATA_CHANNEL_ID", 0))

PARTNER_REQUESTS = {}

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

            view = PartnershipDecisionView(self.ticket_channel_id, result)
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
        return True

    @discord.ui.button(label="Accepter", style=discord.ButtonStyle.success)
    async def accept_callback(self, interaction: discord.Interaction, button: Button):
        ticket_data = PARTNER_REQUESTS[self.ticket_channel_id]["data"]
        ticket_data["status"] = "accepted"
        ticket_channel = interaction.channel

        embed = discord.Embed(
            title=f"Informations complémentaires — {ticket_data['company_name']}",
            description="Préparez le lien permanent et remplissez les infos ci-dessous",
            color=discord.Color.orange()
        )
        embed.add_field(name="Statut", value="❌ Direction : non envoyé\n❌ PDG : non envoyé")
        msg = await ticket_channel.send(embed=embed, view=PartnerInfoView(self.ticket_channel_id))
        ticket_data["info_embed_msg_id"] = msg.id

        await interaction.response.send_message("✅ Informations complémentaires demandées aux deux parties.", ephemeral=False)

    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.danger)
    async def refuse_callback(self, interaction: discord.Interaction, button: Button):
        ticket_data = PARTNER_REQUESTS[self.ticket_channel_id]["data"]
        ticket_data["status"] = "refused"
        await interaction.response.send_message("❌ Partenariat refusé.", ephemeral=False)


class PartnerInfoView(View):
    def __init__(self, ticket_channel_id: int):
        super().__init__(timeout=None)
        self.ticket_channel_id = ticket_channel_id
        self.add_item(Button(label="Envoyer mes informations", style=discord.ButtonStyle.primary, custom_id="send_info"))

    @discord.ui.button(label="Envoyer mes informations", style=discord.ButtonStyle.primary)
    async def send_info_callback(self, interaction: discord.Interaction, button: Button):
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

        ticket_channel = interaction.channel
        msg_id = ticket_data["info_embed_msg_id"]
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

        if all(ticket_data["info_submitted"].values()):
            await self.send_offer_recap(ticket_channel, ticket_data)

    async def send_offer_recap(self, ticket_channel: discord.TextChannel, ticket_data: dict):
        embed = discord.Embed(
            title=f"Récapitulatif des offres — {ticket_data['company_name']}",
            description="Vérifiez les informations avant de procéder à l'acceptation/refus de l'offre.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Direction", value=ticket_data["direction_info"]["offer"], inline=False)
        embed.add_field(name="PDG", value=ticket_data["pdg_info"]["offer"], inline=False)

        view = PartnerOfferDecisionView(self.ticket_channel_id)
        await ticket_channel.send(embed=embed, view=view)


class PartnerOfferDecisionView(View):
    def __init__(self, ticket_channel_id: int):
        super().__init__(timeout=None)
        self.ticket_channel_id = ticket_channel_id
        self.add_item(Button(label="Accepter l'offre", style=discord.ButtonStyle.success, custom_id="accept_offer"))
        self.add_item(Button(label="Refuser l'offre", style=discord.ButtonStyle.danger, custom_id="refuse_offer"))

    @discord.ui.button(label="Accepter l'offre", style=discord.ButtonStyle.success)
    async def accept_offer(self, interaction: discord.Interaction, button: Button):
        ticket_data = PARTNER_REQUESTS[self.ticket_channel_id]["data"]
        ticket_data["status"] = "offer_accepted"

        await interaction.response.send_message(f"✅ Offre acceptée par {interaction.user.mention}", ephemeral=False)
        await self.handle_signature(interaction, ticket_data)

    @discord.ui.button(label="Refuser l'offre", style=discord.ButtonStyle.danger)
    async def refuse_offer(self, interaction: discord.Interaction, button: Button):
        ticket_data = PARTNER_REQUESTS[self.ticket_channel_id]["data"]
        ticket_data["status"] = "offer_refused"
        await interaction.response.send_message(f"❌ Offre refusée par {interaction.user.mention}", ephemeral=False)

    async def handle_signature(self, interaction: discord.Interaction, ticket_data: dict):
        embed = discord.Embed(
            title=f"Signature du partenariat — {ticket_data['company_name']}",
            description="Les deux parties doivent signer pour finaliser le partenariat.",
            color=discord.Color.purple()
        )
        view = PartnerSignatureView(self.ticket_channel_id)
        await interaction.channel.send(embed=embed, view=view)


class PartnerSignatureView(View):
    def __init__(self, ticket_channel_id: int):
        super().__init__(timeout=None)
        self.ticket_channel_id = ticket_channel_id
        self.add_item(Button(label="Signer", style=discord.ButtonStyle.success, custom_id="sign"))

    @discord.ui.button(label="Signer", style=discord.ButtonStyle.success)
    async def sign_callback(self, interaction: discord.Interaction, button: Button):
        ticket_data = PARTNER_REQUESTS[self.ticket_channel_id]["data"]
        side = "direction" if interaction.user.id == ticket_data.get("requester_id") else "pdg"
        ticket_data["signed"][side] = True

        await interaction.response.send_message(f"✅ {interaction.user.mention} a signé le contrat.", ephemeral=False)

        if all(ticket_data["signed"].values()):
            await self.send_final_summary(interaction.channel, ticket_data, interaction.guild)

    async def send_final_summary(self, ticket_channel: discord.TextChannel, ticket_data: dict, guild: discord.Guild):
        embed = discord.Embed(
            title=f"Partenariat finalisé — {ticket_data['company_name']}",
            description="Toutes les informations ont été validées et signées.",
            color=discord.Color.green()
        )
        embed.add_field(name="Direction", value=str(ticket_data["direction_info"]), inline=False)
        embed.add_field(name="PDG", value=str(ticket_data["pdg_info"]), inline=False)

        db_channel = guild.get_channel(PARTNERS_DATA_CHANNEL_ID)
        if db_channel:
            await db_channel.send(embed=embed)

        await ticket_channel.send("✅ Partenariat finalisé et enregistré dans la base de données.")

# ---------------- FONCTION DEPLOY ----------------
async def deploy_partnership_menu(bot):
    from bot.config import CONTACTS_CHANNEL_ID

    channel = bot.get_channel(CONTACTS_CHANNEL_ID)
    if channel is None:
        channel = await bot.fetch_channel(CONTACTS_CHANNEL_ID)

    embed = discord.Embed(
        title="Demander un partenariat",
        description="Cliquez pour commencer le processus.",
        color=discord.Color.blurple()
    )
    view = PartnershipDecisionView(0, {})
    await clean_and_send(channel, embed=embed, view=view)
