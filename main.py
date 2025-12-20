# main.py — ROBO GLOBAL AI
# FASE 1 — REGISTRO FINANCEIRO MINIMO (AFILIADOS)
# 100% alinhado ao schema real da tabela eventos_financeiros

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from supabase import create_client, Client

app = FastAPI(title="Robo Global AI — Fase 1 FINAL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE não configurado")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def log_humano(origem, msg):
    print(f"[{origem}] {msg}")

def registrar_financeiro(registro: dict):
    resp = supabase.table("eventos_financeiros").insert(registro).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Falha ao registrar financeiro")
    return resp.data

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    payload = await request.json()

    try:
        valor_unitario = payload["purchase"]["price"]["value"]
        valor_total = payload["commission"]["value"]
    except KeyError:
        raise HTTPException(status_code=400, detail="Payload Hotmart inválido")

    registro = {
        "sim": "hotmart",
        "token": payload.get("event", "unknown"),
        "qtd": 1,
        "valor_unitario": valor_unitario,
        "valor_total": valor_total,
    }

    registrar_financeiro(registro)
    log_humano("HOTMART", f"REGISTRADO — comissão {valor_total}")

    return {"status": "ok"}

@app.get("/status")
def status():
    return {
        "robo": "Robo Global AI",
        "fase": "FASE 1 — REGISTRO FINANCEIRO",
        "status": "ativo",
        "timestamp": datetime.utcnow().isoformat(),
    }
