import os
from dotenv import load_dotenv

load_dotenv()


def get_env_int(var_name: str) -> int:
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"{var_name} n'est pas défini dans le .env")
    return int(value)


GUILD_ID = get_env_int("GUILD_ID")
MISS_CHANNEL_ID = get_env_int("MISS_CHANNEL_ID")
ROLE_AGENTS_ID = get_env_int("ROLE_AGENTS_ID")
ROLE_SAMS_ID = get_env_int("ROLE_SAMS_ID")
ROLE_LSPD_ID = get_env_int("ROLE_LSPD_ID")
IDENT_CHANNEL_ID = get_env_int("IDENT_CHANNEL_ID")
ROLE_IDENTIFIE_ID = get_env_int("ROLE_IDENTIFIE_ID")
VERIFROLE_CHANNEL_ID = get_env_int("VERIFROLE_CHANNEL_ID")
ASKMISS_CHANNEL_ID = get_env_int("ASKMISS_CHANNEL_ID")
LOC_CHANNEL_ID = get_env_int("LOC_CHANNEL_ID")
ANNOUNCEMENT_CHANNEL_ID = get_env_int("ANNOUNCEMENT_CHANNEL_ID")
TARIF_CHANNEL_ID = get_env_int("TARIF_CHANNEL_ID")

TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("TOKEN n'est pas défini dans le .env")
