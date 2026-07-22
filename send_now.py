import requests, re, smtplib, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_telegram(text):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

def find_email(website):
    pages = ["", "/contact", "/pages/contact", "/press", "/customer-service", "/help"]
    for path in pages:
        try:
            r = requests.get(website + path, headers=HEADERS, timeout=10, allow_redirects=True)
            if r.status_code == 200:
                emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", r.text)
                skip = ["example.com","sentry.io","shopify.com","schema.org","wix.com"]
                valid = [e.lower() for e in emails if not any(s in e.lower() for s in skip) and e.lower() != GMAIL_USER.lower()]
                if valid:
                    for e in valid:
                        if any(k in e for k in ["press","partner","collab","pr@","influencer"]):
                            return e
                    for e in valid:
                        if any(k in e for k in ["hello","info","contact","customercare"]):
                            return e
                    return valid[0]
        except Exception as ex:
            print(f"{path}: {ex}", flush=True)
    return None

brand_name = "Vashi"
email = find_email("https://www.vashi.com")
print(f"Found: {email}", flush=True)

if not email:
    email = "info@vashi.com"  # fallback

subject = f"Partnership Opportunity - Cristiana Rodrigues x {brand_name}"
body = f"""Hi {brand_name} team! \U0001F495

I'm Artur Santos, manager of Cristiana Rodrigues (@cristianarodriguesss), a Portuguese lifestyle, wellness & beauty influencer with a highly engaged audience of 6,959 followers on Instagram.

Cristiana's profile reaches 100k+ monthly views, with 66% coming from non-followers \u2014 meaning real organic discovery. Her audience is predominantly women aged 25\u201334, based in Portugal and Brazil, making her a perfect fit for {brand_name}'s elegant world.

We'd love to explore a gifting collaboration \u2014 beautiful pieces in exchange for authentic story/post content.

\U0001F4CE Media Kit: https://cristianarodriguesss.my.canva.site/cristianarodriguesss

Would you be open to chatting?

Warm regards,
Artur Santos"""

msg = MIMEMultipart()
msg["From"] = GMAIL_USER
msg["To"] = email
msg["Subject"] = subject
msg.attach(MIMEText(body, "plain"))

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
    send_telegram(f"EMAIL ENVIADO PARA VASHI!\n\nPara: {email}\n\nTHE AGENCY")
    print(f"Sent to {email}", flush=True)
except Exception as e:
    send_telegram(f"Erro Vashi: {str(e)}\n\nPara: {email}\nAssunto: {subject}\n\n{body}")
    print(f"Error: {e}", flush=True)
