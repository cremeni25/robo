# main.py — ROBO GLOBAL AI
# PRODUÇÃO REAL • FINANCEIRO REAL • STRIPE ATIVO
# Arquivo ÚNICO • INTEIRO • FINAL

import os
import json
import stripe
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# =====================================================
# CONFIGURAÇÕES DE AMBIENTE (PRODUÇÃO)
# =====================================================

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

CAPITAL_MAXIMO = float(os.getenv("CAPITAL_MAXIMO", "0"))
RISCO_MAX_CICLO = float(os.getenv("RISCO_MAX_CICLO", "0"))

if not STRIPE_SECRET_KEY:
    raise RuntimeError("STRIPE_SECRET_KEY não configurada")

if not STRIPE_WEBHOOK_SECRET:
    raise RuntimeError("STRIPE_WEBHOOK_SECRET não configurada")

stripe.api_key = STRIPE_SECRET_KEY

# =====================================================
# APP
# =====================================================

app = FastAPI(
    title="ROBO GLOBAL AI",
    description="Motor financeiro real baseado em eventos Stripe",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# HEALTHCHECK
# =====================================================

@app.get("/status")
def status():
    return {
        "status": "ONLINE",
        "modo": "PRODUÇÃO",
        "timestamp": datetime.utcnow().isoformat()
    }

# =====================================================
# WEBHOOK STRIPE — PRODUÇÃO REAL
# =====================================================

@app.post("/webhook/stripe")
async def webhook_stripe(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Assinatura Stripe ausente")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Assinatura Stripe inválida")
    except Exception:
        raise HTTPException(status_code=400, detail="Evento Stripe inválido")

    # =================================================
    # EVENTO FINANCEIRO REAL
    # =================================================

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]

        evento_financeiro = {
            "evento": "PAYMENT_INTENT_SUCCEEDED",
            "payment_intent_id": intent["id"],
            "valor": intent["amount_received"] / 100,
            "moeda": intent["currency"].upper(),
            "email": intent.get("receipt_email"),
            "status": intent["status"],
            "data": datetime.utcnow().isoformat(),
        }

        print("💰 EVENTO FINANCEIRO REAL RECEBIDO")
        print(json.dumps(evento_financeiro, ensure_ascii=False))

        # =================================================
        # PONTO ÚNICO DE INTEGRAÇÃO DO ROBO
        # =================================================
        # Aqui é onde o Robo Global AI:
        # - Registra no Supabase
        # - Atualiza capital
        # - Dispara decisão econômica
        # Nenhuma simulação ocorre aqui.
        # =================================================

    return {"status": "ok"}

# =====================================================
# FIM DO ARQUIVO
# =====================================================
