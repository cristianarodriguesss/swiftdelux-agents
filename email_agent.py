import imaplib
import email
from email.header import decode_header
import os
import sys
import requests
import json
from datetime import datetime, timedelta

print("=== EMAIL AGENT START ===", flush=True)

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

print("Gmail user: " + GMAIL_USER, flush=True)
print("Has password: " + str(bool(GMAIL_APP_PASSWORD)), flush=True)


def send_telegram(text):
    try:
        requests.post(
            "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as e:
        print("Telegram error: " + str(e), flush=True)


try:
    from dashboard_data import add_event
except Exception as e:
    print("dashboard_data import error: " + str(e), flush=True)
    def add_event(t, s): pass


def classify_email(sender, subject, body):
    prompt = "Analisa este email recebido.\n"
    prompt += "De: " + sender + "\n"
    prompt += "Assunto: " + subject + "\n"
    prompt += "Corpo: " + body[:500] + "\n\n"
    prompt += "Responde em JSON: {categoria: urgente|cliente|fornecedor|spam|outro, resumo: 1 frase, resposta: rascunho}"

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 400,
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=30
    )
    text = resp.json()["content"][0]["text"]
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def main():
    print("Connecting to Gmail...", flush=True)
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        print("IMAP connected", flush=True)
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        print("Login OK", flush=True)
        mail.select("inbox")

        since = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
        print("Searching since " + since, flush=True)
        status, data = mail.search(None, "(SINCE " + since + ")")
        ids = data[0].split()
        print("Found " + str(len(ids)) + " emails", flush=True)

        if not ids:
            print("No emails found", flush=True)
            mail.logout()
            return

        emails = []
        for eid in ids[-10:]:
            try:
                status, msg_data = mail.fetch(eid, "(RFC822)")
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)
                subject, enc = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(enc or "utf-8", errors="ignore")
                sender = msg.get("From", "Unknown")
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
                emails.append({"subject": subject, "sender": sender, "body": body[:1000]})
            except Exception as e:
                print("Error reading email: " + str(e), flush=True)

        mail.logout()
        print("Processing " + str(len(emails)) + " emails...", flush=True)

        for em in emails:
            try:
                analysis = classify_email(em["sender"], em["subject"], em["body"])
                categoria = analysis.get("categoria", "outro")

                if categoria == "spam":
                    print("Spam skipped: " + em["subject"], flush=True)
                    continue

                line = "-" * 22
                resumo = analysis.get("resumo", "")
                resposta = analysis.get("resposta", "")
                msg_text = (
                    "<b>EMAIL - " + categoria.upper() + "</b>
"
                    "<code>" + line + "</code>

"
                    "De: " + em["sender"] + "
"
                    "Assunto: " + em["subject"] + "

"
                    "<i>" + resumo + "</i>

"
                    "Resposta sugerida:
" + resposta + "

"
                    "<i>THE AGENCY</i>"
                )
                send_telegram(msg_text)
                add_event("email", categoria + ": " + resumo)
                print("OK processed: " + em["subject"], flush=True)

            except Exception as e:
                print("Error processing: " + str(e), flush=True)
                send_telegram("Erro email: " + em.get("subject", "?") + " - " + str(e)[:100])

    except Exception as e:
        print("CRITICAL ERROR: " + str(e), flush=True)
        import traceback
        traceback.print_exc()
        send_telegram("Erro critico email agent: " + str(e)[:200])


if __name__ == "__main__":
    main()
    print("=== EMAIL AGENT DONE ===", flush=True)
