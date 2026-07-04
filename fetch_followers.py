"""
✨ THE AGENCY — Fetch Followers ✨
Vai buscar o número de seguidores do Instagram da Swift Delux
e da Cristiana Rodrigues automaticamente, sem API paga.
Corre 1x por semana via GitHub Actions.
"""

import json
import os
import re
import requests
from datetime import datetime, timezone

DATA_FILE = "dados.json"

ACCOUNTS = {
    "sd": "swiftdelux",
    "cr": "cristianarodriguesss"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


def fetch_followers(username):
    """Vai buscar seguidores do Instagram via página pública."""
    url = f"https://www.instagram.com/{username}/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"⚠️ {username}: HTTP {r.status_code}")
            return None

        # Try to find followers in the page source
        patterns = [
            r'"edge_followed_by":\{"count":(\d+)\}',
            r'"followers_count":(\d+)',
            r'"userInteractionCount":"(\d+)"',
            r'(\d+(?:\.\d+)?[KMk]?) Followers',
        ]

        for pattern in patterns:
            match = re.search(pattern, r.text)
            if match:
                val = match.group(1)
                # Handle K/M suffixes
                if isinstance(val, str) and ('K' in val or 'k' in val):
                    return int(float(val.replace('K','').replace('k','')) * 1000)
                elif isinstance(val, str) and 'M' in val:
                    return int(float(val.replace('M','')) * 1000000)
                return int(val)

        print(f"⚠️ {username}: padrão não encontrado")
        return None

    except Exception as e:
        print(f"⚠️ {username}: erro - {e}")
        return None


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
    data = load_data()
    now = datetime.now(timezone.utc).isoformat()
    updated = False

    # Swift Delux
    sd = fetch_followers(ACCOUNTS["sd"])
    if sd:
        data["followers"] = {"count": sd, "updated_at": now}
        print(f"✅ Swift Delux (@swiftdelux): {sd} seguidores")
        updated = True
    else:
        # Fallback: use environment variable if set
        sd_env = os.environ.get("SD_FOLLOWERS_FALLBACK", "").strip()
        if sd_env:
            data["followers"] = {"count": int(sd_env), "updated_at": now}
            print(f"✅ Swift Delux (fallback): {sd_env} seguidores")
            updated = True

    # Cristiana
    cr = fetch_followers(ACCOUNTS["cr"])
    if cr:
        data["cr_followers"] = {"count": cr, "updated_at": now}
        print(f"✅ Cristiana (@cristianarodriguesss): {cr} seguidores")
        updated = True
    else:
        cr_env = os.environ.get("CR_FOLLOWERS_FALLBACK", "").strip()
        if cr_env:
            data["cr_followers"] = {"count": int(cr_env), "updated_at": now}
            print(f"✅ Cristiana (fallback): {cr_env} seguidores")
            updated = True

    if updated:
        save_data(data)
        print("✅ dados.json atualizado")
    else:
        print("⚠️ Nenhum dado atualizado")


if __name__ == "__main__":
    main()
