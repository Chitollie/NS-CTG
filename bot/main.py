import discord
from discord.ext import commands
from bot.config import TOKEN, GUILD_ID
from bot.utils import missions_data
import importlib
import inspect
import pkgutil

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

    bot.setup_hook = setup_hook

    try:
        from bot import events
        await events.setup_events(bot)
        print("✅ Événements chargés")
    except Exception as e:
        print(f"Erreur chargement événements: {e}")

    try:
        from bot.commands import admin, annonces, menu
        await bot.add_cog(admin.AdminCog(bot))
        await bot.add_cog(annonces.AnnoncesCog(bot))
        await bot.add_cog(menu.MenuCog(bot))
        
        from bot.commands.agents import setup as setup_agents
        await setup_agents(bot)
        
        print("✅ Commandes chargées")
    except Exception as e:
        print(f"Erreur chargement commandes: {e}")

    try:
        from bot.views.identification_view import setup as setup_ident
        await setup_ident(bot)
        print("✅ Vue d'identification chargée")
    except Exception as e:
        print(f"⚠️ Erreur chargement identification: {e}")

    try:
        from bot.views.askmiss_view import setup as setup_askmiss
        await setup_askmiss(bot)
        print("✅ Vue demande missions chargée")
    except Exception as e:
        print(f"⚠️ Erreur chargement askmiss: {e}")

    try:
        from bot.embeds.tarifs import setup as setup_tarifs
        await setup_tarifs(bot)
        print("✅ Embed tarifs chargé")
    except Exception as e:
        print(f"⚠️ Erreur chargement tarifs: {e}")

    try:
        from bot.embeds.localisation import setup as setup_loc
        await setup_loc(bot)
        print("✅ Embed localisation chargé")
    except Exception as e:
        print(f"⚠️ Erreur chargement localisation: {e}")

    try:
        from bot.menu.contact_main import setup as setup_contact_embed
        await setup_contact_embed(bot)
        print("✅ Embed contacts chargé")
    except Exception as e:
        print(f"⚠️ Erreur chargement contacts embed: {e}")

    try:
        from bot.menu.contact_main import setup as setup_contact_main
        await setup_contact_main(bot)
        print("✅ Embed contacts chargé")
    except Exception as e:
        print(f"⚠️ Erreur chargement contacts embed: {e}")


    try:
        from bot.utils.join import setup_join
        setup_join(bot)
        print("✅ Système de join chargé")
    except Exception as e:
        print(f"⚠️ Erreur chargement join: {e}")

    try:
        def _register_views_from_package(package_name: str):
            try:
                pkg = importlib.import_module(package_name)
            except Exception:
                return []
            registered = []
            for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
                full_name = f"{package_name}.{name}"
                try:
                    mod = importlib.import_module(full_name)
                except Exception:
                    continue
                for _, obj in inspect.getmembers(mod, inspect.isclass):
                    try:
                        if issubclass(obj, discord.ui.View) and obj is not discord.ui.View:
                            # Essayer d'instancier avec plusieurs fallback
                            inst = None
                            for args in ((), (0, "", ""), (None,)):
                                try:
                                    inst = obj(*args)
                                    break
                                except TypeError:
                                    continue
                            if inst is not None:
                                bot.add_view(inst)
                                registered.append(f"{full_name}.{obj.__name__}")
                    except Exception:
                        continue
            return registered

        registered_views = []
        registered_views += _register_views_from_package("bot.views")
        registered_views += _register_views_from_package("bot.menu")

        print(f"✅ Views persistantes enregistrées: {len(registered_views)}")
        for v in registered_views:
            print("  -", v)
    except Exception as e:
        print(f"⚠️ Erreur enregistrement views persistantes: {e}")

    return bot

async def main():
    bot_instance = await setup_bot()
    async with bot_instance:
        await bot_instance.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
