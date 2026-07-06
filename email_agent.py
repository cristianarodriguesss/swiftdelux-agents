import imaplib
import email
from email.header import decode_header
import os
import requests
import json
from datetime import datetime, timedelta

print("EMAIL AGENT START", flush=True)

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

print("User: " + GMAIL_USER, flush=True)


def send_telegram(text):
    try:
        requests.post(
            "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as ex:
        print("Telegram error: " + str(ex), flush=True)


try:
    from dashboard_data import add_event
except Exception:
    def add_event(t, s):
        pass


def get_emails():
    print("Connecting IMAP...", flush=True)
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    print("Login OK", flush=True)
    mail.select("inbox")
    since = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
    print("Searching since " + since, flush=True)
    status, data = mail.search(None, "(SINCE " + since + ")")
    ids = data[0].split()
    print("Found " + str(len(ids)) + " emails", flush=True)
    result = []
    for eid in ids[-10:]:
        try:
            status, msg_data = mail.fetch(eid, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            subject_raw, enc = decode_header(msg["Subject"])[0]
            if isinstance(subject_raw, bytes):
                subject = subject_raw.decode(enc or "utf-8", errors="ignore")
            else:
                subject = str(subject_raw)
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
                    body = ""
            result.append({"subject": subject, "sender": sender, "body": body[:800]})
        except Exception as ex:
            print("Error reading email: " + str(ex), flush=True)
    mail.logout()
    return result


def classify(sender, subject, body):
    prompt = "Analisa este email.\n"
    prompt += "De: " + sender + "\n"
    prompt += "Assunto: " + subject + "\n"
    prompt += "Corpo: " + body[:400] + "\n\n"
    prompt += 'Responde em JSON valido: {"categoria":"urgente","resumo":"resumo","resposta":"resposta"}'
    prompt += "\ncategoria deve ser: urgente, cliente, fornecedor, spam ou outro"

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=30
    )
    text = resp.json()["content"][0]["text"].strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def main():
    try:
        emails = get_emails()
        if not emails:
            print("No emails found", flush=True)
            send_telegram("Sem emails nas ultimas 24h.")
            return

        for em in emails:
            try:
                analysis = classify(em["sender"], em["subject"], em["body"])
                cat = analysis.get("categoria", "outro")
                if cat == "spam":
                    print("Spam: " + em["subject"], flush=True)
                    continue

                resumo = analysis.get("resumo", "")
                resposta = analysis.get("resposta", "")
                line = "=" * 20

                parts = []
                parts.append("<b>EMAIL - " + cat.upper() + "</b>")
                parts.append("<code>" + line + "</code>")
                parts.append("")
                parts.append("De: " + em["sender"])
                parts.append("Assunto: " + em["subject"])
                parts.append("")
                parts.append("<i>" + resumo + "</i>")
                parts.append("")
                parts.append("Resposta sugerida:")
                parts.append(resposta)
                parts.append("")
                parts.append("<i>THE AGENCY</i>")

                send_telegram("\n".join(parts))
                add_event("email", cat + ": " + resumo)
                print("OK: " + em["subject"], flush=True)

            except Exception as ex:
                print("Error: " + str(ex), flush=True)
                send_telegram("Erro email: " + str(ex)[:100])

    except Exception as ex:
        print("CRITICAL: " + str(ex), flush=True)
        import traceback
        traceback.print_exc()
        send_telegram("Erro critico: " + str(ex)[:200])


if __name__ == "__main__":
    main()
    print("EMAIL AGENT DONE", flush=True)
