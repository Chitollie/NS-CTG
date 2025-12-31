import discord
from discord.ui import Modal, TextInput
import math

class TarifsModal(Modal, title="Simulation de tarif"):
    duree_minutes = TextInput(label="Durée de la mission (minutes)", placeholder="Ex: 90")
    nb_agents = TextInput(label="Nombre total d'agents nécessaires", placeholder="Ex: 4")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            minutes = int(self.duree_minutes.value)
            nb_agents = int(self.nb_agents.value)
        except ValueError:
            await interaction.response.send_message("❌ Tous les champs numériques doivent être des nombres entiers.", ephemeral=True)
            return

        if minutes <= 0 or nb_agents < 0:
            await interaction.response.send_message("❌ La durée doit être positive et le nombre d'agents nul ou positif.", ephemeral=True)
            return

        t = max(1, math.ceil(minutes / 30))

        base_rate = 10000
        t = max(1, math.ceil(minutes / 30))
        total = t * nb_agents * base_rate


        total_with_percentage = total * 1.3

        def round_up_thousand(n):
            return int(math.ceil(n / 1000.0) * 1000)

        final_price = round_up_thousand(total_with_percentage)


        await interaction.response.send_message(
            f"💸 Estimation pour {nb_agents} agent(s) pendant {minutes} minutes :\n"
            f"• Prix : {final_price:,} $",
            ephemeral=True
        )

