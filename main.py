# main.py — Camada de Execução CONTROLADA (Modo Manual)
# Sequencial ao Plano Diretor
# Escopo: executar ações somente sob comando humano explícito
# Sem autonomia • Sem escala • Com registro total

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

# =====================================================
# CONFIGURAÇÃO
# =====================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Variáveis SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórias")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# =====================================================
# APP
# =====================================================

app = FastAPI(title="Robo Global AI — Execução Controlada Manual")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# EXECUÇÃO CONTROLADA
# =====================================================

def executar_acao(decisao: dict) -> dict:
    """
    Execução manual controlada.
    Aqui a ação é apenas registrada (stub),
    sem integração externa automática.
    """
    return {
        "decisao_id": decisao["id"],
        "acao_executada": "registrada_manual",
        "resultado": "ok",
        "executado_em": datetime.utcnow().isoformat()
    }

# =====================================================
# ENDPOINT MANUAL DE EXECUÇÃO
# =====================================================

@app.post("/execucao/manual/{decisao_id}")
def executar_manual(decisao_id: str):
    # Buscar decisão
    decisao = supabase.table("eventos_decisoes_observacao") \
        .select("*") \
        .eq("id", decisao_id) \
        .execute()

    if not decisao.data:
        raise HTTPException(status_code=404, detail="Decisão não encontrada")

    decisao = decisao.data[0]

    # Executar ação (controlada)
    resultado = executar_acao(decisao)

    # Registrar execução
    supabase.table("eventos_execucoes_manuais").insert({
        "decisao_id": decisao_id,
        "acao": resultado["acao_executada"],
        "resultado": resultado["resultado"],
        "executado_em": resultado["executado_em"]
    }).execute()

    return {
        "status": "ok",
        "mensagem": "Ação executada manualmente",
        "resultado": resultado
    }

# =====================================================
# STATUS HUMANO
# =====================================================

@app.get("/status")
def status():
    return {
        "servico": "Robo Global AI — Execução Controlada",
        "estado": "ativo",
        "modo": "manual",
        "timestamp": datetime.utcnow().isoformat()
    }
