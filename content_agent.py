"""
✨ Swift Delux — Content Agent ✨
Sugere uma ideia de post diária para o Instagram, com legenda
e hashtags, e envia para Telegram com formatação bonita.
"""

import os
import requests
import json
import random
from datetime import datetime
from dashboard_data import add_event

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

ANGLES = [
    "lifestyle aspiracional — a peça no dia a dia de uma mulher europeia, 20-36 anos",
    "detalhe e brilho — foco no acabamento e qualidade da joia",
    "storytelling de marca — porque é que a Swift Delux existe / valores da marca",
    "look completo — como combinar a peça com um outfit",
    "presente / momento especial — a joia como prenda",
    "behind the scenes — processo de criação ou embalagem",
]

DAY_EMOJIS = ["✨", "💎", "🤍", "🌙", "🪞", "🫧"]


def generate_post_idea():
    angle = random.choice(ANGLES)

    prompt = f"""Sugere 1 ideia de post para o Instagram da Swift Delux,
uma marca de joias com público-alvo mulheres de 20-36 anos na Europa,
estética aspiracional e minimalista.

Ângulo de hoje: {angle}

Responde APENAS em JSON válido, sem markdown, neste formato exato:
{{
  "conceito_visual": "descrição curta do que mostrar na imagem/vídeo",
  "legenda": "legenda pronta a publicar, em português, tom aspiracional, 2-3 frases",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
  "melhor_horario": "sugestão de horário de publicação"
}}"""

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    response.raise_for_status()
    text = response.json()["content"][0]["text"]
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def send_telegram_message(text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
    )


def format_message(idea):
    emoji = random.choice(DAY_EMOJIS)
    line = "─" * 24
    today = datetime.now().strftime("%d/%m/%Y")
    hashtags = " ".join(idea["hashtags"])

    return (
        f"{emoji} <b>IDEIA DE POST · {today}</b>\n"
        f"<code>{line}</code>\n\n"
        f"🎬 <b>Conceito visual:</b>\n{idea['conceito_visual']}\n\n"
        f"📝 <b>Legenda:</b>\n<i>{idea['legenda']}</i>\n\n"
        f"🏷️ {hashtags}\n\n"
        f"⏰ <b>Melhor horário:</b> {idea['melhor_horario']}\n\n"
        f"<code>{line}</code>\n"
        f"<i>🤖 Swift Delux Content Agent</i>"
    )


def main():
    idea = generate_post_idea()
    message = format_message(idea)
    send_telegram_message(message)
    add_event("post", idea["legenda"][:80])
    print("✅ Ideia de post enviada para o Telegram.")


if __name__ == "__main__":
    main()
