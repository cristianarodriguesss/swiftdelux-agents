"""
THE AGENCY - Brand Agent v4
Gera 100+ marcas por categoria usando IA e envia outreach automatico.
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

CATEGORIES = [
    {
        "key": "activewear",
        "label": "🏋️ Activewear & Yoga",
        "prompt": "marcas europeias e internacionais de activewear, yoga wear, sportswear feminino, leggings, sutiãs de desporto. Inclui marcas sustentáveis, indie e premium. Foca em marcas com 10k-500k seguidores Instagram."
    },
    {
        "key": "beleza_skincare",
        "label": "✨ Beleza & Skincare",
        "prompt": "marcas de skincare, cuidados de rosto, soros, cremes, SPF, limpeza facial. Prefere marcas clean beauty, naturais, europeias ou com forte presença em Portugal e Brasil."
    },
    {
        "key": "acessorios_beleza",
        "label": "💆 Acessórios de Beleza",
        "prompt": "marcas de acessórios de beleza: gua sha, rolos de jade, máscaras LED infravermelhos, massajadores faciais, packs de drenagem linfática, ferramentas de skincare, FOREO, NuFace e similares."
    },
    {
        "key": "joias",
        "label": "💍 Joias & Acessórios",
        "prompt": "marcas de joias minimalistas, jóias banhadas a ouro, prata, acessórios finos. Marcas europeias, indie, demi-fine jewelry. Evita marcas de luxo extremo (Cartier, Tiffany)."
    },
    {
        "key": "malas",
        "label": "👜 Malas & Bolsas",
        "prompt": "marcas de malas, bolsas, clutches, mochilas premium/luxo acessível. Marcas europeias, independentes, contemporâneas. Preço médio €100-€600."
    },
    {
        "key": "calcado",
        "label": "👠 Calçado",
        "prompt": "marcas de calçado feminino: sapatilhas, botas, sandálias, mules, mocassins. Marcas europeias e internacionais de qualidade média-alta. Evita marcas massivas como Nike/Adidas main line."
    },
    {
        "key": "hoteis",
        "label": "🏨 Hotéis & Resorts",
        "prompt": "hotéis boutique, resorts e propriedades em Portugal e Europa (Espanha, França, Itália, Grécia, Maldivas). Boutique hotels, design hotels, wellness resorts, hotéis com spa."
    }
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


def call_claude(prompt, max_tokens=4000):
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


def generate_brands(category):
    """Usa Claude para gerar 20 marcas por categoria"""
    prompt = f"""Gera uma lista de 20 marcas de {category['prompt']}

Para cada marca indica:
- Nome oficial
- Handle Instagram (sem @)
- Email de press/parcerias/influencer mais provavel
- 2 emails alternativos
- Website

Estas marcas devem ter dimensao media (nao gigantes como Zara/Nike) e ser receptivas a gifting collaborations com influencers de 5k-10k seguidores.

Responde APENAS em JSON valido:
{{"marcas": [{{"nome": "...", "ig": "...", "email": "...", "alt": ["...", "..."], "website": "..."}}]}}"""

    try:
        text = call_claude(prompt, 3000)
        data = json.loads(text)
        return data.get("marcas", [])
    except Exception as e:
        print(f"generate_brands error: {e}", flush=True)
        return []


def generate_email_text(brand, category_label, is_hotel=False):
    if is_hotel:
        prompt = f"""Escreve um email de Cristiana Rodrigues para o hotel/resort {brand['nome']}.

Cristiana: influencer portuguesa lifestyle/wellness/viagens, 6.959 seguidores IG (@cristianarodriguesss), publico mulheres 25-34, Portugal 64% Brasil 24%, 7.513 views/mes, 66% nao seguidores.
Manager: Artur Santos | Media kit: https://cristianarodriguesss.my.canva.site/cristianarodriguesss

Propoe estadia em troca de conteudo autentico (stories, reels, posts).
Max 120 palavras, ingles, profissional.
Assina como Artur Santos, Talent Manager.

JSON: {{"assunto":"...","corpo":"..."}}"""
    else:
        prompt = f"""Escreve email de parceria de Cristiana Rodrigues para {brand['nome']} ({category_label}).

Cristiana: influencer portuguesa lifestyle/wellness/viagens/beleza, 6.959 seguidores IG (@cristianarodriguesss), publico mulheres 25-34, Portugal 64% Brasil 24%, 7.513 views/mes, 66% nao seguidores.
Manager: Artur Santos | Media kit: https://cristianarodriguesss.my.canva.site/cristianarodriguesss

Aberta a gifting (produtos em troca de story/post). Max 120 palavras, ingles, caloroso.
Personaliza para {brand['nome']}.
Assina como Artur Santos, Talent Manager.

JSON: {{"assunto":"...","corpo":"..."}}"""

    try:
        text = call_claude(prompt, 500)
        return json.loads(text)
    except Exception as e:
        print(f"Email gen error: {e}", flush=True)
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
    print("=== BRAND AGENT v4 START ===", flush=True)

    db = load_contacted()
    contacted = set(c.lower() for c in db.get("contacted", []))
    total_sent = 0
    total_failed = 0
    summary_by_cat = {}

    for category in CATEGORIES:
        cat_key = category['key']
        cat_label = category['label']
        is_hotel = cat_key == "hoteis"

        print(f"\n{cat_label}", flush=True)
        send_telegram(f"🔄 A processar <b>{cat_label}</b>...")

        # Generate brands for this category
        brands = generate_brands(category)
        print(f"  Generated {len(brands)} brands", flush=True)

        if not brands:
            continue

        cat_sent = []
        cat_failed = []

        for brand in brands:
            ig = brand.get('ig', '').lower().lstrip('@')
            if not ig:
                continue

            if ig in contacted:
                print(f"  Skip: {brand['nome']}", flush=True)
                continue

            # Generate personalised email
            email_content = generate_email_text(brand, cat_label, is_hotel)
            if not email_content:
                cat_failed.append(brand['nome'])
                total_failed += 1
                continue

            # Try emails
            emails_to_try = []
            if brand.get('email'):
                emails_to_try.append(brand['email'])
            for alt in brand.get('alt', []):
                if alt and alt not in emails_to_try:
                    emails_to_try.append(alt)

            sent = False
            sent_to = None
            for e in emails_to_try[:2]:
                print(f"  {brand['nome']} -> {e}", flush=True)
                if send_email(e, email_content['assunto'], email_content['corpo']):
                    sent = True
                    sent_to = e
                    break
                time.sleep(1)

            if sent:
                contacted.add(ig)
                db["contacted"].append(ig)
                cat_sent.append(f"{brand['nome']}")
                total_sent += 1
                print(f"  ✅ {sent_to}", flush=True)
            else:
                cat_failed.append(brand['nome'])
                total_failed += 1

            time.sleep(2)

        summary_by_cat[cat_label] = {"sent": cat_sent, "failed": cat_failed}

        # Save after each category
        save_contacted(db)

        # Mini update per category
        line = "─" * 18
        cat_msg = (
            f"<b>{cat_label}</b>\n<code>{line}</code>\n"
            f"✅ {len(cat_sent)} enviados\n"
            f"❌ {len(cat_failed)} falharam\n"
        )
        if cat_sent:
            cat_msg += "\n".join(f"  • {n}" for n in cat_sent[:10])
            if len(cat_sent) > 10:
                cat_msg += f"\n  ...+{len(cat_sent)-10} mais"
        send_telegram(cat_msg)
        time.sleep(2)

    # Final summary
    line = "═" * 22
    final_msg = (
        f"🎯 <b>OUTREACH COMPLETO</b>\n<code>{line}</code>\n\n"
        f"✅ <b>Total enviados: {total_sent}</b>\n"
        f"❌ Falharam: {total_failed}\n\n"
        f"<i>THE AGENCY · Brand Agent</i>"
    )
    send_telegram(final_msg)
    print(f"=== DONE: {total_sent} sent, {total_failed} failed ===", flush=True)


if __name__ == "__main__":
    main()
