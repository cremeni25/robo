# main.py — ROBO GLOBAL AI
# BLOCO A + BLOCO B — BACKEND + ACQUISITION ENGINE (META ADS)
# Versão: 1.1
# Data: 25/12/2025
# ARQUIVO COMPLETO PARA SUBSTITUIÇÃO TOTAL

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Dict

# ================================
# ESTADO GLOBAL DA FÁBRICA
# ================================

ENGINE_STATE: Dict[str, any] = {
    "status": "STOPPED",
    "started_at": None,
    "stopped_at": None,
    "capital_investido": 0.0,
    "receita_total": 0.0,
    "resultado_liquido": 0.0,
    "decisao_atual": "Fábrica inativa",
}

# ================================
# MODELOS
# ================================

class FinancialUpdate(BaseModel):
    investido: float = 0.0
    receita: float = 0.0

# ================================
# ENGINE NÚCLEO
# ================================

def start_engine():
    if ENGINE_STATE["status"] == "RUNNING":
        return ENGINE_STATE
    ENGINE_STATE["status"] = "RUNNING"
    ENGINE_STATE["started_at"] = datetime.now(timezone.utc)
    ENGINE_STATE["decisao_atual"] = "Fábrica ativada"
    return ENGINE_STATE


def stop_engine():
    if ENGINE_STATE["status"] == "STOPPED":
        return ENGINE_STATE
    ENGINE_STATE["status"] = "STOPPED"
    ENGINE_STATE["stopped_at"] = datetime.now(timezone.utc)
    ENGINE_STATE["decisao_atual"] = "Fábrica pausada"
    return ENGINE_STATE


def update_financials(investido: float, receita: float):
    ENGINE_STATE["capital_investido"] += investido
    ENGINE_STATE["receita_total"] += receita
    ENGINE_STATE["resultado_liquido"] = ENGINE_STATE["receita_total"] - ENGINE_STATE["capital_investido"]
    return ENGINE_STATE

# ================================
# APP FASTAPI
# ================================

app = FastAPI(title="Robo Global AI", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# ENDPOINTS BLOCO A
# ================================

@app.post("/engine/start")
def engine_start():
    return start_engine()

@app.post("/engine/stop")
def engine_stop():
    return stop_engine()

@app.get("/dashboard/state")
def dashboard_state():
    return ENGINE_STATE

@app.post("/engine/finance")
def engine_finance(update: FinancialUpdate):
    return update_financials(update.investido, update.receita)

@app.get("/status")
def status():
    return {"service": "Robo Global AI", "engine_status": ENGINE_STATE["status"]}

# ================================
# ENDPOINT BLOCO B — ACQUISITION META ADS
# ================================

@app.post("/engine/acquisition/start")
def start_acquisition():
    from acquisition_meta_ads import run_real_test
    return run_real_test()
