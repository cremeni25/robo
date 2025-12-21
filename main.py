# main.py — versão completa e final
# ROBO GLOBAL AI
# Núcleo + C3 (estado sob demanda) + Fase B (decisão governada)
# + E2 (propostas de ação com confirmação humana)
# SEM execução externa • SEM automação • SEM ciclos

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date
import os
import uuid
from supabase import create_client

# =====================================================
# APP
# =====================================================

app = FastAPI(title="ROBO GLOBAL AI", version="3.2")

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
    res = sb().table("eventos_financeiros").select("valor_unitario, created_at").execute()
    return res.data or []

# =====================================================
# MÉTRICAS DE CAPITAL
# =====================================================

def calcular_capital(eventos):
    capital_total = sum([(e.get("valor_unitario") or 0) for e in eventos])
    return {
        "capital_total": round(capital_total, 4),
        "capital_protegido": round(capital_total * CAPITAL_PROTEGIDO_PERC, 4),
        "capital_operacional_max": round(capital_total * CAPITAL_OPERACIONAL_PERC, 4),
        "capital_operacional_disponivel": round(capital_total * CAPITAL_OPERACIONAL_PERC, 4),
    }

# =====================================================
# MÉTRICAS DE RISCO (SEM EXPOSIÇÃO REAL)
# =====================================================

def calcular_risco(capital_total):
    if capital_total <= 0:
        return {"risco_por_ciclo": 0.0, "risco_diario": 0.0, "risco_acumulado": 0.0}
    return {"risco_por_ciclo": 0.0, "risco_diario": 0.0, "risco_acumulado": 0.0}

# =====================================================
# ESTADO DO ROBÔ
# =====================================================

def calcular_estado_robo(capital, risco):
    estado = "OBSERVACAO"
    pode_operar = False
    if capital["capital_operacional_disponivel"] > 0 and risco["risco_diario"] < 0.05:
        estado = "OPERACIONAL"
        pode_operar = True
    if risco["risco_acumulado"] >= RISCO_ACUMULADO_MAX:
        estado = "PAUSADO"
        pode_operar = False
    return {
        "estado_atual": estado,
        "pode_operar": pode_operar,
        "ciclos_negativos_consecutivos": 0,
    }

# =====================================================
# DECISÃO GOVERNADA (FASE B)
# =====================================================

def calcular_decisao(estado, capital, risco):
    if estado["estado_atual"] == "PAUSADO" or risco["risco_acumulado"] >= RISCO_ACUMULADO_MAX:
        return {"decisao": "BLOQUEADO", "motivo": "Estado PAUSADO ou risco acumulado excedido"}
    if estado["estado_atual"] == "OPERACIONAL" and estado["pode_operar"] and capital["capital_operacional_disponivel"] > 0:
        return {"decisao": "AUTORIZADO", "motivo": "Estado OPERACIONAL e capital disponível"}
    return {"decisao": "AGUARDAR", "motivo": "Condições ainda não atendidas"}

# =====================================================
# E2 — PROPOSTAS (MECANISMO INTERNO)
# =====================================================

def criar_proposta_se_permitido():
    eventos = buscar_eventos()
    capital = calcular_capital(eventos)
    risco = calcular_risco(capital["capital_total"])
    estado = calcular_estado_robo(capital, risco)
    decisao = calcular_decisao(estado, capital, risco)

    if decisao["decisao"] != "AUTORIZADO":
        return None

    hoje = date.today().isoformat()
    existentes = (
        sb()
        .table("propostas")
        .select("id")
        .eq("plataforma", "TikTok")
        .eq("data", hoje)
        .eq("status", "AGUARDANDO_CONFIRMACAO")
        .execute()
    )

    if existentes.data:
        return None

    proposta = {
        "id": str(uuid.uuid4()),
        "status": "AGUARDANDO_CONFIRMACAO",
        "plataforma": "TikTok",
        "tipo_conteudo": "Video curto",
        "tema": "Curiosidade / dor simples",
        "produto": "Produto afiliado X",
        "cta": "Link na bio",
        "quantidade": 1,
        "risco_estimado": "BAIXO",
        "decisao_atual": decisao["decisao"],
        "data": hoje,
        "criada_em": datetime.utcnow().isoformat(),
    }

    sb().table("propostas").insert(proposta).execute()
    log_humano("E2", "INFO", "Proposta criada e aguardando confirmação humana")
    return proposta

# =====================================================
# WEBHOOKS (REGISTRO APENAS)
# =====================================================

@app.post("/webhook/universal")
async def webhook_universal(request: Request):
    payload = await request.json()
    sb().table("eventos_financeiros").insert(payload).execute()
    return {"status": "ok"}

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    payload = await request.json()
    sb().table("eventos_financeiros").insert(payload).execute()
    return {"status": "ok"}

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    payload = await request.json()
    sb().table("eventos_financeiros").insert(payload).execute()
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
# C3 — LEITURA
# =====================================================

@app.get("/estado")
def estado():
    eventos = buscar_eventos()
    capital = calcular_capital(eventos)
    risco = calcular_risco(capital["capital_total"])
    return calcular_estado_robo(capital, risco)

@app.get("/capital-detalhado")
def capital_detalhado():
    return calcular_capital(buscar_eventos())

@app.get("/risco")
def risco():
    capital = calcular_capital(buscar_eventos())
    r = calcular_risco(capital["capital_total"])
    return {
        "risco_por_ciclo": f"{r['risco_por_ciclo']*100:.2f}%",
        "risco_diario": f"{r['risco_diario']*100:.2f}%",
        "risco_acumulado": f"{r['risco_acumulado']*100:.2f}%",
    }

@app.get("/decisao")
def decisao():
    eventos = buscar_eventos()
    capital = calcular_capital(eventos)
    risco = calcular_risco(capital["capital_total"])
    estado = calcular_estado_robo(capital, risco)
    d = calcular_decisao(estado, capital, risco)
    return {**d, "timestamp": datetime.utcnow().isoformat()}

# =====================================================
# E2 — ENDPOINTS DE PROPOSTAS
# =====================================================

@app.get("/propostas")
def listar_propostas():
    return sb().table("propostas").select("*").order("criada_em", desc=True).execute().data or []

@app.get("/proposta-atual")
def proposta_atual():
    criar_proposta_se_permitido()
    res = (
        sb()
        .table("propostas")
        .select("*")
        .eq("status", "AGUARDANDO_CONFIRMACAO")
        .order("criada_em", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else {"mensagem": "Nenhuma proposta no momento"}

@app.post("/proposta/{proposta_id}/confirmar")
def confirmar_proposta(proposta_id: str):
    sb().table("propostas").update({"status": "APROVADA"}).eq("id", proposta_id).execute()
    return {"status": "confirmada"}

@app.post("/proposta/{proposta_id}/negar")
def negar_proposta(proposta_id: str):
    sb().table("propostas").update({"status": "NEGADA"}).eq("id", proposta_id).execute()
    return {"status": "negada"}

# =====================================================
# PAINEL GESTOR (COM PROPOSTA)
# =====================================================

@app.get("/painel/gestor")
def painel_gestor():
    eventos = buscar_eventos()
    capital = calcular_capital(eventos)
    risco = calcular_risco(capital["capital_total"])
    estado = calcular_estado_robo(capital, risco)
    decisao = calcular_decisao(estado, capital, risco)
    proposta = (
        sb()
        .table("propostas")
        .select("*")
        .eq("status", "AGUARDANDO_CONFIRMACAO")
        .order("criada_em", desc=True)
        .limit(1)
        .execute()
        .data
    )

    return {
        "estado": estado,
        "capital": capital,
        "risco": risco,
        "decisao": decisao,
        "proposta": proposta[0] if proposta else None,
        "timestamp": datetime.utcnow().isoformat(),
    }
