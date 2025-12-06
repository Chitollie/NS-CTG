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

        #base = 20000
        rate_min = 10000
        rate_max = 15000

        low = ((nb_agents * rate_min) * t) * 1.3
        high = ((nb_agents * rate_max) * t) * 1.3

        def round_up_thousand(n):
            return int(math.ceil(n / 1000.0) * 1000)

        low_r = round_up_thousand(low)
        high_r = round_up_thousand(high)

        await interaction.response.send_message(
            f"💸 Estimation pour {nb_agents} agent(s) pendant {minutes} minutes :\n"
            f"• Fourchette : {low_r:,} — {high_r:,} $\n"
            f"(basée sur {rate_min:,}$/30min à {rate_max:,}$/30min et majoration x1.3)",
            ephemeral=True
        )
