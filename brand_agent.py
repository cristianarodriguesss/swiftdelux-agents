"""
THE AGENCY - Brand Agent v5
Pesquisa emails reais nos websites antes de enviar.
"""

import os, json, requests, time, smtplib, base64, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urljoin, urlparse

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GMAIL_USER = os.environ.get("GMAIL_USER", "cristianarodriguesss.pr@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = "cristianarodriguesss/swiftdelux-agents"
BRANDS_DB_FILE = "brands_contacted.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

CATEGORIES = [
    {"key": "activewear", "label": "🏋️ Activewear & Yoga", "prompt": "marcas europeias de activewear yoga wear sportswear feminino leggings sustentaveis indie premium 10k-500k seguidores Instagram"},
    {"key": "beleza", "label": "✨ Beleza & Skincare", "prompt": "marcas europeias de skincare clean beauty cuidados rosto soros cremes SPF naturais forte presenca Portugal Brasil"},
    {"key": "acessorios_beleza", "label": "💆 Acessórios de Beleza", "prompt": "marcas de gua sha rolos jade mascaras LED infravermelho massajadores faciais drenagem linfatica ferramentas skincare"},
    {"key": "joias", "label": "💍 Joias & Acessórios", "prompt": "marcas de joias minimalistas banhadas ouro prata demi-fine jewelry europeias indie 10k-200k seguidores"},
    {"key": "malas", "label": "👜 Malas & Bolsas", "prompt": "marcas europeias de malas bolsas clutches premium luxo acessivel independentes contemporaneas preco 100-600 euros"},
    {"key": "calcado", "label": "👠 Calçado", "prompt": "marcas europeias de calcado feminino sapatilhas botas sandалias mules mocassins qualidade media-alta"},
    {"key": "hoteis", "label": "🏨 Hotéis & Resorts", "prompt": "hoteis boutique resorts Portugal Espanha Franca Italia Grecia design hotels wellness resorts spa"}
]


def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=15
        )
    except Exception as e:
        print(f"Telegram error: {e}", flush=True)


def call_claude(prompt, max_tokens=3000):
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-sonnet-4-6", "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]},
        timeout=60
    )
    text = resp.json()["content"][0]["text"].strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"): text = text[4:]
    return text.strip()


def extract_emails_from_text(text):
    """Extrai emails de texto HTML"""
    pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    # Filter out common false positives
    skip = ['example.com', 'domain.com', 'email.com', 'test.com', 'sentry.io',
            'wixpress.com', 'shopify.com', 'squarespace.com', 'wordpress.com',
            'amazonaws.com', 'cloudfront.net', 'schema.org', 'w3.org']
    valid = []
    for e in emails:
        e_lower = e.lower()
        if not any(s in e_lower for s in skip):
            valid.append(e_lower)
    return list(set(valid))


def find_press_email(website):
    """Vai ao website e procura email de press/partnerships"""
    if not website:
        return None

    # Normalize website
    if not website.startswith('http'):
        website = 'https://' + website

    print(f"  Searching website: {website}", flush=True)

    # Pages to check for press/contact emails
    paths_to_check = [
        '', '/contact', '/contacts', '/press', '/media',
        '/partnerships', '/influencer', '/collaborate',
        '/work-with-us', '/about', '/legal/contact',
        '/pages/contact', '/pages/press', '/pages/partnerships',
        '/about-us', '/get-in-touch'
    ]

    found_emails = []
    priority_emails = []

    for path in paths_to_check[:8]:  # Check first 8 pages
        try:
            url = website.rstrip('/') + path
            r = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
            if r.status_code != 200:
                continue

            text = r.text.lower()
            emails = extract_emails_from_text(r.text)

            for email in emails:
                # Priority keywords
                if any(kw in email for kw in ['press', 'partner', 'influencer', 'collab', 'pr@', 'media']):
                    if email not in priority_emails:
                        priority_emails.append(email)
                elif any(kw in email for kw in ['hello', 'info', 'contact', 'hola', 'ciao']):
                    if email not in found_emails:
                        found_emails.append(email)

            if priority_emails:
                break  # Found priority email, stop searching

            time.sleep(0.5)

        except Exception as e:
            continue

    # Return best email found
    if priority_emails:
        return priority_emails[0]
    if found_emails:
        return found_emails[0]
    return None


def search_duckduckgo_email(brand_name, website):
    """Pesquisa no DuckDuckGo pelo email de press da marca"""
    try:
        queries = [
            f'"{brand_name}" press email influencer contact',
            f'site:{urlparse(website).netloc} press email' if website else f'"{brand_name}" influencer email contact'
        ]

        for query in queries[:1]:
            r = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1},
                headers=HEADERS, timeout=8
            )
            data = r.json()
            # Check abstract and results for emails
            text = data.get('Abstract', '') + ' '.join([r.get('Text', '') for r in data.get('Results', [])])
            emails = extract_emails_from_text(text)
            if emails:
                return emails[0]

    except Exception as e:
        print(f"  DuckDuckGo error: {e}", flush=True)

    return None


def find_real_email(brand):
    """Tenta encontrar email real: website primeiro, depois DuckDuckGo"""
    website = brand.get('website', '')

    # 1. Try website
    email = find_press_email(website)
    if email:
        print(f"  ✓ Found on website: {email}", flush=True)
        return email, "website"

    # 2. Try DuckDuckGo
    email = search_duckduckgo_email(brand['nome'], website)
    if email:
        print(f"  ✓ Found via search: {email}", flush=True)
        return email, "search"

    print(f"  ✗ Email not found for {brand['nome']}", flush=True)
    return None, None


def generate_brands(category):
    """Gera 20 marcas por categoria"""
    prompt = f"""Lista 20 marcas de {category['prompt']}.

Para cada marca:
- nome: nome oficial
- ig: handle Instagram sem @
- website: URL completo (https://...)

Escolhe marcas de tamanho medio (nao gigantes como Nike/Zara) que sejam receptivas a gifting com micro-influencers (5k-15k seguidores).

Responde APENAS em JSON:
{{"marcas": [{{"nome":"...","ig":"...","website":"https://..."}}]}}"""

    try:
        text = call_claude(prompt, 2000)
        data = json.loads(text)
        return data.get("marcas", [])
    except Exception as e:
        print(f"generate_brands error: {e}", flush=True)
        return []


def generate_email_text(brand, cat_label, is_hotel=False):
    if is_hotel:
        prompt = f"""Email de Cristiana Rodrigues para {brand['nome']} (hotel/resort).
Cristiana: influencer portuguesa lifestyle/wellness/viagens, 6.959 seg IG (@cristianarodriguesss), 25-34 anos, Portugal 64% Brasil 24%, 7.513 views/mes.
Manager: Artur Santos | Media kit: https://cristianarodriguesss.my.canva.site/cristianarodriguesss
Propoe estadia em troca de conteudo. Max 120 palavras, ingles, profissional.
JSON: {{"assunto":"...","corpo":"..."}}"""
    else:
        prompt = f"""Email parceria Cristiana Rodrigues para {brand['nome']} ({cat_label}).
Cristiana: influencer portuguesa lifestyle/wellness/viagens/beleza, 6.959 seg IG (@cristianarodriguesss), 25-34 anos, Portugal 64% Brasil 24%, 7.513 views/mes, 66% nao seguidores.
Manager: Artur Santos | Media kit: https://cristianarodriguesss.my.canva.site/cristianarodriguesss
Aberta a gifting (produtos em troca de story/post). Max 120 palavras, ingles, caloroso.
JSON: {{"assunto":"...","corpo":"..."}}"""

    try:
        text = call_claude(prompt, 400)
        return json.loads(text)
    except:
        return None


def send_email_smtp(to_email, subject, body):
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
        print(f"SMTP error {to_email}: {e}", flush=True)
        return False


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
        if sha: payload["sha"] = sha
        requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{BRANDS_DB_FILE}",
            json=payload,
            headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"},
            timeout=10
        )
    except Exception as e:
        print(f"Save error: {e}", flush=True)


def main():
    print("=== BRAND AGENT v5 START ===", flush=True)

    db = load_contacted()
    contacted = set(c.lower() for c in db.get("contacted", []))
    total_sent = 0
    total_not_found = 0
    total_failed = 0

    for category in CATEGORIES:
        cat_label = category['label']
        is_hotel = category['key'] == 'hoteis'

        print(f"\n{'='*30}", flush=True)
        print(f"{cat_label}", flush=True)
        send_telegram(f"🔄 A pesquisar <b>{cat_label}</b>...")

        brands = generate_brands(category)
        print(f"Generated {len(brands)} brands", flush=True)

        cat_sent = []
        cat_not_found = []

        for brand in brands:
            ig = brand.get('ig', '').lower().lstrip('@')
            if not ig or ig in contacted:
                continue

            print(f"\n  Brand: {brand['nome']}", flush=True)

            # Find real email from website
            real_email, source = find_real_email(brand)

            if not real_email:
                cat_not_found.append(brand['nome'])
                total_not_found += 1
                continue

            # Generate email
            email_content = generate_email_text(brand, cat_label, is_hotel)
            if not email_content:
                total_failed += 1
                continue

            # Send
            # Never send to own email
            if real_email.lower() == GMAIL_USER.lower():
                print(f"  Skip: would send to own email", flush=True)
                continue
            if send_email_smtp(real_email, email_content['assunto'], email_content['corpo']):
                contacted.add(ig)
                db["contacted"].append(ig)
                cat_sent.append(f"{brand['nome']} → {real_email}")
                total_sent += 1
                print(f"  ✅ Sent to {real_email} ({source})", flush=True)
            else:
                total_failed += 1

            time.sleep(2)

        # Save after each category
        save_contacted(db)

        # Category update
        msg = f"<b>{cat_label}</b>\n"
        msg += f"✅ {len(cat_sent)} enviados\n"
        if cat_sent:
            msg += "\n".join(f"  • {n}" for n in cat_sent[:8])
            if len(cat_sent) > 8:
                msg += f"\n  +{len(cat_sent)-8} mais"
        if cat_not_found:
            msg += f"\n⚠️ {len(cat_not_found)} sem email encontrado"
        send_telegram(msg)
        time.sleep(2)

    # Final summary
    send_telegram(
        f"🎯 <b>OUTREACH COMPLETO</b>\n"
        f"{'─'*22}\n\n"
        f"✅ Enviados: <b>{total_sent}</b>\n"
        f"⚠️ Sem email: {total_not_found}\n"
        f"❌ Falharam: {total_failed}\n\n"
        f"<i>THE AGENCY · Brand Agent</i>"
    )
    print(f"=== DONE: {total_sent} sent ===", flush=True)


if __name__ == "__main__":
    main()
