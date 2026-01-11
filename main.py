# main.py — versão final
import os
import hmac
import hashlib
import json
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

# ============================================================
# CONFIG
# ============================================================

APP_NAME = "ROBO GLOBAL AI"
ENV = os.getenv("ENV", "prod")

HOTMART_HMAC_SECRET = os.getenv("HOTMART_HMAC_SECRET", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase credentials not set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# APP
# ============================================================

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# LOGGING
# ============================================================

def log(origin: str, level: str, message: str):
    print(f"[{origin}] [{level}] {message}")

# ============================================================
# CORE
# ============================================================

def normalizar_evento(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "plataforma": "hotmart",
        "evento": payload.get("event"),
        "email": payload.get("data", {}).get("buyer", {}).get("email"),
        "produto": payload.get("data", {}).get("product", {}).get("name"),
        "valor": payload.get("data", {}).get("purchase", {}).get("price", {}).get("value"),
        "moeda": payload.get("data", {}).get("purchase", {}).get("price", {}).get("currency_value"),
        "data": datetime.utcnow().isoformat()
    }

def registrar_evento(evento: Dict[str, Any]):
    try:
        supabase.table("eventos").insert(evento).execute()
        log("CORE", "INFO", "Evento salvo no Supabase")
    except Exception as e:
        log("CORE", "ERROR", f"Erro ao salvar evento: {e}")

def processar_evento(evento: Dict[str, Any]):
    log("CORE", "INFO", f"Processando evento {evento.get('evento')}")
    registrar_evento(evento)

# ============================================================
# SECURITY — HOTMART HMAC
# ============================================================

def validar_hotmart_hmac(raw_body: bytes, header_signature: str):
    if not HOTMART_HMAC_SECRET:
        log("SECURITY", "ERROR", "HOTMART_HMAC_SECRET não configurado")
        raise HTTPException(status_code=500, detail="HMAC secret not configured")

    # Hotmart envia no formato: sha256=HASH
    if header_signature.startswith("sha256="):
        header_signature = header_signature.replace("sha256=", "")

    expected = hmac.new(
        HOTMART_HMAC_SECRET.encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, header_signature):
        log("SECURITY", "ERROR", f"HMAC inválido. Esperado {expected} recebido {header_signature}")
        raise HTTPException(status_code=401, detail="Invalid HMAC")

# ============================================================
# ROUTES
# ============================================================

@app.get("/status")
def status():
    return {
        "app": APP_NAME,
        "env": ENV,
        "time": datetime.utcnow().isoformat(),
        "status": "ok"
    }

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    raw_body = await request.body()

    signature = request.headers.get("X-Hotmart-Hmac-SHA256")
    if not signature:
        log("HOTMART", "ERROR", "Header X-Hotmart-Hmac-SHA256 ausente")
        raise HTTPException(status_code=400, detail="Missing HMAC header")

    validar_hotmart_hmac(raw_body, signature)

    try:
        payload = json.loads(raw_body.decode())
    except Exception:
        log("HOTMART", "ERROR", "JSON inválido")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    log("HOTMART", "INFO", "Webhook recebido e validado")

    evento = normalizar_evento(payload)
    processar_evento(evento)

    return {"status": "received"}

# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {"system": APP_NAME, "status": "running"}
