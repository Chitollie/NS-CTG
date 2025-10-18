import discord
from discord.ui import Modal, TextInput
import math

class TarifsModal(Modal, title="Simulation de tarif"):
    duree_minutes = TextInput(label="Durée de la mission (minutes)", placeholder="Ex: 90")
    nb_recrues = TextInput(label="Nombre de recrues", placeholder="Ex: 4")
    nb_agents = TextInput(label="Nombre d'agents confirmés", placeholder="Ex: 0")
    nb_responsables = TextInput(label="Nombre de responsables", placeholder="Ex: 1")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            minutes = int(self.duree_minutes.value)
            x = int(self.nb_recrues.value)
            y = int(self.nb_agents.value)
            z = int(self.nb_responsables.value)
        except ValueError:
            await interaction.response.send_message("❌ Tous les champs numériques doivent être des nombres entiers.", ephemeral=True)
            return

        # calcule T = temps / 30min
        t = max(1, math.ceil(minutes / 30))

        # formule fournie: 50000+(((X×10000+Y×12500+Z×15000)×T)×1.3)
        base = 50000
        min_component = (x * 10000 + 0 * 12500 + 0 * 15000)
        max_component = (0 * 10000 + y * 12500 + z * 15000)

        # However the user asked for range from 'all recruits' to 'all responsables', so compute two extremes:
        low = base + (((x * 10000 + 0 + 0) * t) * 1.3)
        high = base + (((0 + y * 12500 + z * 15000) * t) * 1.3)

        # Round to thousands
        def round_thousand(n):
            return int(round(n / 1000.0) * 1000)

        low_r = round_thousand(low)
        high_r = round_thousand(high)

        # Ensure low <= high
        if low_r > high_r:
            low_r, high_r = high_r, low_r

        await interaction.response.send_message(f"💸 Estimation : De {low_r:,} à {high_r:,}", ephemeral=True)
