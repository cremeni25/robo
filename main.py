# main.py — ROBO GLOBAL AI
# BLOCO A — BACKEND DA FÁBRICA DE MONETIZAÇÃO
# Versão: 1.0
# Data: 25/12/2025
# Arquivo COMPLETO para SUBSTITUIÇÃO TOTAL

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Dict

# ================================
# ESTADO GLOBAL DA FÁBRICA
# ================================

ENGINE_STATE: Dict[str, any] = {
    "status": "STOPPED",  # RUNNING | STOPPED
    "started_at": None,
    "stopped_at": None,
    "capital_investido": 0.0,
    "receita_total": 0.0,
    "resultado_liquido": 0.0,
    "decisao_atual": "Fábrica inativa",
}

# ================================
# MODELOS DE DADOS
# ================================

class FinancialUpdate(BaseModel):
    investido: float = 0.0
    receita: float = 0.0

# ================================
# FUNÇÕES NÚCLEO DA ENGINE
# ================================

def start_engine():
    if ENGINE_STATE["status"] == "RUNNING":
        return ENGINE_STATE

    ENGINE_STATE["status"] = "RUNNING"
    ENGINE_STATE["started_at"] = datetime.now(timezone.utc)
    ENGINE_STATE["decisao_atual"] = (
        "Fábrica ativada. Aquisição e monetização em execução."
    )
    return ENGINE_STATE


def stop_engine():
    if ENGINE_STATE["status"] == "STOPPED":
        return ENGINE_STATE

    ENGINE_STATE["status"] = "STOPPED"
    ENGINE_STATE["stopped_at"] = datetime.now(timezone.utc)
    ENGINE_STATE["decisao_atual"] = (
        "Fábrica pausada. Nenhum tráfego ativo."
    )
    return ENGINE_STATE


def update_financials(investido: float, receita: float):
    ENGINE_STATE["capital_investido"] += float(investido)
    ENGINE_STATE["receita_total"] += float(receita)
    ENGINE_STATE["resultado_liquido"] = (
        ENGINE_STATE["receita_total"] - ENGINE_STATE["capital_investido"]
    )

    if ENGINE_STATE["resultado_liquido"] > 0:
        ENGINE_STATE["decisao_atual"] = "Operação positiva. Escala permitida."
    else:
        ENGINE_STATE["decisao_atual"] = "Operação negativa. Atenção ou ajuste."

    return ENGINE_STATE


def get_engine_state():
    return ENGINE_STATE

# ================================
# APLICAÇÃO FASTAPI
# ================================

app = FastAPI(
    title="Robo Global AI — Fábrica de Monetização",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)

# ================================
# ENDPOINTS DE VIDA DA FÁBRICA
# ================================

@app.post("/engine/start")
def engine_start():
    state = start_engine()
    return {"status": "OK", "engine": state}


@app.post("/engine/stop")
def engine_stop():
    state = stop_engine()
    return {"status": "OK", "engine": state}


@app.get("/dashboard/state")
def dashboard_state():
    return get_engine_state()

# ================================
# ENDPOINT FINANCEIRO (INTERNO)
# ================================

@app.post("/engine/finance")
def engine_finance(update: FinancialUpdate):
    state = update_financials(update.investido, update.receita)
    return {"status": "OK", "engine": state}

# ================================
# HEALTHCHECK
# ================================

@app.get("/status")
def status():
    return {
        "service": "Robo Global AI",
        "engine_status": ENGINE_STATE["status"],
    }

from acquisition_meta_ads import run_real_test

@app.post("/engine/acquisition/start")
def start_acquisition():
    return run_real_test()
