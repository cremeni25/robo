# main.py — Camada de Integração + Normalização MÍNIMA
# Sequencial ao Plano Diretor
# Escopo: eventos brutos → eventos normalizados
# Sem decisão • Sem Robo • Sem escala • Sem dashboard

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

app = FastAPI(title="Robo Global AI — Normalização Mínima")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# UTILITÁRIOS
# =====================================================

def validar_hmac(secret: str, body: bytes, assinatura: str) -> bool:
    if not secret:
        return True
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, assinatura)

def normalizar_evento(plataforma: str, payload: dict) -> dict:
    """
    Normalização mínima:
    cria um formato comum independente da origem
    """
    return {
        "plataforma": plataforma,
        "tipo_evento": payload.get("event") or payload.get("type") or "desconhecido",
        "valor": payload.get("value") or payload.get("price") or None,
        "moeda": payload.get("currency") or "BRL",
        "referencia": payload.get("transaction") or payload.get("purchase_id"),
        "payload_original": payload,
        "criado_em": datetime.utcnow().isoformat(),
    }

def persistir_bruto(plataforma: str, payload: dict):
    supabase.table("eventos_afiliados_brutos").insert({
        "plataforma_origem": plataforma,
        "payload_original": payload,
        "hash_evento": payload.get("event", f"{plataforma}_{datetime.utcnow().isoformat()}"),
    }).execute()

def persistir_normalizado(evento_normalizado: dict):
    supabase.table("eventos_afiliados_normalizados").insert(evento_normalizado).execute()

# =====================================================
# WEBHOOK HOTMART
# =====================================================

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    raw_body = await request.body()
    assinatura = request.headers.get("X-Hotmart-Hmac-SHA256", "")

    if not validar_hmac(HOTMART_WEBHOOK_SECRET, raw_body, assinatura):
        raise HTTPException(status_code=401, detail="Assinatura Hotmart inválida")

    payload = await request.json()

    persistir_bruto("hotmart", payload)
    evento_norm = normalizar_evento("hotmart", payload)
    persistir_normalizado(evento_norm)

    return {"status": "ok", "origem": "hotmart", "normalizado": True}

# =====================================================
# WEBHOOK EDUZZ
# =====================================================

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    raw_body = await request.body()
    assinatura = request.headers.get("X-Eduzz-Signature", "")

    if not validar_hmac(EDUZZ_WEBHOOK_SECRET, raw_body, assinatura):
        raise HTTPException(status_code=401, detail="Assinatura Eduzz inválida")

    payload = await request.json()

    persistir_bruto("eduzz", payload)
    evento_norm = normalizar_evento("eduzz", payload)
    persistir_normalizado(evento_norm)

    return {"status": "ok", "origem": "eduzz", "normalizado": True}

# =====================================================
# STATUS HUMANO
# =====================================================

@app.get("/status")
def status():
    return {
        "servico": "Robo Global AI — Normalização Mínima",
        "estado": "ativo",
        "timestamp": datetime.utcnow().isoformat()
    }
