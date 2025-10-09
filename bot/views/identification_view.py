import discord
from discord.ui import View, button
from .modals import IdentificationModal

class IdentificationButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="S'identifier", style=discord.ButtonStyle.primary, custom_id="ident_button")
    async def ident_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(IdentificationModal())
