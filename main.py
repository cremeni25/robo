# main.py — ROBO GLOBAL AI
# FASE 2.1 • FONTE ATIVA 3 • RAPIDAPI (JSEARCH)
# AGENTE ECONÔMICO AUTÔNOMO • LOOP ATIVO • RENDER

import os
import asyncio
import threading
import requests
from datetime import datetime
from typing import Dict, Any, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client

# =====================================================
# CONFIGURAÇÕES
# =====================================================

APP_NAME = "ROBO GLOBAL AI"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not RAPIDAPI_KEY:
    raise RuntimeError("CONFIGURAÇÃO INCOMPLETA")

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

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
# ESTADO GLOBAL
# =====================================================

estado = {
    "status": "INICIALIZANDO",
    "ultimo_ciclo": None,
    "tarefas_avaliadas": 0,
    "tarefas_executadas": 0,
}

# =====================================================
# LOG
# =====================================================

def log(origem: str, nivel: str, msg: str):
    print(f"[{origem}] [{nivel}] {msg}")
    sb.table("logs").insert({
        "origem": origem,
        "nivel": nivel,
        "mensagem": msg,
        "timestamp": datetime.utcnow().isoformat(),
    }).execute()

# =====================================================
# FONTE ATIVA — JSEARCH (RAPIDAPI)
# =====================================================

def buscar_tarefas_jsearch() -> List[Dict[str, Any]]:
    url = "https://jsearch.p.rapidapi.com/search"

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    params = {
        "query": "software automation remote",
        "page": "1",
        "num_pages": "1",
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)

    if response.status_code != 200:
        return []

    data = response.json().get("data", [])
    tarefas = []

    for item in data:
        tarefas.append({
            "id_externo": item.get("job_id"),
            "titulo": item.get("job_title"),
            "descricao": item.get("job_description"),
            "empresa": item.get("employer_name"),
            "valor_estimado": 1.0,
            "timestamp": datetime.utcnow().isoformat(),
        })

    return tarefas

# =====================================================
# MOTOR DE DECISÃO
# =====================================================

def decidir_execucao(tarefa: Dict[str, Any]) -> bool:
    return tarefa.get("valor_estimado", 0) > 0.5

# =====================================================
# EXECUTOR SEGURO
# =====================================================

def executar_tarefa(tarefa: Dict[str, Any]):
    sb.table("tarefas_executadas").insert({
        "id_externo": tarefa["id_externo"],
        "titulo": tarefa["titulo"],
        "empresa": tarefa["empresa"],
        "timestamp": datetime.utcnow().isoformat(),
    }).execute()

# =====================================================
# LOOP AUTÔNOMO ATIVO
# =====================================================

async def loop_ativo():
    log("LOOP", "INFO", "Loop ativo iniciado (JSearch)")
    estado["status"] = "OPERANDO"

    while True:
        try:
            tarefas = buscar_tarefas_jsearch()

            for tarefa in tarefas:
                estado["tarefas_avaliadas"] += 1
                sb.table("tarefas_recebidas").insert(tarefa).execute()

                if decidir_execucao(tarefa):
                    executar_tarefa(tarefa)
                    estado["tarefas_executadas"] += 1

            estado["ultimo_ciclo"] = datetime.utcnow().isoformat()

        except Exception as e:
            log("LOOP", "ERRO", str(e))
            estado["status"] = "ERRO"

        await asyncio.sleep(30)

# =====================================================
# STARTUP EVENT (RENDER SAFE)
# =====================================================

@app.on_event("startup")
async def startup():
    def runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(loop_ativo())

    threading.Thread(target=runner, daemon=True).start()

# =====================================================
# STATUS
# =====================================================

@app.get("/status")
def status():
    return estado

# =====================================================
# FIM DO ARQUIVO
# =====================================================
