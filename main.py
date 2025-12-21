# main.py — Camada de AUTONOMIA SUPERVISIONADA
# Sequencial ao Plano Diretor
# Escopo: o Robo PROPÕE ajustes, o humano DECIDE
# Sem autonomia plena • Sem execução automática de mudanças • Tudo auditável

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

app = FastAPI(title="Robo Global AI — Autonomia Supervisionada")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# LÓGICA DE PROPOSTA DE AJUSTES
# =====================================================

def gerar_proposta_ajuste() -> dict:
    """
    Analisa resultados passados e propõe ajustes.
    NÃO executa nada.
    """
    execs = supabase.table("eventos_execucoes_automaticas") \
        .select("resultado, valor") \
        .execute()

    total = len(execs.data)
    sucesso = len([e for e in execs.data if e.get("resultado") == "ok"])

    taxa_sucesso = (sucesso / total) if total > 0 else 0

    proposta = {
        "tipo": "ajuste_parametro",
        "descricao": "Ajustar capital_maximo",
        "taxa_sucesso": taxa_sucesso,
        "sugestao": "aumentar" if taxa_sucesso > 0.7 else "manter",
        "criado_em": datetime.utcnow().isoformat(),
        "status": "pendente"
    }

    return proposta

# =====================================================
# ENDPOINT — GERAR PROPOSTA
# =====================================================

@app.post("/autonomia/propor")
def propor_ajuste():
    proposta = gerar_proposta_ajuste()

    result = supabase.table("eventos_propostas_autonomia") \
        .insert(proposta) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Falha ao registrar proposta")

    return {
        "status": "ok",
        "proposta": result.data[0]
    }

# =====================================================
# ENDPOINT — DECISÃO HUMANA
# =====================================================

@app.post("/autonomia/decidir/{proposta_id}")
def decidir_proposta(proposta_id: str, aprovado: bool):
    proposta = supabase.table("eventos_propostas_autonomia") \
        .select("*") \
        .eq("id", proposta_id) \
        .execute()

    if not proposta.data:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    status = "aprovada" if aprovado else "rejeitada"

    supabase.table("eventos_propostas_autonomia") \
        .update({
            "status": status,
            "decidido_em": datetime.utcnow().isoformat()
        }) \
        .eq("id", proposta_id) \
        .execute()

    return {
        "status": "ok",
        "proposta_id": proposta_id,
        "decisao": status
    }

# =====================================================
# STATUS HUMANO
# =====================================================

@app.get("/status")
def status():
    return {
        "servico": "Robo Global AI — Autonomia Supervisionada",
        "estado": "ativo",
        "timestamp": datetime.utcnow().isoformat()
    }
