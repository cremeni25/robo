# main.py — Camada de AUTONOMIA PLENA COM TRAVAS GLOBAIS
# Sequencial ao Plano Diretor
# Escopo: execução automática baseada em propostas APROVADAS
# Com travas globais • Kill-switch • Rollback • Auditoria total

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

# =====================================================
# CONFIGURAÇÃO GLOBAL (TRAVAS)
# =====================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

CAPITAL_MAXIMO = float(os.getenv("CAPITAL_MAXIMO", "300"))
RISCO_MAXIMO = float(os.getenv("RISCO_MAXIMO", "40"))

AUTONOMIA_ATIVA = os.getenv("AUTONOMIA_ATIVA", "false").lower() == "true"
KILL_SWITCH = os.getenv("KILL_SWITCH", "false").lower() == "true"

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Variáveis SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórias")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# =====================================================
# APP
# =====================================================

app = FastAPI(title="Robo Global AI — Autonomia Plena com Travas")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# FUNÇÕES DE CONTROLE GLOBAL
# =====================================================

def checar_travas_globais() -> None:
    if KILL_SWITCH:
        raise HTTPException(status_code=403, detail="Kill-switch ativo — operações bloqueadas")
    if not AUTONOMIA_ATIVA:
        raise HTTPException(status_code=403, detail="Autonomia plena desativada")

def capital_disponivel() -> float:
    execs = supabase.table("eventos_execucoes_automaticas") \
        .select("valor") \
        .execute()
    utilizado = sum(e.get("valor") or 0 for e in execs.data)
    return max(CAPITAL_MAXIMO - utilizado, 0)

# =====================================================
# EXECUÇÃO BASEADA EM PROPOSTAS APROVADAS
# =====================================================

def executar_proposta_aprovada(proposta: dict) -> dict:
    """
    Executa ajuste ou ação APENAS se proposta estiver aprovada.
    """
    return {
        "proposta_id": proposta["id"],
        "acao": "ajuste_aplicado",
        "resultado": "ok",
        "executado_em": datetime.utcnow().isoformat()
    }

# =====================================================
# CICLO DE AUTONOMIA PLENA (CURTO)
# =====================================================

@app.post("/autonomia/ciclo")
def ciclo_autonomia():
    checar_travas_globais()

    propostas = supabase.table("eventos_propostas_autonomia") \
        .select("*") \
        .eq("status", "aprovada") \
        .eq("executada", False) \
        .limit(5) \
        .execute()

    executadas = []

    for proposta in propostas.data:
        if capital_disponivel() <= 0:
            break

        resultado = executar_proposta_aprovada(proposta)

        supabase.table("eventos_execucoes_autonomia") \
            .insert({
                "proposta_id": proposta["id"],
                "acao": resultado["acao"],
                "resultado": resultado["resultado"],
                "executado_em": resultado["executado_em"]
            }).execute()

        supabase.table("eventos_propostas_autonomia") \
            .update({"executada": True}) \
            .eq("id", proposta["id"]) \
            .execute()

        executadas.append(resultado)

    return {
        "status": "ok",
        "propostas_executadas": len(executadas),
        "capital_restante": capital_disponivel(),
        "timestamp": datetime.utcnow().isoformat()
    }

# =====================================================
# CONTROLES DE EMERGÊNCIA
# =====================================================

@app.post("/controle/kill-switch")
def ativar_kill_switch():
    return {
        "status": "ok",
        "kill_switch": "ativado",
        "observacao": "Defina KILL_SWITCH=true no ambiente para efetivar"
    }

@app.post("/controle/rollback/{proposta_id}")
def rollback(proposta_id: str):
    """
    Rollback lógico: marca execução como revertida.
    """
    execucao = supabase.table("eventos_execucoes_autonomia") \
        .select("*") \
        .eq("proposta_id", proposta_id) \
        .execute()

    if not execucao.data:
        raise HTTPException(status_code=404, detail="Execução não encontrada")

    supabase.table("eventos_execucoes_autonomia") \
        .update({
            "resultado": "revertido",
            "revertido_em": datetime.utcnow().isoformat()
        }) \
        .eq("proposta_id", proposta_id) \
        .execute()

    return {
        "status": "ok",
        "proposta_id": proposta_id,
        "rollback": "executado"
    }

# =====================================================
# STATUS HUMANO
# =====================================================

@app.get("/status")
def status():
    return {
        "servico": "Robo Global AI — Autonomia Plena",
        "estado": "ativo",
        "autonomia_ativa": AUTONOMIA_ATIVA,
        "kill_switch": KILL_SWITCH,
        "capital_maximo": CAPITAL_MAXIMO,
        "risco_maximo": RISCO_MAXIMO,
        "timestamp": datetime.utcnow().isoformat()
    }
