# main.py — ROBO GLOBAL AI
# CÓDIGO-BASE COMPLETO • LOOP AUTÔNOMO • EXECUÇÃO EM RENDER

import os
import asyncio
import threading
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

# =====================================================
# CONFIGURAÇÕES BÁSICAS
# =====================================================

APP_NAME = "ROBO GLOBAL AI"
ENV = os.getenv("ENV", "production")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("SUPABASE NÃO CONFIGURADO")

sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# =====================================================
# FASTAPI
# =====================================================

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# ESTADO GLOBAL DO ROBÔ
# =====================================================

estado_global = {
    "status": "INICIALIZANDO",
    "capital": 0.0,
    "modo": "CONSERVADOR",
    "ultimo_ciclo": None,
}

# =====================================================
# UTILIDADES
# =====================================================

def log(origem: str, nivel: str, mensagem: str):
    texto = f"[{origem}] [{nivel}] {mensagem}"
    print(texto)
    sb.table("logs").insert({
        "origem": origem,
        "nivel": nivel,
        "mensagem": mensagem,
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

# =====================================================
# NORMALIZAÇÃO UNIVERSAL
# =====================================================

def normalizar_evento(payload: Dict[str, Any]) -> Dict[str, Any]:
    evento = {
        "plataforma": payload.get("plataforma", "desconhecida"),
        "produto": payload.get("produto"),
        "valor": float(payload.get("valor", 0)),
        "comissao": float(payload.get("comissao", 0)),
        "status": payload.get("status"),
        "timestamp": datetime.utcnow().isoformat()
    }
    return evento

# =====================================================
# REGISTROS
# =====================================================

def registrar_evento(evento: Dict[str, Any]):
    sb.table("eventos").insert(evento).execute()


def registrar_decisao(decisao: Dict[str, Any]):
    sb.table("decisoes").insert(decisao).execute()


def atualizar_capital(valor: float):
    estado_global["capital"] += valor
    sb.table("capital").insert({
        "valor": valor,
        "total": estado_global["capital"],
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

# =====================================================
# MOTOR DE DECISÃO ECONÔMICA
# =====================================================

def calcular_rentabilidade(evento: Dict[str, Any]) -> float:
    if evento["valor"] == 0:
        return 0.0
    return evento["comissao"] / evento["valor"]


def decidir_acao(evento: Dict[str, Any]) -> Dict[str, Any]:
    roi = calcular_rentabilidade(evento)

    if roi > 0.5:
        acao = "ESCALAR"
    elif roi > 0.2:
        acao = "MANTER"
    else:
        acao = "PAUSAR"

    decisao = {
        "produto": evento["produto"],
        "plataforma": evento["plataforma"],
        "acao": acao,
        "roi": roi,
        "timestamp": datetime.utcnow().isoformat()
    }
    return decisao

# =====================================================
# LOOP AUTÔNOMO
# =====================================================

async def loop_autonomo():
    log("LOOP", "INFO", "Loop autônomo iniciado")
    estado_global["status"] = "OPERANDO"

    while True:
        try:
            eventos = sb.table("eventos").select("*").order("timestamp", desc=True).limit(5).execute().data
            for evento in eventos:
                decisao = decidir_acao(evento)
                registrar_decisao(decisao)
            estado_global["ultimo_ciclo"] = datetime.utcnow().isoformat()
        except Exception as e:
            log("LOOP", "ERRO", str(e))
            estado_global["status"] = "ERRO"
        await asyncio.sleep(10)

# =====================================================
# BACKGROUND WORKER
# =====================================================

def iniciar_background():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(loop_autonomo())

threading.Thread(target=iniciar_background, daemon=True).start()

# =====================================================
# WEBHOOK UNIVERSAL
# =====================================================

@app.post("/webhook/universal")
async def webhook_universal(request: Request):
    payload = await request.json()
    evento = normalizar_evento(payload)
    registrar_evento(evento)
    atualizar_capital(evento["comissao"])
    return {"status": "EVENTO REGISTRADO"}

# =====================================================
# ENDPOINTS DE STATUS
# =====================================================

@app.get("/status")
async def status():
    return {
        "robo": APP_NAME,
        "estado": estado_global
    }

@app.get("/capital")
async def capital():
    return {
        "capital": estado_global["capital"]
    }

@app.get("/decisoes")
async def decisoes():
    dados = sb.table("decisoes").select("*").order("timestamp", desc=True).limit(20).execute().data
    return dados

# =====================================================
# FIM DO ARQUIVO
# =====================================================
