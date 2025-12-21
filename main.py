# main.py — Camada de VISUALIZAÇÃO OPERACIONAL HUMANA (MÍNIMA)
# Plano Diretor — requisito obrigatório
# Escopo: VISÃO REAL do estado do Robo para o humano
# Leitura direta • Linguagem humana • Sem logs técnicos • Sem gráficos

import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

# =====================================================
# CONFIGURAÇÃO
# =====================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

CAPITAL_MAXIMO = float(os.getenv("CAPITAL_MAXIMO", "300"))
RISCO_MAXIMO = float(os.getenv("RISCO_MAXIMO", "40"))
AUTONOMIA_ATIVA = os.getenv("AUTONOMIA_ATIVA", "false").lower() == "true"
ESCALA_ATIVA = os.getenv("ESCALA_ATIVA", "false").lower() == "true"
KILL_SWITCH = os.getenv("KILL_SWITCH", "false").lower() == "true"

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Variáveis SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórias")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# =====================================================
# APP
# =====================================================

app = FastAPI(title="Robo Global AI — Painel Operacional Humano")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# FUNÇÕES DE LEITURA HUMANA
# =====================================================

def contar(tabela: str) -> int:
    r = supabase.table(tabela).select("id", count="exact").execute()
    return r.count or 0

def soma(tabela: str, campo: str) -> float:
    r = supabase.table(tabela).select(campo).execute()
    return sum(x.get(campo) or 0 for x in r.data)

# =====================================================
# PAINEL OPERACIONAL — VISÃO GERAL
# =====================================================

@app.get("/painel/operacional")
def painel_operacional():
    eventos_brutos = contar("eventos_afiliados_brutos")
    eventos_normalizados = contar("eventos_afiliados_normalizados")
    decisoes = contar("eventos_decisoes_observacao")
    execucoes_auto = contar("eventos_execucoes_automaticas")
    execucoes_man = contar("eventos_execucoes_manuais")

    capital_utilizado = soma("eventos_execucoes_automaticas", "valor")
    capital_disponivel = max(CAPITAL_MAXIMO - capital_utilizado, 0)

    estado = "OK"
    if KILL_SWITCH:
        estado = "PAUSADO"
    elif capital_disponivel <= 0:
        estado = "ALERTA"

    return {
        "estado_geral": estado,
        "ciclo_atual": "OPERACIONAL CONTÍNUO",
        "eventos": {
            "brutos": eventos_brutos,
            "normalizados": eventos_normalizados
        },
        "decisoes_registradas": decisoes,
        "execucoes": {
            "automaticas": execucoes_auto,
            "manuais": execucoes_man
        },
        "capital": {
            "maximo": CAPITAL_MAXIMO,
            "utilizado": capital_utilizado,
            "disponivel": capital_disponivel
        },
        "travas": {
            "autonomia_ativa": AUTONOMIA_ATIVA,
            "escala_ativa": ESCALA_ATIVA,
            "kill_switch": KILL_SWITCH,
            "risco_maximo": RISCO_MAXIMO
        },
        "ultima_atualizacao": datetime.utcnow().isoformat()
    }

# =====================================================
# STATUS SIMPLES (CHECK RÁPIDO)
# =====================================================

@app.get("/status")
def status():
    return {
        "robo": "Robo Global AI",
        "estado": "ativo",
        "painel": "operacional_humano",
        "timestamp": datetime.utcnow().isoformat()
    }
