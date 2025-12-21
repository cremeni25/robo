# main.py — versão completa e final
# ROBO GLOBAL AI — C3 + FASE B
# Estado sob demanda • Métricas • Decisão governada
# SEM execução • SEM ciclo automático

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from supabase import create_client

# =====================================================
# APP
# =====================================================

app = FastAPI(title="ROBO GLOBAL AI", version="3.1")

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
# CONSTANTES (C1)
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

    # Sem exposição real nesta fase
    capital_operacional_disponivel = capital_operacional_max

    return {
        "capital_total": round(capital_total, 4),
        "capital_protegido": round(capital_protegido, 4),
        "capital_operacional_max": round(capital_operacional_max, 4),
        "capital_operacional_disponivel": round(capital_operacional_disponivel, 4),
    }

# =====================================================
# MÉTRICAS DE RISCO (SEM EXPOSIÇÃO REAL)
# =====================================================

def calcular_risco(capital_total):
    if capital_total <= 0:
        return {
            "risco_por_ciclo": 0.0,
            "risco_diario": 0.0,
            "risco_acumulado": 0.0,
        }

    return {
        "risco_por_ciclo": 0.0,
        "risco_diario": 0.0,
        "risco_acumulado": 0.0,
    }

# =====================================================
# ESTADO DO ROBÔ (SOB DEMANDA)
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
# DECISÃO ECONÔMICA (FASE B — GOVERNADA)
# =====================================================

def calcular_decisao(estado, capital, risco):
    # BLOQUEADO
    if estado["estado_atual"] == "PAUSADO" or risco["risco_acumulado"] >= RISCO_ACUMULADO_MAX:
        return {
            "decisao": "BLOQUEADO",
            "motivo": "Risco acumulado atingiu o limite ou estado PAUSADO",
        }

    # AUTORIZADO
    if (
        estado["estado_atual"] == "OPERACIONAL"
        and estado["pode_operar"]
        and risco["risco_diario"] < 0.05
        and capital["capital_operacional_disponivel"] > 0
    ):
        return {
            "decisao": "AUTORIZADO",
            "motivo": "Estado OPERACIONAL, risco dentro do limite e capital disponível",
        }

    # AGUARDAR
    return {
        "decisao": "AGUARDAR",
        "motivo": "Estado ainda não permite operação segura",
    }

# =====================================================
# WEBHOOKS (MANTIDOS — REGISTRO APENAS)
# =====================================================

@app.post("/webhook/universal")
async def webhook_universal(request: Request):
    payload = await request.json()
    sb().table("eventos_financeiros").insert(payload).execute()
    log_humano("WEBHOOK", "INFO", "Evento universal registrado")
    return {"status": "ok"}

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    payload = await request.json()
    sb().table("eventos_financeiros").insert(payload).execute()
    log_humano("HOTMART", "INFO", "Evento Hotmart registrado")
    return {"status": "ok"}

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    payload = await request.json()
    sb().table("eventos_financeiros").insert(payload).execute()
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
    return calcular_capital(eventos)

@app.get("/risco")
def risco():
    eventos = buscar_eventos()
    capital = calcular_capital(eventos)
    r = calcular_risco(capital["capital_total"])
    return {
        "risco_por_ciclo": f"{round(r['risco_por_ciclo'] * 100, 2)}%",
        "risco_diario": f"{round(r['risco_diario'] * 100, 2)}%",
        "risco_acumulado": f"{round(r['risco_acumulado'] * 100, 2)}%",
    }

@app.get("/estado")
def estado():
    eventos = buscar_eventos()
    capital = calcular_capital(eventos)
    risco = calcular_risco(capital["capital_total"])
    return calcular_estado_robo(capital, risco)

@app.get("/controle")
def controle():
    eventos = buscar_eventos()
    capital = calcular_capital(eventos)
    risco = calcular_risco(capital["capital_total"])
    stop_geral = risco["risco_acumulado"] >= RISCO_ACUMULADO_MAX
    return {
        "stop_geral_acionado": stop_geral,
        "motivo": "Risco acumulado excedeu limite" if stop_geral else None,
    }

# =====================================================
# FASE B — ENDPOINT DE DECISÃO
# =====================================================

@app.get("/decisao")
def decisao():
    eventos = buscar_eventos()
    capital = calcular_capital(eventos)
    risco = calcular_risco(capital["capital_total"])
    estado = calcular_estado_robo(capital, risco)
    decisao = calcular_decisao(estado, capital, risco)

    return {
        "decisao": decisao["decisao"],
        "motivo": decisao["motivo"],
        "timestamp": datetime.utcnow().isoformat(),
    }

# =====================================================
# PAINEL GESTOR (ATUALIZADO COM DECISÃO)
# =====================================================

@app.get("/painel/gestor")
def painel_gestor():
    eventos = buscar_eventos()
    capital = calcular_capital(eventos)
    risco = calcular_risco(capital["capital_total"])
    estado = calcular_estado_robo(capital, risco)
    decisao = calcular_decisao(estado, capital, risco)

    return {
        "estado": estado,
        "capital": capital,
        "risco": {
            "risco_por_ciclo": f"{round(risco['risco_por_ciclo'] * 100, 2)}%",
            "risco_diario": f"{round(risco['risco_diario'] * 100, 2)}%",
            "risco_acumulado": f"{round(risco['risco_acumulado'] * 100, 2)}%",
        },
        "decisao": decisao,
        "timestamp": datetime.utcnow().isoformat(),
    }
