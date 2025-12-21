# main.py — Camada de Integração + Webhook Hotmart (Ingestão Real Mínima)
# Sequencial ao Plano Diretor
# Escopo: ingestão real Hotmart → Supabase
# Sem decisão • Sem Robo • Sem dashboard

import os
import hmac
import hashlib
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

# =====================================================
# CONFIGURAÇÃO
# =====================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Variáveis SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórias")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# =====================================================
# APP
# =====================================================

app = FastAPI(title="Robo Global AI — Ingestão Hotmart")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# FUNÇÃO DE VALIDAÇÃO HOTMART (HMAC)
# =====================================================

def validar_hotmart_assinatura(body: bytes, assinatura: str) -> bool:
    if not HOTMART_WEBHOOK_SECRET:
        return True  # modo permissivo se secret não estiver definido
    digest = hmac.new(
        HOTMART_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(digest, assinatura)

# =====================================================
# WEBHOOK HOTMART — INGESTÃO REAL
# =====================================================

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    raw_body = await request.body()
    assinatura = request.headers.get("X-Hotmart-Hmac-SHA256", "")

    if not validar_hotmart_assinatura(raw_body, assinatura):
        raise HTTPException(status_code=401, detail="Assinatura Hotmart inválida")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload JSON inválido")

    registro = {
        "plataforma_origem": "hotmart",
        "payload_original": payload,
        "hash_evento": payload.get("event", f"hotmart_{datetime.utcnow().isoformat()}"),
    }

    try:
        result = supabase.table("eventos_afiliados_brutos").insert(registro).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not result.data:
        raise HTTPException(status_code=500, detail="Falha ao persistir evento Hotmart")

    return {
        "status": "ok",
        "mensagem": "Evento Hotmart recebido e persistido",
        "registro_id": result.data[0].get("id")
    }

# =====================================================
# STATUS HUMANO
# =====================================================

@app.get("/status")
def status():
    return {
        "servico": "Robo Global AI — Webhook Hotmart",
        "estado": "ativo",
        "timestamp": datetime.utcnow().isoformat()
    }
