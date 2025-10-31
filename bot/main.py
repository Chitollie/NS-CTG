import discord
from discord.ext import commands
from bot.config import TOKEN, GUILD_ID
from bot.events import setup_events
from bot.commands.menu import menu_cmd
from bot.commands.annonces import annonces_cmd
from bot.commands import admin
from bot.utils.join import setup_join
from bot.embeds import contacts
from bot.views import identification_view, askmiss_view
from bot.views.mission_admin_view import feedback_states, send_note_request, send_comment_request, send_recap, send_modify_choice
from bot.embeds import tarifs, localisation
from bot import config

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Handler déplacé ici après la définition de bot
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if isinstance(message.channel, discord.DMChannel):
        state = feedback_states.get(message.author.id)
        if not state:
            return
        content = message.content.strip().lower()
        if state.step == 1:
            if content == "non":
                await message.channel.send("Merci, aucun feedback n'a été transmis.")
                feedback_states.pop(message.author.id, None)
                return
            if content.isdigit() and 1 <= int(content) <= 5:
                state.note = int(content)
                await send_comment_request(message.author)
                return
            await message.channel.send("Veuillez entrer un chiffre entre 1 et 5, ou 'non'.")
        elif state.step == 2:
            if content == "non":
                state.comment = None
            else:
                state.comment = message.content
            await send_recap(message.author)
        elif state.step == 3:
            if content == "envoyer":
                # Envoi dans le salon admin
                guild = bot.get_guild(config.GUILD_ID)
                channel = guild.get_channel(config.MISSADMIN_CHANNEL_ID)
                if channel:
                    stars = "".join(["⭐" if i < state.note else "☆" for i in range(5)])
                    embed = discord.Embed(
                        title=f"Feedback - {state.mission_data['nom']}",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Note", value=stars, inline=False)
                    embed.add_field(name="Commentaire", value=state.comment if state.comment else "Aucun", inline=False)
                    embed.set_footer(text=f"Client: <@{state.user_id}>")
                    await channel.send(embed=embed)
                await message.channel.send("✅ Merci pour votre feedback !")
                feedback_states.pop(message.author.id, None)
            elif content == "modifier":
                await send_modify_choice(message.author)
        elif state.step == 4:
            if content == "note":
                await send_note_request(message.author)
            elif content == "commentaire":
                await send_comment_request(message.author)
            else:
                await message.channel.send("Veuillez répondre par 'note' ou 'commentaire'.")
from bot.embeds import tarifs, localisation
from bot import config

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def setup_hook():
    bot.tree.add_command(menu_cmd, guild=discord.Object(id=GUILD_ID))
    bot.tree.add_command(annonces_cmd, guild=discord.Object(id=GUILD_ID))

    # --- Diagnostic startup: affiche les IDs chargés et vérifie l'accès aux channels ---
    try:
        ids_to_check = [
            "IDENT_CHANNEL_ID",
            "JOIN_CHANNEL_ID",
            "CONTACTS_CHANNEL_ID",
            "ASKMISS_CHANNEL_ID",
            "LOC_CHANNEL_ID",
            "TARIF_CHANNEL_ID",
            "ANNOUNCEMENT_CHANNEL_ID",
            "VERIFROLE_CHANNEL_ID",
        ]
        print("🔎 Vérification des channels configurés :")
        for name in ids_to_check:
            value = getattr(config, name, None)
            print(f" - {name} = {value}")
            if not value:
                continue
            # Essayer d'obtenir depuis le cache, puis via l'API
            channel = bot.get_channel(value)
            if channel is None:
                try:
                    channel = await bot.fetch_channel(value)
                    print(f"   -> récupéré via API: {getattr(channel, 'name', repr(channel))}")
                except Exception as e:
                    print(f"   -> Impossible de récupérer le channel {value} : {e}")
                    continue

            if isinstance(channel, discord.TextChannel):
                # Utiliser le Member du bot dans le guild pour vérifier les permissions
                bot_member = getattr(channel.guild, 'me', None)
                perms = channel.permissions_for(bot_member) if bot_member else None
                missing = []
                if perms is not None:
                    if not perms.view_channel:
                        missing.append("view_channel")
                    if not perms.send_messages:
                        missing.append("send_messages")
                    if not perms.read_message_history:
                        missing.append("read_message_history")
                if missing:
                    print(f"   -> Permissions manquantes dans {name}: {', '.join(missing)}")
                else:
                    print(f"   -> OK : accès & permissions suffisantes pour {name}")
            else:
                print(f"   -> Le channel {value} n'est pas un TextChannel ou introuvable")
    except Exception as e:
        print(f"⚠️ Erreur lors du diagnostic de démarrage : {e}")

    # Continue setup normal
    await setup_events(bot)
    # Register admin commands (including shutdown)
    # Note: admin.setup is a regular function (attaches signal handlers and commands)
    admin.setup(bot)
    # Register member join handler to send welcome messages
    setup_join(bot)
    # Load contacts extension to send menu view
    await contacts.setup(bot)
    # Initialise les autres embeds/menus (identification, demande d'agents)
    await identification_view.setup(bot)
    await askmiss_view.setup(bot)
    # Initialise tarifs et localisation (si configurés)
    await tarifs.setup(bot)
    await localisation.setup(bot)


@bot.event
async def on_disconnect():
    print("⚠️ Déconnecté de Discord. Tentative de reconnexion...")


@bot.event
async def on_shutdown():
    """Appelé juste avant l'arrêt du bot."""
    print("🔌 Arrêt propre du bot en cours...")
    # Sauvegarder ici les données importantes si nécessaire


if TOKEN is None:
    raise RuntimeError("TOKEN n'est pas défini dans le fichier .env")

try:
    bot.run(TOKEN)
except KeyboardInterrupt:
    print("\n⌨️ Arrêt par Ctrl+C")
except Exception as e:
    print(f"❌ Erreur fatale : {e}")
finally:
    print("🔄 Bot arrêté. Il redémarrera automatiquement sur Replit.")
