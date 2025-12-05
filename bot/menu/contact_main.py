import os
import discord
from discord.ext import commands
from discord.ui import View, Select
from .tickets import create_ticket_channel
from .partner import PartnershipModal
from .contact_agents import send_contact_menu
from bot.utils.auto_messages import clean_and_send
from dotenv import load_dotenv

load_dotenv()
CONTACTS_CHANNEL_ID = int(os.getenv("CONTACTS_CHANNEL_ID", 0))

# ----------------- MENU -----------------
class MainMenuSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Demande de Partenariat", description="Créer une demande de partenariat", value="partnership"),
            discord.SelectOption(label="Autres tickets", description="Créer un ticket classique", value="other"),
            discord.SelectOption(label="Contacter un agent", description="Voir la liste des agents à contacter", value="contact_agent")
        ]
        super().__init__(placeholder="Choisis une option...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]

        if choice == "partnership":
            # créer modal / ouvrir modal de partenariat
            await interaction.response.send_modal(PartnershipModal())
            return

        elif choice == "other":
            # créer un ticket classique
            await create_ticket_channel(interaction)
            return

        elif choice == "contact_agent":
            # afficher le menu de contact agents
            await send_contact_menu(interaction)
            return

class MainMenuView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MainMenuSelect())

# ----------------- DEPLOIEMENT -----------------
async def deploy_contact_main(bot: commands.Bot):
    channel = bot.get_channel(CONTACTS_CHANNEL_ID) or await bot.fetch_channel(CONTACTS_CHANNEL_ID)

    embed = discord.Embed(
        title="Nous contacter",
        description="Choisis une option dans le menu ci-dessous :",
        color=discord.Color.blurple()
    )
    view = MainMenuView()

    await clean_and_send(channel, embed=embed, view=view)

# ----------------- SETUP -----------------
async def setup(bot: commands.Bot):
    """
    Enregistre la View persistante au démarrage.
    Si CONTACTS_AUTO_DEPLOY=1 dans le .env, déploie aussi le message via clean_and_send.
    """
    try:
        # Enregistrer la View pour que les callbacks persistent après un redémarrage
        bot.add_view(MainMenuView())
    except Exception as e:
        print(f"⚠️ Erreur enregistrement MainMenuView: {e}")

    # Optionnel : déployer le message au démarrage si explicitement demandé
    try:
        if os.getenv("CONTACTS_AUTO_DEPLOY", "0") == "1":
            await deploy_contact_main(bot)
    except Exception as e:
        print(f"⚠️ Erreur lors du déploiement du menu contacts: {e}")
