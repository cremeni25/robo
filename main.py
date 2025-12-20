# main.py — ROBO GLOBAL AI
# FASE 1 — MOTOR DE DECISÃO + SCHEDULER + PERSISTÊNCIA
# Estado protocolar: DECIDIR (sem dinheiro, sem ação externa)

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

app = FastAPI(title="ROBO GLOBAL AI", version="fase-1")

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
# SUPABASE (NÃO QUEBRA BOOT)
# =====================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")

supabase = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

# =====================================================
# PARÂMETROS FIXOS — FASE 1 (CONGELADOS)
# =====================================================

CAPITAL_MAXIMO = 300
RISCO_MAXIMO_PERCENT = 10        # %
RETORNO_MINIMO_PERCENT = 30      # %
CICLO_MINUTOS = 5

RISCO_MAXIMO_ABSOLUTO = CAPITAL_MAXIMO * (RISCO_MAXIMO_PERCENT / 100)

# =====================================================
# ESTADOS DO ROBO
# =====================================================

ESTADOS_VALIDOS = [
    "IDLE",
    "ANALISANDO",
    "DECIDIU_AGIR",
    "DECIDIU_NAO_AGIR",
    "BLOQUEADO_POR_RISCO"
]

# =====================================================
# FUNÇÃO CENTRAL — MOTOR DE DECISÃO
# =====================================================

def motor_decisao(capital_disponivel: float) -> dict:
    """
    Motor de decisão da FASE 1.
    Não executa ações externas.
    Sempre retorna decisão + motivo humano.
    """

    agora = datetime.utcnow()

    # Estado inicial
    estado = "ANALISANDO"

    # Regra 1 — Capital zero
    if capital_disponivel <= 0:
        return {
            "estado": "DECIDIU_NAO_AGIR",
            "decisao": "nao_agir",
            "motivo": "Capital disponível é zero. Ação externa não permitida nesta fase.",
            "timestamp": agora.isoformat(),
            "proxima_avaliacao": (agora + timedelta(minutes=CICLO_MINUTOS)).isoformat()
        }

    # Regra 2 — Risco absoluto
    if capital_disponivel > RISCO_MAXIMO_ABSOLUTO:
        return {
            "estado": "BLOQUEADO_POR_RISCO",
            "decisao": "nao_agir",
            "motivo": "Capital disponível excede o risco máximo absoluto permitido.",
            "timestamp": agora.isoformat(),
            "proxima_avaliacao": (agora + timedelta(minutes=CICLO_MINUTOS)).isoformat()
        }

    # Regra 3 — Meta mínima (placeholder lógico, sem aquisição)
    return {
        "estado": "DECIDIU_AGIR",
        "decisao": "agir",
        "motivo": "Parâmetros permitem ação futura. Ação externa será liberada apenas na FASE 2.",
        "timestamp": agora.isoformat(),
        "proxima_avaliacao": (agora + timedelta(minutes=CICLO_MINUTOS)).isoformat()
    }

# =====================================================
# PERSISTÊNCIA — REGISTRO DO CICLO
# =====================================================

def registrar_ciclo(decisao: dict):
    if not supabase:
        return

    supabase.table("decisoes_motor").insert({
        "estado": decisao["estado"],
        "decisao": decisao["decisao"],
        "motivo": decisao["motivo"],
        "timestamp": decisao["timestamp"],
        "proxima_avaliacao": decisao["proxima_avaliacao"]
    }).execute()

# =====================================================
# SCHEDULER — CICLO AUTOMÁTICO
# =====================================================

async def ciclo_motor():
    await asyncio.sleep(3)  # pequena espera para boot completo

    while True:
        try:
            capital_disponivel = 0  # FASE 1 — SEM DINHEIRO

            decisao = motor_decisao(capital_disponivel)
            registrar_ciclo(decisao)

        except Exception as e:
            if supabase:
                supabase.table("decisoes_motor").insert({
                    "estado": "ERRO",
                    "decisao": "erro",
                    "motivo": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                    "proxima_avaliacao": None
                }).execute()

        await asyncio.sleep(CICLO_MINUTOS * 60)

# =====================================================
# EVENTO DE STARTUP
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
# WEBHOOK STRIPE (JÁ VALIDADO — SENSOR FINANCEIRO)
# =====================================================

@app.post("/webhook/stripe")
async def webhook_stripe(
    request: Request,
    stripe_signature: Optional[str] = Header(None)
):
    stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    stripe_api_key = os.getenv("STRIPE_API_KEY")

    if not stripe_webhook_secret or not stripe_api_key:
        return JSONResponse(
            status_code=500,
            content={"erro": "Credenciais Stripe não configuradas"}
        )

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
