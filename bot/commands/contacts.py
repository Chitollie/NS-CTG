import discord
from discord.ui import View, Select, Button

# === CONFIGURATION ===
AGENTS = {
    "Alina Wolf": {"role": "PDG", "numero": "59669-70941", "discord_id": 725425681177247908},
    "Brian Stanford": {"role": "Co-PDG", "numero": "59783-70510", "discord_id": 1263956791818195087},
    "Brice Roca": {"role": "Directeur", "numero": "59158-69882", "discord_id": 471721415574290432}
}

TICKETS_CATEGORY_ID = 1426797063164788808

# === VIEW AVEC LES BOUTONS DE CONTACT ===
class ContactView(View):
    def __init__(self, agent_name: str):
        super().__init__(timeout=None)
        self.agent_name = agent_name
        self.agent_data = AGENTS[agent_name]

        discord_id = self.agent_data["discord_id"]
        self.add_item(Button(label="📨 Discord", style=discord.ButtonStyle.link, url=f"https://discord.com/users/{discord_id}"))

    @discord.ui.button(label="📞 Numéro", style=discord.ButtonStyle.primary)
    async def numero(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            f"**Numéro de {self.agent_name} :** `{self.agent_data.get('numero', 'Non disponible')}`",
            ephemeral=True
        )

    @discord.ui.button(label="🎟️ Ticket", style=discord.ButtonStyle.success)
    async def ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        user = interaction.user
        category = discord.utils.get(guild.categories, id=TICKETS_CATEGORY_ID)
        if not category:
            category = await guild.create_category("tickets")

        existing = discord.utils.get(category.text_channels, name=f"ticket-{user.name.lower()}")
        if existing:
            await interaction.response.send_message(f"⚠️ Tu as déjà un ticket ici : {existing.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        channel = await guild.create_text_channel(f"ticket-{user.name}", category=category, overwrites=overwrites)
        embed = discord.Embed(
            title=f"🎟️ Ticket Ouvert - {self.agent_name}",
            description=f"Salut {user.mention} ! Tu contactes **{self.agent_name}**, {self.agent_data['role']}.\nExplique ta demande ici.",
            color=discord.Color.purple()
        )
        await channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Ton ticket a été créé ici : {channel.mention}", ephemeral=True)

# === MENU SELECT ===
class MenuSelect(Select):
    def __init__(self):
        options = [discord.SelectOption(label=name, description=data["role"]) for name, data in AGENTS.items()]
        super().__init__(placeholder="Choisis un agent à contacter...", options=options)

    async def callback(self, interaction: discord.Interaction):
        agent_name = self.values[0]
        embed = discord.Embed(
            title=f"📇 Contact : {agent_name}",
            description="Choisis une option ci-dessous 👇",
            color=discord.Color.purple()
        )
        embed.add_field(name="Rôle", value=AGENTS[agent_name]["role"], inline=False)
        await interaction.response.send_message(embed=embed, view=ContactView(agent_name), ephemeral=True)

class MenuView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MenuSelect())

# === FONCTION PUBLIQUE POUR ENVOYER LE MENU DE CONTACT (APPELLE DEPUIS PARTNER) ===
async def send_contact_menu(interaction: discord.Interaction):
    embed = discord.Embed(title="📞 Contacter un agent", description="Sélectionne un agent ci-dessous 👇", color=discord.Color.blurple())
    view = MenuView()
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)
