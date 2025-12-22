# main.py — Robô Global AI
# Versão com Fase 1.4 (Hipótese Inicial Controlada)
# Arquivo VITAL — substituição total obrigatória

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

from hypotheses import gerar_hipoteses

# =====================================================
# APP
# =====================================================

app = FastAPI(
    title="Robô Global AI",
    version="1.4.0",
    description="Motor de observabilidade, hipóteses e execução controlada"
)

# =====================================================
# CORS — Dashboard oficial (GitHub Pages)
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# ESTADO GLOBAL DO ROBÔ (CONTROLADO)
# =====================================================

ROBO_STATE = {
    "status": "ATIVO",
    "motivo": "Observabilidade ativa — hipóteses permitidas",
    "fase_atual": "1.4",
    "ultima_atualizacao": datetime.utcnow().isoformat()
}

# =====================================================
# ENDPOINT — STATUS EXECUTIVO (Dashboard)
# =====================================================

@app.get("/status")
def status_robo():
    return {
        "robo": ROBO_STATE,
        "timestamp": datetime.utcnow().isoformat()
    }

# =====================================================
# ENDPOINT — HIPÓTESES (FASE 1.4)
# =====================================================

@app.get("/hipoteses")
def listar_hipoteses():
    hipoteses = gerar_hipoteses()

    return {
        "fase": "1.4",
        "status": "HIPOTESES_GERADAS",
        "total": len(hipoteses),
        "hipoteses": hipoteses,
        "timestamp": datetime.utcnow().isoformat()
    }

# =====================================================
# ENDPOINT — EXECUTAR AUTOMAÇÃO (BLOQUEADO POR PROTOCOLO)
# =====================================================

@app.post("/executar")
def executar_automacao():
    return {
        "status": "BLOQUEADO",
        "motivo": "Nenhuma proposta executável aprovada",
        "timestamp": datetime.utcnow().isoformat()
    }

# =====================================================
# ENDPOINT — ROOT (SANIDADE)
# =====================================================

@app.get("/")
def root():
    return {
        "robo": "GLOBAL AI",
        "estado": ROBO_STATE["status"],
        "fase": ROBO_STATE["fase_atual"],
        "mensagem": "Sistema ativo — observabilidade e hipóteses habilitadas"
    }
