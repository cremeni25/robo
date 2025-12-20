# main.py — ROBO GLOBAL AI
# ETAPA 3: INGESTÃO DE EVENTOS (RAW)
# Correção definitiva: Content-Profile correto

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import hashlib
import json
import os
import requests

# ======================================================
# APP
# ======================================================
app = FastAPI(
    title="Robo Global AI",
    version="1.0.0",
    description="Backend central do Robo Global AI — Afiliados"
)

# ======================================================
# CORS
# ======================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# SUPABASE (REST)
# ======================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase não configurado (env vars ausentes)")

SUPABASE_REST_ENDPOINT = f"{SUPABASE_URL}/rest/v1/eventos_afiliados_raw"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Content-Profile": "robo_global",   # 🔥 OBRIGATÓRIO PARA INSERT
    "Prefer": "return=minimal"
}

# ======================================================
# HEALTH
# ======================================================
@app.get("/health")
def health():
    return {
        "status": "ok",
        "stage": "ETAPA 3 — Ingestão RAW",
        "timestamp": datetime.utcnow().isoformat()
    }

# ======================================================
# ROOT
# ======================================================
@app.get("/")
def root():
    return {
        "message": "Robo Global AI ativo",
        "stage": "ETAPA 3 — Ingestão RAW"
    }

# ======================================================
# WEBHOOK RAW
# ======================================================
@app.post("/webhook/{plataforma}")
async def webhook_raw(plataforma: str, request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload inválido")

    payload_str = json.dumps(payload, sort_keys=True)
    hash_evento = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    data = {
        "plataforma_origem": plataforma,
        "payload_original": payload,
        "hash_evento": hash_evento,
        "data_recebimento": datetime.utcnow().isoformat()
    }

    response = requests.post(
        SUPABASE_REST_ENDPOINT,
        headers=HEADERS,
        json=data,
        timeout=10
    )

    if response.status_code not in (200, 201, 204):
        raise HTTPException(
            status_code=500,
            detail=f"Erro Supabase REST ({response.status_code}): {response.text}"
        )

    return {
        "status": "recebido",
        "plataforma": plataforma,
        "hash_evento": hash_evento
    }
