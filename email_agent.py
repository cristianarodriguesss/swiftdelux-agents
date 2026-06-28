"""
✨ Swift Delux — Email Agent ✨
Lê emails novos do Gmail, classifica-os com Claude, e envia
uma sugestão de resposta bonita e formatada para o Telegram.
"""

import imaplib
import email
from email.header import decode_header
import os
import requests
import json
from datetime import datetime, timedelta

# ── Configuração (via variáveis de ambiente / GitHub Secrets) ──
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

EMOJIS = {
    "urgente": "🔴",
    "cliente": "💎",
    "fornecedor": "📦",
    "spam": "🗑️",
    "outro": "✉️",
}


def fetch_unread_emails(limit=10):
    """Liga ao Gmail via IMAP e busca emails não lidos das últimas 24h."""
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    mail.select("inbox")

    since = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
    status, data = mail.search(None, f'(UNSEEN SINCE {since})')
    ids = data[0].split()[-limit:]

    emails = []
    for eid in ids:
        status, msg_data = mail.fetch(eid, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="ignore")

        sender = msg.get("From", "Desconhecido")

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode(errors="ignore")
                    except Exception:
                        pass
                    break
        else:
            try:
                body = msg.get_payload(decode=True).decode(errors="ignore")
            except Exception:
                body = str(msg.get_payload())

        emails.append({
            "subject": subject,
            "sender": sender,
            "body": body[:1500],
        })

    mail.logout()
    return emails


def classify_and_draft(email_item):
    """Pede à Claude para classificar o email e sugerir resposta."""
    prompt = f"""Analisa este email recebido pela Swift Delux (marca de joias).

De: {email_item['sender']}
Assunto: {email_item['subject']}
Corpo: {email_item['body']}

Responde APENAS em JSON válido, sem markdown, neste formato exato:
{{
  "categoria": "urgente" | "cliente" | "fornecedor" | "spam" | "outro",
  "resumo": "resumo de 1 frase do que o email pede",
  "resposta_sugerida": "rascunho de resposta profissional e simpática em português, pronta a enviar ou ajustar"
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
            "max_tokens": 600,
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


def format_message(email_item, analysis):
    emoji = EMOJIS.get(analysis["categoria"], "✉️")
    line = "─" * 24
    return (
        f"{emoji} <b>NOVO EMAIL · {analysis['categoria'].upper()}</b>\n"
        f"<code>{line}</code>\n\n"
        f"👤 <b>De:</b> {email_item['sender']}\n"
        f"📌 <b>Assunto:</b> {email_item['subject']}\n\n"
        f"💭 <i>{analysis['resumo']}</i>\n\n"
        f"<code>{line}</code>\n"
        f"✍️ <b>Resposta sugerida:</b>\n\n"
        f"{analysis['resposta_sugerida']}\n\n"
        f"<code>{line}</code>\n"
        f"<i>🤖 Swift Delux Email Agent</i>"
    )


def main():
    emails = fetch_unread_emails()

    if not emails:
        print("Sem emails novos.")
        return

    for email_item in emails:
        try:
            analysis = classify_and_draft(email_item)
            if analysis["categoria"] == "spam":
                continue
            message = format_message(email_item, analysis)
            send_telegram_message(message)
            print(f"✅ Processado: {email_item['subject']}")
        except Exception as e:
            print(f"⚠️ Erro a processar email '{email_item['subject']}': {e}")


if __name__ == "__main__":
    main()
