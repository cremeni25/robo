# main.py — versão completa e final
# ROBO GLOBAL AI
# FASE 2 — ESTADO DECISÓRIO DISTRIBUÍDO (MULTI-INSTÂNCIA)
# Eventos ≠ Ações • Snapshot Imutável • Decisão Singular
# Logs humanos: [ORIGEM] [NÍVEL] mensagem

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
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
APP_VERSION = "2.0.0"
APP_PHASE = "ESTADO_DECISORIO_DISTRIBUIDO"

ENV = os.getenv("ENV", "production")
INSTANCE_ID = os.getenv("INSTANCE_ID", str(uuid.uuid4()))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET")
EDUZZ_WEBHOOK_SECRET = os.getenv("EDUZZ_WEBHOOK_SECRET")

LOCK_TTL_SECONDS = int(os.getenv("LOCK_TTL_SECONDS", "60"))
DECISION_BATCH_SIZE = int(os.getenv("DECISION_BATCH_SIZE", "10"))

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Supabase não configurado corretamente")

sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# =====================================================
# APP
# =====================================================

app = FastAPI(title=APP_NAME, version=APP_VERSION)

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

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def utc_now_iso() -> str:
    return utc_now().isoformat()

# =====================================================
# SEGURANÇA — HMAC
# =====================================================

def verify_hmac_sha256(payload: bytes, signature: str, secret: str) -> bool:
    if not secret:
        return False
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)

# =====================================================
# SNAPSHOTS — IDEMPOTÊNCIA
# =====================================================

def snapshot_exists(platform: str, external_event_id: str) -> bool:
    res = (
        sb.table("event_snapshots")
        .select("id")
        .eq("platform", platform)
        .eq("external_event_id", external_event_id)
        .limit(1)
        .execute()
    )
    return len(res.data) > 0

def persist_snapshot(snapshot: Dict[str, Any]):
    sb.table("event_snapshots").insert(snapshot).execute()
    log("SNAPSHOT", "INFO", f"Registrado {snapshot.get('platform')} | {snapshot.get('external_event_id')}")

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
# DECISION CURSOR
# =====================================================

def get_decision_cursor() -> Optional[str]:
    res = sb.table("decision_cursor").select("*").limit(1).execute()
    return res.data[0]["last_snapshot_id"] if res.data else None

def update_decision_cursor(snapshot_id: str):
    sb.table("decision_cursor").upsert(
        {"id": 1, "last_snapshot_id": snapshot_id, "updated_at": utc_now_iso()}
    ).execute()

# =====================================================
# LOCK DISTRIBUÍDO
# =====================================================

def acquire_lock(snapshot_id: str) -> bool:
    expires_at = utc_now() + timedelta(seconds=LOCK_TTL_SECONDS)
    try:
        sb.table("decision_locks").insert({
            "snapshot_id": snapshot_id,
            "instance_id": INSTANCE_ID,
            "locked_at": utc_now_iso(),
            "expires_at": expires_at.isoformat()
        }).execute()
        log("LOCK", "INFO", f"Lock adquirido para snapshot {snapshot_id}")
        return True
    except Exception:
        return False

def release_lock(snapshot_id: str):
    sb.table("decision_locks") \
      .delete() \
      .eq("snapshot_id", snapshot_id) \
      .eq("instance_id", INSTANCE_ID) \
      .execute()
    log("LOCK", "INFO", f"Lock liberado para snapshot {snapshot_id}")

def cleanup_expired_locks():
    sb.table("decision_locks") \
      .delete() \
      .lt("expires_at", utc_now_iso()) \
      .execute()

# =====================================================
# DECISÃO — REGISTRO IMUTÁVEL
# =====================================================

def record_decision(snapshot: Dict[str, Any], conclusion: Dict[str, Any]):
    decision = {
        "snapshot_id": snapshot["id"],
        "platform": snapshot["platform"],
        "canonical_event": snapshot["canonical_event"],
        "conclusion": conclusion,
        "instance_id": INSTANCE_ID,
        "created_at": utc_now_iso()
    }
    sb.table("decision_records").insert(decision).execute()
    log("DECISAO", "INFO", f"Decisão registrada para snapshot {snapshot['id']}")

# =====================================================
# ESTADO DECISÓRIO — LÓGICA PURA
# =====================================================

def estado_decisorio(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Função PURA, determinística.
    Nenhuma ação externa.
    """
    return {
        "avaliacao": "NEUTRA",
        "motivo": "Evento registrado sem impacto decisório nesta fase",
        "risco": "BAIXO"
    }

# =====================================================
# LOOP DISTRIBUÍDO DE DECISÃO
# =====================================================

def decisor_loop():
    while True:
        try:
            cleanup_expired_locks()

            cursor = get_decision_cursor()
            query = sb.table("event_snapshots").select("*").order("id").limit(DECISION_BATCH_SIZE)
            if cursor:
                query = query.gt("id", cursor)

            snapshots = query.execute().data or []

            for snap in snapshots:
                snapshot_id = snap["id"]

                if not acquire_lock(snapshot_id):
                    continue

                try:
                    decision = estado_decisorio(snap)
                    record_decision(snap, decision)
                    update_decision_cursor(snapshot_id)
                finally:
                    release_lock(snapshot_id)

        except Exception as e:
            log("DECISOR", "ERRO", f"Falha no loop decisório: {str(e)}")

        time.sleep(2)

# =====================================================
# START LOOP EM BACKGROUND
# =====================================================

threading.Thread(target=decisor_loop, daemon=True).start()

# =====================================================
# WEBHOOKS — HOTMART
# =====================================================

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Hotmart-Hmac-SHA256")

    if not signature or not verify_hmac_sha256(raw_body, signature, HOTMART_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = json.loads(raw_body.decode())
    external_id = payload.get("id")

    if not external_id:
        raise HTTPException(status_code=400, detail="Evento sem ID")

    if snapshot_exists("HOTMART", external_id):
        return {"status": "duplicado_ignorado"}

    persist_snapshot(normalize_hotmart(payload))
    return {"status": "evento_registrado"}

# =====================================================
# WEBHOOKS — EDUZZ
# =====================================================

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Eduzz-Signature")

    if not signature or not verify_hmac_sha256(raw_body, signature, EDUZZ_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = json.loads(raw_body.decode())
    external_id = payload.get("event_id")

    if not external_id:
        raise HTTPException(status_code=400, detail="Evento sem ID")

    if snapshot_exists("EDUZZ", external_id):
        return {"status": "duplicado_ignorado"}

    persist_snapshot(normalize_eduzz(payload))
    return {"status": "evento_registrado"}

# =====================================================
# STATUS / HEALTH
# =====================================================

@app.get("/status")
def status():
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "phase": APP_PHASE,
        "instance_id": INSTANCE_ID,
        "timestamp": utc_now_iso()
    }

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": utc_now_iso()}

# =====================================================
# BOOTSTRAP
# =====================================================

log("SYSTEM", "INFO", f"{APP_NAME} iniciado | fase {APP_PHASE} | instância {INSTANCE_ID}")
