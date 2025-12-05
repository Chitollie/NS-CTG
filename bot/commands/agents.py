import discord
from discord import app_commands
from discord.ext import commands

grades = [
    "Recrue",   # 0
    "Agent",    # 1
    "Agent supérieur", # 2
    "Responsable",  # 3
    "Chef d'unité", # 4
    "Manager",  # 5
]

ANNONCES_CHANNEL_ID = 123456789012345678

@app_commands.command(name="agents", description="Gestionnaire des agents.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    agent="L'agent à gérer",
    type="Type d'action (ex : Rank)",
    action="Action si type = Rank : up ou down"
)
async def agents_cmd(interaction: discord.Interaction, agent: discord.Member, type: str, action: str = None):
    await interaction.response.defer(ephemeral=True)

    type = type.lower()
    if type not in ["up", "down"]:
        return await interaction.followup.send("Type invalide. Utilise `up` ou `down`.")

    guild_roles = {role.name: role for role in interaction.guild.roles}

    current_index = None
    for i, grade in enumerate(grades):
        if grade in guild_roles and guild_roles[grade] in agent.roles:
            current_index = i
            break

    annonces_channel = interaction.guild.get_channel(ANNONCES_CHANNEL_ID)
    if annonces_channel is None:
        return await interaction.followup.send("Channel d'annonces introuvable !")

    if type == "rank":
        if action is None:
            return await interaction.followup.send("Précise une action : `up` ou `down`.")
        action = action.lower()
        if action not in ["up", "down"]:
            return await interaction.followup.send("Action invalide. Utilise `up` ou `down`.")
        type = action

    # --- UP ---
    if type == "up":
        if current_index is None:
            new_grade = grades[0]
            await agent.add_roles(guild_roles[new_grade])
            await annonces_channel.send(f"📈 **{agent.mention} est maintenant {new_grade} !** 👏")
            return await interaction.followup.send(f"Grade ajouté : {new_grade}")

        if current_index == len(grades) - 1:
            return await interaction.followup.send("Impossible de UP, il est déjà au grade maximal.")

        old_role = guild_roles[grades[current_index]]
        new_role = guild_roles[grades[current_index + 1]]

        await agent.remove_roles(old_role)
        await agent.add_roles(new_role)

        await annonces_channel.send(f"📈 **{agent.mention} est passé de {old_role.name} à {new_role.name} !** 🚀")
        return await interaction.followup.send(f"UP effectué : {old_role.name} → {new_role.name}")

    # --- DOWN ---
    if type == "down":
        if current_index is None:
            return await interaction.followup.send("Cet agent n'a aucun grade.")

        if current_index == 0:
            old_role = guild_roles[grades[0]]
            await agent.remove_roles(old_role)

            await annonces_channel.send(f"📉 **{agent.mention} a été retiré de Recrue. Il ne fait plus partie des agents.**")
            try:
                await agent.send("❌ Vous avez été **licencié** et retiré de l'équipe des agents.")
            except:
                pass

            return await interaction.followup.send("Recrue retirée et agent licencié.")

        old_role = guild_roles[grades[current_index]]
        new_role = guild_roles[grades[current_index - 1]]

        await agent.remove_roles(old_role)
        await agent.add_roles(new_role)

        await annonces_channel.send(f"📉 **{agent.mention} est descendu de {old_role.name} à {new_role.name}.**")
        return await interaction.followup.send(f"DOWN effectué : {old_role.name} → {new_role.name}")
