# main.py — versão completa e final
# ROBO GLOBAL AI
# Núcleo + C3 + E2 + E3 + E3.2 (Histórico Visual Operacional)
# SEM automação externa • SEM ciclos • UMA ação por proposta

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date
import os
import uuid
from supabase import create_client

# =====================================================
# APP
# =====================================================

app = FastAPI(title="ROBO GLOBAL AI", version="3.4")

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
# CAPITAL / RISCO (INALTERADOS)
# =====================================================

def buscar_eventos():
    res = sb().table("eventos_financeiros").select("valor_unitario").execute()
    return res.data or []

def calcular_capital(eventos):
    total = sum([(e.get("valor_unitario") or 0) for e in eventos])
    return {
        "capital_total": round(total, 4),
        "capital_operacional_disponivel": round(total * 0.3, 4),
    }

def calcular_estado():
    capital = calcular_capital(buscar_eventos())
    return {
        "estado_atual": "OPERACIONAL" if capital["capital_operacional_disponivel"] > 0 else "OBSERVACAO",
        "pode_operar": capital["capital_operacional_disponivel"] > 0,
    }

# =====================================================
# E2 — PROPOSTAS
# =====================================================

def criar_proposta_se_permitido():
    estado = calcular_estado()
    if not estado["pode_operar"]:
        return None

    hoje = date.today().isoformat()
    existentes = (
        sb()
        .table("propostas")
        .select("id")
        .eq("status", "AGUARDANDO_CONFIRMACAO")
        .eq("data", hoje)
        .execute()
    )

    if existentes.data:
        return None

    proposta = {
        "id": str(uuid.uuid4()),
        "status": "AGUARDANDO_CONFIRMACAO",
        "plataforma": "TikTok",
        "tema": "Curiosidade / dor simples",
        "produto": "Produto afiliado X",
        "cta": "Link na bio",
        "data": hoje,
        "criada_em": datetime.utcnow().isoformat(),
    }

    sb().table("propostas").insert(proposta).execute()
    return proposta

# =====================================================
# E3 — PACOTE DE EXECUÇÃO
# =====================================================

def gerar_pacote_execucao(proposta):
    return {
        "texto": f"{proposta['tema']} — veja como isso pode ajudar você.",
        "cta": proposta["cta"],
        "checklist": [
            "Publicar 1 conteúdo",
            "Inserir CTA corretamente",
            "Conferir link",
        ],
        "gerado_em": datetime.utcnow().isoformat(),
    }

# =====================================================
# HISTÓRICO (E3.2)
# =====================================================

def registrar_historico(proposta, tipo, status, origem):
    registro = {
        "id": str(uuid.uuid4()),
        "data_hora": datetime.utcnow().isoformat(),
        "tipo_execucao": tipo,          # MANUAL | AUTOMACAO
        "plataforma": proposta["plataforma"],
        "proposta_id": proposta["id"],
        "tema": proposta["tema"],
        "produto": proposta["produto"],
        "status": status,               # EXECUTADA | FALHOU | PAUSADA
        "origem": origem,               # HUMANO | ROBO
    }
    sb().table("historico_operacional").insert(registro).execute()

# =====================================================
# ENDPOINTS BASE
# =====================================================

@app.get("/status")
def status():
    return {"status": "ativo", "timestamp": datetime.utcnow().isoformat()}

# =====================================================
# PROPOSTAS
# =====================================================

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
    return res.data[0] if res.data else {}

@app.post("/proposta/{proposta_id}/confirmar")
def confirmar_proposta(proposta_id: str):
    sb().table("propostas").update({"status": "APROVADA"}).eq("id", proposta_id).execute()
    return {"status": "APROVADA"}

@app.post("/proposta/{proposta_id}/preparar-execucao")
def preparar_execucao(proposta_id: str):
    res = sb().table("propostas").select("*").eq("id", proposta_id).execute()
    proposta = res.data[0]
    pacote = gerar_pacote_execucao(proposta)
    sb().table("propostas").update({
        "status": "PRONTA_PARA_EXECUCAO",
        "pacote_execucao": pacote
    }).eq("id", proposta_id).execute()
    return pacote

@app.post("/proposta/{proposta_id}/confirmar-execucao")
def confirmar_execucao(proposta_id: str):
    res = sb().table("propostas").select("*").eq("id", proposta_id).execute()
    proposta = res.data[0]

    sb().table("propostas").update({
        "status": "EXECUTADA",
        "executada_em": datetime.utcnow().isoformat()
    }).eq("id", proposta_id).execute()

    # >>> REGISTRO NO HISTÓRICO (E3.2)
    registrar_historico(
        proposta=proposta,
        tipo="MANUAL",
        status="EXECUTADA",
        origem="HUMANO"
    )

    return {"status": "EXECUTADA"}

# =====================================================
# HISTÓRICO — LEITURA
# =====================================================

@app.get("/historico-operacional")
def historico_operacional():
    res = (
        sb()
        .table("historico_operacional")
        .select("*")
        .order("data_hora", desc=True)
        .limit(20)
        .execute()
    )
    return res.data or []
