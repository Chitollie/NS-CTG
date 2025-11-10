import discord
from discord.ext import commands
from bot.config import (
    GUILD_ID,
    IDENT_CHANNEL_ID,
    ASKMISS_CHANNEL_ID,
    LOC_CHANNEL_ID,
    GUILD_ID,
    MISSADMIN_CHANNEL_ID,
)
from bot.views.identification_view import IdentificationButtonView
from bot.views.askmiss_view import AskMissView
from bot.embeds.localisation import send_localisation_image
from bot.embeds.tarifs import send_tarifs
from bot.views.tarifs_view import TarifsModal
from bot.views.missions_admin_view import (
    feedback_states,
    send_note_request,
    send_comment_request,
    send_recap,
    send_modify_choice,
)

# Dictionnaire des états de feedback
feedback_states = {}


async def setup_events(bot: commands.Bot):

    @bot.event
    async def on_ready():
        print(f"✅ Connecté en tant que {bot.user}")
        try:
            # Synchronisation des commandes slash
            synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
            print(f"Commandes slash synchronisées : {len(synced)}")
        except Exception as e:
            print(f"Erreur lors de la synchro des commandes : {e}")

        print("ℹ️ on_ready completed — embeds are handled by their setup functions.")

    @bot.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return

        # Vérifie si c'est un message privé (DM)
        if not isinstance(message.channel, discord.DMChannel):
            return

        # Récupère l'état du feedback
        state = feedback_states.get(message.author.id)
        if not state:
            return

        content = message.content.strip().lower()

        # Étape 1 — Demande de note
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

        # Étape 2 — Demande de commentaire
        elif state.step == 2:
            if content == "non":
                state.comment = None
            else:
                state.comment = message.content

            await send_recap(message.author)

        # Étape 3 — Récapitulatif / envoi
        elif state.step == 3:
            if content == "envoyer":
                guild = bot.get_guild(GUILD_ID)
                channel = guild.get_channel(MISSADMIN_CHANNEL_ID)
                if channel:
                    stars = "".join(["⭐" if i < state.note else "☆" for i in range(5)])
                    embed = discord.Embed(
                        title=f"Feedback - {state.mission_data['nom']}",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Note", value=stars, inline=False)
                    embed.add_field(
                        name="Commentaire",
                        value=state.comment if state.comment else "Aucun",
                        inline=False
                    )
                    embed.set_footer(text=f"Client: <@{state.user_id}>")
                    await channel.send(embed=embed)

                await message.channel.send("✅ Merci pour votre feedback !")
                feedback_states.pop(message.author.id, None)

            elif content == "modifier":
                await send_modify_choice(message.author)

        # Étape 4 — Choix de modification
        elif state.step == 4:
            if content == "note":
                await send_note_request(message.author)
            elif content == "commentaire":
                await send_comment_request(message.author)
            else:
                await message.channel.send("Veuillez répondre par 'note' ou 'commentaire'.")
