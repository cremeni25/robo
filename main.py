# main.py — ROBO GLOBAL AI
# OPERAÇÃO REAL • 24/7 • DECISÃO → CONFIRMAÇÃO → AÇÃO
# SEM SIMULAÇÃO • SEM LOGS • SEM ESPELHO

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from supabase import create_client
import os
import requests

# =====================================================
# APP
# =====================================================

app = FastAPI()

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

def sb():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise Exception("SUPABASE NÃO CONFIGURADO")
    return create_client(url, key)

# =====================================================
# LIMITES
# =====================================================

def limite_ok(valor):
    return isinstance(valor, (int, float)) and 0 < valor <= 5000

# =====================================================
# ESTADO
# =====================================================

def estado_atual():
    res = sb().table("estado_atual").select("*").eq("id", 1).execute()
    return res.data[0] if res.data else None


def bootstrap():
    estado = estado_atual()
    if estado:
        return estado

    ciclo = sb().table("ciclos").insert({
        "decisao": "BOOTSTRAP",
        "resultado": "INICIALIZADO",
        "capital_antes": 0,
        "capital_depois": 0,
        "status": "SUCESSO",
        "payload": {}
    }).execute()

    sb().table("estado_atual").insert({
        "id": 1,
        "fase": "OPERANDO",
        "capital": 0,
        "ultima_decisao": "BOOTSTRAP",
        "ultimo_ciclo_id": ciclo.data[0]["id"],
        "atualizado_em": datetime.utcnow().isoformat()
    }).execute()

    return estado_atual()

# =====================================================
# AÇÃO PENDENTE (ÚNICA)
# =====================================================

acao_pendente = {
    "tipo": None,
    "criada_em": None
}

# =====================================================
# ENDPOINTS BÁSICOS
# =====================================================

@app.get("/ping")
def ping():
    return {"ok": True}


@app.get("/estado")
def estado():
    return estado_atual() or {}


@app.get("/status")
def status():
    return estado()

# =====================================================
# CICLO AUTÔNOMO — DECIDE
# =====================================================

@app.post("/ciclo")
def ciclo():
    bootstrap()

    global acao_pendente
    acao_pendente = {
        "tipo": "PUBLICAR_E_ATIVAR_TRAFEGO",
        "criada_em": datetime.utcnow().isoformat()
    }

    return {
        "status": "acao_pendente",
        "acao": acao_pendente
    }

# =====================================================
# CONFIRMAÇÃO HUMANA — EXECUTA
# =====================================================

@app.post("/confirmar-acao")
def confirmar_acao():
    global acao_pendente

    if not acao_pendente["tipo"]:
        return {"status": "nenhuma_acao"}

    # ===== AÇÃO REAL A — PUBLICAÇÃO =====
    webhook_publicacao = os.getenv("WEBHOOK_PUBLICACAO_URL")
    if webhook_publicacao:
        requests.post(webhook_publicacao, json={
            "acao": "PUBLICAR_CONTEUDO",
            "origem": "ROBO_GLOBAL_AI",
            "timestamp": datetime.utcnow().isoformat()
        }, timeout=10)

    # ===== AÇÃO REAL B — TRÁFEGO =====
    webhook_trafego = os.getenv("WEBHOOK_TRAFEGO_URL")
    if webhook_trafego:
        requests.post(webhook_trafego, json={
            "acao": "ATIVAR_TRAFEGO",
            "orcamento_diario": 10,
            "origem": "ROBO_GLOBAL_AI",
            "timestamp": datetime.utcnow().isoformat()
        }, timeout=10)

    estado = estado_atual()
    capital_antes = estado["capital"]

    ciclo = sb().table("ciclos").insert({
        "decisao": acao_pendente["tipo"],
        "resultado": "EXECUTADO",
        "capital_antes": capital_antes,
        "capital_depois": capital_antes,
        "status": "SUCESSO",
        "payload": acao_pendente
    }).execute()

    sb().table("estado_atual").update({
        "ultima_decisao": acao_pendente["tipo"],
        "ultimo_ciclo_id": ciclo.data[0]["id"],
        "atualizado_em": datetime.utcnow().isoformat()
    }).eq("id", 1).execute()

    acao_pendente = {"tipo": None, "criada_em": None}

    return {"status": "acao_real_executada"}

# =====================================================
# WEBHOOK HOTMART
# =====================================================

@app.post("/webhook/hotmart")
def webhook_hotmart(payload: dict):
    valor = float(payload.get("purchase", {}).get("price", 0))
    if not limite_ok(valor):
        return {"ok": False}

    estado = estado_atual()
    antes = estado["capital"]
    depois = antes + valor

    ciclo = sb().table("ciclos").insert({
        "decisao": "VENDA_HOTMART",
        "resultado": "CONFIRMADA",
        "capital_antes": antes,
        "capital_depois": depois,
        "status": "SUCESSO",
        "payload": payload
    }).execute()

    sb().table("estado_atual").update({
        "capital": depois,
        "ultima_decisao": "VENDA_HOTMART",
        "ultimo_ciclo_id": ciclo.data[0]["id"],
        "atualizado_em": datetime.utcnow().isoformat()
    }).eq("id", 1).execute()

    return {"ok": True}

# =====================================================
# WEBHOOK EDUZZ
# =====================================================

@app.post("/webhook/eduzz")
def webhook_eduzz(payload: dict):
    valor = float(payload.get("transaction", {}).get("price", 0))
    if not limite_ok(valor):
        return {"ok": False}

    estado = estado_atual()
    antes = estado["capital"]
    depois = antes + valor

    ciclo = sb().table("ciclos").insert({
        "decisao": "VENDA_EDUZZ",
        "resultado": "CONFIRMADA",
        "capital_antes": antes,
        "capital_depois": depois,
        "status": "SUCESSO",
        "payload": payload
    }).execute()

    sb().table("estado_atual").update({
        "capital": depois,
        "ultima_decisao": "VENDA_EDUZZ",
        "ultimo_ciclo_id": ciclo.data[0]["id"],
        "atualizado_em": datetime.utcnow().isoformat()
    }).eq("id", 1).execute()

    return {"ok": True}
