import discord
from discord.ext import commands
from discord.ui import View, Select, Button

# === CONFIGURATION ===
AGENTS = {
    "Alina Wolf": {
        "role": "PDG",
        "numero": "555-0234",
        "discord_id": 765306791093076058
    },
    "Brian Stanford": {
        "role": "Co-PDG",
        "numero": "555-0987",
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

        # On ajoute le bouton Email comme lien direct vers le profil Discord
        discord_id = self.agent_data["discord_id"]
        self.add_item(
            Button(
                label="📨 Email",
                style=discord.ButtonStyle.link,
                url=f"https://discord.com/users/{discord_id}"
            )
        )

    # Bouton "Numéro"
    @discord.ui.button(label="📞 Numéro", style=discord.ButtonStyle.primary)
    async def numero(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        numero = self.agent_data.get("numero", "Non disponible")
        await interaction.followup.send(
            f"**Numéro de {self.agent_name} :** `{numero}`",
            ephemeral=True
        )

    # Bouton "Ticket"
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

        # Vérifie si l’utilisateur a déjà un ticket ouvert
        existing_ticket = discord.utils.get(category.text_channels, name=f"ticket-{user.name.lower()}")
        if existing_ticket:
            await interaction.response.send_message(
                f"⚠️ Tu as déjà un ticket ouvert ici : {existing_ticket.mention}",
                ephemeral=True
            )
            return

        # Crée un nouveau salon
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites=overwrites
        )

        # Embed d'accueil dans le ticket
        embed = discord.Embed(
            title=f"🎟️ Ticket Ouvert - {self.agent_name}",
            description=(
                f"Salut {user.mention} ! 👋\n"
                f"Tu contactes **{self.agent_name}**, {self.agent_data['role']}.\n"
                "Explique ta demande ici, un membre de l’équipe te répondra dès que possible 💬"
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
        agent_data = AGENTS[agent_name]

        # Embed général de contact
        embed = discord.Embed(
            title=f"📇 Contact : {agent_name}",
            description="Choisis une option ci-dessous 👇",
            color=discord.Color.purple()
        )
        embed.add_field(name="Rôle", value=agent_data["role"], inline=False)
        embed.add_field(name="Numéro", value=f"`{agent_data['numero']}`", inline=False)

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


async def setup(bot: commands.Bot):
    try:
        from bot import config
        from ..utils.auto_messages import clean_and_send
    except Exception as e:
        print(f"⚠️ Erreur d'import : {e}")
        return

    contacts_channel_id = getattr(config, "CONTACTS_CHANNEL_ID", None)
    if contacts_channel_id is None:
        print("⚠️ CONTACTS_CHANNEL_ID n'est pas défini")
        return

    async def send_contact_menu():
        channel = bot.get_channel(contacts_channel_id)
        if channel is None:
            try:
                channel = await bot.fetch_channel(contacts_channel_id)
            except Exception:
                print(f"⚠️ Impossible de trouver le channel {contacts_channel_id}")
                return

        # Vérifie que c'est un channel texte
        if not isinstance(channel, discord.TextChannel):
            print(f"⚠️ Le channel {contacts_channel_id} n'est pas un channel texte")
            return

        # Nettoie et envoie le nouveau message
        try:
            msg = await clean_and_send(
                channel,
                content="📞 Choisis une personne à contacter :",
                view=MenuView(),
                bot_filter="Choisis une personne à contacter"
            )
            if msg:
                print("✅ Menu de contact envoyé avec succès")
            else:
                print("⚠️ Le message n'a pas pu être envoyé")
        except Exception as e:
            print(f"⚠️ Erreur lors de l'envoi du menu : {e}")

    # Si le bot est déjà prêt, envoie tout de suite, sinon attache un listener au ready
    if getattr(bot, "is_ready", lambda: True)():
        # Some bot implementations mark is_ready differently; attempt to send anyway
        bot.loop.create_task(send_contact_menu())
    else:
        @bot.event
        async def on_ready():
            # Envoi le message une seule fois
            await send_contact_menu()
