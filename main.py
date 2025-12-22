# main.py — versão completa e final
# ROBO GLOBAL AI
# Integração REAL Hotmart + Eduzz
# Estado Decisório Soberano • Eventos ≠ Ações • Snapshot Imutável
# Logs humanos no padrão: [ORIGEM] [NÍVEL] mensagem

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import os
import json
import hmac
import hashlib
import uuid
import threading
import time

from supabase import create_client, Client

# =====================================================
# CONFIGURAÇÃO BÁSICA
# =====================================================

APP_NAME = "ROBO GLOBAL AI"
APP_VERSION = "1.0.0"
APP_PHASE = "INTEGRACAO_REAL_HOTMART_EDUZZ"

ENV = os.getenv("ENV", "production")
INSTANCE_ID = os.getenv("INSTANCE_ID", str(uuid.uuid4()))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET")
EDUZZ_WEBHOOK_SECRET = os.getenv("EDUZZ_WEBHOOK_SECRET")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Supabase não configurado corretamente")

sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# =====================================================
# APP
# =====================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION
)

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
# LOGS HUMANOS
# =====================================================

def log(origem: str, nivel: str, mensagem: str):
    print(f"[{origem}] [{nivel}] {mensagem}")

# =====================================================
# UTILIDADES DE TEMPO
# =====================================================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# =====================================================
# SEGURANÇA — HMAC
# =====================================================

def verify_hmac_sha256(payload: bytes, signature: str, secret: str) -> bool:
    if not secret:
        return False
    digest = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(digest, signature)

# =====================================================
# SNAPSHOT — IDEMPOTÊNCIA
# =====================================================

def snapshot_exists(platform: str, external_event_id: str) -> bool:
    try:
        res = (
            sb.table("event_snapshots")
            .select("id")
            .eq("platform", platform)
            .eq("external_event_id", external_event_id)
            .limit(1)
            .execute()
        )
        return len(res.data) > 0
    except Exception as e:
        log("SNAPSHOT", "ERRO", f"Falha ao verificar duplicidade: {str(e)}")
        raise

def persist_snapshot(snapshot: Dict[str, Any]):
    try:
        sb.table("event_snapshots").insert(snapshot).execute()
        log("SNAPSHOT", "INFO", f"Snapshot registrado: {snapshot.get('platform')} | {snapshot.get('external_event_id')}")
    except Exception as e:
        log("SNAPSHOT", "ERRO", f"Falha ao persistir snapshot: {str(e)}")
        raise

# =====================================================
# NORMALIZAÇÃO CANÔNICA
# =====================================================

def normalize_hotmart(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "platform": "HOTMART",
        "external_event_id": payload.get("id"),
        "canonical_event": payload.get("event"),
        "value": payload.get("data", {}).get("purchase", {}).get("price", {}).get("value"),
        "currency": payload.get("data", {}).get("purchase", {}).get("price", {}).get("currency"),
        "product_id": payload.get("data", {}).get("product", {}).get("id"),
        "affiliate_id": payload.get("data", {}).get("affiliate", {}).get("affiliate_code"),
        "event_timestamp": payload.get("creation_date"),
        "received_at": utc_now_iso(),
        "status": "REGISTRADO",
        "raw_payload": payload
    }

def normalize_eduzz(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "platform": "EDUZZ",
        "external_event_id": payload.get("event_id"),
        "canonical_event": payload.get("event_type"),
        "value": payload.get("sale", {}).get("value"),
        "currency": payload.get("sale", {}).get("currency"),
        "product_id": payload.get("product", {}).get("id"),
        "affiliate_id": payload.get("affiliate", {}).get("id"),
        "event_timestamp": payload.get("event_date"),
        "received_at": utc_now_iso(),
        "status": "REGISTRADO",
        "raw_payload": payload
    }

# =====================================================
# ESTADO DECISÓRIO — CONSUMO PASSIVO
# =====================================================

def estado_decisorio_consumir(snapshot: Dict[str, Any]):
    """
    IMPORTANTE:
    - Não executa ações externas
    - Apenas atualiza estados internos ou métricas
    - Implementação mínima para integração
    """
    log("ESTADO_DECISORIO", "INFO",
        f"Snapshot consumido: {snapshot.get('platform')} | {snapshot.get('canonical_event')}")

# =====================================================
# PIPELINE DE CONSUMO ASSÍNCRONO (SIMPLIFICADO)
# =====================================================

def consumir_snapshot_async(snapshot: Dict[str, Any]):
    def task():
        try:
            estado_decisorio_consumir(snapshot)
        except Exception as e:
            log("ESTADO_DECISORIO", "ERRO", f"Falha no consumo: {str(e)}")
    threading.Thread(target=task, daemon=True).start()

# =====================================================
# WEBHOOK — HOTMART
# =====================================================

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Hotmart-Hmac-SHA256")

    if not signature:
        log("HOTMART", "ERRO", "Assinatura ausente")
        raise HTTPException(status_code=401, detail="Assinatura ausente")

    if not verify_hmac_sha256(raw_body, signature, HOTMART_WEBHOOK_SECRET):
        log("HOTMART", "ERRO", "Assinatura inválida")
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = json.loads(raw_body.decode())
    external_id = payload.get("id")

    if not external_id:
        log("HOTMART", "ERRO", "Evento sem ID externo")
        raise HTTPException(status_code=400, detail="Evento sem ID externo")

    if snapshot_exists("HOTMART", external_id):
        log("HOTMART", "INFO", f"Evento duplicado ignorado: {external_id}")
        return {"status": "duplicado_ignorado"}

    snapshot = normalize_hotmart(payload)
    persist_snapshot(snapshot)

    consumir_snapshot_async(snapshot)

    return {"status": "evento_registrado"}

# =====================================================
# WEBHOOK — EDUZZ
# =====================================================

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Eduzz-Signature")

    if not signature:
        log("EDUZZ", "ERRO", "Assinatura ausente")
        raise HTTPException(status_code=401, detail="Assinatura ausente")

    if not verify_hmac_sha256(raw_body, signature, EDUZZ_WEBHOOK_SECRET):
        log("EDUZZ", "ERRO", "Assinatura inválida")
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = json.loads(raw_body.decode())
    external_id = payload.get("event_id")

    if not external_id:
        log("EDUZZ", "ERRO", "Evento sem ID externo")
        raise HTTPException(status_code=400, detail="Evento sem ID externo")

    if snapshot_exists("EDUZZ", external_id):
        log("EDUZZ", "INFO", f"Evento duplicado ignorado: {external_id}")
        return {"status": "duplicado_ignorado"}

    snapshot = normalize_eduzz(payload)
    persist_snapshot(snapshot)

    consumir_snapshot_async(snapshot)

    return {"status": "evento_registrado"}

# =====================================================
# ENDPOINTS OPERACIONAIS EXISTENTES / BÁSICOS
# =====================================================

@app.get("/status")
def status():
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "phase": APP_PHASE,
        "environment": ENV,
        "instance_id": INSTANCE_ID,
        "timestamp": utc_now_iso()
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": utc_now_iso()
    }

# =====================================================
# READINESS / LIVENESS (RENDER)
# =====================================================

@app.get("/ready")
def ready():
    try:
        sb.table("event_snapshots").select("id").limit(1).execute()
        return {"ready": True}
    except Exception as e:
        log("SYSTEM", "ERRO", f"Readiness falhou: {str(e)}")
        raise HTTPException(status_code=503, detail="Not ready")

@app.get("/live")
def live():
    return {"live": True}

# =====================================================
# BOOTSTRAP LOG
# =====================================================

log("SYSTEM", "INFO", f"{APP_NAME} iniciado | versão {APP_VERSION} | instância {INSTANCE_ID}")
