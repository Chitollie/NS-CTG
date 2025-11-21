# contact_main.py
import discord
from discord.ext import commands
from discord.ui import View, Select
from tickets import create_ticket_channel
from partner import PartnershipModal
from contact_agents import send_contact_menu
from utils.auto_message import clean_and_send  # <-- ton script auto_message
import os
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
            ticket_channel = await create_ticket_channel(interaction.guild, "partnership", interaction.user)
            if ticket_channel:
                await interaction.response.send_modal(PartnershipModal(ticket_channel.id))

        elif choice == "other":
            ticket_channel = await create_ticket_channel(interaction.guild, "other", interaction.user)
            if ticket_channel:
                embed = discord.Embed(
                    title="Bienvenue dans ton ticket 💬",
                    description="Explique-nous ta demande ici !",
                    color=discord.Color.blurple()
                )
                await ticket_channel.send(embed=embed)
                await interaction.response.send_message(f"✅ Ticket créé : {ticket_channel.mention}", ephemeral=True)

        elif choice == "contact_agent":
            await send_contact_menu(interaction)

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
