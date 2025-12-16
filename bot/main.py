import os
import discord
from discord.ext import commands
from bot.config import TOKEN, GUILD_ID
from bot.utils import missions_data
import importlib
import inspect
import pkgutil

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
#   S E T U P   H O O K  –  Discord.py 2.x
# ============================================================

@bot.event
async def setup_hook():

    # --- Sync des slash commands côté serveur ---
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("✅ Slash commands synchronisées")
    except Exception as e:
        print(f"❌ Erreur sync : {e}")

    # --- Chargement des événements ---
    try:
        from bot import events
        await events.setup_events(bot)
        print("✅ Événements chargés")
    except Exception as e:
        print(f"❌ Erreur chargement events : {e}")

    # --- Chargement des Cogs ---
    try:
        from bot.commands import admin, annonces, menu
        await bot.add_cog(admin.AdminCog(bot))
        await bot.add_cog(annonces.AnnoncesCog(bot))
        await bot.add_cog(menu.MenuCog(bot))
        await events.setup_events(bot)

        from bot.commands.agents import setup as setup_agents
        await setup_agents(bot)
        await events.setup_events(bot)

        print("✅ Commandes chargées")
    except Exception as e:
        print(f"❌ Erreur commands : {e}")

    # --- VUES ----
    try:
        from bot.views.identification_view import setup as setup_ident
        await setup_ident(bot)
        print("✅ Identification view chargée")
    except Exception as e:
        print(f"⚠️ Erreur identification view : {e}")

    try:
        from bot.views.askmiss_view import setup as setup_ask
        await setup_ask(bot)
        print("✅ AskMission view chargée")
    except Exception as e:
        print(f"⚠️ Erreur askmiss view : {e}")

    # --- EMBEDS / MENUS ---
    for module_path, label in [
        ("bot.embeds.tarifs", "Tarifs"),
        ("bot.embeds.localisation", "Localisation"),
        ("bot.menu.contact_main", "Contacts"),
    ]:
        try:
            mod = importlib.import_module(module_path)
            await mod.setup(bot)
            print(f"✅ Embed {label} chargé")
        except Exception as e:
            print(f"⚠️ Erreur embed {label} : {e}")

    # --- JOIN UTILS ---
    try:
        from bot.utils.join import setup_join
        setup_join(bot)
        print("✅ System JOIN chargé")
    except Exception as e:
        print(f"⚠️ Erreur join : {e}")

    # --- RESTAURATION DES MISSIONS ---
    try:
        missions_data.load_missions()
        await missions_data.restore_missions_views(bot)
        print("✅ Missions restaurées")
    except Exception as e:
        print(f"⚠️ Erreur restauration missions : {e}")

    # --- Views persistantes automatiques ---
    try:
        registered = register_persistent_views(bot)
        print(f"✅ Views persistantes enregistrées : {len(registered)}")
        for v in registered:
            print("  -", v)
    except Exception as e:
        print(f"⚠️ Erreur persistent views : {e}")



# ============================================================
#   Fonction de scan automatique des Views persistantes
# ============================================================

def register_persistent_views(bot):
    registered = []

    def scan_package(pkg_name: str):
        try:
            pkg = importlib.import_module(pkg_name)
        except Exception:
            return

        for _, name, _ in pkgutil.iter_modules(pkg.__path__):
            full = f"{pkg_name}.{name}"
            try:
                mod = importlib.import_module(full)
            except Exception:
                continue

            for _, obj in inspect.getmembers(mod, inspect.isclass):
                if issubclass(obj, discord.ui.View) and obj is not discord.ui.View:
                    try:
                        instance = obj()
                        bot.add_view(instance)
                        registered.append(f"{full}.{obj.__name__}")
                    except Exception:
                        pass

    scan_package("bot.views")
    scan_package("bot.menu")

    return registered



# ============================================================
#                     L A U N C H   B O T
# ============================================================

async def main():
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
