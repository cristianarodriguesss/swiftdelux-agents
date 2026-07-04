"""
✨ THE AGENCY — Update Metrics ✨
Atualiza seguidores do Instagram (Swift Delux e Cristiana) e/ou
regista uma nova parceria. Corre via "Run workflow" no GitHub.
"""

import os
import json
from datetime import datetime, timezone
from dashboard_data import set_followers, add_event

DATA_FILE = "dados.json"


def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"events": []}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    sd_followers = os.environ.get("FOLLOWERS", "").strip()
    cr_followers = os.environ.get("CR_FOLLOWERS", "").strip()
    partnership = os.environ.get("PARTNERSHIP", "").strip()

    data = load_data()

    if sd_followers:
        data["followers"] = {
            "count": int(sd_followers),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        print(f"✅ Swift Delux seguidores: {sd_followers}")

    if cr_followers:
        data["cr_followers"] = {
            "count": int(cr_followers),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        print(f"✅ Cristiana seguidores: {cr_followers}")

    if partnership:
        if "events" not in data:
            data["events"] = []
        data["events"].append({
            "type": "partnership",
            "summary": partnership,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        print(f"✅ Parceria registada: {partnership}")

    if sd_followers or cr_followers or partnership:
        save_data(data)
    else:
        print("Nada para atualizar — preenche pelo menos um campo.")


if __name__ == "__main__":
    main()
