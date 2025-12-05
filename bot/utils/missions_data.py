import json
import os
import datetime
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_PATH = os.path.normpath(os.path.join(DATA_DIR, "missions.json"))

missions: Dict[int, Dict[str, Any]] = {}

def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def load_missions():
    global missions
    _ensure_data_dir()
    if not os.path.exists(DATA_PATH):
        missions = {}
        return
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        missions = {}
        for k, v in raw.items():
            try:
                mid = int(k)
            except Exception:
                continue
            v.setdefault("agents_confirmed", {})
            agents = {}
            for aid, val in v.get("agents_confirmed", {}).items():
                try:
                    agents[int(aid)] = bool(val)
                except Exception:
                    pass
            v["agents_confirmed"] = agents
            dt = v.get("date")
            if isinstance(dt, str):
                try:
                    v["date"] = datetime.datetime.fromisoformat(dt)
                except Exception:
                    v["date"] = None
            missions[mid] = v
    except Exception as e:
        print(f"Error loading missions file: {e}")
        missions = {}

def save_missions():
    try:
        _ensure_data_dir()
        to_dump = {}
        for mid, data in missions.items():
            copy = dict(data)
            # convert agents keys to str and date to iso if needed
            copy["agents_confirmed"] = {str(k): v for k, v in copy.get("agents_confirmed", {}).items()}
            if isinstance(copy.get("date"), datetime.datetime):
                copy["date"] = copy["date"].isoformat()
            to_dump[str(mid)] = copy
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(to_dump, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving missions file: {e}")

async def restore_missions_views(bot):
    try:
        from ..views.mission_admin_view import MissionParticipationView, MissionTrackingView
        from ..views.mission_view import MissionValidationView
    except Exception as e:
        print(f"Error importing views for restore: {e}")
        return

    for msg_id, data in list(missions.items()):
        try:
            channel_raw = data.get("channel")
            ch_id = None
            if isinstance(channel_raw, int):
                ch_id = channel_raw
            else:
                try:
                    ch_id = int(str(channel_raw)) if channel_raw is not None else None
                except Exception:
                    ch_id = None
            if ch_id:
                ch = bot.get_channel(ch_id)
                if ch:
                    try:
                        m_msg = await ch.fetch_message(int(msg_id))
                        if data.get("admin_msg_id"):
                            await m_msg.edit(view=MissionParticipationView(data, int(msg_id)))
                            try:
                                embed = m_msg.embeds[0]
                                if embed and embed.description:
                                    new_desc = embed.description.replace("⏳ En cours de validation par un haut gradé", "").strip()
                                    embed.description = new_desc
                                    await m_msg.edit(embed=embed)
                            except Exception:
                                pass
                        else:
                            try:
                                mv = MissionValidationView(
                                    nom=data.get("nom", ""),
                                    user_id=data.get("id", ""),
                                    lieu=data.get("lieu", ""),
                                    nb_agents=int(data.get("nb_agents", 0)),
                                    date=data.get("date", None)
                                )
                                await m_msg.edit(view=mv)
                            except Exception:
                                pass
                    except Exception:
                        pass

            admin_msg_id = data.get("admin_msg_id")
            if admin_msg_id:
                admin_channel_raw = data.get("admin_channel")
                admin_ch_id = None
                if isinstance(admin_channel_raw, int):
                    admin_ch_id = admin_channel_raw
                else:
                    try:
                        admin_ch_id = int(str(admin_channel_raw)) if admin_channel_raw is not None else None
                    except Exception:
                        admin_ch_id = None
                if not admin_ch_id:
                    try:
                        from ..config import MISSADMIN_CHANNEL_ID
                        admin_ch_id = MISSADMIN_CHANNEL_ID
                    except Exception:
                        admin_ch_id = None
                if admin_ch_id:
                    adm_ch = bot.get_channel(admin_ch_id)
                    if adm_ch:
                        try:
                            a_msg = await adm_ch.fetch_message(int(admin_msg_id))
                            await a_msg.edit(view=MissionTrackingView(data, int(msg_id)))
                        except Exception:
                            pass

        except Exception as e:
            print(f"Error restoring mission {msg_id}: {e}")