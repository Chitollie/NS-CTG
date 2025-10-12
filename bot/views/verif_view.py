import discord
from discord.ui import View, button
from ..config import ROLE_IDENTIFIE_ID, ROLE_LSPD_ID, ROLE_SAMS_ID

class VerificationRoleView(View):
    def __init__(self, user_id: int, grade: str, nick: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.grade = grade.lower()
        self.nick = nick

    @button(label="✅ Accepter", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Erreur : pas de serveur trouvé.", ephemeral=True)
            return

        member = guild.get_member(self.user_id)
        if not member:
            await interaction.response.send_message("⚠️ Membre introuvable.", ephemeral=True)
            return

        try:
            await member.edit(nick=self.nick)
            base_role = guild.get_role(ROLE_IDENTIFIE_ID)
            specific_role = None

            if self.grade == "lspd":
                specific_role = guild.get_role(ROLE_LSPD_ID)
            elif self.grade == "sams":
                specific_role = guild.get_role(ROLE_SAMS_ID)

            if base_role:
                await member.add_roles(base_role)
            if specific_role:
                await member.add_roles(specific_role)

            await interaction.response.send_message(
                f"✅ Rôle {self.grade.upper()} attribué à {member.mention}.", ephemeral=True
            )
            await interaction.message.edit(
                content=f"✅ Demande approuvée pour {member.mention}",
                view=None
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ Permissions insuffisantes.", ephemeral=True)
        except discord.HTTPException:
            await interaction.response.send_message("❌ Erreur lors de l’attribution du rôle.", ephemeral=True)

    @button(label="❌ Refuser", style=discord.ButtonStyle.danger)
    async def refuse(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚫 Demande refusée.", ephemeral=True)
        await interaction.message.edit(content="🚫 Demande refusée.", view=None)