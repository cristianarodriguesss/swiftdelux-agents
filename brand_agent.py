"""
THE AGENCY - Brand Agent v2
Sugere e contacta automaticamente marcas relevantes para Cristiana Rodrigues.
Corre às quartas-feiras.
"""

import os, json, requests, time, smtplib, base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GMAIL_USER = os.environ.get("GMAIL_USER", "cristianarodriguesss.pr@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = "cristianarodriguesss/swiftdelux-agents"

# Marcas já contactadas (não voltar a contactar)
BRANDS_DB_FILE = "brands_contacted.json"

# Nicho da Cristiana
NICHO = """
Cristiana Rodrigues - influencer portuguesa, lifestyle/wellness/viagens/beleza
6.959 seguidores IG (@cristianarodriguesss)
Público: mulheres 25-34, Portugal (64%) e Brasil (24%)
Nichos: fatos de treino/activewear, roupa casual/moda, malas e acessórios, yoga/pilates, calçado, beleza, viagens, wellness
"""

# Lista de marcas por categoria para contactar automaticamente
AUTO_BRANDS = {
    "activewear_yoga": [
        {"nome": "Girlfriend Collective", "ig": "@girlfriendcollective", "email": "press@girlfriendcollective.com", "alt": ["influencer@girlfriendcollective.com"]},
        {"nome": "Lululemon Portugal", "ig": "@lululemon", "email": "influencer@lululemon.com", "alt": ["press@lululemon.com"]},
        {"nome": "Alo Yoga", "ig": "@aloyoga", "email": "influencer@aloyoga.com", "alt": ["press@aloyoga.com", "partnerships@aloyoga.com"]},
        {"nome": "Vuori", "ig": "@vuoriclothing", "email": "influencer@vuoriclothing.com", "alt": ["press@vuoriclothing.com"]},
        {"nome": "Adidas Women", "ig": "@adidaswomen", "email": "influencer.eu@adidas.com", "alt": ["press@adidas.com"]},
        {"nome": "Nike Women", "ig": "@nikewomen", "email": "influencer.eu@nike.com", "alt": ["press@nike.com"]},
        {"nome": "Decathlon Portugal", "ig": "@decathlonportugal", "email": "marketing@decathlon.pt", "alt": ["press@decathlon.pt"]},
        {"nome": "Sismo Active", "ig": "@sismoactive", "email": "info@sismoactive.com", "alt": ["geral@sismoactive.com"]},
    ],
    "moda_roupa": [
        {"nome": "Zara", "ig": "@zara", "email": "press@zara.com", "alt": ["influencer@zara.com"]},
        {"nome": "Mango", "ig": "@mango", "email": "press@mango.com", "alt": ["influencer@mango.com", "pr@mango.com"]},
        {"nome": "& Other Stories", "ig": "@andotherstories", "email": "press@andotherstories.com", "alt": ["influencer@andotherstories.com"]},
        {"nome": "Arket", "ig": "@arketofficial", "email": "press@arket.com", "alt": []},
        {"nome": "COS", "ig": "@cosstores", "email": "press@cosstores.com", "alt": ["influencer@cosstores.com"]},
        {"nome": "Massimo Dutti", "ig": "@massimodutti", "email": "press@massimodutti.com", "alt": []},
        {"nome": "Pull & Bear", "ig": "@pullandbear", "email": "press@pullandbear.com", "alt": []},
        {"nome": "Stradivarius", "ig": "@stradivarius", "email": "press@stradivarius.com", "alt": []},
    ],
    "malas_acessorios": [
        {"nome": "Parfois", "ig": "@parfois", "email": "marketing@parfois.com", "alt": ["press@parfois.com", "influencer@parfois.com"]},
        {"nome": "Primark Accessories", "ig": "@primark", "email": "press@primark.com", "alt": []},
        {"nome": "Tous", "ig": "@tous", "email": "press@tous.com", "alt": ["influencer@tous.com"]},
        {"nome": "Mango Accessories", "ig": "@mango", "email": "accessories.press@mango.com", "alt": ["press@mango.com"]},
    ],
    "calcado": [
        {"nome": "Zara Shoes", "ig": "@zara", "email": "press@zara.com", "alt": []},
        {"nome": "Alohas", "ig": "@alohas", "email": "press@alohas.com", "alt": ["influencer@alohas.com", "hello@alohas.com"]},
        {"nome": "Steve Madden", "ig": "@stevemadden", "email": "press@stevemadden.com", "alt": ["influencer@stevemadden.com"]},
        {"nome": "Veja Shoes", "ig": "@veja", "email": "press@veja-store.com", "alt": ["contact@veja-store.com"]},
        {"nome": "Golden Goose", "ig": "@goldengoose", "email": "press@goldengoose.com", "alt": []},
    ],
    "wellness_beleza": [
        {"nome": "Rituals", "ig": "@rituals", "email": "press@rituals.com", "alt": ["influencer@rituals.com", "partnerships@rituals.com"]},
        {"nome": "Sol de Janeiro", "ig": "@soldejaneiro", "email": "press@soldejaneiro.com", "alt": ["influencer@soldejaneiro.com"]},
        {"nome": "Glossier", "ig": "@glossier", "email": "press@glossier.com", "alt": ["influencer@glossier.com"]},
        {"nome": "NARS Cosmetics", "ig": "@narsissist", "email": "press@narscosmetics.com", "alt": []},
        {"nome": "Charlotte Tilbury", "ig": "@charlottetilbury", "email": "press@charlottetilbury.com", "alt": []},
        {"nome": "Lush Cosmetics", "ig": "@lushcosmetics", "email": "press@lush.com", "alt": []},
    ]
}

CATEGORY_LABELS = {
    "activewear_yoga": "🏋️ Activewear & Yoga",
    "moda_roupa": "👗 Moda & Roupa",
    "malas_acessorios": "👜 Malas & Acessórios",
    "calcado": "👠 Calçado",
    "wellness_beleza": "✨ Wellness & Beleza",
}


def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=15
        )
    except Exception as e:
        print(f"Telegram error: {e}", flush=True)


def call_claude(prompt, max_tokens=600):
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-sonnet-4-6", "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]},
        timeout=30
    )
    text = resp.json()["content"][0]["text"].strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"): text = text[4:]
    return text.strip()


def load_contacted():
    try:
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{BRANDS_DB_FILE}",
            headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            db = json.loads(base64.b64decode(data['content']).decode())
            db['_sha'] = data['sha']
            return db
    except Exception as e:
        print(f"Load contacted error: {e}", flush=True)
    return {"contacted": [], "_sha": None}


def save_contacted(db):
    sha = db.pop('_sha', None)
    try:
        content = base64.b64encode(json.dumps(db, indent=2, ensure_ascii=False).encode()).decode()
        payload = {"message": "Update brands contacted", "content": content}
        if sha:
            payload["sha"] = sha
        requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{BRANDS_DB_FILE}",
            json=payload,
            headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"},
            timeout=10
        )
    except Exception as e:
        print(f"Save contacted error: {e}", flush=True)


def generate_email(brand):
    prompt = f"""Escreve um email de parceria de Cristiana Rodrigues para {brand['nome']}.

Cristiana Rodrigues:
- Influencer portuguesa de lifestyle, wellness, viagens e beleza
- 6.959 seguidores Instagram ({brand['ig']})
- Público: mulheres 25-34 anos, Portugal (64%) e Brasil (24%)
- 7.513 visualizações últimos 30 dias, 66% de não seguidores
- Manager: Artur Santos
- Media kit: https://cristianarodriguesss.my.canva.site/cristianarodriguesss

Email em inglês, profissional mas caloroso, máximo 150 palavras.
Menciona que está completamente aberta a receber produtos em troca de um story ou publicação (gifting collaboration).
Personaliza para a marca {brand['nome']}.
Assina como Artur Santos, Talent Manager.

Responde APENAS em JSON: {{"assunto":"...","corpo":"..."}}"""

    try:
        text = call_claude(prompt, 600)
        return json.loads(text)
    except Exception as e:
        print(f"generate_email error: {e}", flush=True)
        return None


def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"send_email error to {to_email}: {e}", flush=True)
        return False


def main():
    print("=== BRAND AGENT v2 START ===", flush=True)

    db = load_contacted()
    contacted = [c.lower() for c in db.get("contacted", [])]

    results = {"sent": [], "failed": [], "skipped": []}

    for category, brands in AUTO_BRANDS.items():
        cat_label = CATEGORY_LABELS.get(category, category)
        print(f"\nProcessing {cat_label}...", flush=True)

        for brand in brands:
            brand_key = brand['ig'].lower().lstrip('@')

            if brand_key in contacted:
                print(f"  Skip (already contacted): {brand['nome']}", flush=True)
                results["skipped"].append(brand['nome'])
                continue

            # Generate personalised email
            email_content = generate_email(brand)
            if not email_content:
                print(f"  Failed to generate email for {brand['nome']}", flush=True)
                results["failed"].append(brand['nome'])
                continue

            # Try emails in order
            emails_to_try = [brand['email']] + brand.get('alt', [])
            sent = False
            sent_to = None

            for e in emails_to_try[:3]:
                print(f"  Trying {brand['nome']} -> {e}", flush=True)
                if send_email(e, email_content['assunto'], email_content['corpo']):
                    sent = True
                    sent_to = e
                    break
                time.sleep(2)

            if sent:
                db["contacted"].append(brand_key)
                results["sent"].append({**brand, "sent_to": sent_to, "cat": cat_label})
                print(f"  ✅ Sent to {sent_to}", flush=True)
            else:
                results["failed"].append(brand['nome'])
                print(f"  ❌ Failed: {brand['nome']}", flush=True)

            time.sleep(3)  # Rate limit

    # Save updated contacted list
    save_contacted(db)

    # Send Telegram summary
    line = "─" * 22
    msg = f"🎯 <b>OUTREACH AUTOMÁTICO — RELATÓRIO</b>\n<code>{line}</code>\n\n"

    if results["sent"]:
        msg += f"✅ <b>{len(results['sent'])} emails enviados:</b>\n"
        # Group by category
        by_cat = {}
        for b in results["sent"]:
            cat = b['cat']
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append(b)

        for cat, brands in by_cat.items():
            msg += f"\n<b>{cat}</b>\n"
            for b in brands:
                msg += f"  • {b['nome']} → <code>{b['sent_to']}</code>\n"

    if results["failed"]:
        msg += f"\n❌ <b>{len(results['failed'])} falharam:</b>\n"
        for n in results["failed"]:
            msg += f"  • {n}\n"

    if results["skipped"]:
        msg += f"\n⏭ {len(results['skipped'])} já contactadas anteriormente\n"

    msg += f"\n<i>THE AGENCY · Brand Agent</i>"
    send_telegram(msg)

    print("=== BRAND AGENT v2 DONE ===", flush=True)


if __name__ == "__main__":
    main()
