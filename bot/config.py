import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

def get_env_int(var_name: str, default: int | None = None) -> int:
    value = os.getenv(var_name)
    if value is None:
        if default is not None:
            return default
        raise ValueError(f"{var_name} n'est pas défini dans le .env")
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"{var_name} doit être un entier, reçu: {value}")

def get_env_list(var_name: str) -> list[int]:
    value = os.getenv(var_name)
    if not value:
        return []
    return [int(v.strip()) for v in value.split(",") if v.strip().isdigit()]

TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("TOKEN n'est pas défini dans le .env")

GUILD_ID = get_env_int("GUILD_ID")
MISS_CHANNEL_ID = get_env_int("MISS_CHANNEL_ID")
MISSADMIN_CHANNEL_ID = get_env_int("MISSADMIN_CHANNEL_ID")
RADIO_CHANNEL_ID = get_env_int("RADIO_CHANNEL_ID")
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
CONTACTS_CHANNEL_ID = get_env_int("CONTACTS_CHANNEL_ID")
JOIN_CHANNEL_ID = get_env_int("JOIN_CHANNEL_ID")
PARTNERS_DATA_CHANNEL_ID = get_env_int("PARTNERS_DATA_CHANNEL_ID")
PARTNER_FCHANNEL_ID = get_env_int("PARTNER_FCHANNEL_ID")
TICKETS_CATEGORY_ID = get_env_int("TICKETS_CATEGORY_ID")
AGENTS_CHANNEL_ID = get_env_int("AGENTS_CHANNEL_ID")

GRADE_DR = get_env_list("GRADE_DR")
GRADE_AGTCONF = get_env_list("GRADE_AGTCONF")
GRADE_RCR = get_env_list("GRADE_RCR")