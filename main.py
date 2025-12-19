# main.py — versão completa e final
# ROBO GLOBAL AI — FASE 2A.3 (EVENTOS AUTÔNOMOS VIA RAPIDAPI)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import os
import requests
from supabase import create_client

# =====================================================
# APP
# =====================================================

app = FastAPI(title="ROBO GLOBAL AI", version="2.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# ENV
# =====================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # anon key (não service role)
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "jsearch.p.rapidapi.com")

CAPITAL_MAXIMO = float(os.getenv("CAPITAL_MAXIMO", "0"))
RISCO_MAX_CICLO = float(os.getenv("RISCO_MAX_CICLO", "0"))

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL ou SUPABASE_KEY não configurados")

if not RAPIDAPI_KEY:
    raise RuntimeError("RAPIDAPI_KEY não configurada")

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================
# HELPERS
# =====================================================

def agora_utc():
    return datetime.now(timezone.utc).isoformat()

def obter_resumo_financeiro():
    resp = sb.table("eventos_financeiros").select("*").execute()
    eventos = resp.data or []

    total = sum([float(e.get("valor_total", 0)) for e in eventos])
    quantidade = len(eventos)
    ultimo = eventos[-1] if eventos else None

    return total, quantidade, ultimo

def registrar_evento(valor_total, valor_unitario, token, eu_ia=True, sim=False):
    sb.table("eventos_financeiros").insert({
        "valor_total": valor_total,
        "valor_unitario": valor_unitario,
        "token": token,
        "eu_ia": eu_ia,
        "sim": sim,
        "criado_em": agora_utc()
    }).execute()

# =====================================================
# STATUS
# =====================================================

@app.get("/status")
def status():
    return {
        "app": "ROBO GLOBAL AI",
        "env": "production",
        "status": "online",
        "ts": agora_utc()
    }

# =====================================================
# FINANCEIRO HUMANO
# =====================================================

@app.get("/financeiro/resumo")
def financeiro_resumo():
    total, quantidade, ultimo = obter_resumo_financeiro()

    return {
        "total_recebido": round(total, 2),
        "quantidade_eventos": quantidade,
        "ultimo_evento": ultimo,
        "atualizado_em": agora_utc()
    }

# =====================================================
# FASE 2A.3 — ENDPOINT OPERACIONAL REAL
# =====================================================

@app.post("/ciclo/rapidapi")
def ciclo_rapidapi():
    total_atual, _, _ = obter_resumo_financeiro()

    # Verificação de capital
    if total_atual <= -CAPITAL_MAXIMO:
        raise HTTPException(
            status_code=403,
            detail="CAPITAL_MAXIMO atingido. Operação bloqueada."
        )

    # Custo máximo permitido neste ciclo
    custo_maximo = RISCO_MAX_CICLO

    # Configuração da chamada real (mínimo viável)
    url = "https://jsearch.p.rapidapi.com/search"
    querystring = {
        "query": "software engineer",
        "page": "1",
        "num_pages": "1"
    }

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    # Execução real
    response = requests.get(url, headers=headers, params=querystring, timeout=15)

    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Erro RapidAPI: {response.status_code}"
        )

    # Custo estimado conservador (proteção)
    custo_estimado = min(custo_maximo, 1.00) * -1

    registrar_evento(
        valor_total=custo_estimado,
        valor_unitario=custo_estimado,
        token="RAPIDAPI:JSEARCH",
        eu_ia=True,
        sim=False
    )

    return {
        "status": "executado",
        "origem": "RAPIDAPI:JSEARCH",
        "custo_registrado": custo_estimado,
        "capital_restante_estimado": round(total_atual + custo_estimado, 2),
        "ts": agora_utc()
    }

# =====================================================
# ROOT
# =====================================================

@app.get("/")
def root():
    return {
        "msg": "ROBO GLOBAL AI ATIVO",
        "fase": "2A.3 — EVENTOS AUTÔNOMOS VIA RAPIDAPI"
    }
