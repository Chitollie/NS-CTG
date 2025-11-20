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
    from bot.config import TICKETS_CATEGORY_ID, CONTRACTS_DATA_CHANNEL_ID, FORUM_CHANNEL_ID, GRADE_DR
except Exception:
    # si manquent, on définit des fallback pour éviter les ImportError
    TICKETS_CATEGORY_ID = None
    CONTRACTS_DATA_CHANNEL_ID = None
    FORUM_CHANNEL_ID = None
    # GRADE_DR doit exister normalement ; sinon on met vide
    try:
        GRADE_DR  # type: ignore
    except NameError:
        GRADE_DR = []

logger = logging.getLogger("partnerships_view")
logger.setLevel(logging.INFO)

# Stockage en mémoire de l'état des demandes (simple persist en mémoire)
PARTNER_REQUESTS: Dict[int, Dict[str, Any]] = {}
# Clés:
# ticket_channel_id -> {
#   "requester_id": int,
#   "company_name": str,
#   "pdg_id": int,
#   "pdg_display": str,
#   "pdg_info": { ... },  # formulaire pdg
#   "direction_info": { ... }, # formulaire direction
#   "status": "pending" | "accepted" | "refused" | "signed"
# }

# ------------------------------
# Modals
# ------------------------------
class PartnershipModal(Modal):
    """Modal pour la première demande de partenariat (PDG info)"""
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
        # Renvoyé au caller pour gestion par le view
        self.custom_result = {
            "first_name": self.first_name.value.strip(),
            "last_name": self.last_name.value.strip(),
            "pdg_id": self.pdg_id.value.strip(),
            "company_name": self.company_name.value.strip(),
            "company_type": self.company_type.value.strip(),
        }
        # stocker temporairement sur l'interaction pour que la view récupère la donnée
        interaction.client._last_partnership_modal = (interaction, self.custom_result)

class SimpleTicketModal(Modal):
    """Modal pour ticket simple (Autres) - demande rapide"""
    def __init__(self):
        super().__init__(title="Ticket - Information (Autres)")
        self.subject = TextInput(label="Sujet", placeholder="Titre succinct", required=True)
        self.description = TextInput(label="Description", style=discord.TextStyle.paragraph, placeholder="Expliquez votre demande", required=False)
        self.add_item(self.subject)
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        interaction.client._last_simple_ticket = (interaction, {
            "subject": self.subject.value.strip(),
            "description": self.description.value.strip()
        })


class QuestionnaireModal(Modal):
    """Modal pour questionnaire envoyé soit au PDG soit à la direction"""
    def __init__(self, title="Questionnaire - Partenariat"):
        super().__init__(title=title)
        self.presentation = TextInput(label="Présentation de l'entreprise", style=discord.TextStyle.paragraph, required=True)
        self.invite_link = TextInput(label="Lien d'invitation / site", placeholder="URL", required=True)
        self.reductions = TextInput(label="Réductions / Offres (facultatif)", required=False)
        self.expectations = TextInput(label="Ce que vous attendez (ou proposez)", style=discord.TextStyle.paragraph, required=False)
        self.more = TextInput(label="Autre chose à dire ?", style=discord.TextStyle.paragraph, required=False)

        self.add_item(self.presentation)
        self.add_item(self.invite_link)
        self.add_item(self.reductions)
        self.add_item(self.expectations)
        self.add_item(self.more)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        interaction.client._last_questionnaire = (interaction, {
            "presentation": self.presentation.value.strip(),
            "invite_link": self.invite_link.value.strip(),
            "reductions": self.reductions.value.strip(),
            "expectations": self.expectations.value.strip(),
            "more": self.more.value.strip(),
        })

# ------------------------------
# Views & Buttons
# ------------------------------
class PartnershipSelectView(View):
    """Vue principale placée dans CONTACTS_CHANNEL_ID"""
    def __init__(self):
        super().__init__(timeout=None)
        options = [
            discord.SelectOption(label="Demande de Partenariat", description="Remplir la demande de partenariat (PDG)", value="partnership"),
            discord.SelectOption(label="Autres", description="Ouvrir un ticket simple", value="other"),
        ]
        self.add_item(Select(placeholder="Que souhaitez-vous ?", min_values=1, max_values=1, options=options, custom_id="partnership_main_select",))

    @discord.ui.select(custom_id="partnership_main_select")
    async def on_select(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        choice = select.values[0]
        if choice == "other":
            modal = SimpleTicketModal()
            await interaction.response.send_modal(modal)
            # modal on_submit attaches result to interaction.client._last_simple_ticket
            # We wait a small moment for the modal to be processed
            await asyncio.sleep(0.2)
            result = getattr(interaction.client, "_last_simple_ticket", None)
            if result:
                _, data = result
                await create_simple_ticket(interaction.client, interaction.user, data["subject"], data["description"], interaction)
            else:
                await interaction.followup.send("❌ Une erreur est survenue lors de l'ouverture du ticket.", ephemeral=True)
        else:  # partnership
            modal = PartnershipModal()
            await interaction.response.send_modal(modal)
            await asyncio.sleep(0.2)
            last = getattr(interaction.client, "_last_partnership_modal", None)
            if last:
                _interaction, data = last
                # on crée le ticket et poste l'embed de demande
                await create_partnership_ticket(interaction.client, interaction.user, data, interaction)
            else:
                await interaction.followup.send("❌ Une erreur est survenue lors de l'envoi du formulaire.", ephemeral=True)


class PartnershipDecisionView(View):
    """View attachée au message initial du ticket pour la direction: Accepter / Refuser"""
    def __init__(self, ticket_channel_id: int):
        super().__init__(timeout=None)
        self.ticket_channel_id = ticket_channel_id
        self.add_item(Button(style=discord.ButtonStyle.success, label="Accepter", custom_id=f"part_accept_{ticket_channel_id}"))
        self.add_item(Button(style=discord.ButtonStyle.danger, label="Refuser", custom_id=f"part_refuse_{ticket_channel_id}"))

    @discord.ui.button(custom_id=None)
    async def _dummy(self, button: Button, interaction: discord.Interaction):
        # never used; we need explicit callbacks by custom_id handling below
        pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Allow only members in GRADE_DR to press - GRADE_DR contains user IDs ints
        if not hasattr(interaction.client, "user"):
            return False
        user_id = interaction.user.id
        if GRADE_DR and user_id not in GRADE_DR:
            await interaction.response.send_message("❌ Seuls les membres de la direction peuvent effectuer cette action.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        # optionally disable buttons on timeout
        for item in self.children:
            item.disabled = True

# We'll handle custom_id clicks in an event listener (below) because
# discord.ui.Button with dynamic custom_id callbacks are awkward to register inline.
# But we provide helpers to process accept/refuse.

# ------------------------------
# Helper functions
# ------------------------------
def _short_id() -> str:
    return str(random.randint(1000, 9999))

async def create_ticket_channel(guild: discord.Guild, name: str, requester: discord.Member) -> Optional[discord.TextChannel]:
    """Crée un channel ticket sous la catégorie si possible, sinon à la racine.
       Règle les permissions pour @everyone denié, requester allow, direction allow.
    """
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False, send_messages=False),
        requester: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
    }
    # ajouter overwrite pour chaque membre de GRADE_DR si fournie
    try:
        for did in GRADE_DR:
            member = guild.get_member(int(did))
            if member:
                overwrites[member] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
    except Exception:
        pass

    category = None
    if TICKETS_CATEGORY_ID:
        category = guild.get_channel(int(TICKETS_CATEGORY_ID))
        if not isinstance(category, discord.CategoryChannel):
            category = None

    try:
        channel_name = f"ticket-{name}-{_short_id()}"
        if category:
            chan = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        else:
            chan = await guild.create_text_channel(channel_name, overwrites=overwrites)
        return chan
    except Exception as e:
        logger.exception(f"Erreur création channel ticket: {e}")
        return None

async def create_simple_ticket(bot: discord.Client, user: discord.User, subject: str, description: str, interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
        await interaction.followup.send("❌ Impossible de créer le ticket : serveur introuvable.", ephemeral=True)
        return
    member = guild.get_member(user.id)
    chan = await create_ticket_channel(guild, "autres", member or user)
    if not chan:
        await interaction.followup.send("❌ Impossible de créer le ticket.", ephemeral=True)
        return

    embed = discord.Embed(title=f"Ticket: {subject}", description=description or "Aucune description fournie", color=discord.Color.blurple())
    embed.set_footer(text=f"Ouvert par {user} • ID {user.id}")
    await chan.send(embed=embed)
    await interaction.followup.send(f"✅ Ticket créé : {chan.mention}", ephemeral=True)
    # sauvegarde simple
    PARTNER_REQUESTS[chan.id] = {
        "requester_id": user.id,
        "subject": subject,
        "description": description,
        "status": "open",
    }

async def create_partnership_ticket(bot: discord.Client, user: discord.User, form_data: Dict[str, str], interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
        await interaction.followup.send("❌ Serveur introuvable.", ephemeral=True)
        return
    # Validate pdg id
    try:
        pdg_id_int = int(form_data["pdg_id"])
    except Exception:
        await interaction.followup.send("❌ L'ID Discord fourni pour le PDG est invalide.", ephemeral=True)
        return

    # create ticket
    member = guild.get_member(user.id)
    chan = await create_ticket_channel(guild, form_data["company_name"][:20].lower().replace(" ", "-"), member or user)
    if not chan:
        await interaction.followup.send("❌ Impossible de créer le ticket.", ephemeral=True)
        return

    # build embed with the request
    embed = discord.Embed(
        title=f"Demande de Partenariat — {form_data['company_name']}",
        description=f"**Type :** {form_data['company_type']}",
        color=discord.Color.gold()
    )
    embed.add_field(name="PDG", value=f"{form_data['first_name']} {form_data['last_name']} (<@{pdg_id_int})", inline=False)
    embed.add_field(name="ID PDG", value=str(pdg_id_int), inline=True)
    embed.add_field(name="Entreprise", value=form_data["company_name"], inline=True)
    embed.set_footer(text=f"Demandé par {user} • ID {user.id}")

    # message for direction -> includes decision buttons (view)
    decision_view = PartnershipDecisionView(chan.id)
    msg = await chan.send(embed=embed, view=decision_view)
    await interaction.followup.send(f"✅ Votre demande a été envoyée. Ticket : {chan.mention}", ephemeral=True)

    # store request
    PARTNER_REQUESTS[chan.id] = {
        "requester_id": user.id,
        "pdg_id": pdg_id_int,
        "pdg_display": f"{form_data['first_name']} {form_data['last_name']}",
        "company_name": form_data["company_name"],
        "company_type": form_data["company_type"],
        "request_embed_msg_id": msg.id,
        "status": "pending",
        "pdg_info": None,
        "direction_info": None,
    }

# ------------------------------
# Event handlers: custom_id handling for dynamic buttons
# ------------------------------
async def handle_button_interaction(interaction: discord.Interaction):
    """Doit être appelé depuis ton events.py -> on_interaction / on_component ou via cog."""
    # handle custom_id prefix
    cid = interaction.data.get("custom_id") if interaction.data else None
    if not cid:
        return

    # Accept / Refuse prefixed by part_accept_ or part_refuse_
    if cid.startswith("part_accept_") or cid.startswith("part_refuse_"):
        # extract channel id
        try:
            _, action, chan_id_s = cid.split("_", 2)
            chan_id = int(chan_id_s)
        except Exception:
            await interaction.response.send_message("Erreur interne (ID channel).", ephemeral=True)
            return

        # permission check: only direction allowed
        if GRADE_DR and interaction.user.id not in GRADE_DR:
            await interaction.response.send_message("❌ Seuls les membres de la direction peuvent faire ça.", ephemeral=True)
            return

        request = PARTNER_REQUESTS.get(chan_id)
        if not request:
            await interaction.response.send_message("❌ Demande introuvable.", ephemeral=True)
            return

        guild = interaction.guild
        channel = guild.get_channel(chan_id) if guild else None
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("❌ Channel introuvable.", ephemeral=True)
            return

        if action == "accept":
            # update status and post next step message
            request["status"] = "accepted"
            # post a message visible to channel (non éphémère) to send questionnaire
            q_view = View()
            btn_send_q = Button(label="Envoyer le questionnaire de confirmation", style=discord.ButtonStyle.primary, custom_id=f"send_q_{chan_id}")
            q_view.add_item(btn_send_q)
            await channel.send(
                content="✅ La direction a accepté la demande. Préparez le lien d'invitation permanente de votre site si besoin.",
                embed=discord.Embed(title="Envoyer le questionnaire de confirmation", description="Cliquez sur le bouton pour envoyer le questionnaire au PDG demandeur.", color=discord.Color.blue()),
                view=q_view
            )
            await interaction.response.send_message("✅ Demande acceptée et questionnaire prêt à être envoyé.", ephemeral=True)

        else:  # refuse
            request["status"] = "refused"
            # notify the requester by DM
            requester_id = request.get("requester_id")
            try:
                user = await interaction.client.fetch_user(requester_id)
                if user:
                    await user.send(f"❌ Votre demande de partenariat pour **{request.get('company_name','(entreprise)')}** a été refusée par la direction.")
            except Exception:
                pass
            await channel.send(embed=discord.Embed(title="Demande refusée", description="La direction a refusé cette demande.", color=discord.Color.red()))
            await interaction.response.send_message("✅ Demande refusée et le demandeur a été notifié.", ephemeral=True)

    elif cid.startswith("send_q_"):
        # direction clicked to send questionnaire to PDG
        try:
            _, chan_id_s = cid.split("_", 1)
            chan_id = int(chan_id_s)
        except Exception:
            await interaction.response.send_message("Erreur interne (ID channel).", ephemeral=True)
            return
        request = PARTNER_REQUESTS.get(chan_id)
        if not request:
            await interaction.response.send_message("❌ Demande introuvable.", ephemeral=True)
            return

        # send questionnaire modal to the PDG (via DM)
        pdg_id = request.get("pdg_id")
        try:
            pdg_user = await interaction.client.fetch_user(pdg_id)
            if not pdg_user:
                await interaction.response.send_message("❌ Impossible de retrouver le PDG (ID invalide).", ephemeral=True)
                return
            modal = QuestionnaireModal(title=f"Questionnaire - {request.get('company_name')}")
            # send as a modal to the PDG: we need an interaction with them -> can't directly send modal to arbitrary user
            # Alternative: DM the PDG with a message containing a button that opens the modal via a follow-up interaction with them.
            # Simpler: open the modal to the direction member and ask them to forward results AND we will also offer to send to PDG via DM message with button to allow PDG to open the modal.
            # We'll attempt to DM the PDG with instructions and a link-like message.
            # Send simple DM asking PDG to reply (fallback)
            try:
                dm = await pdg_user.create_dm()
                await dm.send(f"Bonjour, la direction vous demande de compléter le questionnaire de confirmation pour le partenariat **{request.get('company_name')}**.\nVeuillez répondre au message ci-dessous avec les informations demandées.")
                # we'll open a modal on the direction's side to collect PDG data? No — better pattern:
                # Send the modal to the direction contactor to fill the PDG-side on behalf if PDG can't open modal.
            except Exception:
                pass

            # - "Envoyer questionnaire au PDG (DM)" (attempt to DM instructions)
            # - "Remplir pour PDG" (la direction remplit le questionnaire pour le PDG ici)
            ch = interaction.guild.get_channel(chan_id)
            if not ch:
                await interaction.response.send_message("❌ Channel introuvable.", ephemeral=True)
                return

            q_view = View()
            btn_dm_pdg = Button(label="Envoyer questionnaire au PDG (DM)", style=discord.ButtonStyle.secondary, custom_id=f"dm_pdg_{chan_id}")
            btn_fill_for_pdg = Button(label="Remplir pour le PDG", style=discord.ButtonStyle.primary, custom_id=f"fill_pdg_{chan_id}")
            q_view.add_item(btn_dm_pdg)
            q_view.add_item(btn_fill_for_pdg)
            await ch.send(embed=discord.Embed(title="Action requise: envoyer questionnaire", description="Envoyez le questionnaire au PDG ou remplissez-le pour lui.", color=discord.Color.greyple()), view=q_view)
            await interaction.response.send_message("✅ Options envoyées dans le ticket.", ephemeral=True)
        except Exception as e:
            logger.exception(f"Erreur send_q_: {e}")
            await interaction.response.send_message("Erreur interne.", ephemeral=True)

    elif cid.startswith("dm_pdg_"):
        try:
            _, chan_id_s = cid.split("_", 1)
            chan_id = int(chan_id_s)
            req = PARTNER_REQUESTS.get(chan_id)
            if not req:
                await interaction.response.send_message("Demande introuvable.", ephemeral=True)
                return
            pdg_id = req.get("pdg_id")
            pdg_user = await interaction.client.fetch_user(pdg_id)
            if not pdg_user:
                await interaction.response.send_message("PDG introuvable (ID invalide).", ephemeral=True)
                return
            q_msg = (
                "Bonjour, merci d'avoir contacté notre direction.\n"
                "Veuillez répondre à ce message en fournissant :\n"
                "1) Présentation de l'entreprise\n"
                "2) Lien / site\n"
                "3) Réductions / offres (facultatif)\n"
                "4) Ce que vous attendez\n"
                "5) Autre (facultatif)\n\n"
                "Vous pouvez copier/coller vos réponses ou envoyer plusieurs messages."
            )
            await pdg_user.send(q_msg)
            await interaction.response.send_message("✅ DM envoyé au PDG (si possible).", ephemeral=True)
        except Exception as e:
            logger.exception(f"Erreur dm_pdg_: {e}")
            await interaction.response.send_message("Erreur lors de l'envoi du DM.", ephemeral=True)

    elif cid.startswith("fill_pdg_") or cid.startswith("fill_dir_"):
        try:
            _, chan_id_s = cid.split("_", 1)
            chan_id = int(chan_id_s)
            modal = QuestionnaireModal(title="Questionnaire - Remplissez les champs")
            await interaction.response.send_modal(modal)
            await asyncio.sleep(0.2)
            last = getattr(interaction.client, "_last_questionnaire", None)
            if not last:
                await interaction.followup.send("❌ Aucun résultat reçu du questionnaire.", ephemeral=True)
                return
            _int, answers = last
            request = PARTNER_REQUESTS.get(chan_id)
            if not request:
                await interaction.followup.send("❌ Demande introuvable.", ephemeral=True)
                return
            if cid.startswith("fill_pdg_"):
                request["pdg_info"] = answers
                await interaction.followup.send("✅ Questionnaire (PDG) enregistré.", ephemeral=True)
                ch = interaction.guild.get_channel(chan_id)
                if ch:
                    em = discord.Embed(title="Questionnaire - Réponses PDG", color=discord.Color.green())
                    em.add_field(name="Présentation", value=answers.get("presentation","Aucun"), inline=False)
                    em.add_field(name="Lien", value=answers.get("invite_link","Aucun"), inline=False)
                    em.add_field(name="Réductions", value=answers.get("reductions","Aucun"), inline=False)
                    em.add_field(name="Attentes", value=answers.get("expectations","Aucun"), inline=False)
                    em.add_field(name="Autre", value=answers.get("more","Aucun"), inline=False)
                    await ch.send(embed=em)
            else:
                request["direction_info"] = answers
                await interaction.followup.send("✅ Questionnaire (Direction) enregistré.", ephemeral=True)
                ch = interaction.guild.get_channel(chan_id)
                if ch:
                    em = discord.Embed(title="Questionnaire - Réponses Direction", color=discord.Color.orange())
                    em.add_field(name="Présentation (Direction)", value=answers.get("presentation","Aucun"), inline=False)
                    em.add_field(name="Lien", value=answers.get("invite_link","Aucun"), inline=False)
                    em.add_field(name="Réductions", value=answers.get("reductions","Aucun"), inline=False)
                    em.add_field(name="Attentes", value=answers.get("expectations","Aucun"), inline=False)
                    em.add_field(name="Autre", value=answers.get("more","Aucun"), inline=False)
                    await ch.send(embed=em)
            if request.get("pdg_info") and request.get("direction_info"):
                sign_view = View()
                btn_sign = Button(label="Signer", style=discord.ButtonStyle.success, custom_id=f"sign_{chan_id}")
                btn_cancel = Button(label="Refuser / Annuler", style=discord.ButtonStyle.danger, custom_id=f"cancel_{chan_id}")
                sign_view.add_item(btn_sign)
                sign_view.add_item(btn_cancel)
                ch = interaction.guild.get_channel(chan_id)
                if ch:
                    await ch.send(embed=discord.Embed(title="Les deux parties ont envoyé les informations. Signer le contrat ?", color=discord.Color.brand_green()), view=sign_view)
        except Exception as e:
            logger.exception(f"Erreur fill_pdg_/fill_dir_: {e}")
            await interaction.response.send_message("Erreur interne lors de l'ouverture du questionnaire.", ephemeral=True)

    elif cid.startswith("sign_") or cid.startswith("cancel_"):
        try:
            action, chan_id_s = cid.split("_", 1)
            chan_id = int(chan_id_s)
            request = PARTNER_REQUESTS.get(chan_id)
            if not request:
                await interaction.response.send_message("Demande introuvable.", ephemeral=True)
                return
            guild = interaction.guild
            ch = guild.get_channel(chan_id)
            if not ch:
                await interaction.response.send_message("Channel introuvable.", ephemeral=True)
                return

            if action == "sign":
                request["status"] = "signed"
                pdg_id = request.get("pdg_id")
                requester = request.get("requester_id")
                em = discord.Embed(title=f"Contrat signé — {request.get('company_name')}", color=discord.Color.green())
                em.add_field(name="Entreprise", value=request.get("company_name","N/A"), inline=False)
                em.add_field(name="PDG", value=f"{request.get('pdg_display','N/A')} (<@{pdg_id}>)", inline=False)
                em.add_field(name="PDG - Partie", value=str(request.get("pdg_info") or "N/A"), inline=False)
                em.add_field(name="Notre partie", value=str(request.get("direction_info") or "N/A"), inline=False)
                try:
                    pdg_user = await interaction.client.fetch_user(pdg_id)
                    if pdg_user:
                        await pdg_user.send(embed=em)
                except Exception:
                    pass
                if CONTRACTS_DATA_CHANNEL_ID:
                    try:
                        target = guild.get_channel(int(CONTRACTS_DATA_CHANNEL_ID))
                        if isinstance(target, discord.TextChannel):
                            await target.send(embed=em)
                    except Exception:
                        logger.exception("Erreur envoi contrat au channel de stockage")
                if FORUM_CHANNEL_ID:
                    try:
                        forum = guild.get_channel(int(FORUM_CHANNEL_ID))
                        if isinstance(forum, discord.TextChannel):
                            thread = await forum.create_thread(name=request.get("company_name","partenariat"), message=None)
                            await thread.send(f"Présentation de {request.get('company_name')}\n{request.get('pdg_info',{}).get('presentation','')}\nLien: {request.get('pdg_info',{}).get('invite_link','')}")
                    except Exception:
                        logger.exception("Erreur création post/forum")
                await ch.send(embed=discord.Embed(title="Contrat signé ✓", description="Le contrat a été signé et les parties ont été notifiées.", color=discord.Color.green()))
                await interaction.response.send_message("✅ Contrat signé.", ephemeral=True)
            else:
                request["status"] = "cancelled"
                pdg_id = request.get("pdg_id")
                try:
                    pdg_user = await interaction.client.fetch_user(pdg_id)
                    if pdg_user:
                        await pdg_user.send(f"❌ Le processus de signature pour **{request.get('company_name')}** a été annulé par la direction.")
                except Exception:
                    pass
                await ch.send(embed=discord.Embed(title="Processus annulé", description="La direction a annulé/le refusé.", color=discord.Color.red()))
                await interaction.response.send_message("✅ Processus annulé.", ephemeral=True)
        except Exception as e:
            logger.exception(f"Erreur sign/cancel: {e}")
            await interaction.response.send_message("Erreur interne.", ephemeral=True)


async def deploy_partnership_menu(bot: discord.Client):
    """Call this once on startup to post the main menu in CONTACTS_CHANNEL_ID (or re-post manually)."""
    try:
        guilds = bot.guilds
        if not guilds:
            logger.warning("Bot not in any guilds.")
            return

        target_channel = None
        for g in guilds:
            ch = g.get_channel(int(CONTACTS_CHANNEL_ID))
            if ch:
                target_channel = ch
                guild = g
                break
        if not target_channel:
            logger.warning("CONTACTS_CHANNEL_ID introuvable dans les guilds du bot.")
            return
        view = PartnershipSelectView()
        embed = discord.Embed(
            title="Contact - Partenariats",
            description="Choisissez une option dans le menu ci-dessous.",
            color=discord.Color.blurple()
        )
        await target_channel.send(embed=embed, view=view)
        logger.info("Menu de partenariats déployé.")
    except Exception:
        logger.exception("Erreur deploy_partnership_menu")
