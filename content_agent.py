"""
â¨ THE AGENCY â Content Agent â¨
Sugere uma ideia de post diÃ¡ria para o Instagram, com legenda,
hashtags, melhor horÃ¡rio, e envia para Telegram com formataÃ§Ã£o bonita.
TambÃ©m envia resumo diÃ¡rio de emails.
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
    "lifestyle aspiracional â a peÃ§a no dia a dia de uma mulher europeia, 20-36 anos",
    "detalhe e brilho â foco no acabamento e qualidade da joia",
    "storytelling de marca â os valores da Swift Delux",
    "look completo â como combinar a peÃ§a com um outfit",
    "presente / momento especial â a joia como prenda",
    "behind the scenes â processo de criaÃ§Ã£o ou embalagem",
]

ANGLES_CR = [
    "wellness matinal â rotina de manhÃ£, mindfulness, self-care",
    "viagem e lifestyle â destino europeu, hotel aesthetic, momento de luxo acessÃ­vel",
    "beleza â skincare rotina, produto favorito do momento, before/after",
    "moda â outfit do dia, tendÃªncia da estaÃ§Ã£o, como combinar peÃ§as",
    "autenticidade â momento real, pensamento do dia, bastidores da vida",
]

DAY_EMOJIS_SD = ["â¨", "ð", "ð¤", "ð", "ðª", "ð«§"]
DAY_EMOJIS_CR = ["ð¸", "âï¸", "ð«", "ð¿", "ð¤", "âï¸"]

# Melhores horÃ¡rios baseados no pÃºblico PT/BR feminino 20-35
BEST_TIMES = [
    "19h00â21h00 (hora de Lisboa) â pico de engagement para o teu pÃºblico",
    "12h00â13h00 (hora de Lisboa) â pausa do almoÃ§o, alto trÃ¡fego",
    "20h00â22h00 (hora de Lisboa) â melhor para Reels e saves",
    "18h30â20h00 (hora de Lisboa) â saÃ­da do trabalho, muito engagement",
]


def generate_post_sd():
    angle = random.choice(ANGLES_SD)
    prompt = f"""Sugere 1 ideia de post para o Instagram da Swift Delux,
marca de joias minimalistas, pÃºblico feminino 20-36 anos na Europa.
Ãngulo: {angle}

Responde APENAS em JSON vÃ¡lido:
{{
  "conceito_visual": "descriÃ§Ã£o do que mostrar na imagem/vÃ­deo (mÃ¡x 1 frase)",
  "legenda": "legenda em portuguÃªs europeu, tom aspiracional, 2-3 frases + emoji",
  "hashtags": ["#tag1","#tag2","#tag3","#tag4","#tag5","#tag6","#tag7","#tag8"],
  "cta": "call to action curto para o final da legenda"
}}"""
    return _call_claude(prompt, 400)


def generate_post_cr():
    angle = random.choice(ANGLES_CR)
    prompt = f"""Sugere 1 ideia de post para o Instagram de Cristiana Rodrigues,
influencer portuguesa de lifestyle, wellness, viagens e beleza.
Pºblico: mulheres 20-35 anos, Portugal e Brasil.
Ãngulo: {angle}

Responde APENAS em JSON vÃ¡lido:
{{
  "conceito_visual": "descriÃ§Ã£o do que mostrar na imagem/vÃ­deo (mÃ¡x 1 frase)",
  "legenda": "legenda em portuguÃªs europeu, tom autÃªntico e aspiracional, 2-3 frases + emoji",
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
    line = "â" * 22
    today = datetime.now().strftime("%d/%m/%Y")
    hashtags = " ".join(idea["hashtags"])
    best_time = random.choice(BEST_TIMES)
    return (
        f"{emoji} <b>SWIFT DELUX Â· POST DO DIA Â· {today}</b>\n"
        f"<code>{line}</code>\n\n"
        f"ð¬ <b>Conceito:</b> {idea['conceito_visual']}\n\n"
        f"ð <b>Legenda:</b>\n<i>{idea['legenda']}</i>\n\n"
        f"ð {idea['cta']}\n\n"
        f"ð·ï¸ <code>{hashtags}</code>\n\n"
        f"â° <b>Melhor horÃ¡rio:</b> {best_time}\n\n"
        f"<code>{line}</code>\n"
        f"<i>ð¤ THE AGENCY Â· Content Agent</i>"
    )


def format_post_cr(idea):
    emoji = random.choice(DAY_EMOJIS_CR)
    line = "â" * 22
    today = datetime.now().strftime("%d/%m/%Y")
    hashtags = " ".join(idea["hashtags"])
    best_time = random.choice(BEST_TIMES)
    return (
        f"{emoji} <b>@CRIS Â· POST DO DIA Â· {today}</b>\n"
        f"<code>{line}</code>\n\n"
        f"ð¬ <b>Conceito:</b> {idea['conceito_visual']}\n\n"
        f"ð <b>Legenda:</b>\n<i>{idea['legenda']}</i>\n\n"
        f"ð {idea['cta']}\n\n"
        f"ð·ï¸ <code>{hashtags}</code>\n\n"
        f"â° <b>Melhor horÃ¡rio:</b> {best_time}\n\n"
        f"<code>{line}</code>\n"
        f"<i>ð¤ THE AGENCY Â· Content Agent</i>"
    )


def format_email_summary():
    """Resumo diÃ¡rio de emails das Ãºltimas 24h."""
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

    line = "â" * 22
    return (
        f"ð <b>RESUMO DE EMAILS Â· {datetime.now().strftime('%d/%m/%Y')}</b>\n"
        f"<code>{line}</code>\n\n"
        f"ð§ <b>Total recebidos (24h):</b> {total}\n"
        f"ð´ Urgentes: {urgentes}\n"
        f"ð Clientes: {clientes}\n"
        f"ð¦ Fornecedores: {fornecedores}\n\n"
        f"<i>Abre o dashboard para ver as respostas sugeridas.</i>\n\n"
        f"<code>{line}</code>\n"
        f"<i>ð¤ THE AGENCY Â· Email Summary</i>"
    )


def main():
    # Briefing diario
    try:
        briefing = generate_briefing()
        if briefing:
            line = "=" * 22
            hl = chr(10).join(f"• {d}" for d in briefing.get("destaques",[]))
            tk = chr(10).join(f"• {t}" for t in briefing.get("tarefas",[]))
            msg = f"OK <b>AGENCY BRIEFING · {briefing['date']}</b>{chr(10)}<code>{line}</code>{chr(10)}{chr(10)}{briefing['resumo']}{chr(10)}{chr(10)}<b>Destaques:</b>{chr(10)}{hl}{chr(10)}{chr(10)}<b>Para hoje:</b>{chr(10)}{tk}{chr(10)}{chr(10)}<i>THE AGENCY</i>"
            send_telegram(msg)
    except Exception as e:
        print(f"Erro briefing: {e}")

    # Post Swift Delux
    try:
        idea_sd = generate_post_sd()
        send_telegram(format_post_sd(idea_sd))
        add_event("post", idea_sd["legenda"][:80])
        print("â Post Swift Delux enviado")
    except Exception as e:
        print(f"â ï¸ Erro post SD: {e}")

    # Post Cristiana
    try:
        idea_cr = generate_post_cr()
        send_telegram(format_post_cr(idea_cr))
        add_event("post_cr", idea_cr["legenda"][:80])
        print("â Post Cristiana enviado")
    except Exception as e:
        print(f"â ï¸ Erro post CR: {e}")

    # Resumo de emails
    try:
        summary = format_email_summary()
        if summary:
            send_telegram(summary)
            print("â Resumo de emails enviado")
        else:
            print("Sem emails nas Ãºltimas 24h para resumir")
    except Exception as e:
        print(f"â ï¸ Erro resumo emails: {e}")


def generate_briefing():
    """Gera o briefing diário e guarda no dados.json."""
    try:
        dados = load_dados()
        events = dados.get("events", [])
        from datetime import timedelta
        ago7 = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        ago24 = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        posts7 = len([e for e in events if e.get("type") in ("post","post_cr") and e.get("timestamp","") > ago7])
        emails24 = len([e for e in events if e.get("type") == "email" and e.get("timestamp","") > ago24])
        deals = len([e for e in events if e.get("type") == "partnership"])
        sd_ig = dados.get("followers",{}).get("count", 0)
        cr_ig = dados.get("cr_followers",{}).get("count", 0)

        prompt = f"""Es assistente de THE AGENCY, agencia portuguesa que gere Swift Delux (joias) e Cristiana Rodrigues (influencer).
Gera um briefing diario conciso em portugues europeu.

Dados actuais:
- Swift Delux IG: {sd_ig} seguidores (meta: 10.000)
- @cristiana IG: {cr_ig} seguidores
- Parcerias fechadas: {deals}
- Emails ultimas 24h: {emails24}
- Posts sugeridos (7 dias): {posts7}

Responde APENAS em JSON valido:
{{"resumo":"1-2 frases sobre o estado actual","destaques":["d1","d2","d3"],"tarefas":["t1","t2","t3","t4"]}}"""

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-6", "max_tokens": 400, "messages": [{"role": "user", "content": prompt}]},
        )
        response.raise_for_status()
        text = response.json()["content"][0]["text"]
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        briefing = json.loads(text)
        briefing["date"] = datetime.now().strftime("%d/%m/%Y")

        # Save to dados.json
        dados["briefing"] = briefing
        with open("dados.json", "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

        print("OK Briefing gerado")
        return briefing
    except Exception as e:
        print(f"Erro briefing: {e}")
        return None


if __name__ == "__main__":
    main()
