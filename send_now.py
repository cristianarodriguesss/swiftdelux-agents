import requests, re, smtplib, json, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

def send_telegram(text):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)

def find_email(website):
    pages = ["", "/contact", "/contacts", "/pages/contact", "/about", "/press", "/partnerships"]
    for path in pages:
        try:
            r = requests.get(website + path, headers=HEADERS, timeout=10, allow_redirects=True)
            if r.status_code == 200:
                emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", r.text)
                skip = ["example.com", "sentry.io", "shopify.com", "schema.org", "wix.com"]
                valid = [e.lower() for e in emails if not any(s in e.lower() for s in skip) and e.lower() != GMAIL_USER.lower()]
                if valid:
                    for e in valid:
                        if any(k in e for k in ["press", "partner", "collab", "info", "hello", "contact"]):
                            return e
                    return valid[0]
        except Exception as ex:
            print(f"Error {path}: {ex}", flush=True)
    return None

def generate_email(brand_name, product_type):
    prompt = f"""Email de parceria Cristiana Rodrigues para {brand_name}.
Cristiana: influencer portuguesa lifestyle/wellness/viagens/beleza, 6.959 seg IG (@cristianarodriguesss), 25-34 anos, Portugal 64% Brasil 24%, 7.513 views/mes, 66% nao seguidores.
Manager: Artur Santos | Media kit: https://cristianarodriguesss.my.canva.site/cristianarodriguesss
Produto da marca: {product_type}
Aberta a gifting (produtos em troca de story/post). Max 130 palavras, ingles, caloroso.
JSON: {{"assunto":"...","corpo":"..."}}"""
    resp = requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-sonnet-4-6", "max_tokens": 500, "messages": [{"role": "user", "content": prompt}]},
        timeout=30)
    text = resp.json()["content"][0]["text"].strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"): text = text[4:]
    return json.loads(text.strip())

print("Searching Ceranoir email...", flush=True)
email = find_email("https://www.ceranoir.com")
print(f"Found: {email}", flush=True)

if not email:
    # Try common patterns
    for attempt in ["info@ceranoir.com", "hello@ceranoir.com", "contact@ceranoir.com"]:
        email = attempt
        break

email_content = generate_email("Ceranoir", "joias e acessorios")

msg = MIMEMultipart()
msg["From"] = GMAIL_USER
msg["To"] = email
msg["Subject"] = email_content["assunto"]
msg.attach(MIMEText(email_content["corpo"], "plain"))

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
    send_telegram(f"✅ <b>Email enviado para Ceranoir!</b>\n\nPara: <code>{email}</code>\n\n<b>Assunto:</b> {email_content[\'assunto\']}\n\n<b>Email:</b>\n{email_content[\'corpo\']}\n\n<i>THE AGENCY</i>")
    print(f"Email sent to {email}", flush=True)
except Exception as e:
    send_telegram(f"❌ Erro Ceranoir: {str(e)}\n\nEmail para enviar manualmente:\nPara: {email}\nAssunto: {email_content[\'assunto\']}\n\n{email_content[\'corpo\']}")
    print(f"Error: {e}", flush=True)
