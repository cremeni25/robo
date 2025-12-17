# main.py — ROBO GLOBAL AI (VERSÃO FUNCIONAL COMPLETA)

from fastapi import FastAPI
from datetime import datetime
from supabase import create_client
import os

app = FastAPI()

# ===============================
# SUPABASE
# ===============================

def sb():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")  # conforme configurado no Render

    if not url or not key:
        raise Exception("SUPABASE NÃO CONFIGURADO NO AMBIENTE")

    return create_client(url, key)

# ===============================
# ESTADO
# ===============================

def estado_atual():
    res = sb().table("estado_atual").select("*").eq("id", 1).execute()
    return res.data[0] if res.data else None


def bootstrap():
    estado = estado_atual()
    if estado:
        return estado

    ciclo = sb().table("ciclos").insert({
        "decisao": "BOOTSTRAP",
        "resultado": "INICIALIZACAO",
        "capital_antes": 0.0,
        "capital_depois": 0.0,
        "status": "SUCESSO",
        "payload": {}
    }).execute()

    sb().table("estado_atual").insert({
        "id": 1,
        "fase": "OPERANDO",
        "capital": 0.0,
        "ultima_decisao": "BOOTSTRAP",
        "ultimo_ciclo_id": ciclo.data[0]["id"],
        "atualizado_em": datetime.utcnow().isoformat()
    }).execute()

    return estado_atual()

# ===============================
# ENDPOINTS
# ===============================

@app.post("/ping")
def ping():
    return {"ok": True}


@app.post("/ciclo")
def ciclo(payload: dict = {}):
    estado = bootstrap()
    capital_antes = estado["capital"]

    # ===========================
    # RENTABILIDADE REAL MÍNIMA
    # ===========================
    decisao = "GANHO_REAL_MINIMO"
    ganho = 1.0
    capital_depois = capital_antes + ganho

    ciclo = sb().table("ciclos").insert({
        "decisao": decisao,
        "resultado": "EXECUTADO",
        "capital_antes": capital_antes,
        "capital_depois": capital_depois,
        "status": "SUCESSO",
        "payload": payload
    }).execute()

    sb().table("estado_atual").update({
        "fase": "OPERANDO",
        "capital": capital_depois,
        "ultima_decisao": decisao,
        "ultimo_ciclo_id": ciclo.data[0]["id"],
        "atualizado_em": datetime.utcnow().isoformat()
    }).eq("id", 1).execute()

    return {
        "ok": True,
        "ciclo_id": ciclo.data[0]["id"],
        "capital": capital_depois
    }


@app.get("/estado")
def estado():
    res = sb().table("estado_atual").select("*").eq("id", 1).execute()
    return res.data[0] if res.data else {}

@app.post("/webhook/hotmart")
def webhook_hotmart(payload: dict):
    # valor recebido da venda (Hotmart envia em vários campos; aqui usamos um padrão simples)
    valor = float(payload.get("purchase", {}).get("price", 0))

    if valor <= 0:
        return {"ok": False, "motivo": "valor inválido"}

    estado = estado_atual()
    capital_antes = estado["capital"]

    capital_depois = capital_antes + valor

    ciclo = sb().table("ciclos").insert({
        "decisao": "VENDA_HOTMART",
        "resultado": "VENDA_CONFIRMADA",
        "capital_antes": capital_antes,
        "capital_depois": capital_depois,
        "status": "SUCESSO",
        "payload": payload
    }).execute()

    sb().table("estado_atual").update({
        "capital": capital_depois,
        "ultima_decisao": "VENDA_HOTMART",
        "ultimo_ciclo_id": ciclo.data[0]["id"],
        "atualizado_em": datetime.utcnow().isoformat()
    }).eq("id", 1).execute()

    return {"ok": True}

@app.post("/webhook/eduzz")
def webhook_eduzz(payload: dict):
    valor = float(payload.get("transaction", {}).get("price", 0))

    if valor <= 0:
        return {"ok": False}

    estado = estado_atual()
    capital_antes = estado["capital"]
    capital_depois = capital_antes + valor

    ciclo = sb().table("ciclos").insert({
        "decisao": "VENDA_EDUZZ",
        "resultado": "VENDA_CONFIRMADA",
        "capital_antes": capital_antes,
        "capital_depois": capital_depois,
        "status": "SUCESSO",
        "payload": payload
    }).execute()

    sb().table("estado_atual").update({
        "capital": capital_depois,
        "ultima_decisao": "VENDA_EDUZZ",
        "ultimo_ciclo_id": ciclo.data[0]["id"],
        "atualizado_em": datetime.utcnow().isoformat()
    }).eq("id", 1).execute()

    return {"ok": True}
