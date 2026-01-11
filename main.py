# main.py — versão final com GO ROUTER

import os
import hmac
import hashlib
import json
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from supabase import create_client, Client

# ============================================================
# CONFIG
# ============================================================

APP_NAME = "ROBO GLOBAL AI"
ENV = os.getenv("ENV", "prod")

HOTMART_HMAC_SECRET = os.getenv("HOTMART_HMAC_SECRET", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

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

def log(origin, level, msg):
    print(f"[{origin}] [{level}] {msg}")

# ============================================================
# GO ROUTER — CORE DE DINHEIRO
# ============================================================

@app.get("/go/{slug}")
def go_router(slug: str, request: Request):
    try:
        res = supabase.table("offers").select("*").eq("slug", slug).limit(1).execute()
    except Exception as e:
        log("GO", "ERROR", f"Supabase error {e}")
        raise HTTPException(500, "Database error")

    if not res.data:
        log("GO", "ERROR", f"Slug not found: {slug}")
        raise HTTPException(404, "Offer not found")

    offer = res.data[0]
    target_url = offer["hotmart_url"]

    click = {
        "slug": slug,
        "offer_id": offer["id"],
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "ts": datetime.utcnow().isoformat()
    }

    try:
        supabase.table("clicks").insert(click).execute()
        log("GO", "INFO", f"Click registrado {slug}")
    except Exception as e:
        log("GO", "ERROR", f"Erro ao salvar clique {e}")

    return RedirectResponse(url=target_url, status_code=302)

# ============================================================
# HOTMART HMAC
# ============================================================

def get_hotmart_signature(headers):
    return (
        headers.get("X-Hotmart-Hmac-SHA256")
        or headers.get("X-Hotmart-Hmac")
        or headers.get("X-Hotmart-Hmac-Signature")
    )

def validate_hotmart_hmac(raw_body, signature):
    if not signature:
        raise HTTPException(400, "Missing HMAC")

    if signature.startswith("sha256="):
        signature = signature.replace("sha256=", "")

    expected = hmac.new(
        HOTMART_HMAC_SECRET.encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(401, "Invalid HMAC")

# ============================================================
# WEBHOOK
# ============================================================

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    raw = await request.body()
    sig = get_hotmart_signature(request.headers)

    validate_hotmart_hmac(raw, sig)

    payload = json.loads(raw.decode())

    event = {
        "platform": "hotmart",
        "event": payload.get("event"),
        "email": payload.get("data", {}).get("buyer", {}).get("email"),
        "product": payload.get("data", {}).get("product", {}).get("name"),
        "value": payload.get("data", {}).get("purchase", {}).get("price", {}).get("value"),
        "currency": payload.get("data", {}).get("purchase", {}).get("price", {}).get("currency_value"),
        "ts": datetime.utcnow().isoformat()
    }

    supabase.table("events").insert(event).execute()
    log("HOTMART", "INFO", "Evento salvo")

    return {"status": "ok"}

# ============================================================
# STATUS
# ============================================================

@app.get("/status")
def status():
    return {"system": APP_NAME, "env": ENV, "status": "ok"}

# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {"system": APP_NAME, "running": True}
