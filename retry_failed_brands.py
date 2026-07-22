import os, json, requests, time, smtplib, base64, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = "cristianarodriguesss/swiftdelux-agents"

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

def send_telegram(text):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"TG error: {e}", flush=True)

def call_claude(prompt, max_tokens=600):
    resp = requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-sonnet-4-6", "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]},
        timeout=30)
    text = resp.json()["content"][0]["text"].strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"): text = text[4:]
    return text.strip()

def find_email(website):
    if not website: return None
    if not website.startswith("http"): website = "https://" + website
    pages = ["", "/contact", "/pages/contact", "/press", "/partnerships"]
    for path in pages:
        try:
            r = requests.get(website.rstrip("/") + path, headers=HEADERS, timeout=8, allow_redirects=True)
            if r.status_code == 200:
                emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", r.text)
                skip = ["example.com","sentry.io","shopify.com","schema.org","wix.com"]
                valid = [e.lower() for e in emails if not any(s in e.lower() for s in skip) and e.lower() != GMAIL_USER.lower()]
                if valid:
                    for e in valid:
                        if any(k in e for k in ["press","partner","collab","info","hello"]):
                            return e
                    return valid[0]
        except: continue
    return None

def generate_email(brand_name, cat):
    """Template FIXO"""
    subject = f"Partnership Opportunity - Cristiana Rodrigues x {brand_name}"
    body = f"""Hi {brand_name} team! \U0001F495

I'm Artur Santos, manager of Cristiana Rodrigues (@cristianarodriguesss), a Portuguese lifestyle, wellness & beauty influencer with a highly engaged audience of 6,959 followers on Instagram.

Cristiana's profile reaches 100k+ monthly views, with 66% coming from non-followers \u2014 meaning real organic discovery. Her audience is predominantly women aged 25\u201334, based in Portugal and Brazil, making her a perfect fit for {brand_name}'s world.

We'd love to explore a gifting collaboration \u2014 beautiful pieces in exchange for authentic story/post content.

\U0001F4CE Media Kit: https://cristianarodriguesss.my.canva.site/cristianarodriguesss

Would you be open to chatting?

Warm regards,
Artur Santos"""
    return {"assunto": subject, "corpo": body}

def send_email(to, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"Send error {to}: {e}", flush=True)
        return False

def load_contacted():
    try:
        r = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/contents/brands_contacted.json",
            headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            db = json.loads(base64.b64decode(data["content"]).decode())
            db["_sha"] = data["sha"]
            return db
    except: pass
    return {"contacted": [], "_sha": None}

def save_contacted(db):
    sha = db.pop("_sha", None)
    content = base64.b64encode(json.dumps(db, indent=2, ensure_ascii=False).encode()).decode()
    payload = {"message": "Retry failed brands", "content": content}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GITHUB_REPO}/contents/brands_contacted.json",
        json=payload, headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}, timeout=10)

# Brands that FAILED on the first mass attempt (bounced due to Gmail block)
RETRY_BRANDS = [
    {"nome": "Rohnisch", "ig": "rohnisch", "website": "https://www.rohnisch.com", "cat": "activewear"},
    {"nome": "Sandqvist", "ig": "sandqvist", "website": "https://www.sandqvist.com", "cat": "activewear"},
    {"nome": "Wolven", "ig": "wolvenwear", "website": "https://wolvenwear.com", "cat": "activewear"},
    {"nome": "Nagnata", "ig": "nagnata", "website": "https://nagnata.com", "cat": "activewear"},
    {"nome": "Tala", "ig": "wearetala", "website": "https://wearetala.com", "cat": "activewear"},
    {"nome": "Adanola", "ig": "adanola", "website": "https://www.adanola.com", "cat": "activewear"},
    {"nome": "Pai Skincare", "ig": "paiskincare", "website": "https://www.paiskincare.com", "cat": "beleza"},
    {"nome": "Typology", "ig": "typology", "website": "https://typology.com", "cat": "beleza"},
    {"nome": "Byoma", "ig": "byoma", "website": "https://byoma.com", "cat": "beleza"},
    {"nome": "Medik8", "ig": "medik8", "website": "https://www.medik8.com", "cat": "beleza"},
    {"nome": "Skin Gym", "ig": "skingym", "website": "https://skingym.com", "cat": "acessorios_beleza"},
    {"nome": "Sacheu Beauty", "ig": "sacheubeauty", "website": "https://sacheu.com", "cat": "acessorios_beleza"},
    {"nome": "Mount Lai", "ig": "mountlai", "website": "https://mountlai.com", "cat": "acessorios_beleza"},
    {"nome": "FaceGym", "ig": "facegym", "website": "https://facegym.com", "cat": "acessorios_beleza"},
    {"nome": "Foreo", "ig": "foreo", "website": "https://www.foreo.com", "cat": "acessorios_beleza"},
    {"nome": "Otiumberg", "ig": "otiumberg", "website": "https://otiumberg.com", "cat": "joias"},
    {"nome": "Missoma", "ig": "missoma", "website": "https://missoma.com", "cat": "joias"},
    {"nome": "Ana Luisa", "ig": "analuisany", "website": "https://www.analuisa.com", "cat": "joias"},
    {"nome": "Maria Black", "ig": "mariablackjewellery", "website": "https://www.maria-black.com", "cat": "joias"},
    {"nome": "Polene Paris", "ig": "poleneparis", "website": "https://www.polene-paris.com", "cat": "malas"},
    {"nome": "Strathberry", "ig": "strathberry", "website": "https://www.strathberry.com", "cat": "malas"},
    {"nome": "Cuyana", "ig": "cuyana", "website": "https://www.cuyana.com", "cat": "malas"},
    {"nome": "Wandler", "ig": "wandler_amsterdam", "website": "https://wandler.com", "cat": "malas"},
    {"nome": "Alohas", "ig": "alohas", "website": "https://www.alohas.com", "cat": "calcado"},
    {"nome": "Veja", "ig": "veja", "website": "https://project.veja-store.com", "cat": "calcado"},
    {"nome": "Miista", "ig": "miista", "website": "https://miista.com", "cat": "calcado"},
    {"nome": "By Far", "ig": "byfar_official", "website": "https://byfar.com", "cat": "calcado"},
    {"nome": "Bairro Alto Hotel", "ig": "bairroaltohotel", "website": "https://www.bairroaltohotel.com", "cat": "hoteis"},
    {"nome": "Torel Boutique Hotels", "ig": "torelhotels", "website": "https://www.torel.pt", "cat": "hoteis"},
    {"nome": "Sublime Comporta", "ig": "sublimecomporta", "website": "https://www.sublimecomporta.pt", "cat": "hoteis"},
    {"nome": "Vila Vita Parc", "ig": "vilavitaparc", "website": "https://www.vilavitaparc.com", "cat": "hoteis"},
]

def main():
    print("=== RETRY FAILED BRANDS - FRIDAY ===", flush=True)
    db = load_contacted()
    contacted = set(c.lower() for c in db.get("contacted", []))

    sent_count = 0
    failed_count = 0

    send_telegram("🔄 <b>A reenviar emails que falharam...</b>")

    for brand in RETRY_BRANDS:
        ig = brand["ig"].lower()
        if ig in contacted:
            continue

        print(f"\nProcessing {brand[\'nome\']}", flush=True)
        email = find_email(brand["website"])

        if not email:
            print(f"  No email found", flush=True)
            failed_count += 1
            continue

        email_content = generate_email(brand["nome"], brand["cat"])
        if not email_content:
            failed_count += 1
            continue

        if send_email(email, email_content["assunto"], email_content["corpo"]):
            contacted.add(ig)
            db["contacted"].append(ig)
            sent_count += 1
            print(f"  Sent to {email}", flush=True)
            send_telegram(f"✅ {brand[\'nome\']} → <code>{email}</code>")
        else:
            failed_count += 1

        save_contacted(dict(db))
        time.sleep(300)  # 30 min entre emails

    send_telegram(f"🎯 <b>Retry completo!</b>\n✅ Enviados: {sent_count}\n❌ Falharam: {failed_count}")
    print(f"DONE: {sent_count} sent, {failed_count} failed", flush=True)

if __name__ == "__main__":
    import time
    main()
