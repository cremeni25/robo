# main.py — versão completa e final
# ROBO GLOBAL AI — C3 IMPLEMENTADO
# Estado calculado sob demanda (stateless)
# Métricas de capital e risco
# Endpoints de leitura + painel humano
# SEM decisão econômica • SEM ciclo automático

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date
import os
from supabase import create_client

# =====================================================
# APP
# =====================================================

app = FastAPI(title="ROBO GLOBAL AI", version="3.0")

# =====================================================
# CORS
# =====================================================

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

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def sb():
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# =====================================================
# LOG HUMANO
# =====================================================

def log_humano(origem, nivel, mensagem):
    print(f"[{origem}] [{nivel}] {mensagem}")

# =====================================================
# CONSTANTES DE RISCO (C1)
# =====================================================

CAPITAL_OPERACIONAL_PERC = 0.30
CAPITAL_PROTEGIDO_PERC = 0.70

RISCO_POR_CICLO_MAX = 0.05
RISCO_DIARIO_MAX = 0.10
RISCO_ACUMULADO_MAX = 0.20

# =====================================================
# FUNÇÕES BASE (LEITURA)
# =====================================================

def buscar_eventos():
    supabase = sb()
    res = (
        supabase.table("eventos_financeiros")
        .select("valor_unitario, created_at")
        .execute()
    )
    return res.data or []

# =====================================================
# MÉTRICAS DE CAPITAL
# =====================================================

def calcular_capital(eventos):
    capital_total = sum([(e.get("valor_unitario") or 0) for e in eventos])

    capital_protegido = capital_total * CAPITAL_PROTEGIDO_PERC
    capital_operacional_max = capital_total * CAPITAL_OPERACIONAL_PERC

    # Neste estágio não existe capital "em risco" real
    capital_operacional_disponivel = capital_operacional_max

    return {
        "capital_total": round(capital_total, 4),
        "capital_protegido": round(capital_protegido, 4),
        "capital_operacional_max": round(capital_operacional_max, 4),
        "capital_operacional_disponivel": round(capital_operacional_disponivel, 4),
    }

# =====================================================
# MÉTRICAS DE RISCO (ESTÁGIO ATUAL: SEM EXPOSIÇÃO)
# =====================================================

def calcular_risco(eventos, capital_total):
    if capital_total <= 0:
        return {
            "risco_por_ciclo": 0.0,
            "risco_diario": 0.0,
            "risco_acumulado": 0.0,
        }

    # Como ainda não há operações de risco,
    # todas as métricas permanecem em 0
    return {
        "risco_por_ciclo": 0.0,
        "risco_diario": 0.0,
        "risco_acumulado": 0.0,
    }

# =====================================================
# ESTADO DO ROBÔ (CALCULADO SOB DEMANDA)
# =====================================================

def calcular_estado_robo(capital, risco):
    estado_atual = "OBSERVACAO"
    pode_operar = False
    ciclos_negativos_consecutivos = 0

    if capital["capital_operacional_disponivel"] > 0 and risco["risco_diario"] < 0.05:
        estado_atual = "OPERACIONAL"
        pode_operar = True

    if risco["risco_acumulado"] >= RISCO_ACUMULADO_MAX:
        estado_atual = "PAUSADO"
        pode_operar = False

    return {
        "estado_atual": estado_atual,
        "pode_operar": pode_operar,
        "ciclos_negativos_consecutivos": ciclos_negativos_consecutivos,
    }

# =====================================================
# WEBHOOKS (MANTIDOS — REGISTRO APENAS)
# =====================================================

@app.post("/webhook/universal")
async def webhook_universal(request: Request):
    payload = await request.json()
    supabase = sb()
    supabase.table("eventos_financeiros").insert(payload).execute()
    log_humano("WEBHOOK", "INFO", "Evento universal registrado")
    return {"status": "ok"}

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    payload = await request.json()
    supabase = sb()
    supabase.table("eventos_financeiros").insert(payload).execute()
    log_humano("HOTMART", "INFO", "Evento Hotmart registrado")
    return {"status": "ok"}

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    payload = await request.json()
    supabase = sb()
    supabase.table("eventos_financeiros").insert(payload).execute()
    log_humano("EDUZZ", "INFO", "Evento Eduzz registrado")
    return {"status": "ok"}

# =====================================================
# ENDPOINTS BASE
# =====================================================

@app.get("/")
def root():
    return {"robo": "ROBO GLOBAL AI", "status": "online"}

@app.get("/status")
def status():
    return {"status": "ativo", "timestamp": datetime.utcnow().isoformat()}

# =====================================================
# C3 — ENDPOINTS DE LEITURA
# =====================================================

@app.get("/capital-detalhado")
def capital_detalhado():
    eventos = buscar_eventos()
    capital = calcular_capital(eventos)
    return capital

@app.get("/risco")
def risco():
    eventos = buscar_eventos()
    capital = calcular_capital(eventos)
    risco = calcular_risco(eventos, capital["capital_total"])

    return {
        "risco_por_ciclo": f"{round(risco['risco_por_ciclo'] * 100, 2)}%",
        "risco_diario": f"{round(risco['risco_diario'] * 100, 2)}%",
        "risco_acumulado": f"{round(risco['risco_acumulado'] * 100, 2)}%",
    }

@app.get("/estado")
def estado():
    eventos = buscar_eventos()
    capital = calcular_capital(eventos)
    risco = calcular_risco(eventos, capital["capital_total"])
    estado = calcular_estado_robo(capital, risco)

    return estado

@app.get("/controle")
def controle():
    eventos = buscar_eventos()
    capital = calcular_capital(eventos)
    risco = calcular_risco(eventos, capital["capital_total"])

    stop_geral = risco["risco_acumulado"] >= RISCO_ACUMULADO_MAX

    return {
        "stop_geral_acionado": stop_geral,
        "motivo": "Risco acumulado excedeu limite"
        if stop_geral
        else None,
    }

# =====================================================
# PAINEL HUMANO (CONSOLIDADO)
# =====================================================

@app.get("/painel/gestor")
def painel_gestor():
    eventos = buscar_eventos()
    capital = calcular_capital(eventos)
    risco = calcular_risco(eventos, capital["capital_total"])
    estado = calcular_estado_robo(capital, risco)

    return {
        "estado": {
            "estado_atual": estado["estado_atual"],
            "pode_operar": estado["pode_operar"],
            "ciclos_negativos_consecutivos": estado["ciclos_negativos_consecutivos"],
        },
        "capital": capital,
        "risco": {
            "risco_por_ciclo": f"{round(risco['risco_por_ciclo'] * 100, 2)}%",
            "risco_diario": f"{round(risco['risco_diario'] * 100, 2)}%",
            "risco_acumulado": f"{round(risco['risco_acumulado'] * 100, 2)}%",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
