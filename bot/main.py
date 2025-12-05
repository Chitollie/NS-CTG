import discord
from discord.ext import commands
from bot.config import TOKEN, GUILD_ID
from bot.utils import missions_data

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

async def setup_bot():
    async def setup_hook():
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("✅ Commandes slash synchronisées")
        
        try:
            missions_data.load_missions()
            await missions_data.restore_missions_views(bot)
            print("✅ Missions restaurées")
        except Exception as e:
            print(f"Erreur restauration missions: {e}")
        
        try:
            from bot.commands.agents import setup as setup_agents
            await setup_agents(bot)
            print("✅ Système agents chargé")
        except Exception as e:
            print(f"Erreur chargement agents: {e}")

    bot.setup_hook = setup_hook

    try:
        from bot import events
        await events.setup_events(bot)
        print("✅ Événements chargés")
    except Exception as e:
        print(f"Erreur chargement événements: {e}")

    try:
        from bot.commands import admin, agents, annonces, menu
        await bot.add_cog(admin.AdminCog(bot))
        await bot.add_cog(agents.AgentsCog(bot))
        await bot.add_cog(annonces.AnnoncesCog(bot))
        await bot.add_cog(menu.MenuCog(bot))
        print("✅ Commandes chargées")
    except Exception as e:
        print(f"Erreur chargement commandes: {e}")

    return bot

async def main():
    bot_instance = await setup_bot()
    async with bot_instance:
        await bot_instance.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
