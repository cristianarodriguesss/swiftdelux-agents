"""
THE AGENCY - Brand Agent v3
Outreach automatico para marcas europeias pequenas/medias.
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
BRANDS_DB_FILE = "brands_contacted.json"

AUTO_BRANDS = {
    "activewear": [
        {"nome": "Sismo Active", "ig": "@sismoactive", "email": "info@sismoactive.com", "alt": ["geral@sismoactive.com"], "pais": "🇵🇹"},
        {"nome": "Girlfriend Collective", "ig": "@girlfriendcollective", "email": "press@girlfriendcollective.com", "alt": ["influencer@girlfriendcollective.com"], "pais": "🇺🇸"},
        {"nome": "Rohnisch", "ig": "@rohnisch", "email": "press@rohnisch.com", "alt": ["info@rohnisch.com", "influencer@rohnisch.com"], "pais": "🇸🇪"},
        {"nome": "Sandqvist", "ig": "@sandqvist", "email": "press@sandqvist.com", "alt": ["info@sandqvist.com"], "pais": "🇸🇪"},
        {"nome": "Organic Basics", "ig": "@organicbasics", "email": "press@organicbasics.com", "alt": ["hello@organicbasics.com"], "pais": "🇩🇰"},
        {"nome": "Wolven", "ig": "@wolvenwear", "email": "press@wolven.com", "alt": ["hello@wolven.com"], "pais": "🇺🇸"},
        {"nome": "Nagnata", "ig": "@nagnata", "email": "press@nagnata.com", "alt": ["hello@nagnata.com"], "pais": "🇦🇺"},
        {"nome": "Varley", "ig": "@varleyactive", "email": "press@varley.com", "alt": ["influencer@varley.com"], "pais": "🇬🇧"},
        {"nome": "Tala", "ig": "@wearetala", "email": "press@wearetala.com", "alt": ["hello@wearetala.com"], "pais": "🇬🇧"},
        {"nome": "Adanola", "ig": "@adanola", "email": "press@adanola.com", "alt": ["hello@adanola.com"], "pais": "🇬🇧"},
    ],
    "beleza_skincare": [
        {"nome": "Pai Skincare", "ig": "@paiskincare", "email": "press@paiskincare.com", "alt": ["hello@paiskincare.com"], "pais": "🇬🇧"},
        {"nome": "Typology", "ig": "@typology", "email": "press@typology.com", "alt": ["contact@typology.com"], "pais": "🇫🇷"},
        {"nome": "Drunk Elephant", "ig": "@drunkelephant", "email": "press@drunkelephant.com", "alt": ["influencer@drunkelephant.com"], "pais": "🇺🇸"},
        {"nome": "Byoma", "ig": "@byoma", "email": "press@byoma.com", "alt": ["hello@byoma.com"], "pais": "🇬🇧"},
        {"nome": "Medik8", "ig": "@medik8", "email": "press@medik8.com", "alt": ["influencer@medik8.com"], "pais": "🇬🇧"},
        {"nome": "Allies of Skin", "ig": "@alliesofskin", "email": "press@alliesofskin.com", "alt": ["hello@alliesofskin.com"], "pais": "🇸🇬"},
        {"nome": "Grown Alchemist", "ig": "@grownalchemist", "email": "press@grownalchemist.com", "alt": ["contact@grownalchemist.com"], "pais": "🇦🇺"},
        {"nome": "Espa", "ig": "@espaskincare", "email": "press@espaskincare.com", "alt": ["info@espaskincare.com"], "pais": "🇬🇧"},
        {"nome": "Sol de Janeiro", "ig": "@soldejaneiro", "email": "press@soldejaneiro.com", "alt": ["influencer@soldejaneiro.com"], "pais": "🇧🇷"},
        {"nome": "Rituals", "ig": "@rituals", "email": "influencer@rituals.com", "alt": ["press@rituals.com"], "pais": "🇳🇱"},
    ],
    "acessorios_beleza": [
        {"nome": "Skin Gym", "ig": "@skingym", "email": "press@skingym.com", "alt": ["hello@skingym.com", "influencer@skingym.com"], "pais": "🇺🇸"},
        {"nome": "Sacheu Beauty", "ig": "@sacheubeauty", "email": "press@sacheu.com", "alt": ["hello@sacheu.com"], "pais": "🇺🇸"},
        {"nome": "Mount Lai", "ig": "@mountlai", "email": "press@mountlai.com", "alt": ["hello@mountlai.com"], "pais": "🇺🇸"},
        {"nome": "Wildling Beauty", "ig": "@wildlingbeauty", "email": "press@wildlingbeauty.com", "alt": ["hello@wildlingbeauty.com"], "pais": "🇩🇪"},
        {"nome": "Nurse Jamie", "ig": "@nursejamie", "email": "press@nursejamie.com", "alt": ["info@nursejamie.com"], "pais": "🇺🇸"},
        {"nome": "FaceGym", "ig": "@facegym", "email": "press@facegym.com", "alt": ["hello@facegym.com"], "pais": "🇬🇧"},
        {"nome": "Foreo", "ig": "@foreo", "email": "press@foreo.com", "alt": ["influencer@foreo.com"], "pais": "🇸🇪"},
        {"nome": "NuFace", "ig": "@nuface", "email": "press@nuface.com", "alt": ["influencer@nuface.com"], "pais": "🇺🇸"},
    ],
    "joias_acessorios": [
        {"nome": "Otiumberg", "ig": "@otiumberg", "email": "press@otiumberg.com", "alt": ["hello@otiumberg.com"], "pais": "🇬🇧"},
        {"nome": "Mejuri", "ig": "@mejuri", "email": "press@mejuri.com", "alt": ["influencer@mejuri.com"], "pais": "🇨🇦"},
        {"nome": "Missoma", "ig": "@missoma", "email": "press@missoma.com", "alt": ["influencer@missoma.com"], "pais": "🇬🇧"},
        {"nome": "Ana Luisa", "ig": "@analuisany", "email": "press@analuisa.com", "alt": ["influencer@analuisa.com"], "pais": "🇺🇸"},
        {"nome": "Edblad", "ig": "@edblad", "email": "press@edblad.com", "alt": ["info@edblad.com"], "pais": "🇸🇪"},
        {"nome": "Maria Black", "ig": "@mariablackjewellery", "email": "press@maria-black.com", "alt": ["hello@maria-black.com"], "pais": "🇩🇰"},
        {"nome": "Emma & Chloe", "ig": "@emmaandchloe", "email": "press@emmaandchloe.com", "alt": ["contact@emmaandchloe.com"], "pais": "🇫🇷"},
        {"nome": "Soru Jewellery", "ig": "@sorujewellery", "email": "press@sorujewellery.com", "alt": ["hello@sorujewellery.com"], "pais": "🇬🇧"},
    ],
    "malas_luxo": [
        {"nome": "Polene Paris", "ig": "@poleneparis", "email": "press@polene-paris.com", "alt": ["contact@polene-paris.com"], "pais": "🇫🇷"},
        {"nome": "Strathberry", "ig": "@strathberry", "email": "press@strathberry.com", "alt": ["hello@strathberry.com"], "pais": "🇬🇧"},
        {"nome": "Yuzefi", "ig": "@yuzefi", "email": "press@yuzefi.com", "alt": ["hello@yuzefi.com"], "pais": "🇬🇧"},
        {"nome": "Cuyana", "ig": "@cuyana", "email": "press@cuyana.com", "alt": ["influencer@cuyana.com"], "pais": "🇺🇸"},
        {"nome": "Staud", "ig": "@staud", "email": "press@staud.clothing", "alt": ["hello@staud.clothing"], "pais": "🇺🇸"},
        {"nome": "A-ESQUE", "ig": "@aesque", "email": "press@a-esque.com", "alt": ["hello@a-esque.com"], "pais": "🇦🇺"},
        {"nome": "Wandler", "ig": "@wandler_amsterdam", "email": "press@wandler.com", "alt": ["hello@wandler.com"], "pais": "🇳🇱"},
        {"nome": "Songmont", "ig": "@songmont_official", "email": "press@songmont.com", "alt": ["hello@songmont.com"], "pais": "🇨🇳"},
    ],
    "calcado": [
        {"nome": "Alohas", "ig": "@alohas", "email": "press@alohas.com", "alt": ["hello@alohas.com", "influencer@alohas.com"], "pais": "🇪🇸"},
        {"nome": "Veja", "ig": "@veja", "email": "press@veja-store.com", "alt": ["contact@veja-store.com"], "pais": "🇫🇷"},
        {"nome": "Miista", "ig": "@miista", "email": "press@miista.com", "alt": ["hello@miista.com"], "pais": "🇬🇧"},
        {"nome": "ATP Atelier", "ig": "@atpatelier", "email": "press@atpatelier.com", "alt": ["hello@atpatelier.com"], "pais": "🇸🇪"},
        {"nome": "By Far", "ig": "@byfar_official", "email": "press@byfar.com", "alt": ["hello@byfar.com"], "pais": "🇧🇬"},
        {"nome": "Intentionally Blank", "ig": "@intentionallyblank", "email": "press@intentionallyblank.com", "alt": ["hello@intentionallyblank.com"], "pais": "🇺🇸"},
        {"nome": "Malone Souliers", "ig": "@malonesouliers", "email": "press@malonesouliers.com", "alt": ["info@malonesouliers.com"], "pais": "🇬🇧"},
    ],
    "hoteis": [
        {"nome": "Bairro Alto Hotel Lisboa", "ig": "@bairroaltohotel", "email": "press@bairroaltohotel.com", "alt": ["marketing@bairroaltohotel.com", "info@bairroaltohotel.com"], "pais": "🇵🇹"},
        {"nome": "Pestana Collection", "ig": "@pestanahotels", "email": "marketing@pestana.com", "alt": ["press@pestana.com"], "pais": "🇵🇹"},
        {"nome": "Torel Boutique Hotels", "ig": "@torelhotels", "email": "marketing@torel.pt", "alt": ["info@torel.pt", "press@torel.pt"], "pais": "🇵🇹"},
        {"nome": "Flores Village Hotel Azores", "ig": "@floresvillage", "email": "info@floresvillage.com", "alt": ["press@floresvillage.com"], "pais": "🇵🇹"},
        {"nome": "Vila Vita Parc", "ig": "@vilavitaparc", "email": "press@vilavitaparc.com", "alt": ["marketing@vilavitaparc.com"], "pais": "🇵🇹"},
        {"nome": "Martinhal Resorts", "ig": "@martinhalresorts", "email": "marketing@martinhal.com", "alt": ["press@martinhal.com"], "pais": "🇵🇹"},
        {"nome": "Sublime Comporta", "ig": "@sublimecomporta", "email": "press@sublimecomporta.com", "alt": ["marketing@sublimecomporta.com", "info@sublimecomporta.com"], "pais": "🇵🇹"},
        {"nome": "Six Senses Douro Valley", "ig": "@sixsensesdourovalley", "email": "reservations-dourovalley@sixsenses.com", "alt": ["press@sixsenses.com"], "pais": "🇵🇹"},
    ]
}

CATEGORY_LABELS = {
    "activewear": "🏋️ Activewear",
    "beleza_skincare": "✨ Beleza & Skincare",
    "acessorios_beleza": "💆 Acessórios de Beleza",
    "joias_acessorios": "💍 Joias & Acessórios",
    "malas_luxo": "👜 Malas",
    "calcado": "👠 Calçado",
    "hoteis": "🏨 Hotéis",
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
        print(f"Load error: {e}", flush=True)
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
        print("State saved", flush=True)
    except Exception as e:
        print(f"Save error: {e}", flush=True)


def generate_email(brand, category):
    is_hotel = category == "hoteis"
    if is_hotel:
        prompt = f"""Escreve um email de Cristiana Rodrigues para o hotel {brand['nome']} a propor uma colaboracao.

Cristiana Rodrigues:
- Influencer portuguesa de lifestyle, wellness e viagens
- 6.959 seguidores Instagram (@cristianarodriguesss)
- Publico: mulheres 25-34 anos, Portugal (64%) e Brasil (24%)
- 7.513 visualizacoes ultimos 30 dias, 66% de nao seguidores
- Media kit: https://cristianarodriguesss.my.canva.site/cristianarodriguesss

Proposta: estadias em troca de conteudo autentico (stories, posts, reels) mostrando a experiencia no hotel.
Email em ingles, profissional, max 130 palavras.
Assina como Artur Santos, Talent Manager.

Responde APENAS em JSON: {{"assunto":"...","corpo":"..."}}"""
    else:
        prompt = f"""Escreve um email de parceria de Cristiana Rodrigues para {brand['nome']} ({brand['ig']}).

Cristiana Rodrigues:
- Influencer portuguesa de lifestyle, wellness, viagens e beleza
- 6.959 seguidores Instagram (@cristianarodriguesss)
- Publico: mulheres 25-34 anos, Portugal (64%) e Brasil (24%)
- 7.513 visualizacoes ultimos 30 dias, 66% de nao seguidores
- Media kit: https://cristianarodriguesss.my.canva.site/cristianarodriguesss

Email em ingles, profissional mas caloroso, max 130 palavras.
Menciona que esta aberta a gifting collaboration (produtos em troca de story/post).
Personaliza para a marca {brand['nome']}.
Assina como Artur Santos, Talent Manager.

Responde APENAS em JSON: {{"assunto":"...","corpo":"..."}}"""

    try:
        text = call_claude(prompt, 500)
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
        print(f"send_email error {to_email}: {e}", flush=True)
        return False


def main():
    print("=== BRAND AGENT v3 START ===", flush=True)

    db = load_contacted()
    contacted = [c.lower() for c in db.get("contacted", [])]
    results = {"sent": [], "failed": []}

    for category, brands in AUTO_BRANDS.items():
        cat_label = CATEGORY_LABELS.get(category, category)
        print(f"\n{cat_label}", flush=True)

        for brand in brands:
            brand_key = brand['ig'].lower().lstrip('@')

            if brand_key in contacted:
                print(f"  Skip: {brand['nome']}", flush=True)
                continue

            email_content = generate_email(brand, category)
            if not email_content:
                results["failed"].append({"nome": brand['nome'], "motivo": "Erro ao gerar email"})
                continue

            emails_to_try = [brand['email']] + brand.get('alt', [])
            sent = False
            sent_to = None

            for e in emails_to_try[:3]:
                print(f"  {brand['nome']} -> {e}", flush=True)
                if send_email(e, email_content['assunto'], email_content['corpo']):
                    sent = True
                    sent_to = e
                    break
                time.sleep(2)

            if sent:
                db["contacted"].append(brand_key)
                results["sent"].append({**brand, "sent_to": sent_to, "cat": cat_label})
                print(f"  ✅ {sent_to}", flush=True)
            else:
                results["failed"].append({"nome": brand['nome'], "ig": brand['ig'], "motivo": "Email falhou"})
                print(f"  ❌ {brand['nome']}", flush=True)

            time.sleep(3)

    save_contacted(db)

    # Telegram summary
    line = "─" * 22
    msg = f"🎯 <b>OUTREACH COMPLETO</b>\n<code>{line}</code>\n\n"

    if results["sent"]:
        by_cat = {}
        for b in results["sent"]:
            cat = b['cat']
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append(b)

        msg += f"✅ <b>{len(results['sent'])} emails enviados:</b>\n"
        for cat, brands in by_cat.items():
            msg += f"\n<b>{cat}</b>\n"
            for b in brands:
                msg += f"  • {b['pais']} {b['nome']}\n"

    if results["failed"]:
        msg += f"\n❌ <b>{len(results['failed'])} falharam:</b>\n"
        for b in results["failed"]:
            msg += f"  • {b['nome']}\n"

    msg += f"\n<i>THE AGENCY · Brand Agent</i>"
    send_telegram(msg)
    print("=== BRAND AGENT v3 DONE ===", flush=True)


if __name__ == "__main__":
    main()
