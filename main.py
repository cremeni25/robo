# main.py — Camada de Integração + Webhooks Hotmart e EDUZZ (Ingestão Real Mínima)
# Sequencial ao Plano Diretor
# Escopo: ingestão real mínima → Supabase
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
EDUZZ_WEBHOOK_SECRET = os.getenv("EDUZZ_WEBHOOK_SECRET")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Variáveis SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórias")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# =====================================================
# APP
# =====================================================

app = FastAPI(title="Robo Global AI — Ingestão Real Mínima")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# VALIDAÇÕES DE ASSINATURA
# =====================================================

def validar_hmac_sha256(secret: str, body: bytes, assinatura: str) -> bool:
    if not secret:
        return True  # modo permissivo se secret não estiver definido
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, assinatura)


# =====================================================
# WEBHOOK HOTMART
# =====================================================

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    raw_body = await request.body()
    assinatura = request.headers.get("X-Hotmart-Hmac-SHA256", "")

    if not validar_hmac_sha256(HOTMART_WEBHOOK_SECRET, raw_body, assinatura):
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

    result = supabase.table("eventos_afiliados_brutos").insert(registro).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Falha ao persistir evento Hotmart")

    return {"status": "ok", "origem": "hotmart"}


# =====================================================
# WEBHOOK EDUZZ — INGESTÃO REAL MÍNIMA
# =====================================================

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    raw_body = await request.body()
    assinatura = request.headers.get("X-Eduzz-Signature", "")

    if not validar_hmac_sha256(EDUZZ_WEBHOOK_SECRET, raw_body, assinatura):
        raise HTTPException(status_code=401, detail="Assinatura Eduzz inválida")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload JSON inválido")

    registro = {
        "plataforma_origem": "eduzz",
        "payload_original": payload,
        "hash_evento": payload.get("event", f"eduzz_{datetime.utcnow().isoformat()}"),
    }

    result = supabase.table("eventos_afiliados_brutos").insert(registro).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Falha ao persistir evento Eduzz")

    return {"status": "ok", "origem": "eduzz"}


# =====================================================
# STATUS HUMANO
# =====================================================

@app.get("/status")
def status():
    return {
        "servico": "Robo Global AI — Ingestão Real Mínima (Hotmart + Eduzz)",
        "estado": "ativo",
        "timestamp": datetime.utcnow().isoformat()
    }
