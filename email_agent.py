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

print(f"Gmail user: {GMAIL_USER}", flush=True)
print(f"Has password: {bool(GMAIL_APP_PASSWORD)}", flush=True)

def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as e:
        print(f"Telegram error: {e}", flush=True)

try:
    from dashboard_data import add_event
except Exception as e:
    print(f"dashboard_data import error: {e}", flush=True)
    def add_event(t, s): pass

def main():
    print("Connecting to Gmail...", flush=True)
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        print("IMAP connected", flush=True)
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        print("Login OK", flush=True)
        mail.select("inbox")
        since = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
        print(f"Searching since {since}...", flush=True)
        status, data = mail.search(None, f"(SINCE {since})")
        ids = data[0].split()
        print(f"Found {len(ids)} emails", flush=True)

        if not ids:
            print("No emails found", flush=True)
            send_telegram("No emails in last 24h.")
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
                            except:
                                pass
                            break
                else:
                    try:
                        body = msg.get_payload(decode=True).decode(errors="ignore")
                    except:
                        body = str(msg.get_payload())
                emails.append({"subject": subject, "sender": sender, "body": body[:1000]})
            except Exception as e:
                print(f"Error reading email: {e}", flush=True)

        mail.logout()
        print(f"Processing {len(emails)} emails...", flush=True)

        for em in emails:
            try:
                prompt = (
                    "Analisa este email recebido pela Swift Delux ou Cristiana Rodrigues.\n\n"
                    f"De: {em['sender']}\nAssunto: {em['subject']}\nCorpo: {em['body']}\n\n"
                    'Responde APENAS em JSON: {"categoria":"urgente|cliente|fornecedor|spam|outro","resumo":"1 frase","resposta":"rascunho de resposta"}\'
                )
                resp = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                    json={"model": "claude-sonnet-4-6", "max_tokens": 400, "messages": [{"role": "user", "content": prompt}]},
                    timeout=30
                )
                text = resp.json()["content"][0]["text"]
                text = text.strip().replace("```json","").replace("```","").strip()
                analysis = json.loads(text)

                if analysis["categoria"] == "spam":
                    print(f"Spam: {em['subject']}", flush=True)
                    continue

                emojis = {"urgente":"XX","cliente":"XX","fornecedor":"XX","outro":"XX"}
                emoji = emojis.get(analysis["categoria"], "XX")
                line = "-" * 22
                msg_text = (
                    f"{emoji} <b>EMAIL - {analysis['categoria'].upper()}</b>\n"
                    f"<code>{line}</code>\n\n"
                    f"De: {em['sender']}\n"
                    f"Assunto: {em['subject']}\n\n"
                    f"<i>{analysis['resumo']}</i>\n\n"
                    f"Resposta sugerida:\n{analysis['resposta']}\n\n"
                    f"<i>THE AGENCY</i>"
                )
                send_telegram(msg_text)
                add_event("email", f"{analysis['categoria']}: {analysis['resumo']}")
                print(f"OK: {em['subject']}", flush=True)
            except Exception as e:
                print(f"Error processing email: {e}", flush=True)
                send_telegram(f"Erro a processar email: {em.get('subject','?')} - {str(e)[:100]}")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        send_telegram(f"Erro critico no email agent: {str(e)[:200]}")

if __name__ == "__main__":
    main()
    print("=== EMAIL AGENT DONE ===", flush=True)
