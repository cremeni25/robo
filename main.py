# main.py — ROBO GLOBAL AI (versão operacional final)
# Substituição integral do arquivo

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

def log(origin: str, level: str, msg: str):
    print(f"[{origin}] [{level}] {msg}")

# ============================================================
# SCORE (LEITURA FINAL)
# ============================================================

def obter_score_produto(id_produto: str) -> float:
    try:
        res = supabase.table("produto_score_atual") \
            .select("score") \
            .eq("id_produto", id_produto) \
            .limit(1) \
            .execute()
    except Exception as e:
        log("SCORE", "ERROR", f"Erro Supabase: {e}")
        return 0.0

    if not res.data:
        return 0.0

    return float(res.data[0]["score"])

# ============================================================
# GO ROUTER — CORE DE DINHEIRO
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

    status = offer.get("status", "active")
    if status != "active":
        log("GO", "INFO", f"Offer {slug} com status {status}")
        raise HTTPException(403, "Offer not available")

    score = obter_score_produto(offer["id"])
    if score < 50:
        log("GO", "INFO", f"Offer {slug} bloqueada por score {score}")
        raise HTTPException(403, "Offer blocked by performance")

    target_url = offer["hotmart_url"]

    click = {
        "slug": slug,
        "offer_id": offer["id"],
        "score": score,
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "ts": datetime.utcnow().isoformat()
    }

    try:
        supabase.table("clicks").insert(click).execute()
    except Exception as e:
        log("GO", "ERROR", f"Erro ao salvar clique {e}")

    decision = {
        "offer_id": offer["id"],
        "slug": slug,
        "decision": "REDIRECT",
        "target": target_url,
        "score": score,
        "ts": datetime.utcnow().isoformat()
    }

    try:
        supabase.table("decisions").insert(decision).execute()
    except Exception as e:
        log("GO", "ERROR", f"Erro ao salvar decisão {e}")

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

def validate_hotmart_hmac(raw_body: bytes, signature: str):
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
# WEBHOOK HOTMART
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
