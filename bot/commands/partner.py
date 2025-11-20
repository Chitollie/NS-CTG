import discord
from discord import app_commands
from discord.ui import View, Select, Button, Modal, TextInput
from typing import Dict, Any, Optional
import random
import asyncio
import logging

from bot.config import (
    CONTACTS_CHANNEL_ID,
    TICKETS_CATEGORY_ID,
    CONTRACTS_DATA_CHANNEL_ID,
    FORUM_CHANNEL_ID,
    GRADE_DR,
)
try:
    from bot.config import TICKETS_CATEGORY_ID, CONTRACTS_DATA_CHANNEL_ID, FORUM_CHANNEL_ID, GRADE_DR, CONTACTS_CHANNEL_ID
except Exception:
    TICKETS_CATEGORY_ID = None
    CONTRACTS_DATA_CHANNEL_ID = None
    FORUM_CHANNEL_ID = None
    try:
        GRADE_DR
    except NameError:
        GRADE_DR = []

logger = logging.getLogger("partnerships_view")
logger.setLevel(logging.INFO)

# ---------------------- CLEAN & SEND POUR LE MENU SELECT ----------------------
_last_contact_message: Dict[int, int] = {} 

async def clean_and_send(channel: discord.TextChannel, content: Optional[str] = None, *, embed: Optional[discord.Embed] = None, view: Optional[discord.ui.View] = None):
    """
    Envoie ou édite le message du menu select dans CONTACTS_CHANNEL_ID.
    (Minimal — conserve uniquement l'id du message pour l'éditer)
    """
    msg = None
    last_id = _last_contact_message.get(channel.id)

    if last_id:
        try:
            prev = await channel.fetch_message(last_id)
            await prev.edit(content=content, embed=embed, view=view)
            msg = prev
        except Exception as e:
            logger.warning(f"Impossible d'éditer le dernier message : {e}")

    if msg is None:
        try:
            msg = await channel.send(content=content, embed=embed, view=view)
            _last_contact_message[channel.id] = msg.id
        except Exception as e:
            logger.exception(f"Impossible d'envoyer le message dans le channel {channel.id}: {e}")

    return msg

# ------------------------------ PARTNER REQUESTS ------------------------------
PARTNER_REQUESTS: Dict[int, Dict[str, Any]] = {}

# ------------------------------ Modals ------------------------------
class PartnershipModal(Modal):
    def __init__(self):
        super().__init__(title="Demande de Partenariat - Informations")
        self.first_name = TextInput(label="Prénom du PDG", placeholder="Prénom", required=True, max_length=64)
        self.last_name = TextInput(label="Nom du PDG", placeholder="Nom", required=True, max_length=64)
        self.pdg_id = TextInput(label="ID Discord du PDG", placeholder="7254...", required=True, max_length=30)
        self.company_name = TextInput(label="Nom de l'entreprise", placeholder="Ex: Club XYZ", required=True, max_length=100)
        self.company_type = TextInput(label="Type (bar, boutique...)", placeholder="Ex: Bar / Boutique / Service", required=True, max_length=64)
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
        interaction.client._last_partnership_modal = (interaction, result)

        chan_id = getattr(interaction.client, "_pending_partner_channel", None)
        if chan_id:
            guild = interaction.guild or (interaction.client.guilds[0] if interaction.client.guilds else None)
            channel = None
            if guild:
                channel = guild.get_channel(int(chan_id))
                if channel is None:
                    try:
                        channel = await interaction.client.fetch_channel(int(chan_id))
                    except Exception:
                        channel = None

            if channel and isinstance(channel, discord.TextChannel):
                try:
                    pdg_id_int = int(result["pdg_id"])
                except Exception:
                    pdg_id_int = None

                embed = discord.Embed(
                    title=f"Demande de Partenariat — {result['company_name']}",
                    description=f"**Type :** {result['company_type']}",
                    color=discord.Color.gold()
                )
                pdg_field_value = f"{result['first_name']} {result['last_name']}"
                if pdg_id_int:
                    pdg_field_value += f" (<@{pdg_id_int}>)"
                embed.add_field(name="PDG", value=pdg_field_value, inline=False)
                embed.add_field(name="ID PDG", value=str(result['pdg_id']), inline=True)
                embed.add_field(name="Entreprise", value=result["company_name"], inline=True)
                embed.set_footer(text=f"Demandé par {interaction.user} • ID {interaction.user.id}")

                decision_view = PartnershipDecisionView(channel.id)
                msg = await channel.send(embed=embed, view=decision_view)

                PARTNER_REQUESTS[channel.id] = {
                    "requester_id": interaction.user.id,
                    "pdg_id": pdg_id_int,
                    "pdg_display": f"{result['first_name']} {result['last_name']}",
                    "company_name": result["company_name"],
                    "company_type": result["company_type"],
                    "request_embed_msg_id": msg.id,
                    "status": "pending",
                    "pdg_info": None,
                    "direction_info": None,
                }

                try:
                    del interaction.client._pending_partner_channel
                except Exception:
                    pass

                try:
                    await interaction.followup.send("✅ Votre demande a été postée dans le ticket.", ephemeral=True)
                except Exception:
                    pass
                return

        await interaction.followup.send("✅ Données reçues. Une action manuelle est peut-être nécessaire pour les publier.", ephemeral=True)

# ------------------------------ Views ------------------------------
class PartnershipSelectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        options = [
            discord.SelectOption(label="Demande de Partenariat", description="Remplir la demande de partenariat (PDG)", value="partnership"),
            discord.SelectOption(label="Autres", description="Ouvrir un ticket simple", value="other"),
        ]
        self.add_item(Select(
            placeholder="Que souhaitez-vous ?",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="partnership_main_select",
        ))

    @discord.ui.select(custom_id="partnership_main_select")
    async def on_select(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        choice = select.values[0]
        guild = interaction.guild
        member = guild.get_member(interaction.user.id) or interaction.user
        chan = await create_ticket_channel(guild, "demande" if choice == "partnership" else "autres", member)
        if not chan:
            await interaction.followup.send("❌ Impossible de créer le ticket.", ephemeral=True)
            return
        await interaction.followup.send(f"✅ Ticket créé : {chan.mention}", ephemeral=True)
        if choice == "other":
            embed = discord.Embed(
                title="Bienvenue dans ton ticket 💬",
                description="Explique-nous ta demande et nous reviendrons vers toi !",
                color=discord.Color.blurple()
            )
            await chan.send(embed=embed)
            PARTNER_REQUESTS[chan.id] = {"requester_id": interaction.user.id, "subject": "Autres", "description": None, "status": "open"}
            return
        await start_partner_flow(chan, interaction.user, interaction.client)

class PartnershipDecisionView(View):
    def __init__(self, ticket_channel_id: int):
        super().__init__(timeout=None)
        self.ticket_channel_id = ticket_channel_id
        self.add_item(Button(style=discord.ButtonStyle.success, label="Accepter", custom_id=f"part_accept_{ticket_channel_id}"))
        self.add_item(Button(style=discord.ButtonStyle.danger, label="Refuser", custom_id=f"part_refuse_{ticket_channel_id}"))

# ------------------------------ Helpers ------------------------------
def _short_id() -> str:
    return str(random.randint(1000, 9999))

async def create_ticket_channel(guild: discord.Guild, name: str, requester: discord.Member) -> Optional[discord.TextChannel]:
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False, send_messages=False),
        requester: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
    }
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

async def start_partner_flow(ticket_channel: discord.TextChannel, opener_user: discord.User, bot_client: discord.Client):
    try:
        embed = discord.Embed(
            title="Demande de Partenariat - Étapes",
            description=(
                "Bienvenue ! Pour lancer la demande de partenariat, cliquez sur **Remplir la demande** "
                "et remplissez les informations du PDG (ou remplissez au nom du PDG)."
            ),
            color=discord.Color.gold()
        )
        view = View()
        btn = Button(label="Remplir la demande", style=discord.ButtonStyle.primary, custom_id=f"start_partner_modal_{ticket_channel.id}")
        view.add_item(btn)
        await ticket_channel.send(content=f"Bonjour {opener_user.mention} — démarrez la demande ci-dessous :", embed=embed, view=view)
        PARTNER_REQUESTS[ticket_channel.id] = {
            "requester_id": opener_user.id, "status": "open", "company_name": None, "pdg_id": None,
            "pdg_display": None, "pdg_info": None, "direction_info": None
        }
    except Exception as e:
        logger.exception(f"Erreur start_partner_flow: {e}")
        try:
            await ticket_channel.send("❌ Une erreur est survenue lors du démarrage du flux partenaire.")
        except Exception:
            pass

# ------------------------------ DEPLOY MENU ------------------------------
async def deploy_partnership_menu(bot: discord.Client):
    """Call this once on startup to post the main menu in CONTACTS_CHANNEL_ID"""
    try:
        target_channel = bot.get_channel(int(CONTACTS_CHANNEL_ID))
        if target_channel is None:
            try:
                target_channel = await bot.fetch_channel(int(CONTACTS_CHANNEL_ID))
            except Exception as e:
                logger.exception(f"Impossible de fetcher le channel {CONTACTS_CHANNEL_ID}: {e}")
                return
        if not isinstance(target_channel, discord.TextChannel):
            logger.warning(f"Le channel {CONTACTS_CHANNEL_ID} n'est pas un TextChannel")
            return
        embed = discord.Embed(
            title="Contact - Partenariats",
            description="Choisissez une option dans le menu ci-dessous.",
            color=discord.Color.blurple()
        )
        view = PartnershipSelectView()
        msg = await clean_and_send(target_channel, content=None, embed=embed, view=view)
        if msg:
            logger.info("✅ Menu de partenariats déployé.")
        else:
            logger.warning("⚠️ Le message n'a pas pu être envoyé")
    except Exception:
        logger.exception("Erreur deploy_partnership_menu")

# Pour planifier le déploiement après que le bot soit ready :
def schedule_deploy(bot: discord.Client):
    bot.loop.create_task(deploy_partnership_menu(bot))
