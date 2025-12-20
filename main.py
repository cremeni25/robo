# main.py — ROBO GLOBAL AI
# FASE 1 + FASE 2A
# Motor de decisão + Motor autônomo de busca e análise de oportunidades
# SEM atuação humana • SEM dinheiro • SEM execução externa

import os
import asyncio
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from supabase import create_client
import stripe

# =====================================================
# APP
# =====================================================

app = FastAPI(title="ROBO GLOBAL AI", version="fase-2a-autonomo")

# =====================================================
# CORS
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# SUPABASE
# =====================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")

supabase = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

# =====================================================
# PARÂMETROS GERAIS
# =====================================================

CICLO_DECISAO_MIN = 5
CICLO_BUSCA_MIN = 30   # busca de oportunidades a cada 30 min

# =====================================================
# FASE 1 — MOTOR DE DECISÃO (JÁ VALIDADO)
# =====================================================

def motor_decisao(capital_disponivel: float) -> dict:
    agora = datetime.utcnow()

    if capital_disponivel <= 0:
        return {
            "estado": "DECIDIU_NAO_AGIR",
            "decisão": "nao_agir",
            "razão": "Capital zero. Ação externa proibida.",
            "carimbo_de_data": agora.isoformat(),
            "proxima_avaliação": (agora + timedelta(minutes=CICLO_DECISAO_MIN)).isoformat()
        }

    return {
        "estado": "DECIDIU_AGIR",
        "decisão": "agir",
        "razão": "Condições futuras permitiriam ação. Execução só em fases posteriores.",
        "carimbo_de_data": agora.isoformat(),
        "proxima_avaliação": (agora + timedelta(minutes=CICLO_DECISAO_MIN)).isoformat()
    }

def registrar_decisao(decisao: dict):
    if supabase:
        supabase.table("decides_motor").insert(decisao).execute()

async def ciclo_motor_decisao():
    await asyncio.sleep(3)
    while True:
        try:
            decisao = motor_decisao(0)
            registrar_decisao(decisao)
        except Exception:
            pass
        await asyncio.sleep(CICLO_DECISAO_MIN * 60)

# =====================================================
# FASE 2A — MOTOR AUTÔNOMO DE BUSCA E ANÁLISE
# =====================================================

FONTES_PUBLICAS = [
    {
        "origem": "https://www.futurepedia.io/",
        "categoria": "AI Tools"
    },
    {
        "origem": "https://www.saasworthy.com/",
        "categoria": "SaaS"
    }
]

def calcular_score(oferta: dict) -> int:
    score = 0

    if oferta.get("preco_estimado"):
        score += 20
    if oferta.get("modelo_receita") == "recorrente":
        score += 25
    if oferta.get("publico_alvo"):
        score += 20
    if len(oferta.get("descricao_curta", "")) > 40:
        score += 15
    score += 10  # risco operacional baixo (fase exploratória)

    return min(score, 100)

def extrair_ofertas_fonte(fonte: dict) -> List[dict]:
    ofertas = []

    try:
        resp = requests.get(fonte["origem"], timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        cards = soup.find_all("a")[:10]  # leitura superficial controlada

        for card in cards:
            nome = card.get_text(strip=True)
            if len(nome) < 5:
                continue

            oferta = {
                "origem": fonte["origem"],
                "nome_oferta": nome[:120],
                "categoria": fonte["categoria"],
                "descricao_curta": f"Oferta identificada automaticamente em {fonte['origem']}",
                "preco_estimado": None,
                "modelo_receita": "recorrente",
                "publico_alvo": "global",
            }

            score = calcular_score(oferta)
            oferta["score_viabilidade"] = score
            oferta["status"] = "priorizada" if score >= 60 else "identificada"
            oferta["motivo"] = f"Score automático {score} baseado em modelo recorrente e público global."
            oferta["criado_em"] = datetime.utcnow().isoformat()

            ofertas.append(oferta)

    except Exception:
        pass

    return ofertas

def registrar_oportunidade(oferta: dict):
    if not supabase:
        return

    supabase.table("oportunidades_robo").insert(oferta).execute()

async def ciclo_busca_oportunidades():
    await asyncio.sleep(10)
    while True:
        try:
            for fonte in FONTES_PUBLICAS:
                ofertas = extrair_ofertas_fonte(fonte)
                for oferta in ofertas:
                    registrar_oportunidade(oferta)
        except Exception:
            pass

        await asyncio.sleep(CICLO_BUSCA_MIN * 60)

# =====================================================
# STARTUP
# =====================================================

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(ciclo_motor_decisao())
    asyncio.create_task(ciclo_busca_oportunidades())

# =====================================================
# STATUS
# =====================================================

@app.get("/status")
async def status():
    return {
        "status": "online",
        "fase": "1 + 2A",
        "motor_decisao": "ativo",
        "motor_busca": "ativo",
        "timestamp": datetime.utcnow().isoformat()
    }

# =====================================================
# STRIPE — SENSOR FINANCEIRO (INALTERADO)
# =====================================================

@app.post("/webhook/stripe")
async def webhook_stripe(
    request: Request,
    stripe_signature: Optional[str] = Header(None)
):
    stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    stripe_api_key = os.getenv("STRIPE_API_KEY")

    if not stripe_webhook_secret or not stripe_api_key:
        return JSONResponse(status_code=500, content={"erro": "Stripe não configurado"})

    stripe.api_key = stripe_api_key
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=stripe_webhook_secret
        )
    except Exception as e:
        return JSONResponse(status_code=400, content={"erro": str(e)})

    if supabase:
        supabase.table("eventos_financeiros").insert({
            "origem": "stripe",
            "evento": event["type"],
            "valor": event["data"]["object"].get("amount", 0) / 100,
            "moeda": event["data"]["object"].get("currency"),
            "payload": event,
            "criado_em": datetime.utcnow().isoformat()
        }).execute()

    return {"status": "ok"}
