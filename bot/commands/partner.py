import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select, Button, Modal, TextInput
from typing import Dict, Any, Optional
import random
import logging

# ---------------- CONFIG ----------------
CONTACTS_CHANNEL_ID = 123456789012345678  # à remplacer par ton vrai ID
TICKETS_CATEGORY_ID = 987654321098765432  # à remplacer par ton vrai ID
GRADE_DR = []  # liste des IDs des membres qui peuvent voir tous les tickets

logger = logging.getLogger("partner")
logger.setLevel(logging.INFO)

# ---------------- GLOBALS ----------------
PARTNER_REQUESTS: Dict[int, Dict[str, Any]] = {}
_last_contact_message: Dict[int, int] = {}  # channel_id -> message_id

# ---------------- HELPERS ----------------
def _short_id() -> str:
    return str(random.randint(1000, 9999))

async def create_ticket_channel(guild: discord.Guild, name: str, requester: discord.Member) -> Optional[discord.TextChannel]:
    overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False)}
    overwrites[requester] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
    for did in GRADE_DR:
        member = guild.get_member(int(did))
        if member:
            overwrites[member] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
    category = None
    if TICKETS_CATEGORY_ID:
        category = guild.get_channel(int(TICKETS_CATEGORY_ID))
        if not isinstance(category, discord.CategoryChannel):
            category = None
    try:
        channel_name = f"ticket-{name}-{_short_id()}"
        if category:
            return await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        return await guild.create_text_channel(channel_name, overwrites=overwrites)
    except Exception as e:
        logger.exception(f"Erreur création channel ticket: {e}")
        return None

async def clean_and_send(channel: discord.TextChannel, content: Optional[str] = None, *, embed: Optional[discord.Embed] = None, view: Optional[discord.ui.View] = None):
    msg = None
    last_id = _last_contact_message.get(channel.id)
    if last_id:
        try:
            prev = await channel.fetch_message(last_id)
            await prev.edit(content=content, embed=embed, view=view)
            msg = prev
        except Exception:
            pass
    if msg is None:
        try:
            msg = await channel.send(content=content, embed=embed, view=view)
            _last_contact_message[channel.id] = msg.id
        except Exception as e:
            logger.exception(f"Impossible d'envoyer le message dans le channel {channel.id}: {e}")
    return msg

# ---------------- MODALS ----------------
class PartnershipModal(Modal):
    def __init__(self, ticket_channel_id: int):
        super().__init__(title="Demande de Partenariat")
        self.ticket_channel_id = ticket_channel_id
        self.first_name = TextInput(label="Prénom du PDG", placeholder="Prénom", required=True, max_length=64)
        self.last_name = TextInput(label="Nom du PDG", placeholder="Nom", required=True, max_length=64)
        self.pdg_id = TextInput(label="ID Discord du PDG", placeholder="7254...", required=True, max_length=30)
        self.company_name = TextInput(label="Nom de l'entreprise", placeholder="Ex: Club XYZ", required=True, max_length=100)
        self.company_type = TextInput(label="Type (bar, boutique...)", placeholder="Ex: Bar / Boutique", required=True, max_length=64)
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
            "pdg_id": self.pdg_id.value.strip(),
            "company_name": self.company_name.value.strip(),
            "company_type": self.company_type.value.strip(),
        }
        ticket_channel = interaction.guild.get_channel(self.ticket_channel_id)
        if ticket_channel:
            embed = discord.Embed(
                title=f"Demande de Partenariat — {result['company_name']}",
                description=f"**Type :** {result['company_type']}",
                color=discord.Color.gold()
            )
            embed.add_field(name="PDG", value=f"{result['first_name']} {result['last_name']} (<@{result['pdg_id']}>)", inline=False)
            embed.add_field(name="ID PDG", value=result['pdg_id'], inline=True)
            embed.add_field(name="Entreprise", value=result['company_name'], inline=True)
            embed.set_footer(text=f"Demandé par {interaction.user} • ID {interaction.user.id}")

            view = PartnershipDecisionView(ticket_channel.id)
            msg = await ticket_channel.send(embed=embed, view=view)

            PARTNER_REQUESTS[ticket_channel.id] = {
                "requester_id": interaction.user.id,
                "pdg_id": int(result['pdg_id']),
                "pdg_display": f"{result['first_name']} {result['last_name']}",
                "company_name": result["company_name"],
                "company_type": result["company_type"],
                "request_embed_msg_id": msg.id,
                "status": "pending"
            }

        await interaction.followup.send("✅ Votre demande a été postée dans le ticket.", ephemeral=True)

# ---------------- VIEWS ----------------
class PartnershipSelectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        options = [
            discord.SelectOption(label="Demande de Partenariat", description="Remplir la demande de partenariat", value="partnership"),
            discord.SelectOption(label="Autres", description="Ouvrir un ticket simple", value="other"),
        ]
        self.add_item(Select(
            placeholder="Que souhaitez-vous ?",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="partnership_main_select"
        ))

    @discord.ui.select(custom_id="partnership_main_select")
    async def select_callback(self, select: Select, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        choice = select.values[0]
        ticket_channel = await create_ticket_channel(interaction.guild, choice, interaction.user)
        if not ticket_channel:
            await interaction.followup.send("❌ Impossible de créer le ticket.", ephemeral=True)
            return
        await interaction.followup.send(f"✅ Ticket créé : {ticket_channel.mention}", ephemeral=True)

        if choice == "other":
            embed = discord.Embed(title="Bienvenue dans ton ticket 💬", description="Explique-nous ta demande ici !", color=discord.Color.blurple())
            await ticket_channel.send(embed=embed)
            PARTNER_REQUESTS[ticket_channel.id] = {"requester_id": interaction.user.id, "subject": "Autres", "status": "open"}
        else:
            # ajout d'un bouton pour ouvrir le modal
            view = View()
            btn = Button(label="Remplir la demande", style=discord.ButtonStyle.primary)
            async def btn_callback(interaction_: discord.Interaction):
                await interaction_.response.send_modal(PartnershipModal(ticket_channel.id))
            btn.callback = btn_callback
            view.add_item(btn)
            embed = discord.Embed(title="Demande de Partenariat", description="Clique sur le bouton ci-dessous pour remplir la demande.", color=discord.Color.gold())
            await ticket_channel.send(embed=embed, view=view)

class PartnershipDecisionView(View):
    def __init__(self, ticket_channel_id: int):
        super().__init__(timeout=None)
        self.ticket_channel_id = ticket_channel_id
        accept_btn = Button(style=discord.ButtonStyle.success, label="Accepter")
        refuse_btn = Button(style=discord.ButtonStyle.danger, label="Refuser")
        accept_btn.callback = self.accept_callback
        refuse_btn.callback = self.refuse_callback
        self.add_item(accept_btn)
        self.add_item(refuse_btn)

    async def accept_callback(self, interaction: discord.Interaction):
        PARTNER_REQUESTS[self.ticket_channel_id]["status"] = "accepted"
        await interaction.response.send_message("✅ Partenariat accepté.", ephemeral=False)

    async def refuse_callback(self, interaction: discord.Interaction):
        PARTNER_REQUESTS[self.ticket_channel_id]["status"] = "refused"
        await interaction.response.send_message("❌ Partenariat refusé.", ephemeral=False)

# ---------------- DEPLOY MENU ----------------
async def deploy_partnership_menu(bot: commands.Bot):
    try:
        channel = bot.get_channel(CONTACTS_CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(CONTACTS_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            logger.warning(f"Le channel {CONTACTS_CHANNEL_ID} n'est pas un TextChannel")
            return
        embed = discord.Embed(title="Contact - Partenariats", description="Choisissez une option ci-dessous :", color=discord.Color.blurple())
        view = PartnershipSelectView()
        await clean_and_send(channel, embed=embed, view=view)
        logger.info("✅ Menu de partenariats déployé.")
    except Exception:
        logger.exception("Erreur lors du déploiement du menu de partenariats.")

def schedule_deploy(bot: commands.Bot):
    bot.loop.create_task(deploy_partnership_menu(bot))
