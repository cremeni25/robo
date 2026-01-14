# main.py — ROBO GLOBAL AI
# ARQUITETURA FINAL — WEBHOOKS DINÂMICOS
# SUBSTITUIÇÃO INTEGRAL
# ➜ NUNCA MAIS REFAZER main.py PARA NOVA PLATAFORMA

import os
import hmac
import hashlib
import json
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from supabase import create_client, Client

# ============================================================
# CONFIG
# ============================================================

APP_NAME = "ROBO GLOBAL AI"
ENV = os.getenv("ENV", "prod")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

HOTMART_HMAC_SECRET = os.getenv("HOTMART_HMAC_SECRET", "")
CLICKBANK_SECRET = os.getenv("CLICKBANK_SECRET", "")

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
# LOG
# ============================================================

def log(origin: str, level: str, msg: str):
    print(f"[{origin}] [{level}] {msg}")

# ============================================================
# GO ROUTER (INALTERADO)
# ============================================================

@app.get("/go/{slug}")
def go_router(slug: str, request: Request):
    return executar_go(slug, request)


@app.get("/go")
def go_router_query(produto: str = Query(None), request: Request = None):
    if not produto:
        raise HTTPException(400, "Produto ausente")
    return executar_go(produto, request)


def executar_go(slug: str, request: Request):
    res = supabase.table("offers").select("*").eq("slug", slug).limit(1).execute()
    if not res.data:
        raise HTTPException(404, "Offer not found")

    offer = res.data[0]
    if offer.get("status") != "active":
        raise HTTPException(403, "Offer not available")

    supabase.table("clicks").insert({
        "slug": slug,
        "offer_id": offer["id"],
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "ts": datetime.utcnow().isoformat()
    }).execute()

    supabase.table("decisions").insert({
        "offer_id": offer["id"],
        "slug": slug,
        "decision": "REDIRECT",
        "target": offer["hotmart_url"],
        "ts": datetime.utcnow().isoformat()
    }).execute()

    return RedirectResponse(url=offer["hotmart_url"], status_code=302)

# ============================================================
# HMAC HOTMART (OPCIONAL)
# ============================================================

def validate_hotmart(raw: bytes, headers: Dict[str, Any]):
    sig = headers.get("X-Hotmart-Hmac-SHA256")
    if not sig:
        return True

    expected = hmac.new(
        HOTMART_HMAC_SECRET.encode(),
        raw,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, sig.replace("sha256=", ""))

# ============================================================
# WEBHOOK UNIVERSAL (CHAVE DA SOLUÇÃO)
# ============================================================

@app.post("/webhook/{platform}")
async def webhook_universal(platform: str, request: Request):
    raw = await request.body()

    # validações específicas (se existirem)
    if platform == "hotmart":
        if not validate_hotmart(raw, request.headers):
            raise HTTPException(401, "Invalid HMAC")

    payload = json.loads(raw.decode())

    supabase.table("events").insert({
        "platform": platform,
        "payload": payload,
        "headers": dict(request.headers),
        "ts": datetime.utcnow().isoformat()
    }).execute()

    log("WEBHOOK", "INFO", f"Evento recebido: {platform}")

    return {"status": "ok"}

# ============================================================
# STATUS
# ============================================================

@app.get("/status")
def status():
    return {
        "system": APP_NAME,
        "env": ENV,
        "status": "ok"
    }

# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "system": APP_NAME,
        "running": True
    }
