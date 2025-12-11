import discord
from discord.ui import View, Select, Button
from .tickets import create_ticket_channel, clean_and_send
import os
from dotenv import load_dotenv

load_dotenv()
TICKETS_CATEGORY_ID = int(os.getenv("TICKETS_CATEGORY_ID", 0))

AGENTS = {
    "Alina Wolf": {"role": "PDG", "numero": "59669-70941", "discord_id": 725425681177247908},
    "Brian Stanford": {"role": "Co-PDG", "numero": "59783-70510", "discord_id": 1263956791818195087},
    #"Brice Roca": {"role": "Directeur", "numero": "59158-69882", "discord_id": 471721415574290432},
}


# === VIEWS ===
class ContactView(View):
    def __init__(self, agent_name: str):
        super().__init__(timeout=None)
        self.agent_name = agent_name
        self.agent_data = AGENTS[agent_name]

        discord_id = self.agent_data["discord_id"]
        self.add_item(Button(label="📨 Email", style=discord.ButtonStyle.link, url=f"https://discord.com/users/{discord_id}"))

    @discord.ui.button(label="📞 Numéro", style=discord.ButtonStyle.primary)
    async def numero(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(f"**Numéro de {self.agent_name} :** `{self.agent_data['numero']}`", ephemeral=True)

    @discord.ui.button(label="🎟️ Ticket", style=discord.ButtonStyle.success)
    async def ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        user = interaction.user
        ticket_channel = await create_ticket_channel(guild, user.name.lower(), user, category_id=TICKETS_CATEGORY_ID)
        if ticket_channel:
            embed = discord.Embed(
                title=f"🎟️ Ticket Ouvert - {self.agent_name}",
                description=f"Salut {user.mention} ! 👋\nTu contactes **{self.agent_name}**, {self.agent_data['role']}.\nExplique ta demande ici.",
                color=discord.Color.purple()
            )
            await ticket_channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Ticket créé : {ticket_channel.mention}", ephemeral=True)

class MenuSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=name, description=data["role"], value=name)
            for name, data in AGENTS.items()
        ]
        super().__init__(placeholder="Choisis un agent à contacter...", options=options)

    async def callback(self, interaction: discord.Interaction):
        agent_name = self.values[0]
        embed = discord.Embed(title=f"📇 Contact : {agent_name}", description="Choisis une option ci-dessous 👇", color=discord.Color.purple())
        embed.add_field(name="Rôle", value=AGENTS[agent_name]["role"], inline=False)
        await interaction.response.send_message(embed=embed, view=ContactView(agent_name), ephemeral=True)

class MenuView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MenuSelect())

async def send_contact_menu(interaction: discord.Interaction):
    await interaction.response.send_message(
        "📞 Choisis une personne à contacter :",
        view=MenuView(),
        ephemeral=True
    )
