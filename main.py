# main.py — ROBO GLOBAL AI
# FASE 2A — EXECUÇÃO FINANCEIRA REAL (API + FEED)

import os
import time
import threading
from datetime import datetime, timezone
from typing import Optional, List

import requests
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

# =====================================================
# CONFIGURAÇÃO OBRIGATÓRIA
# =====================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not RAPIDAPI_KEY:
    raise RuntimeError("CONFIGURAÇÃO INCOMPLETA")

sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================
# APP
# =====================================================

app = FastAPI(title="ROBO GLOBAL AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# ESTADO GLOBAL DO ROBO
# =====================================================

ESTADO = {
    "status": "INICIALIZANDO",
    "ultimo_ciclo": None,
    "tarefas_avaliadas": 0,
    "tarefas_executadas": 0,
}

# =====================================================
# LOG
# =====================================================

def log(origem: str, nivel: str, mensagem: str):
    try:
        sb.table("logs").insert({
            "origem": origem,
            "nivel": nivel,
            "mensagem": mensagem,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }).execute()
    except Exception:
        pass

# =====================================================
# FONTE DE DADOS — RAPIDAPI / JSEARCH
# =====================================================

def buscar_oportunidades():
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    params = {
        "query": "software engineer",
        "page": "1",
        "num_pages": "1"
    }

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    oportunidades = []
    for item in data.get("data", []):
        oportunidades.append({
            "id_externo": item.get("job_id"),
            "titulo": item.get("job_title"),
            "empresa": item.get("employer_name"),
            "pais": item.get("job_country"),
            "categoria": item.get("job_employment_type"),
            "valor_estimado": item.get("job_salary_max") or 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    return oportunidades

# =====================================================
# LOOP AUTÔNOMO
# =====================================================

def loop_autonomo():
    global ESTADO
    log("LOOP", "INFO", "Loop autônomo iniciado")
    ESTADO["status"] = "OPERANDO"

    while True:
        try:
            oportunidades = buscar_oportunidades()
            ESTADO["tarefas_avaliadas"] += len(oportunidades)

            for op in oportunidades:
                sb.table("tarefas_recebidas").insert(op).execute()
                ESTADO["tarefas_executadas"] += 1

            ESTADO["ultimo_ciclo"] = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            ESTADO["status"] = "ERRO"
            log("LOOP", "ERRO", str(e))
        time.sleep(60)

# =====================================================
# ENDPOINT STATUS
# =====================================================

@app.get("/status")
def status():
    return ESTADO

# =====================================================
# API MONETIZADA — CONSUMO SOB DEMANDA
# =====================================================

@app.get("/api/oportunidades")
def api_oportunidades(
    authorization: Optional[str] = Header(None),
    limit: int = 50
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente")

    token = authorization.replace("Bearer ", "").strip()

    token_row = sb.table("api_tokens").select("*").eq("token", token).eq("ativo", True).single().execute().data
    if not token_row:
        raise HTTPException(status_code=403, detail="Token inválido")

    dados = sb.table("tarefas_recebidas").select("*").limit(limit).execute().data
    quantidade = len(dados)

    if quantidade > 0:
        valor_unitario = float(token_row["valor_unitario"])
        sb.table("eventos_financeiros").insert({
            "origem": "API",
            "token": token,
            "quantidade": quantidade,
            "valor_unitario": valor_unitario,
            "valor_total": quantidade * valor_unitario,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }).execute()

    return {
        "meta": {
            "quantidade": quantidade,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "dados": dados
    }

# =====================================================
# FEED MONETIZADO — CONSUMO PERIÓDICO
# =====================================================

@app.get("/feed/oportunidades/{feed_token}")
def feed_oportunidades(feed_token: str):
    token_row = sb.table("feed_tokens").select("*").eq("token", feed_token).eq("ativo", True).single().execute().data
    if not token_row:
        raise HTTPException(status_code=403, detail="Token inválido")

    ultimo = token_row.get("ultimo_consumo")
    query = sb.table("tarefas_recebidas").select("*")
    if ultimo:
        query = query.gt("timestamp", ultimo)

    dados = query.execute().data
    quantidade = len(dados)

    if quantidade > 0:
        valor_unitario = float(token_row["valor_unitario"])
        sb.table("eventos_financeiros").insert({
            "origem": "FEED",
            "token": feed_token,
            "quantidade": quantidade,
            "valor_unitario": valor_unitario,
            "valor_total": quantidade * valor_unitario,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }).execute()

        sb.table("feed_tokens").update({
            "ultimo_consumo": datetime.now(timezone.utc).isoformat()
        }).eq("token", feed_token).execute()

    return {
        "quantidade": quantidade,
        "dados": dados
    }

# =====================================================
# STARTUP
# =====================================================

@app.on_event("startup")
def startup():
    t = threading.Thread(target=loop_autonomo, daemon=True)
    t.start()
