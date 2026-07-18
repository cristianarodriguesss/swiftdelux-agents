"""
THE AGENCY - Outreach Agent
Le mensagens do Telegram com /marca @handle
Pesquisa email da marca e envia email de parceria automaticamente.
Corre de hora a hora.
"""

import os
import json
import requests
import time
import imaplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GMAIL_USER = os.environ.get("GMAIL_USER", "cristianarodriguesss.pr@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")


def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=15
        )
    except Exception as e:
        print(f"Telegram error: {e}", flush=True)


def call_claude(prompt, max_tokens=800):
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-sonnet-4-6", "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]},
        timeout=30
    )
    text = resp.json()["content"][0]["text"].strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def get_telegram_updates(offset=None):
    """Busca mensagens novas do bot"""
    params = {"timeout": 5, "allowed_updates": ["message"]}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
            params=params, timeout=10
        )
        return r.json().get("result", [])
    except Exception as e:
        print(f"Telegram getUpdates error: {e}", flush=True)
        return []


def load_processed():
    """Load list of processed update IDs"""
    try:
        with open("outreach_state.json", "r") as f:
            return json.load(f)
    except Exception:
        return {"processed_ids": [], "last_offset": 0, "sent_brands": []}


def save_processed(state):
    try:
        with open("outreach_state.json", "w") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Save state error: {e}", flush=True)


def find_brand_info(handle):
    """Pesquisa info e email da marca via Claude"""
    prompt = f"""A marca de Instagram {handle} foi identificada para parceria com Cristiana Rodrigues, influencer portuguesa de lifestyle/wellness/viagens/beleza (6.959 seguidores, público 25-34 anos, Portugal e Brasil).

Pesquisa tudo o que sabes sobre esta marca:
1. Nome oficial da marca
2. Website
3. Email de imprensa ou parcerias (press@, partnerships@, collab@, hello@, info@)
4. Nicho/categoria
5. Porque seria uma boa parceria para a Cristiana

Se nao conheceres o email exato, sugere o mais provavel baseado no dominio da marca.

Responde APENAS em JSON:
{{"nome": "...", "website": "...", "email": "...", "email_confianca": "alta/media/baixa", "nicho": "...", "razao_parceria": "..."}}"""

    try:
        text = call_claude(prompt, 500)
        return json.loads(text)
    except Exception as e:
        print(f"Erro find_brand_info: {e}", flush=True)
        return None


def generate_outreach_email(brand_info, handle):
    """Gera email de outreach personalizado"""
    prompt = f"""Escreve um email de parceria de Cristiana Rodrigues para a marca {brand_info.get('nome', handle)}.

Sobre a Cristiana:
- Influencer portuguesa de lifestyle, wellness, viagens e beleza
- 6.959 seguidores no Instagram (@cristianarodriguesss)
- Publico: mulheres 25-34 anos, Portugal (64%) e Brasil (24%)
- 7.513 visualizacoes ultimos 30 dias, 66,6% nao seguidores
- Manager: Artur Santos (talent manager)
- Media kit: https://cristianarodriguesss.my.canva.site/cristianarodriguesss

Sobre a marca:
- Nome: {brand_info.get('nome', handle)}
- Instagram: {handle}
- Nicho: {brand_info.get('nicho', 'moda/lifestyle')}
- Razao de parceria: {brand_info.get('razao_parceria', '')}

Escreve um email em ingles, profissional mas caloroso, curto (max 150 palavras), que:
1. Se apresenta brevemente
2. Explica porque a marca e perfeita para a Cristiana
3. Propoe colaboracao (post, story, reel)
4. Inclui link do media kit
5. Assina como Artur Santos, Talent Manager

Responde APENAS em JSON:
{{"assunto": "...", "corpo": "..."}}"""

    try:
        text = call_claude(prompt, 600)
        return json.loads(text)
    except Exception as e:
        print(f"Erro generate_email: {e}", flush=True)
        return None


def send_email(to_email, subject, body):
    """Envia email via Gmail"""
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Erro send_email: {e}", flush=True)
        return False


def process_marca_command(handle, state):
    """Processa comando /marca @handle"""
    handle = handle.strip().lstrip('@')
    full_handle = f"@{handle}"

    # Check if already sent
    if handle.lower() in [b.lower() for b in state.get("sent_brands", [])]:
        send_telegram(f"⚠️ Já enviaste um outreach para <b>{full_handle}</b> anteriormente.")
        return

    send_telegram(f"🔍 A pesquisar informação sobre <b>{full_handle}</b>...")

    # Find brand info
    brand_info = find_brand_info(full_handle)
    if not brand_info:
        send_telegram(f"❌ Não consegui encontrar informação sobre {full_handle}. Tenta com o nome da marca em vez do handle.")
        return

    email = brand_info.get("email")
    if not email:
        send_telegram(
            f"⚠️ <b>{brand_info.get('nome', handle)}</b>\n"
            f"Não consegui encontrar o email de contacto.\n"
            f"Website: {brand_info.get('website', 'não encontrado')}\n"
            f"Tenta encontrar manualmente em: {brand_info.get('website', '')}/contact"
        )
        return

    # Generate email
    email_content = generate_outreach_email(brand_info, full_handle)
    if not email_content:
        send_telegram(f"❌ Erro ao gerar email para {full_handle}.")
        return

    # Send email
    sent = send_email(email, email_content["assunto"], email_content["corpo"])

    conf_emoji = {"alta": "🟢", "media": "🟡", "baixa": "🔴"}.get(brand_info.get("email_confianca", "baixa"), "⚪")

    if sent:
        state["sent_brands"].append(handle.lower())
        line = "─" * 22
        msg = (
            f"✅ <b>EMAIL ENVIADO!</b>\n"
            f"<code>{line}</code>\n\n"
            f"<b>Marca:</b> {brand_info.get('nome', handle)}\n"
            f"<b>Instagram:</b> {full_handle}\n"
            f"<b>Email:</b> <code>{email}</code> {conf_emoji}\n"
            f"<b>Nicho:</b> {brand_info.get('nicho', '')}\n\n"
            f"<b>Assunto enviado:</b>\n<i>{email_content['assunto']}</i>\n\n"
            f"<b>Email enviado:</b>\n{email_content['corpo'][:300]}...\n\n"
            f"<i>THE AGENCY · Outreach Agent</i>"
        )
        send_telegram(msg)
        print(f"OK Email enviado para {email} ({handle})", flush=True)
    else:
        # Email failed - send preview for manual sending
        line = "─" * 22
        msg = (
            f"⚠️ <b>EMAIL GERADO (envio manual)</b>\n"
            f"<code>{line}</code>\n\n"
            f"<b>Para:</b> <code>{email}</code> {conf_emoji}\n"
            f"<b>Assunto:</b> {email_content['assunto']}\n\n"
            f"{email_content['corpo']}\n\n"
            f"<i>THE AGENCY · Outreach Agent</i>"
        )
        send_telegram(msg)


def main():
    print("=== OUTREACH AGENT START ===", flush=True)

    state = load_processed()
    updates = get_telegram_updates(state.get("last_offset", 0))

    if not updates:
        print("Sem mensagens novas", flush=True)
        return

    for update in updates:
        update_id = update.get("update_id", 0)
        if update_id <= state.get("last_offset", 0):
            continue

        state["last_offset"] = update_id + 1

        msg = update.get("message", {})
        text = msg.get("text", "").strip()
        chat_id = str(msg.get("chat", {}).get("id", ""))

        # Only process messages from our chat
        if chat_id != str(TELEGRAM_CHAT_ID):
            continue

        print(f"Message: {text}", flush=True)

        # Handle /marca command
        if text.lower().startswith("/marca"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                send_telegram(
                    "📝 <b>Como usar:</b>\n"
                    "<code>/marca @handle_da_marca</code>\n\n"
                    "Exemplos:\n"
                    "<code>/marca @zara</code>\n"
                    "<code>/marca @mango</code>\n"
                    "<code>/marca @rituals</code>"
                )
            else:
                handle = parts[1].strip()
                process_marca_command(handle, state)
                time.sleep(2)

        # Help command
        elif text.lower() in ["/help", "/start", "/ajuda"]:
            send_telegram(
                "🤝 <b>OUTREACH AGENT</b>\n\n"
                "Envia-me uma marca para contactar:\n"
                "<code>/marca @handle_da_marca</code>\n\n"
                "Eu vou:\n"
                "1. Pesquisar o email da marca\n"
                "2. Gerar um email de parceria personalizado\n"
                "3. Enviar automaticamente em teu nome\n"
                "4. Confirmar aqui no Telegram\n\n"
                "<i>THE AGENCY · Outreach Agent</i>"
            )

    save_processed(state)
    print("=== OUTREACH AGENT DONE ===", flush=True)


if __name__ == "__main__":
    main()
