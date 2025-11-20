import discord
from discord.ext import commands
from discord.ui import View, Select, Button

# === CONFIGURATION ===
AGENTS = {
    "Alina Wolf": {
        "role": "PDG",
        "numero": "59669-70941",
        "discord_id": 725425681177247908
    },
    "Brian Stanford": {
        "role": "Co-PDG",
        "numero": "59783-70510",
        "discord_id": 1263956791818195087
    },
    "Brice Roca": {
        "role": "Directeur",
        "numero": "59158-69882",
        "discord_id": 471721415574290432
    }
}
TICKETS_CATEGORY_ID = 1426797063164788808

# === VIEW AVEC LES BOUTONS DE CONTACT ===
class ContactView(View):
    def __init__(self, agent_name: str):
        super().__init__(timeout=None)
        self.agent_name = agent_name
        self.agent_data = AGENTS[agent_name]

        # Bouton Email comme lien direct vers le profil Discord
        discord_id = self.agent_data["discord_id"]
        self.add_item(
            Button(
                label="📨 Email",
                style=discord.ButtonStyle.link,
                url=f"https://discord.com/users/{discord_id}"
            )
        )

    @discord.ui.button(label="📞 Numéro", style=discord.ButtonStyle.primary)
    async def numero(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        numero = self.agent_data.get("numero", "Non disponible")
        await interaction.followup.send(
            f"**Numéro de {self.agent_name} :** `{numero}`",
            ephemeral=True
        )

    @discord.ui.button(label="🎟️ Ticket", style=discord.ButtonStyle.success)
    async def ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        user = interaction.user

        if guild is None:
            await interaction.response.send_message("Erreur : serveur introuvable.", ephemeral=True)
            return

        category = discord.utils.get(guild.categories, id=TICKETS_CATEGORY_ID)
        if not category:
            category = await guild.create_category("tickets")

        existing_ticket = discord.utils.get(category.text_channels, name=f"ticket-{user.name.lower()}")
        if existing_ticket:
            await interaction.response.send_message(
                f"⚠️ Tu as déjà un ticket ouvert ici : {existing_ticket.mention}",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title=f"🎟️ Ticket Ouvert - {self.agent_name}",
            description=(
                f"Salut {user.mention} ! 👋\n"
                f"Tu contactes **{self.agent_name}**, {self.agent_data['role']}.\n"
                "Explique ta demande ici, on te répondra dès que possible 💬"
            ),
            color=discord.Color.purple()
        )
        await channel.send(embed=embed)
        await interaction.response.send_message(
            f"✅ Ton ticket a été créé ici : {channel.mention}",
            ephemeral=True
        )

# === MENU PRINCIPAL ===
class MenuSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=name, description=data["role"])
            for name, data in AGENTS.items()
        ]
        super().__init__(placeholder="Choisis un agent à contacter...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        agent_name = self.values[0]

        embed = discord.Embed(
            title=f"📇 Contact : {agent_name}",
            description="Choisis une option ci-dessous 👇",
            color=discord.Color.purple()
        )
        embed.add_field(name="Rôle", value=AGENTS[agent_name]["role"], inline=False)

        await interaction.followup.send(
            embed=embed,
            view=ContactView(agent_name),
            ephemeral=True
        )

# === VIEW PRINCIPALE ===
class MenuView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MenuSelect())

# === FONCTION PUBLIQUE POUR PARTNER.PY ===
async def send_contact_menu(interaction: discord.Interaction):
    """Envoie le menu de contact lorsqu'un utilisateur clique sur l'option 'Contacter un agent'."""
    try:
        embed = discord.Embed(
            title="📞 Choisis une personne à contacter",
            description="Sélectionne un agent ci-dessous 👇",
            color=discord.Color.blurple()
        )
        await interaction.followup.send(embed=embed, view=MenuView(), ephemeral=True)
    except Exception as e:
        await interaction.followup.send("⚠️ Impossible d'afficher le menu de contact.", ephemeral=True)
        print(f"Erreur send_contact_menu : {e}")
