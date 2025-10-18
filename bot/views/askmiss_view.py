import discord
from discord.ui import View, button
from .modals import DemandeAgentsModal

class AskMissView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Faire une demande d'agents", style=discord.ButtonStyle.primary, custom_id="askmiss_button")
    async def askmiss_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DemandeAgentsModal())
