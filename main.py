# main.py — ROBO GLOBAL AI
# FASE 1 — MOTOR DE DECISÃO + SCHEDULER
# Backend alinhado ao modelo real: public.decides_motor

import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from supabase import create_client
import stripe

# =====================================================
# APP
# =====================================================

app = FastAPI(title="ROBO GLOBAL AI", version="fase-1-alinhada")

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
# PARÂMETROS FIXOS — FASE 1
# =====================================================

CAPITAL_MAXIMO = 300
RISCO_MAXIMO_PERCENT = 10
RETORNO_MINIMO_PERCENT = 30
CICLO_MINUTOS = 5

# =====================================================
# MOTOR DE DECISÃO
# =====================================================

def motor_decisao(capital_disponivel: float) -> dict:
    agora = datetime.utcnow()

    if capital_disponivel <= 0:
        return {
            "estado": "DECIDIU_NAO_AGIR",
            "decisão": "nao_agir",
            "razão": "Capital disponível é zero. FASE 1 não permite ação externa.",
            "carimbo_de_data": agora.isoformat(),
            "proxima_avaliação": (agora + timedelta(minutes=CICLO_MINUTOS)).isoformat()
        }

    return {
        "estado": "DECIDIU_AGIR",
        "decisão": "agir",
        "razão": "Condições permitiriam ação futura. Execução ocorrerá apenas na FASE 2.",
        "carimbo_de_data": agora.isoformat(),
        "proxima_avaliação": (agora + timedelta(minutes=CICLO_MINUTOS)).isoformat()
    }

# =====================================================
# REGISTRO NO BANCO (ALINHADO)
# =====================================================

def registrar_decisao(decisao: dict):
    if not supabase:
        return

    supabase.table("decides_motor").insert(decisao).execute()

# =====================================================
# SCHEDULER
# =====================================================

async def ciclo_motor():
    await asyncio.sleep(3)
    while True:
        try:
            capital_disponivel = 0
            decisao = motor_decisao(capital_disponivel)
            registrar_decisao(decisao)
        except Exception:
            pass

        await asyncio.sleep(CICLO_MINUTOS * 60)

# =====================================================
# STARTUP
# =====================================================

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(ciclo_motor())

# =====================================================
# STATUS
# =====================================================

@app.get("/status")
async def status():
    return {
        "status": "online",
        "fase": 1,
        "motor": "ativo",
        "ciclo_minutos": CICLO_MINUTOS,
        "timestamp": datetime.utcnow().isoformat()
    }

# =====================================================
# STRIPE (SENSOR — JÁ VALIDADO)
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
