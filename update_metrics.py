"""
✨ Swift Delux — Update Metrics ✨
Script manual: atualiza o número de seguidores do Instagram e/ou
regista uma nova parceria fechada. Corre via "Run workflow" no GitHub,
preenchendo os campos que aparecem (followers / parceria).
"""

import os
from dashboard_data import set_followers, add_event


def main():
    followers = os.environ.get("FOLLOWERS", "").strip()
    partnership = os.environ.get("PARTNERSHIP", "").strip()

    if followers:
        set_followers(followers)
        print(f"✅ Seguidores atualizados: {followers}")

    if partnership:
        add_event("partnership", partnership)
        print(f"✅ Parceria registada: {partnership}")

    if not followers and not partnership:
        print("Nada para atualizar — preenche pelo menos um campo.")


if __name__ == "__main__":
    main()
