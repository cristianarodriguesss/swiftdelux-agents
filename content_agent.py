"""
THE AGENCY - Content Agent
Gera conteudo diario para Swift Delux e Cristiana Rodrigues.
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
    "lifestyle aspiracional - a peca no dia a dia de uma mulher europeia",
    "detalhe e brilho - foco no acabamento e qualidade da joia",
    "storytelling de marca - os valores da Swift Delux",
    "look completo - como combinar a peca com um outfit",
    "presente especial - a joia como prenda",
    "behind the scenes - processo de criacao",
]

ANGLES_CR = [
    "wellness matinal - rotina de manha, mindfulness, self-care",
    "viagem e lifestyle - destino europeu, momento aspiracional",
    "beleza - skincare rotina, produto favorito",
    "moda - outfit do dia, tendencia da estacao",
    "autenticidade - momento real, bastidores da vida",
    "motivacao - reflexao pessoal, algo que aprendeste",
]

STORY_THEMES = [
    "O meu ritual de manha nos primeiros 30 minutos do dia",
    "O produto de beleza que nao largo - honesto",
    "O que estou a ouvir esta semana - recomendacoes",
    "Bastidores do meu trabalho como influencer",
    "A minha rotina de exercicio atual",
    "Dica do destino que mais gostei ultimamente",
    "Dia na minha vida - formato simples e autentico",
]

BEST_TIMES = [
    "18h00-21h00 (Lisboa) - pico maximo do teu publico",
    "19h00-21h00 (Lisboa) - melhor para Reels",
    "12h00-13h00 (Lisboa) - pausa do almoco",
    "20h00-21h30 (Lisboa) - maximo de engagement",
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
    posts7 = len([e for e in events if e.get("type") in ("post", "post_cr") and e.get("timestamp", "") > ago7])
    emails24 = len([e for e in events if e.get("type") == "email" and e.get("timestamp", "") > ago24])
    deals = len([e for e in events if e.get("type") == "partnership"])
    sd_ig = dados.get("followers", {}).get("count", 1254)
    cr_ig = dados.get("cr_followers", {}).get("count", 6959)

    prompt = (
        "Es assistente de THE AGENCY, agencia portuguesa que gere Swift Delux (joias) e Cristiana Rodrigues (influencer).\n"
        "Gera briefing diario conciso em portugues europeu.\n\n"
        f"Dados:\n"
        f"- Swift Delux IG: {sd_ig} seguidores (meta 10k)\n"
        f"- Cristiana IG: {cr_ig} seguidores\n"
        f"- Parcerias: {deals}\n"
        f"- Emails 24h: {emails24}\n"
        f"- Posts 7 dias: {posts7}\n\n"
        'Responde APENAS em JSON: {"resumo":"1-2 frases","destaques":["d1","d2","d3"],"tarefas":["t1","t2","t3","t4"]}'
    )

    try:
        text = call_claude(prompt, 400)
        briefing = json.loads(text)
        briefing["date"] = datetime.now().strftime("%d/%m/%Y")
        dados["briefing"] = briefing
        line = "=" * 22
        hl = "\n".join("* " + d for d in briefing.get("destaques", []))
        tk = "\n".join("* " + t for t in briefing.get("tarefas", []))
        msg = (
            "OK <b>AGENCY BRIEFING - " + briefing["date"] + "</b>\n"
            "<code>" + line + "</code>\n\n"
            + briefing["resumo"] + "\n\n"
            "<b>Destaques:</b>\n" + hl + "\n\n"
            "<b>Para hoje:</b>\n" + tk + "\n\n"
            "<i>THE AGENCY</i>"
        )
        send_telegram(msg)
        print("OK Briefing enviado")
    except Exception as e:
        print(f"Erro briefing: {e}")


def generate_post_sd():
    angle = random.choice(ANGLES_SD)
    prompt = (
        "Sugere 1 ideia de post para Instagram da Swift Delux (joias minimalistas, mulheres 20-36, Europa).\n"
        f"Angulo: {angle}\n\n"
        'JSON valido: {"conceito_visual":"descricao breve","legenda":"portugues europeu, 2-3 frases + emoji","hashtags":["#t1","#t2","#t3","#t4","#t5","#t6","#t7","#t8"],"cta":"call to action curto"}'
    )
    try:
        idea = json.loads(call_claude(prompt, 400))
        best_time = random.choice(BEST_TIMES)
        line = "-" * 22
        hashtags = " ".join(idea.get("hashtags", []))
        msg = (
            "XX <b>SWIFT DELUX - POST DO DIA</b>\n"
            "<code>" + line + "</code>\n\n"
            "VIDEO <b>Conceito:</b> " + idea.get("conceito_visual", "") + "\n\n"
            "TEXTO <b>Legenda:</b>\n<i>" + idea.get("legenda", "") + "</i>\n\n"
            "GO " + idea.get("cta", "") + "\n\n"
            "TAGS <code>" + hashtags + "</code>\n\n"
            "RELOGIO <b>Horario:</b> " + best_time + "\n\n"
            "<i>THE AGENCY</i>"
        )
        send_telegram(msg)
        add_event("post", idea.get("legenda", "")[:80])
        print("OK Post Swift Delux enviado")
    except Exception as e:
        print(f"Erro post SD: {e}")


def generate_post_cr():
    angle = random.choice(ANGLES_CR)
    prompt = (
        "Sugere 1 ideia de post para Instagram de Cristiana Rodrigues, influencer portuguesa de lifestyle, wellness, viagens e beleza.\n"
        "Publico: mulheres 25-34, Portugal e Brasil, autentica e aspiracional.\n"
        f"Angulo: {angle}\n\n"
        'JSON valido: {"conceito_visual":"descricao breve","legenda":"portugues europeu, 2-3 frases + emoji","hashtags":["#t1","#t2","#t3","#t4","#t5","#t6","#t7","#t8","#t9","#t10"],"cta":"call to action curto"}'
    )
    try:
        idea = json.loads(call_claude(prompt, 400))
        best_time = random.choice(BEST_TIMES)
        line = "-" * 22
        hashtags = " ".join(idea.get("hashtags", []))
        msg = (
            "FLOR <b>@CRIS - POST DO DIA</b>\n"
            "<code>" + line + "</code>\n\n"
            "VIDEO <b>Conceito:</b> " + idea.get("conceito_visual", "") + "\n\n"
            "TEXTO <b>Legenda:</b>\n<i>" + idea.get("legenda", "") + "</i>\n\n"
            "GO " + idea.get("cta", "") + "\n\n"
            "TAGS <code>" + hashtags + "</code>\n\n"
            "RELOGIO <b>Horario:</b> " + best_time + "\n\n"
            "<i>THE AGENCY</i>"
        )
        send_telegram(msg)
        add_event("post_cr", idea.get("legenda", "")[:80])
        print("OK Post Cristiana enviado")
    except Exception as e:
        print(f"Erro post CR: {e}")


def generate_story_cr():
    theme = random.choice(STORY_THEMES)
    prompt = (
        "Cria um script de Story para Instagram de Cristiana Rodrigues (influencer portuguesa, lifestyle/wellness/viagens/beleza).\n"
        f"Tema: {theme}\n"
        "Duracao: 60 segundos, tom autentico e conversacional.\n"
        "Publico: mulheres 25-34, Portugal e Brasil.\n\n"
        'JSON valido: {"titulo":"titulo chamativo para capa","script":"script completo dividido em 3-4 momentos","dica":"dica de producao","cta":"call to action final"}'
    )
    try:
        story = json.loads(call_claude(prompt, 500))
        line = "-" * 22
        msg = (
            "TELEMOVEL <b>@CRIS - SCRIPT DE STORY</b>\n"
            "<code>" + line + "</code>\n\n"
            "ALVO <b>Capa:</b> " + story.get("titulo", "") + "\n\n"
            "LIVRO <b>Script:</b>\n" + story.get("script", "") + "\n\n"
            "LAMPADA <b>Dica:</b> " + story.get("dica", "") + "\n\n"
            "GO <b>CTA:</b> " + story.get("cta", "") + "\n\n"
            "<i>THE AGENCY</i>"
        )
        send_telegram(msg)
        print("OK Script de story enviado")
    except Exception as e:
        print(f"Erro story CR: {e}")


def email_summary(dados):
    events = dados.get("events", [])
    ago24 = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    recent = [e for e in events if e.get("type") == "email" and e.get("timestamp", "") > ago24]
    if not recent:
        return
    urgentes = sum(1 for e in recent if "urgente" in e.get("summary", "").lower())
    clientes = sum(1 for e in recent if "cliente" in e.get("summary", "").lower())
    fornecedores = sum(1 for e in recent if "fornecedor" in e.get("summary", "").lower())
    line = "-" * 22
    msg = (
        "GRAFICO <b>RESUMO DE EMAILS - " + datetime.now().strftime("%d/%m/%Y") + "</b>\n"
        "<code>" + line + "</code>\n\n"
        "EMAIL <b>Total (24h):</b> " + str(len(recent)) + "\n"
        "VERMELHO Urgentes: " + str(urgentes) + "\n"
        "XX Clientes: " + str(clientes) + "\n"
        "CAIXA Fornecedores: " + str(fornecedores) + "\n\n"
        "<i>Abre o dashboard para ver as respostas sugeridas.</i>\n\n"
        "<i>THE AGENCY</i>"
    )
    send_telegram(msg)
    print("OK Resumo emails enviado")


def weekly_summary(dados):
    if datetime.now().weekday() != 0:
        return
    events = dados.get("events", [])
    ago7 = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent = [e for e in events if e.get("timestamp", "") > ago7]
    posts = len([e for e in recent if e.get("type") in ("post", "post_cr")])
    emails = len([e for e in recent if e.get("type") == "email"])
    deals = len([e for e in events if e.get("type") == "partnership"])
    sd_ig = dados.get("followers", {}).get("count", 0)
    cr_ig = dados.get("cr_followers", {}).get("count", 0)

    prompt = (
        "Gera um resumo semanal para a influencer Cristiana Rodrigues em portugues europeu.\n"
        f"Dados: posts sugeridos {posts}, emails {emails}, parcerias {deals}, Swift Delux {sd_ig} seg, Cristiana {cr_ig} seg.\n\n"
        'JSON: {"resumo":"2-3 frases","conquistas":["c1","c2"],"foco":["f1","f2","f3"]}'
    )
    try:
        data = json.loads(call_claude(prompt, 400))
        line = "=" * 22
        conquistas = "\n".join("* " + c for c in data.get("conquistas", []))
        foco = "\n".join("* " + f for f in data.get("foco", []))
        msg = (
            "CALENDARIO <b>RESUMO SEMANAL - THE AGENCY</b>\n"
            "<code>" + line + "</code>\n\n"
            + data.get("resumo", "") + "\n\n"
            "<b>Conquistas:</b>\n" + conquistas + "\n\n"
            "<b>Foco proxima semana:</b>\n" + foco + "\n\n"
            "<i>THE AGENCY</i>"
        )
        send_telegram(msg)
        print("OK Resumo semanal enviado")
    except Exception as e:
        print(f"Erro resumo semanal: {e}")


def followers_reminder(dados):
    if datetime.now().weekday() != 0:
        return
    sd_ig = dados.get("followers", {}).get("count", 0)
    cr_ig = dados.get("cr_followers", {}).get("count", 0)
    line = "-" * 22
    msg = (
        "GRAFICO <b>ACTUALIZAR SEGUIDORES - Segunda-feira</b>\n"
        "<code>" + line + "</code>\n\n"
        "Ultimos valores guardados:\n"
        "XX Swift Delux IG: <b>" + str(sd_ig) + "</b>\n"
        "FLOR @cris IG: <b>" + str(cr_ig) + "</b>\n\n"
        "Para actualizar:\n"
        "1. Abre o Instagram de cada conta\n"
        "2. Ve quantos seguidores tens agora\n"
        "3. GitHub - Actions - Swift Delux Agents - Run workflow\n"
        "4. Preenche os campos e corre\n\n"
        "<i>THE AGENCY</i>"
    )
    send_telegram(msg)
    print("OK Lembrete seguidores enviado")


def main():
    dados = load_dados()

    generate_briefing(dados)
    generate_post_sd()
    generate_post_cr()
    generate_story_cr()
    email_summary(dados)
    weekly_summary(dados)
    followers_reminder(dados)

    save_dados(dados)


if __name__ == "__main__":
    main()
