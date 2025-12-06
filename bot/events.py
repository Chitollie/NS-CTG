import discord
from discord.ext import commands
from bot.config import (
    GUILD_ID,
    MISSADMIN_CHANNEL_ID,
)
from bot.views.mission_admin_view import (
    feedback_states,
    send_note_request,
    send_comment_request,
    send_recap,
    send_modify_choice
)


async def setup_events(bot: commands.Bot):

    # ===============================================================
    #  EVENT : ON_READY
    # ===============================================================
    @bot.event
    async def on_ready():
        print(f"✅ Connecté en tant que {bot.user}")
        print("ℹ️ on_ready terminé — les embeds sont gérés par leurs setup().")

    # ===============================================================
    #  EVENT : ON_MESSAGE  (DM FEEDBACK)
    # ===============================================================
    @bot.event
    async def on_message(message: discord.Message):

        # Ignore les bots
        if message.author.bot:
            return

        # IMPORTANT : ne JAMAIS bloquer les commandes !
        await bot.process_commands(message)

        # On ne gère que les DMs
        if not isinstance(message.channel, discord.DMChannel):
            return

        # Récupère l'état du feedback
        state = feedback_states.get(message.author.id)
        if not state:
            return  

        content = message.content.strip().lower()

        # ===========================================================
        # ÉTAPE 1 — Choix note (1-5) ou "non"
        # ===========================================================
        if state.step == 1:
            if content == "non":
                await message.channel.send("Merci, aucun feedback n'a été transmis.")
                feedback_states.pop(message.author.id, None)
                return

            if content.isdigit() and 1 <= int(content) <= 5:
                state.note = int(content)
                await send_comment_request(message.author)
                return

            return await message.channel.send(
                "Veuillez entrer **un chiffre entre 1 et 5**, ou **'non'**."
            )

        # ===========================================================
        # ÉTAPE 2 — Commentaire facultatif
        # ===========================================================
        if state.step == 2:
            state.comment = None if content == "non" else message.content
            return await send_recap(message.author)

        # ===========================================================
        # ÉTAPE 3 — Envoyer ou modifier
        # ===========================================================
        if state.step == 3:
            if content == "envoyer":
                guild = bot.get_guild(GUILD_ID)
                channel = guild.get_channel(MISSADMIN_CHANNEL_ID) if guild else None

                if channel:
                    stars = "".join("⭐" if i < (state.note or 0) else "☆" for i in range(5))
                    embed = discord.Embed(
                        title="Nouveau feedback",
                        description=f"Note : {stars}\nCommentaire : {state.comment or 'Aucun'}"
                    )
                    await channel.send(embed=embed)

                await message.channel.send("✅ Merci pour votre feedback !")
                feedback_states.pop(message.author.id, None)
                return

            if content == "modifier":
                return await send_modify_choice(message.author)

        # ===========================================================
        # ÉTAPE 4 — Modification : note ou commentaire ?
        # ===========================================================
        if state.step == 4:
            if content == "note":
                return await send_note_request(message.author)

            if content == "commentaire":
                return await send_comment_request(message.author)

            return await message.channel.send("Réponse invalide. Choisissez **'note'** ou **'commentaire'**.")
