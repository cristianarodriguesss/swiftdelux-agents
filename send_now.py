import requests, json, smtplib, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

subject = "Partnership Opportunity - Cristiana Rodrigues x Organic Basics"
body = """Hi Organic Basics Team,

I'm reaching out on behalf of Cristiana Rodrigues (@cristianarodriguesss), a Portuguese lifestyle, wellness, and beauty influencer with a highly engaged audience of 6,959 followers - primarily women aged 25-34 based in Portugal and Brazil.

Over the last 30 days, Cristiana's content reached 7,513 views, with 66% coming from non-followers, reflecting strong organic growth and discoverability.

Given Cristiana's focus on conscious living and authentic recommendations, Organic Basics feels like a natural fit. We'd love to explore a gifting collaboration - products in exchange for dedicated story and/or feed content.

You can explore her full media kit here: https://cristianarodriguesss.my.canva.site/cristianarodriguesss

We'd be happy to discuss further. Looking forward to hearing from you!

Warm regards,
Artur Santos
Talent Manager - Cristiana Rodrigues"""

try:
    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = "partnerships@organicbasics.com"
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
    print("Email sent!")
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": "✅ <b>EMAIL ENVIADO!</b>\n\nPara: partnerships@organicbasics.com\nAssunto: Partnership Opportunity - Cristiana Rodrigues x Organic Basics\n\n<i>THE AGENCY</i>", "parse_mode": "HTML"})
except Exception as e:
    print(f"Error: {e}")
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": f"❌ Erro: {str(e)}", "parse_mode": "HTML"})
