# main.py — ROBO GLOBAL AI
# ARQUIVO ÚNICO • DEFINITIVO • PRODUÇÃO
# Inclui:
# - /status
# - /painel/operacional  (VISÃO HUMANA OBRIGATÓRIA)
# - Webhooks Hotmart + Eduzz (ingestão real mínima)
# - Persistência Supabase
# - Sem dashboards externos
# - Sem lógica paralela
# - Sem versões duplicadas

import os
import hmac
import hashlib
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

# =====================================================
# CONFIGURAÇÕES DE AMBIENTE
# =====================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET", "")
EDUZZ_WEBHOOK_SECRET = os.getenv("EDUZZ_WEBHOOK_SECRET", "")

CAPITAL_MAXIMO = float(os.getenv("CAPITAL_MAXIMO", "300"))
RISCO_MAXIMO = float(os.getenv("RISCO_MAXIMO", "40"))

AUTONOMIA_ATIVA = os.getenv("AUTONOMIA_ATIVA", "false").lower() == "true"
ESCALA_ATIVA = os.getenv("ESCALA_ATIVA", "false").lower() == "true"
KILL_SWITCH = os.getenv("KILL_SWITCH", "false").lower() == "true"

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórias")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# =====================================================
# APP
# =====================================================

app = FastAPI(title="Robo Global AI — Produção")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# UTILITÁRIOS
# =====================================================

def validar_hmac(secret: str, body: bytes, assinatura: str) -> bool:
    if not secret:
        return True
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, assinatura)

def contar(tabela: str) -> int:
    r = supabase.table(tabela).select("id", count="exact").execute()
    return r.count or 0

def soma(tabela: str, campo: str) -> float:
    r = supabase.table(tabela).select(campo).execute()
    return sum(x.get(campo) or 0 for x in r.data)

# =====================================================
# STATUS (CHECK BÁSICO)
# =====================================================

@app.get("/status")
def status():
    return {
        "robo": "Robo Global AI",
        "estado": "ativo",
        "painel": "operacional_humano",
        "timestamp": datetime.utcnow().isoformat()
    }

# =====================================================
# PAINEL OPERACIONAL HUMANO (OBRIGATÓRIO)
# =====================================================

@app.get("/painel/operacional")
def painel_operacional():
    eventos_brutos = contar("eventos_afiliados_brutos")
    eventos_normalizados = contar("eventos_afiliados_normalizados")
    decisoes = contar("eventos_decisoes_observacao")
    exec_auto = contar("eventos_execucoes_automaticas")
    exec_manual = contar("eventos_execucoes_manuais")

    capital_utilizado = soma("eventos_execucoes_automaticas", "valor")
    capital_disponivel = max(CAPITAL_MAXIMO - capital_utilizado, 0)

    estado = "OK"
    if KILL_SWITCH:
        estado = "PAUSADO"
    elif capital_disponivel <= 0:
        estado = "ALERTA"

    return {
        "estado_geral": estado,
        "ciclo": "OPERACIONAL_CONTINUO",
        "eventos": {
            "brutos": eventos_brutos,
            "normalizados": eventos_normalizados
        },
        "decisoes_registradas": decisoes,
        "execucoes": {
            "automaticas": exec_auto,
            "manuais": exec_manual
        },
        "capital": {
            "maximo": CAPITAL_MAXIMO,
            "utilizado": capital_utilizado,
            "disponivel": capital_disponivel
        },
        "travas": {
            "autonomia_ativa": AUTONOMIA_ATIVA,
            "escala_ativa": ESCALA_ATIVA,
            "kill_switch": KILL_SWITCH,
            "risco_maximo": RISCO_MAXIMO
        },
        "ultima_atualizacao": datetime.utcnow().isoformat()
    }

# =====================================================
# WEBHOOK HOTMART — INGESTÃO REAL MÍNIMA
# =====================================================

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    raw_body = await request.body()
    assinatura = request.headers.get("X-Hotmart-Hmac-SHA256", "")

    if not validar_hmac(HOTMART_WEBHOOK_SECRET, raw_body, assinatura):
        raise HTTPException(status_code=401, detail="Assinatura Hotmart inválida")

    payload = await request.json()

    supabase.table("eventos_afiliados_brutos").insert({
        "plataforma_origem": "hotmart",
        "payload_original": payload,
        "hash_evento": payload.get("event", f"hotmart_{datetime.utcnow().isoformat()}")
    }).execute()

    return {"status": "ok", "origem": "hotmart"}

# =====================================================
# WEBHOOK EDUZZ — INGESTÃO REAL MÍNIMA
# =====================================================

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    raw_body = await request.body()
    assinatura = request.headers.get("X-Eduzz-Signature", "")

    if not validar_hmac(EDUZZ_WEBHOOK_SECRET, raw_body, assinatura):
        raise HTTPException(status_code=401, detail="Assinatura Eduzz inválida")

    payload = await request.json()

    supabase.table("eventos_afiliados_brutos").insert({
        "plataforma_origem": "eduzz",
        "payload_original": payload,
        "hash_evento": payload.get("event", f"eduzz_{datetime.utcnow().isoformat()}")
    }).execute()

    return {"status": "ok", "origem": "eduzz"}
