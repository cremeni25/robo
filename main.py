# main.py — ROBO GLOBAL AI
# FASE 2A.4 — ATIVAÇÃO DE RECEITA REAL (A+B)
# API + FEED + BILLING AUTOMÁTICO

import os
import time
import threading
from datetime import datetime, timezone
from typing import Optional

import requests
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

# =====================================================
# CONFIGURAÇÃO
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

app = FastAPI(title="ROBO GLOBAL AI — Monetização Real")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# ESTADO GLOBAL
# =====================================================

ESTADO = {
    "status": "INICIALIZANDO",
    "ultimo_ciclo": None,
    "tarefas_avaliadas": 0,
    "tarefas_executadas": 0,
}

# =====================================================
# UTIL
# =====================================================

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def log(origem: str, nivel: str, mensagem: str):
    try:
        sb.table("logs").insert({
            "origem": origem,
            "nivel": nivel,
            "mensagem": mensagem,
            "timestamp": now_iso()
        }).execute()
    except Exception:
        pass

# =====================================================
# FONTE — RAPIDAPI / JSEARCH
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

    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    ops = []
    for item in data.get("data", []):
        ops.append({
            "id_externo": item.get("job_id"),
            "titulo": item.get("job_title"),
            "empresa": item.get("employer_name"),
            "descricao": item.get("job_description"),
            "valor_estimado": item.get("job_salary_max") or 0,
            "timestamp": now_iso()
        })
    return ops

# =====================================================
# LOOP AUTÔNOMO
# =====================================================

def loop_autonomo():
    global ESTADO
    log("LOOP", "INFO", "Loop autônomo iniciado")
    ESTADO["status"] = "OPERANDO"

    while True:
        try:
            ops = buscar_oportunidades()
            ESTADO["tarefas_avaliadas"] += len(ops)

            for op in ops:
                sb.table("tarefas_recebidas").insert(op).execute()
                ESTADO["tarefas_executadas"] += 1

            ESTADO["ultimo_ciclo"] = now_iso()
        except Exception as e:
            ESTADO["status"] = "ERRO"
            log("LOOP", "ERRO", str(e))

        time.sleep(60)

# =====================================================
# STATUS
# =====================================================

@app.get("/status")
def status():
    return ESTADO

# =====================================================
# BILLING — ASSINATURA + PAY PER DATA
# =====================================================

def registrar_evento_financeiro(origem: str, token: str, quantidade: int, valor_unitario: float):
    if quantidade <= 0:
        return
    sb.table("eventos_financeiros").insert({
        "origem": origem,
        "token": token,
        "quantidade": quantidade,
        "valor_unitario": valor_unitario,
        "valor_total": quantidade * valor_unitario,
        "timestamp": now_iso()
    }).execute()

# =====================================================
# API PRIVADA — MONETIZAÇÃO
# =====================================================

@app.get("/api/oportunidades")
def api_oportunidades(
    authorization: Optional[str] = Header(None),
    limit: int = 50
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente")

    token = authorization.replace("Bearer ", "").strip()

    tok = sb.table("api_tokens").select("*").eq("token", token).eq("ativo", True).single().execute().data
    if not tok:
        raise HTTPException(status_code=403, detail="Token inválido")

    dados = sb.table("tarefas_recebidas").select("*").limit(limit).execute().data
    qtd = len(dados)

    registrar_evento_financeiro(
        origem="API",
        token=token,
        quantidade=qtd,
        valor_unitario=float(tok["valor_unitario"])
    )

    return {
        "meta": {"quantidade": qtd, "timestamp": now_iso()},
        "dados": dados
    }

# =====================================================
# FEED — MONETIZAÇÃO
# =====================================================

@app.get("/feed/oportunidades/{feed_token}")
def feed_oportunidades(feed_token: str):
    tok = sb.table("feed_tokens").select("*").eq("token", feed_token).eq("ativo", True).single().execute().data
    if not tok:
        raise HTTPException(status_code=403, detail="Token inválido")

    ultimo = tok.get("ultimo_consumo")
    q = sb.table("tarefas_recebidas").select("*")
    if ultimo:
        q = q.gt("timestamp", ultimo)

    dados = q.execute().data
    qtd = len(dados)

    registrar_evento_financeiro(
        origem="FEED",
        token=feed_token,
        quantidade=qtd,
        valor_unitario=float(tok["valor_unitario"])
    )

    sb.table("feed_tokens").update({"ultimo_consumo": now_iso()}).eq("token", feed_token).execute()

    return {"quantidade": qtd, "dados": dados}

# =====================================================
# BILLING STATUS (VISÃO HUMANA)
# =====================================================

@app.get("/billing/status")
def billing_status():
    eventos = sb.table("eventos_financeiros").select("*").execute().data
    total = sum(float(e["valor_total"]) for e in eventos)
    return {
        "eventos": len(eventos),
        "receita_total": total,
        "timestamp": now_iso()
    }

# =====================================================
# STARTUP
# =====================================================

@app.on_event("startup")
def startup():
    t = threading.Thread(target=loop_autonomo, daemon=True)
    t.start()
