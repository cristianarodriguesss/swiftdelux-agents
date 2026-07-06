"""
✨ THE AGENCY — Content Agent ✨
Gera conteudo diario para Swift Delux e Cristiana Rodrigues.
Envia briefing, ideias de post, script de story e resumo de emails.
"""

import os
import requests
import json
import random
from datetime import datetime, timezone, timedelta
from dashboard_data import add_event

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

ANGLES_SD = [
    "lifestyle aspiracional — a peca no dia a dia de uma mulher europeia, 20-36 anos",
    "detalhe e brilho — foco no acabamento e qualidade da joia",
    "storytelling de marca — os valores da Swift Delux",
    "look completo — como combinar a peca com um outfit",
    "presente / momento especial — a joia como prenda",
    "behind the scenes — processo de criacao ou embalagem",
]

ANGLES_CR = [
    "wellness matinal — rotina de manha, mindfulness, self-care",
    "viagem e lifestyle — destino europeu, hotel aesthetic, momento de luxo acessivel",
    "beleza — skincare rotina, produto favorito do momento",
    "moda — outfit do dia, tendencia da estacao, como combinar pecas",
    "autenticidade — momento real, pensamento do dia, bastidores da vida",
    "motivacao — frase do dia, algo que aprendeste, reflexao pessoal",
]

STORY_THEMES = [
    "O meu ritual de manha — o que faco nos primeiros 30 minutos do dia",
    "O produto de beleza que nao largo — antes e depois honesto",
    "O que estou a ouvir/ler esta semana — recomendacoes autentecas",
    "Bastidores do meu trabalho como influencer — o que ningem mostra",
    "A minha rotina de exercicio atual — o que funciona para mim",
    "Viagem rapida — dica do destino que mais gostei ultimamente",
    "Shopping haul honesto — o que vale e o que nao vale a pena",
    "Dia na minha vida — formato simples e autenticidade",
]

BEST_TIMES = [
    "18h00-21h00 (Lisboa) — pico maximo do teu publico",
    "19h00-21h00 (Lisboa) — melhor para Reels",
    "12h00-13h00 (Lisboa) — pausa do almoco, bom para posts",
    "20h00-21h30 (Lisboa) — maximo de engagement noturno",
]


def call_claude(prompt, max_tokens=500):
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    response.raise_for_status()
    text = response.json()["content"][0]["text"]
    return text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()


def send_telegram(text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
    )


def load_dados():
    try:
        with open("dados.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"events": []}


def save_dados(dados):
    with open("dados.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def generate_briefing(dados):
    events = dados.get("events", [])
    ago7 = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    ago24 = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    posts7 = len([e for e in events if e.get("type") in ("post","post_cr") and e.get("timestamp","") > ago7])
    emails24 = len([e for e in events if e.get("type") == "email" and e.get("timestamp","") > ago24])
    deals = len([e for e in events if e.get("type") == "partnership"])
    sd_ig = dados.get("followers", {}).get("count", 1254)
    cr_ig = dados.get("cr_followers", {}).get("count", 6959)

    prompt = f"""Es assistente de THE AGENCY, agencia portuguesa que gere Swift Delux (joias) e Cristiana Rodrigues (influencer lifestyle/wellness/viagens).
Gera briefing diario conciso em portugues europeu.

Dados:
- Swift Delux IG: {sd_ig} seguidores (meta 10k, actualmente a {round(sd_ig/10000*100)}%)
- Cristiana IG: {cr_ig} seguidores (publico: 54% mulheres, 25-34 anos, Portugal e Brasil)
- Parcerias fechadas: {deals}
- Emails ultimas 24h: {emails24}
- Posts sugeridos (7 dias): {posts7}
- Melhor horario publicar: 18h-21h

Responde APENAS em JSON valido:
{{"resumo":"1-2 frases sobre estado actual","destaques":["d1","d2","d3"],"tarefas":["t1","t2","t3","t4"]}}"""

    try:
        text = call_claude(prompt, 400)
        briefing = json.loads(text)
        briefing["date"] = datetime.now().strftime("%d/%m/%Y")
        dados["briefing"] = briefing

        line = "=" * 22
        hl = "\n".join(f"• {d}" for d in briefing.get("destaques", []))
        tk = "\n".join(f"• {t}" for t in briefing.get("tarefas", []))
        msg = (
            f"✦ <b>AGENCY BRIEFING · {briefing['date']}</b>\n"
            f"<code>{line}</code>\n\n"
            f"{briefing['resumo']}\n\n"
            f"<b>Destaques:</b>\n{hl}\n\n"
            f"<b>Para hoje:</b>\n{tk}\n\n"
            f"<i>THE AGENCY</i>"
        )
        send_telegram(msg)
        print("OK Briefing enviado")
    except Exception as e:
        print(f"Erro briefing: {e}")


def generate_post_sd():
    angle = random.choice(ANGLES_SD)
    prompt = f"""Sugere 1 ideia de post para Instagram da Swift Delux (joias minimalistas, mulheres 20-36, Europa).
Angulo: {angle}

JSON valido:
{{"conceito_visual":"descricao breve","legenda":"em portugues europeu, 2-3 frases + emoji","hashtags":["#t1","#t2","#t3","#t4","#t5","#t6","#t7","#t8"],"cta":"call to action curto"}}"""
    try:
        idea = json.loads(call_claude(prompt, 400))
        best_time = random.choice(BEST_TIMES)
        line = "-" * 22
        msg = (
            f"💎 <b>SWIFT DELUX · POST DO DIA</b>\n"
            f"<code>{line}</code>\n\n"
            f"🎬 <b>Conceito:</b> {idea['conceito_visual']}\n\n"
            f"📝 <b>Legenda:</b>\n<i>{idea['legenda']}</i>\n\n"
            f"👉 {idea.get('cta','')}\n\n"
            f"🏷 <code>{' '.join(idea['hashtags'])}</code>\n\n"
            f"⏰ <b>Horario:</b> {best_time}\n\n"
            f"<i>THE AGENCY · Content Agent</i>"
        )
        send_telegram(msg)
        add_event("post", idea["legenda"][:80])
        print("OK Post Swift Delux enviado")
    except Exception as e:
        print(f"Erro post SD: {e}")


def generate_post_cr():
    angle = random.choice(ANGLES_CR)
    prompt = f"""Sugere 1 ideia de post para Instagram de Cristiana Rodrigues, influencer portuguesa de lifestyle, wellness, viagens e beleza.
Publico: mulheres 25-34, Portugal e Brasil, autentica e aspiracional.
Angulo: {angle}

JSON valido:
{{"conceito_visual":"descricao breve","legenda":"em portugues europeu, autenticidade, 2-3 frases + emoji","hashtags":["#t1","#t2","#t3","#t4","#t5","#t6","#t7","#t8","#t9","#t10"],"cta":"call to action curto"}}"""
    try:
        idea = json.loads(call_claude(prompt, 400))
        best_time = random.choice(BEST_TIMES)
        line = "-" * 22
        msg = (
            f"🌸 <b>@CRIS · POST DO DIA</b>\n"
            f"<code>{line}</code>\n\n"
            f"🎬 <b>Conceito:</b> {idea['conceito_visual']}\n\n"
            f"📝 <b>Legenda:</b>\n<i>{idea['legenda']}</i>\n\n"
            f"👉 {idea.get('cta','')}\n\n"
            f"🏷 <code>{' '.join(idea['hashtags'])}</code>\n\n"
            f"⏰ <b>Horario:</b> {best_time}\n\n"
            f"<i>THE AGENCY · Content Agent</i>"
        )
        send_telegram(msg)
        add_event("post_cr", idea["legenda"][:80])
        print("OK Post Cristiana enviado")
    except Exception as e:
        print(f"Erro post CR: {e}")


def generate_story_cr():
    theme = random.choice(STORY_THEMES)
    prompt = f"""Cria um script de Story para Instagram de Cristiana Rodrigues (influencer portuguesa, lifestyle/wellness/viagens/beleza).
Tema: {theme}
Duracao: 60 segundos, tom autentico e conversacional.
Publico: mulheres 25-34, Portugal e Brasil.

JSON valido:
{{"titulo":"titulo chamativo para a capa do story","script":"script completo de 60 segundos, dividido em 3-4 momentos","dica":"dica de producao (luz, local, roupa)","cta":"call to action no final"}}"""
    try:
        story = json.loads(call_claude(prompt, 500))
        line = "-" * 22
        msg = (
            f"📱 <b>@CRIS · SCRIPT DE STORY</b>\n"
            f"<code>{line}</code>\n\n"
            f"🎯 <b>Capa:</b> {story['titulo']}\n\n"
            f"📖 <b>Script:</b>\n{story['script']}\n\n"
            f"💡 <b>Dica de producao:</b> {story['dica']}\n\n"
            f"👉 <b>CTA:</b> {story['cta']}\n\n"
            f"<i>THE AGENCY · Story Agent</i>"
        )
        send_telegram(msg)
        print("OK Script de story enviado")
    except Exception as e:
        print(f"Erro story CR: {e}")


def email_summary(dados):
    events = dados.get("events", [])
    ago24 = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    recent = [e for e in events if e.get("type") == "email" and e.get("timestamp","") > ago24]
    if not recent:
        return
    urgentes = sum(1 for e in recent if "urgente" in e.get("summary","").lower())
    clientes = sum(1 for e in recent if "cliente" in e.get("summary","").lower())
    fornecedores = sum(1 for e in recent if "fornecedor" in e.get("summary","").lower())
    line = "-" * 22
    msg = (
        f"📊 <b>RESUMO DE EMAILS · {datetime.now().strftime('%d/%m/%Y')}</b>\n"
        f"<code>{line}</code>\n\n"
        f"📧 <b>Total (24h):</b> {len(recent)}\n"
        f"🔴 Urgentes: {urgentes}\n"
        f"💎 Clientes: {clientes}\n"
        f"📦 Fornecedores: {fornecedores}\n\n"
        f"<i>Abre o dashboard para ver as respostas sugeridas.</i>\n\n"
        f"<i>THE AGENCY · Email Summary</i>"
    )
    send_telegram(msg)
    print("OK Resumo emails enviado")


def weekly_summary(dados):
    """Envia resumo semanal todas as segundas-feiras."""
    if datetime.now().weekday() != 0:  # 0 = segunda-feira
        return
    events = dados.get("events", [])
    ago7 = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent = [e for e in events if e.get("timestamp","") > ago7]
    posts = len([e for e in recent if e.get("type") in ("post","post_cr")])
    emails = len([e for e in recent if e.get("type") == "email"])
    deals = len([e for e in events if e.get("type") == "partnership"])
    sd_ig = dados.get("followers", {}).get("count", 0)
    cr_ig = dados.get("cr_followers", {}).get("count", 0)

    prompt = f"""Gera um resumo semanal para a influencer Cristiana Rodrigues em portugues europeu.
Dados da semana:
- Posts sugeridos: {posts}
- Emails processados: {emails}
- Parcerias totais: {deals}
- Swift Delux: {sd_ig} seguidores
- Cristiana IG: {cr_ig} seguidores

Responde APENAS em JSON: {{"resumo":"2-3 frases sobre a semana","conquistas":["c1","c2"],"foco_proxima_semana":["f1","f2","f3"]}}"""

    try:
        text = call_claude(prompt, 400)
        data = json.loads(text)
        line = "=" * 22
        conquistas = "\n".join(f"• {c}" for c in data.get("conquistas", []))
        foco = "\n".join(f"• {f}" for f in data.get("foco_proxima_semana", []))
        msg = (
            f"📅 <b>RESUMO SEMANAL · THE AGENCY</b>\n"
            f"<code>{line}</code>\n\n"
            f"{data['resumo']}\n\n"
            f"<b>Conquistas desta semana:</b>\n{conquistas}\n\n"
            f"<b>Foco para a proxima semana:</b>\n{foco}\n\n"
            f"<i>THE AGENCY · Weekly Summary</i>"
        )
        send_telegram(msg)
        print("OK Resumo semanal enviado")
    except Exception as e:
        print(f"Erro resumo semanal: {e}")


def check_followup_alerts(dados):
    """Alerta para parcerias sem resposta ha mais de 7 dias."""
    # This would need CRM data - placeholder for now
    pass


def main():
    dados = load_dados()

    # 1. Briefing diario
    generate_briefing(dados)

    # 2. Post Swift Delux
    generate_post_sd()

    # 3. Post Cristiana
    generate_post_cr()

    # 4. Script de Story para Cristiana
    generate_story_cr()

    # 5. Resumo de emails
    email_summary(dados)

    # 6. Resumo semanal (so as segundas)
    weekly_summary(dados)

    # Save dados
    save_dados(dados)


if __name__ == "__main__":
    main()
