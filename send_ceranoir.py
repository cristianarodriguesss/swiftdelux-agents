import requests, smtplib, json, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_telegram(text):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)

prompt = """Email de parceria de Cristiana Rodrigues para Ceranoir (marca de joias/acessorios).
Cristiana: influencer portuguesa lifestyle/wellness/viagens/beleza, 6.959 seg IG (@cristianarodriguesss), 25-34 anos, Portugal 64% Brasil 24%, 7.513 views/mes, 66% nao seguidores.
Manager: Artur Santos | Media kit: https://cristianarodriguesss.my.canva.site/cristianarodriguesss
Aberta a gifting (produtos em troca de story/post). Max 130 palavras, ingles, caloroso.
JSON: {"assunto":"...","corpo":"..."}"""

resp = requests.post("https://api.anthropic.com/v1/messages",
    headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
    json={"model": "claude-sonnet-4-6", "max_tokens": 500, "messages": [{"role": "user", "content": prompt}]},
    timeout=30)
text = resp.json()["content"][0]["text"].strip()
if "```" in text:
    text = text.split("```")[1]
    if text.startswith("json"): text = text[4:]
email_content = json.loads(text.strip())

email = "collab@ceranoir.com"
msg = MIMEMultipart()
msg["From"] = GMAIL_USER
msg["To"] = email
msg["Subject"] = email_content["assunto"]
msg.attach(MIMEText(email_content["corpo"], "plain"))

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
    send_telegram("EMAIL ENVIADO PARA CERANOIR!\n\nPara: " + email + "\n\nAssunto: " + email_content["assunto"] + "\n\nCorpo:\n" + email_content["corpo"] + "\n\nTHE AGENCY")
    print("Email sent to " + email, flush=True)
except Exception as e:
    send_telegram("Erro Ceranoir: " + str(e) + "\n\nEmail para enviar manualmente:\nPara: " + email + "\nAssunto: " + email_content["assunto"] + "\n\n" + email_content["corpo"])
    print("Error: " + str(e), flush=True)
