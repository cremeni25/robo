# main.py — ROBO GLOBAL AI
# VERSÃO OPERACIONAL — PLATAFORMAS RESTAURADAS
# SUBSTITUIÇÃO INTEGRAL

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
EDUZZ_TOKEN = os.getenv("EDUZZ_TOKEN", "")
MONETIZZE_TOKEN = os.getenv("MONETIZZE_TOKEN", "")
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
# GO ROUTER — SEM BLOQUEIO
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
    try:
        res = supabase.table("offers").select("*").eq("slug", slug).limit(1).execute()
    except Exception as e:
        log("GO", "ERROR", f"Supabase error {e}")
        raise HTTPException(500, "Database error")

    if not res.data:
        log("GO", "ERROR", f"Slug not found: {slug}")
        raise HTTPException(404, "Offer not found")

    offer = res.data[0]

    if offer.get("status") != "active":
        raise HTTPException(403, "Offer not available")

    target_url = offer["hotmart_url"]

    click = {
        "slug": slug,
        "offer_id": offer["id"],
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "ts": datetime.utcnow().isoformat()
    }

    supabase.table("clicks").insert(click).execute()

    supabase.table("decisions").insert({
        "offer_id": offer["id"],
        "slug": slug,
        "decision": "REDIRECT",
        "target": target_url,
        "ts": datetime.utcnow().isoformat()
    }).execute()

    return RedirectResponse(url=target_url, status_code=302)

# ============================================================
# HOTMART
# ============================================================

def get_hotmart_signature(headers):
    return headers.get("X-Hotmart-Hmac-SHA256")

def validate_hotmart_hmac(raw_body: bytes, signature: str):
    if not signature:
        raise HTTPException(400, "Missing HMAC")

    expected = hmac.new(
        HOTMART_HMAC_SECRET.encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature.replace("sha256=", "")):
        raise HTTPException(401, "Invalid HMAC")

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    raw = await request.body()
    validate_hotmart_hmac(raw, get_hotmart_signature(request.headers))
    payload = json.loads(raw.decode())

    supabase.table("events").insert({
        "platform": "hotmart",
        "payload": payload,
        "ts": datetime.utcnow().isoformat()
    }).execute()

    return {"status": "ok"}

# ============================================================
# EDUZZ
# ============================================================

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    payload = await request.json()

    supabase.table("events").insert({
        "platform": "eduzz",
        "payload": payload,
        "ts": datetime.utcnow().isoformat()
    }).execute()

    return {"status": "ok"}

# ============================================================
# MONETIZZE
# ============================================================

@app.post("/webhook/monetizze")
async def webhook_monetizze(request: Request):
    payload = await request.json()

    supabase.table("events").insert({
        "platform": "monetizze",
        "payload": payload,
        "ts": datetime.utcnow().isoformat()
    }).execute()

    return {"status": "ok"}

# ============================================================
# CLICKBANK
# ============================================================

@app.post("/webhook/clickbank")
async def webhook_clickbank(request: Request):
    payload = await request.json()

    supabase.table("events").insert({
        "platform": "clickbank",
        "payload": payload,
        "ts": datetime.utcnow().isoformat()
    }).execute()

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
