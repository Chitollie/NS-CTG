import discord
from discord.ui import View, Select
from .modals import DemandeAgentsModal

class MenuSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Demande d'agents", description="Faire une demande de personnel"),
            discord.SelectOption(label="Infos sur nos services", description="Voir les services proposés"),
            discord.SelectOption(label="Contacter un consultant", description="Être mis en relation"),
        ]
        super().__init__(placeholder="Choisis une option...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Demande d'agents":
            await interaction.response.send_modal(DemandeAgentsModal())
        elif self.values[0] == "Infos sur nos services":
            await interaction.response.send_message(
                "ℹ️ Nos services incluent la sécurité événementielle, la protection rapprochée et plus.", ephemeral=True
            )
        elif self.values[0] == "Contacter un consultant":
            await interaction.response.send_message("👔 Un consultant va te recontacter bientôt.", ephemeral=True)

class MenuView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MenuSelect())
