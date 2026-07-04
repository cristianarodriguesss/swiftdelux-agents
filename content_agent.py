"""
✨ THE AGENCY — Content Agent ✨
Sugere uma ideia de post diária para o Instagram, com legenda,
hashtags, melhor horário, e envia para Telegram com formatação bonita.
Também envia resumo diário de emails.
"""

import os
import requests
import json
import random
from datetime import datetime, timezone
from dashboard_data import add_event

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

ANGLES_SD = [
    "lifestyle aspiracional — a peça no dia a dia de uma mulher europeia, 20-36 anos",
    "detalhe e brilho — foco no acabamento e qualidade da joia",
    "storytelling de marca — os valores da Swift Delux",
    "look completo — como combinar a peça com um outfit",
    "presente / momento especial — a joia como prenda",
    "behind the scenes — processo de criação ou embalagem",
]

ANGLES_CR = [
    "wellness matinal — rotina de manhã, mindfulness, self-care",
    "viagem e lifestyle — destino europeu, hotel aesthetic, momento de luxo acessível",
    "beleza — skincare rotina, produto favorito do momento, before/after",
    "moda — outfit do dia, tendência da estação, como combinar peças",
    "autenticidade — momento real, pensamento do dia, bastidores da vida",
]

DAY_EMOJIS_SD = ["✨", "💎", "🤍", "🌙", "🪞", "🫧"]
DAY_EMOJIS_CR = ["🌸", "✈️", "💫", "🌿", "🤍", "☀️"]

# Melhores horários baseados no público PT/BR feminino 20-35
BEST_TIMES = [
    "19h00–21h00 (hora de Lisboa) — pico de engagement para o teu público",
    "12h00–13h00 (hora de Lisboa) — pausa do almoço, alto tráfego",
    "20h00–22h00 (hora de Lisboa) — melhor para Reels e saves",
    "18h30–20h00 (hora de Lisboa) — saída do trabalho, muito engagement",
]


def generate_post_sd():
    angle = random.choice(ANGLES_SD)
    prompt = f"""Sugere 1 ideia de post para o Instagram da Swift Delux,
marca de joias minimalistas, público feminino 20-36 anos na Europa.
Ângulo: {angle}

Responde APENAS em JSON válido:
{{
  "conceito_visual": "descrição do que mostrar na imagem/vídeo (máx 1 frase)",
  "legenda": "legenda em português europeu, tom aspiracional, 2-3 frases + emoji",
  "hashtags": ["#tag1","#tag2","#tag3","#tag4","#tag5","#tag6","#tag7","#tag8"],
  "cta": "call to action curto para o final da legenda"
}}"""
    return _call_claude(prompt, 400)


def generate_post_cr():
    angle = random.choice(ANGLES_CR)
    prompt = f"""Sugere 1 ideia de post para o Instagram de Cristiana Rodrigues,
influencer portuguesa de lifestyle, wellness, viagens e beleza.
P�blico: mulheres 20-35 anos, Portugal e Brasil.
Ângulo: {angle}

Responde APENAS em JSON válido:
{{
  "conceito_visual": "descrição do que mostrar na imagem/vídeo (máx 1 frase)",
  "legenda": "legenda em português europeu, tom autêntico e aspiracional, 2-3 frases + emoji",
  "hashtags": ["#tag1","#tag2","#tag3","#tag4","#tag5","#tag6","#tag7","#tag8","#tag9","#tag10"],
  "cta": "call to action curto para o final da legenda"
}}"""
    return _call_claude(prompt, 400)


def _call_claude(prompt, max_tokens):
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    response.raise_for_status()
    text = response.json()["content"][0]["text"]
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def load_dados():
    try:
        with open("dados.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"events": []}


def send_telegram(text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
    )


def format_post_sd(idea):
    emoji = random.choice(DAY_EMOJIS_SD)
    line = "─" * 22
    today = datetime.now().strftime("%d/%m/%Y")
    hashtags = " ".join(idea["hashtags"])
    best_time = random.choice(BEST_TIMES)
    return (
        f"{emoji} <b>SWIFT DELUX · POST DO DIA · {today}</b>\n"
        f"<code>{line}</code>\n\n"
        f"🎬 <b>Conceito:</b> {idea['conceito_visual']}\n\n"
        f"📝 <b>Legenda:</b>\n<i>{idea['legenda']}</i>\n\n"
        f"👉 {idea['cta']}\n\n"
        f"🏷️ <code>{hashtags}</code>\n\n"
        f"⏰ <b>Melhor horário:</b> {best_time}\n\n"
        f"<code>{line}</code>\n"
        f"<i>🤖 THE AGENCY · Content Agent</i>"
    )


def format_post_cr(idea):
    emoji = random.choice(DAY_EMOJIS_CR)
    line = "─" * 22
    today = datetime.now().strftime("%d/%m/%Y")
    hashtags = " ".join(idea["hashtags"])
    best_time = random.choice(BEST_TIMES)
    return (
        f"{emoji} <b>@CRIS · POST DO DIA · {today}</b>\n"
        f"<code>{line}</code>\n\n"
        f"🎬 <b>Conceito:</b> {idea['conceito_visual']}\n\n"
        f"📝 <b>Legenda:</b>\n<i>{idea['legenda']}</i>\n\n"
        f"👉 {idea['cta']}\n\n"
        f"🏷️ <code>{hashtags}</code>\n\n"
        f"⏰ <b>Melhor horário:</b> {best_time}\n\n"
        f"<code>{line}</code>\n"
        f"<i>🤖 THE AGENCY · Content Agent</i>"
    )


def format_email_summary():
    """Resumo diário de emails das últimas 24h."""
    dados = load_dados()
    events = dados.get("events", [])
    from datetime import timedelta
    ago24 = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    recent = [e for e in events if e.get("type") == "email" and e.get("timestamp", "") > ago24]
    total = len(recent)
    urgentes = sum(1 for e in recent if "urgente" in e.get("summary", "").lower())
    clientes = sum(1 for e in recent if "cliente" in e.get("summary", "").lower())
    fornecedores = sum(1 for e in recent if "fornecedor" in e.get("summary", "").lower())

    if total == 0:
        return None

    line = "─" * 22
    return (
        f"📊 <b>RESUMO DE EMAILS · {datetime.now().strftime('%d/%m/%Y')}</b>\n"
        f"<code>{line}</code>\n\n"
        f"📧 <b>Total recebidos (24h):</b> {total}\n"
        f"🔴 Urgentes: {urgentes}\n"
        f"💎 Clientes: {clientes}\n"
        f"📦 Fornecedores: {fornecedores}\n\n"
        f"<i>Abre o dashboard para ver as respostas sugeridas.</i>\n\n"
        f"<code>{line}</code>\n"
        f"<i>🤖 THE AGENCY · Email Summary</i>"
    )


def main():
    # Post Swift Delux
    try:
        idea_sd = generate_post_sd()
        send_telegram(format_post_sd(idea_sd))
        add_event("post", idea_sd["legenda"][:80])
        print("✅ Post Swift Delux enviado")
    except Exception as e:
        print(f"⚠️ Erro post SD: {e}")

    # Post Cristiana
    try:
        idea_cr = generate_post_cr()
        send_telegram(format_post_cr(idea_cr))
        add_event("post_cr", idea_cr["legenda"][:80])
        print("✅ Post Cristiana enviado")
    except Exception as e:
        print(f"⚠️ Erro post CR: {e}")

    # Resumo de emails
    try:
        summary = format_email_summary()
        if summary:
            send_telegram(summary)
            print("✅ Resumo de emails enviado")
        else:
            print("Sem emails nas últimas 24h para resumir")
    except Exception as e:
        print(f"⚠️ Erro resumo emails: {e}")


if __name__ == "__main__":
    main()
