"""
THE AGENCY - Brand Agent
Sugere marcas para contactar e vai buscar emails de imprensa/parcerias.
Corre semanalmente (quartas-feiras).
"""

import os
import json
import requests
import time
from datetime import datetime, timezone

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


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
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def load_wishlist():
    """Load wishlist from dados.json"""
    try:
        with open("dados.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
        return dados.get("wishlist", [])
    except Exception:
        return []


def suggest_new_brands():
    """Sugere 5 marcas novas para Cristiana contactar"""
    prompt = """Cristiana Rodrigues é uma influencer portuguesa com 6.959 seguidores no Instagram.
Nicho: lifestyle, wellness, viagens, beleza, moda minimalista.
Público: mulheres 25-34 anos, Portugal e Brasil.

Sugere 5 marcas portuguesas ou internacionais com presença em Portugal que seriam perfeitas para parceria.
Prefere marcas acessíveis a mid-range, estilos clean/minimalista/natural.

Para cada marca inclui:
- Nome da marca
- Instagram handle
- Nicho/categoria
- Porque é uma boa parceria
- Email de imprensa/parcerias (se conheceres, senão coloca null)
- Website

Responde APENAS em JSON:
{"marcas": [{"nome": "...", "instagram": "@...", "nicho": "...", "razao": "...", "email": "..." ou null, "website": "..."}]}"""

    try:
        text = call_claude(prompt, 1000)
        data = json.loads(text)
        return data.get("marcas", [])
    except Exception as e:
        print(f"Erro sugestoes: {e}", flush=True)
        return []


def find_brand_email(brand_name, website, instagram):
    """Tenta encontrar email de imprensa/parcerias de uma marca"""
    prompt = f"""Preciso do email de imprensa ou parcerias da marca "{brand_name}".
Instagram: {instagram}
Website: {website or 'desconhecido'}

Com base no teu conhecimento, qual é o email de contacto para parcerias/imprensa desta marca?
Se não souberes com certeza, sugere o formato mais provável (ex: press@marca.com, partnerships@marca.com, collab@marca.com).

Responde APENAS em JSON: {{"email": "email@exemplo.com", "confianca": "alta/media/baixa", "nota": "breve explicacao"}}"""

    try:
        text = call_claude(prompt, 200)
        data = json.loads(text)
        return data
    except Exception:
        return {"email": None, "confianca": "baixa", "nota": "Não encontrado"}


def send_new_brands_report(brands):
    """Envia relatório de marcas sugeridas para Telegram"""
    if not brands:
        return

    line = "─" * 22
    msg = f"🎯 <b>MARCAS SUGERIDAS ESTA SEMANA</b>\n<code>{line}</code>\n\n"
    msg += "Baseado no teu nicho: lifestyle · wellness · viagens · beleza\n\n"

    for i, b in enumerate(brands, 1):
        msg += f"<b>{i}. {b['nome']}</b>\n"
        msg += f"   {b.get('instagram', '')} · {b.get('nicho', '')}\n"
        msg += f"   💡 {b.get('razao', '')}\n"
        if b.get('email'):
            msg += f"   📧 <code>{b['email']}</code>\n"
        if b.get('website'):
            msg += f"   🌐 {b.get('website', '')}\n"
        msg += "\n"

    msg += "<i>THE AGENCY · Brand Agent</i>"
    send_telegram(msg)
    print(f"OK Sugestoes enviadas: {len(brands)} marcas", flush=True)


def send_wishlist_emails_report(wishlist_with_emails):
    """Envia emails encontrados para marcas da wishlist"""
    if not wishlist_with_emails:
        return

    line = "─" * 22
    msg = f"📋 <b>EMAILS DA TUA WISHLIST</b>\n<code>{line}</code>\n\n"

    for item in wishlist_with_emails:
        found = item.get("email_info", {})
        email = found.get("email")
        conf = found.get("confianca", "baixa")
        conf_emoji = {"alta": "🟢", "media": "🟡", "baixa": "🔴"}.get(conf, "⚪")

        msg += f"<b>{item['brand']}</b> {conf_emoji}\n"
        if item.get('ig'):
            msg += f"   {item['ig']}\n"
        if email:
            msg += f"   📧 <code>{email}</code>\n"
            if found.get("nota"):
                msg += f"   <i>{found['nota']}</i>\n"
        else:
            msg += f"   ❌ Email não encontrado\n"
        msg += "\n"

    msg += "💡 <b>Dica:</b> Começa pelas marcas com confiança 🟢 alta!\n\n"
    msg += "<i>THE AGENCY · Brand Agent</i>"
    send_telegram(msg)
    print(f"OK Wishlist emails enviados: {len(wishlist_with_emails)} marcas", flush=True)


def main():
    print("=== BRAND AGENT START ===", flush=True)

    # 1. Sugerir marcas novas
    print("A gerar sugestoes de marcas...", flush=True)
    new_brands = suggest_new_brands()
    if new_brands:
        send_new_brands_report(new_brands)
        time.sleep(2)

    # 2. Ir buscar emails das marcas na wishlist
    wishlist = load_wishlist()
    print(f"Wishlist tem {len(wishlist)} marcas", flush=True)

    if wishlist:
        enriched = []
        for item in wishlist[:10]:  # Limita a 10 para nao demorar muito
            brand_name = item.get("brand", "")
            if not brand_name:
                continue
            print(f"A procurar email: {brand_name}", flush=True)
            email_info = find_brand_email(
                brand_name,
                item.get("website", ""),
                item.get("ig", "")
            )
            enriched.append({**item, "email_info": email_info})
            time.sleep(1)  # Evita rate limiting

        if enriched:
            send_wishlist_emails_report(enriched)

    print("=== BRAND AGENT DONE ===", flush=True)


if __name__ == "__main__":
    main()
