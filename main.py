# main.py — ROBO GLOBAL AI
# Versão correta para DEPLOY OK na Render
# Correção estrutural: nenhuma variável externa quebra o boot

import os
import json
from datetime import datetime

from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import stripe
from supabase import create_client

# =====================================================
# APP
# =====================================================

app = FastAPI(title="ROBO GLOBAL AI", version="1.0.0")

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
# STATUS
# =====================================================

@app.get("/status")
async def status():
    return {
        "status": "online",
        "servico": "robo-global-api-v2",
        "timestamp": datetime.utcnow().isoformat()
    }

# =====================================================
# WEBHOOK STRIPE (VALIDAÇÃO SOMENTE AQUI)
# =====================================================

@app.post("/webhook/stripe")
async def webhook_stripe(
    request: Request,
    stripe_signature: str = Header(None)
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
        return JSONResponse(
            status_code=400,
            content={"erro": "Webhook Stripe inválido", "detalhe": str(e)}
        )

    # =================================================
    # PROCESSAMENTO FINANCEIRO REAL
    # =================================================

    evento_tipo = event["type"]
    dados = event["data"]["object"]

    registro = {
        "origem": "stripe",
        "evento": evento_tipo,
        "valor": dados.get("amount", 0) / 100 if dados.get("amount") else 0,
        "moeda": dados.get("currency"),
        "payload": event,
        "criado_em": datetime.utcnow().isoformat()
    }

    if supabase:
        supabase.table("eventos_financeiros").insert(registro).execute()

    return {"status": "ok"}

# =====================================================
# FINANCEIRO — RESUMO (PROTEGIDO)
# =====================================================

@app.get("/financeiro/resumo")
async def financeiro_resumo(authorization: str = Header(None)):
    api_key = os.getenv("API_KEY_INTERNA")

    if not api_key or authorization != f"Bearer {api_key}":
        return JSONResponse(status_code=401, content={"erro": "Unauthorized"})

    if not supabase:
        return {"total": 0, "mensagem": "Supabase não configurado"}

    dados = supabase.table("eventos_financeiros").select("valor").execute()

    total = sum(item["valor"] for item in dados.data) if dados.data else 0

    return {
        "total_recebido": total,
        "eventos": len(dados.data)
    }
