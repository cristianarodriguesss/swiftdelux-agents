"""
Funções auxiliares partilhadas para guardar histórico de atividade
num ficheiro dados.json, lido pelo dashboard (index.html).
"""

import json
import os
from datetime import datetime, timezone

DATA_FILE = os.path.join(os.path.dirname(__file__), "dados.json")
MAX_EVENTS = 200  # evita que o ficheiro cresça para sempre


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"events": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"events": []}


def set_followers(count):
    data = load_data()
    data["followers"] = {
        "count": int(count),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_event(event_type, summary):
    """event_type: 'email', 'post' ou 'partnership'"""
    data = load_data()
    data["events"].append({
        "type": event_type,
        "summary": summary,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    data["events"] = data["events"][-MAX_EVENTS:]
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
