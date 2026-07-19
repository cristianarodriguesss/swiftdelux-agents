"""
THE AGENCY - Outreach Agent
Le mensagens /marca @handle do Telegram e envia emails de parceria.
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
STATE_FILE = "outreach_state.json"



# Base de dados de emails conhecidos
KNOWN_EMAILS = {
    "rituals": {"email": "press@rituals.com", "alternativas": ["partnerships@rituals.com", "influencer@rituals.com"]},
    "soldejaneiro": {"email": "press@soldejaneiro.com", "alternativas": ["influencer@soldejaneiro.com", "partnerships@soldejaneiro.com"]},
    "sol_de_janeiro": {"email": "press@soldejaneiro.com", "alternativas": ["influencer@soldejaneiro.com"]},
    "safairstore": {"email": "geral@safairstore.com", "alternativas": ["press@safairstore.com", "info@safairstore.com"]},
    "safair_store": {"email": "geral@safairstore.com", "alternativas": ["press@safairstore.com"]},
    "sismoactive": {"email": "info@sismoactive.com", "alternativas": ["geral@sismoactive.com", "press@sismoactive.com"]},
    "sismo_active": {"email": "info@sismoactive.com", "alternativas": ["geral@sismoactive.com"]},
    "rsvp_paris": {"email": "contact@rsvp-paris.com", "alternativas": ["press@rsvp-paris.com", "info@rsvp-paris.com"]},
    "rsvpparis": {"email": "contact@rsvp-paris.com", "alternativas": ["press@rsvp-paris.com"]},
    "zara": {"email": "press@zara.com", "alternativas": ["influencer@zara.com"]},
    "mango": {"email": "press@mango.com", "alternativas": ["influencer@mango.com", "pr@mango.com"]},
    "nars": {"email": "press@nars.com", "alternativas": ["influencer@nars.com"]},
    "narscosmetics": {"email": "press@nars.com", "alternativas": ["influencer@nars.com"]},
    "lush": {"email": "press@lush.com", "alternativas": ["influencer@lush.co.uk"]},
    "lushcosmetics": {"email": "press@lush.com", "alternativas": []},
    "glossier": {"email": "press@glossier.com", "alternativas": ["influencer@glossier.com"]},
    "cerave": {"email": "pr@cerave.com", "alternativas": ["press@cerave.com"]},
    "laroche_posay": {"email": "press@laroche-posay.com", "alternativas": []},
    "loreal": {"email": "press@loreal.com", "alternativas": ["influencer@loreal.com"]},
    "hm": {"email": "press@hm.com", "alternativas": ["influencer@hm.com"]},
    "hmofficial": {"email": "press@hm.com", "alternativas": []},
    "primark": {"email": "press@primark.com", "alternativas": []},
    "asos": {"email": "press@asos.com", "alternativas": ["influencer@asos.com"]},
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


def call_claude(prompt, max_tokens=800):
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-sonnet-4-6", "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]},
        timeout=30
    )
    text = resp.json()["content"][0]["text"].strip()
    if "```" in text:
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def load_state():
    """Load state from GitHub repo"""
    try:
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{STATE_FILE}",
            headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            content = base64.b64decode(data['content']).decode('utf-8')
            state = json.loads(content)
            state['_sha'] = data['sha']
            return state
    except Exception as e:
        print(f"Load state error: {e}", flush=True)
    return {"processed_ids": [], "last_offset": 0, "sent_brands": [], "_sha": None}


def save_state(state):
    """Save state to GitHub repo"""
    sha = state.pop('_sha', None)
    try:
        content = base64.b64encode(json.dumps(state, indent=2, ensure_ascii=False).encode()).decode()
        payload = {"message": "Update outreach state", "content": content}
        if sha:
            payload["sha"] = sha
        r = requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{STATE_FILE}",
            json=payload,
            headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"},
            timeout=10
        )
        print(f"State saved: {r.status_code}", flush=True)
    except Exception as e:
        print(f"Save state error: {e}", flush=True)


def get_telegram_updates(offset=0):
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
            params={"offset": offset, "limit": 50, "timeout": 5},
            timeout=15
        )
        return r.json().get("result", [])
    except Exception as e:
        print(f"getUpdates error: {e}", flush=True)
        return []


def find_brand_info(handle):
    prompt = f"""A marca de Instagram {handle} foi identificada para parceria com Cristiana Rodrigues, influencer portuguesa de lifestyle/wellness/viagens/beleza.

Com base no teu conhecimento desta marca:
1. Nome oficial
2. Website
3. Email de imprensa/parcerias (tenta ser preciso - usa press@, partnerships@, influencer@, collab@, pr@, hello@)
4. Emails alternativos a tentar se o primeiro falhar
5. Nicho/categoria
6. Porque seria boa parceria para Cristiana

Responde APENAS em JSON valido:
{{"nome":"...","website":"...","email":"...","emails_alternativos":["alt1@marca.com","alt2@marca.com"],"email_confianca":"alta/media/baixa","nicho":"...","razao_parceria":"..."}}"""

    try:
        text = call_claude(prompt, 500)
        return json.loads(text)
    except Exception as e:
        print(f"find_brand_info error: {e}", flush=True)
        return None


def generate_email(brand_info, handle):
    prompt = f"""Escreve um email de parceria de Cristiana Rodrigues para {brand_info.get('nome', handle)}.

Cristiana Rodrigues:
- Influencer portuguesa de lifestyle, wellness, viagens e beleza
- 6.959 seguidores Instagram (@cristianarodriguesss)
- Publico: mulheres 25-34 anos, Portugal (64%) e Brasil (24%)
- 7.513 views ultimos 30 dias, 66% de nao seguidores
- Manager: Artur Santos
- Media kit: https://cristianarodriguesss.my.canva.site/cristianarodriguesss

Marca: {brand_info.get('nome', handle)} | {handle} | {brand_info.get('nicho', '')}
Razao: {brand_info.get('razao_parceria', '')}

Email em ingles, profissional mas caloroso, max 150 palavras.
Deve mencionar que Cristiana esta aberta a receber produtos em troca de um story ou publicacao (gifting collaboration).
Assina como Artur Santos, Talent Manager.

Responde APENAS em JSON:
{{"assunto":"...","corpo":"..."}}"""

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


def process_marca(handle, state):
    handle = handle.strip().lstrip('@')
    full_handle = f"@{handle}"
    handle_lower = handle.lower()

    if handle_lower in [b.lower() for b in state.get("sent_brands", [])]:
        send_telegram(f"⚠️ Ja enviaste outreach para <b>{full_handle}</b> anteriormente.")
        return

    send_telegram(f"🔍 A pesquisar <b>{full_handle}</b>...")

    brand_info = find_brand_info(full_handle)
    
    # Override with known correct emails
    handle_key = handle_lower.replace('.', '_').replace('-', '_')
    if handle_key in KNOWN_EMAILS:
        known = KNOWN_EMAILS[handle_key]
        if brand_info:
            brand_info['email'] = known['email']
            brand_info['emails_alternativos'] = known['alternativas']
            brand_info['email_confianca'] = 'alta'
        print(f"Using known email for {handle}: {known['email']}", flush=True)
    if not brand_info:
        send_telegram(f"❌ Nao encontrei informacao sobre {full_handle}.")
        return

    email_content = generate_email(brand_info, full_handle)
    if not email_content:
        send_telegram(f"❌ Erro ao gerar email para {full_handle}.")
        return

    # Try multiple emails
    emails_to_try = []
    if brand_info.get('email'):
        emails_to_try.append(brand_info['email'])
    for alt in brand_info.get('emails_alternativos', []):
        if alt and alt not in emails_to_try:
            emails_to_try.append(alt)

    sent = False
    sent_to = None
    for e in emails_to_try[:3]:
        print(f"Trying {e}...", flush=True)
        if send_email(e, email_content["assunto"], email_content["corpo"]):
            sent = True
            sent_to = e
            break
        time.sleep(2)

    conf_emoji = {"alta": "🟢", "media": "🟡", "baixa": "🔴"}.get(brand_info.get("email_confianca", "baixa"), "⚪")
    line = "─" * 22

    if sent:
        state["sent_brands"].append(handle_lower)
        msg = (
            f"✅ <b>EMAIL ENVIADO!</b>\n<code>{line}</code>\n\n"
            f"<b>Marca:</b> {brand_info.get('nome', handle)}\n"
            f"<b>Instagram:</b> {full_handle}\n"
            f"<b>Email:</b> <code>{sent_to}</code> {conf_emoji}\n\n"
            f"<b>Assunto:</b>\n<i>{email_content['assunto']}</i>\n\n"
            f"<b>Corpo:</b>\n{email_content['corpo']}\n\n"
            f"<i>THE AGENCY · Outreach Agent</i>"
        )
    else:
        # Manual fallback - full email text to copy
        emails_tried = ", ".join(emails_to_try) if emails_to_try else "nenhum encontrado"
        msg = (
            f"❌ <b>Emails falharam — copia e envia manualmente</b>\n<code>{line}</code>\n\n"
            f"<b>Marca:</b> {brand_info.get('nome', handle)}\n"
            f"<b>Website:</b> {brand_info.get('website', '')}\n"
            f"<b>Emails tentados:</b> {emails_tried}\n\n"
            f"<b>ASSUNTO:</b>\n<code>{email_content['assunto']}</code>\n\n"
            f"<b>CORPO:</b>\n<code>{email_content['corpo']}</code>\n\n"
            f"<i>THE AGENCY · Outreach Agent</i>"
        )

    send_telegram(msg)


def main():
    print("=== OUTREACH AGENT START ===", flush=True)

    state = load_state()
    print(f"Last offset: {state.get('last_offset', 0)}", flush=True)
    print(f"Sent brands: {state.get('sent_brands', [])}", flush=True)

    updates = get_telegram_updates(state.get("last_offset", 0))
    print(f"New updates: {len(updates)}", flush=True)

    new_offset = state.get("last_offset", 0)

    for update in updates:
        update_id = update.get("update_id", 0)
        new_offset = max(new_offset, update_id + 1)

        msg = update.get("message", {})
        text = msg.get("text", "").strip()
        chat_id = str(msg.get("chat", {}).get("id", ""))

        if chat_id != str(TELEGRAM_CHAT_ID):
            continue

        print(f"Processing: {text}", flush=True)

        if text.lower().startswith("/marca"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                send_telegram(
                    "📝 <b>Como usar:</b>\n"
                    "<code>/marca @handle_da_marca</code>\n\n"
                    "Exemplos:\n"
                    "<code>/marca @zara</code>\n"
                    "<code>/marca @rituals</code>"
                )
            else:
                process_marca(parts[1].strip(), state)
                time.sleep(2)

        elif text.lower() in ["/help", "/start", "/ajuda"]:
            send_telegram(
                "🤝 <b>OUTREACH AGENT</b>\n\n"
                "Envia uma marca para contactar:\n"
                "<code>/marca @handle_da_marca</code>\n\n"
                "Eu vou pesquisar o email, gerar um email de parceria e enviar automaticamente!\n\n"
                "<i>THE AGENCY · Outreach Agent</i>"
            )

    state["last_offset"] = new_offset
    save_state(state)
    print("=== OUTREACH AGENT DONE ===", flush=True)


if __name__ == "__main__":
    main()
