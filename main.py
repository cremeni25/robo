# main.py — ROBO GLOBAL AI
# FASE 1 — WEBHOOKS + REGISTRO FINANCEIRO (AFILIADOS)
# PROPÓSITO ÚNICO: captar e registrar eventos reais de afiliados

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from supabase import create_client, Client

# =====================================================
# APP
# =====================================================

app = FastAPI(title="Robo Global AI — Fase 1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# SUPABASE
# =====================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE não configurado corretamente")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================
# UTILITÁRIOS
# =====================================================

def log_humano(origem: str, mensagem: str):
    print(f"[{origem.upper()}] {mensagem}")

def validar_campos(evento: dict, campos: list, origem: str):
    for campo in campos:
        if campo not in evento or evento[campo] in [None, ""]:
            log_humano(origem, f"ERRO — campo ausente: {campo}")
            raise HTTPException(status_code=400, detail=f"Campo ausente: {campo}")

def registrar_evento(evento: dict, origem: str):
    resposta = supabase.table("eventos_financeiros").insert(evento).execute()
    if not resposta.data:
        log_humano(origem, "ERRO — falha ao registrar evento no Supabase")
        raise HTTPException(status_code=500, detail="Falha ao registrar evento")
    log_humano(
        origem,
        f"EVENTO REGISTRADO — {evento['evento']} — {evento['valor_comissao']} {evento['moeda']}",
    )

# =====================================================
# NORMALIZAÇÃO
# =====================================================

def normalizar_evento(plataforma: str, payload: dict) -> dict:
    agora = datetime.utcnow().isoformat()

    if plataforma == "hotmart":
        return {
            "plataforma_origem": "hotmart",
            "evento": payload.get("event"),
            "produto_id": payload.get("product", {}).get("id"),
            "valor_bruto": payload.get("purchase", {}).get("price", {}).get("value"),
            "valor_comissao": payload.get("commission", {}).get("value"),
            "moeda": payload.get("purchase", {}).get("price", {}).get("currency"),
            "status_financeiro": payload.get("status"),
            "timestamp_evento": payload.get("purchase", {}).get("date") or agora,
            "payload_original": payload,
        }

    if plataforma == "eduzz":
        return {
            "plataforma_origem": "eduzz",
            "evento": payload.get("event"),
            "produto_id": payload.get("product_id"),
            "valor_bruto": payload.get("sale_amount"),
            "valor_comissao": payload.get("commission_amount"),
            "moeda": payload.get("currency", "BRL"),
            "status_financeiro": payload.get("sale_status"),
            "timestamp_evento": payload.get("created_at") or agora,
            "payload_original": payload,
        }

    if plataforma == "stripe":
        data = payload.get("data", {}).get("object", {})
        return {
            "plataforma_origem": "stripe",
            "evento": payload.get("type"),
            "produto_id": data.get("metadata", {}).get("product_id"),
            "valor_bruto": (data.get("amount", 0) or 0) / 100,
            "valor_comissao": float(data.get("metadata", {}).get("commission_amount") or 0),
            "moeda": data.get("currency", "").upper(),
            "status_financeiro": data.get("status"),
            "timestamp_evento": datetime.utcfromtimestamp(data.get("created", 0)).isoformat()
            if data.get("created")
            else agora,
            "payload_original": payload,
        }

    raise HTTPException(status_code=400, detail="Plataforma não suportada")

# =====================================================
# WEBHOOKS
# =====================================================

CAMPOS_OBRIGATORIOS = [
    "plataforma_origem",
    "evento",
    "produto_id",
    "valor_bruto",
    "valor_comissao",
    "moeda",
    "status_financeiro",
    "timestamp_evento",
    "payload_original",
]

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    payload = await request.json()
    evento = normalizar_evento("hotmart", payload)
    validar_campos(evento, CAMPOS_OBRIGATORIOS, "HOTMART")
    registrar_evento(evento, "HOTMART")
    return {"status": "ok"}

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    payload = await request.json()
    evento = normalizar_evento("eduzz", payload)
    validar_campos(evento, CAMPOS_OBRIGATORIOS, "EDUZZ")
    registrar_evento(evento, "EDUZZ")
    return {"status": "ok"}

@app.post("/webhook/stripe")
async def webhook_stripe(request: Request):
    payload = await request.json()
    evento = normalizar_evento("stripe", payload)
    validar_campos(evento, CAMPOS_OBRIGATORIOS, "STRIPE")
    registrar_evento(evento, "STRIPE")
    return {"status": "ok"}

# =====================================================
# STATUS
# =====================================================

@app.get("/status")
def status():
    return {
        "robo": "Robo Global AI",
        "fase": "FASE 1 — Webhooks + Registro",
        "status": "ativo",
        "timestamp": datetime.utcnow().isoformat(),
    }
