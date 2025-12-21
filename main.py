# main.py — Camada de ESCALA CONTROLADA (Automação Gradual)
# Sequencial ao Plano Diretor
# Escopo: executar automaticamente decisões AUTORIZADAS, com freios
# Com limites • Com pausa • Com auditoria • Sem autonomia plena

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

CAPITAL_MAXIMO = float(os.getenv("CAPITAL_MAXIMO", "300"))
RISCO_MAXIMO = float(os.getenv("RISCO_MAXIMO", "40"))
ESCALA_ATIVA = os.getenv("ESCALA_ATIVA", "false").lower() == "true"

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Variáveis SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórias")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# =====================================================
# APP
# =====================================================

app = FastAPI(title="Robo Global AI — Escala Controlada")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# FUNÇÕES DE CONTROLE
# =====================================================

def capital_disponivel() -> float:
    registros = supabase.table("eventos_execucoes_automaticas") \
        .select("valor") \
        .execute()
    utilizado = sum(r.get("valor") or 0 for r in registros.data)
    return max(CAPITAL_MAXIMO - utilizado, 0)

def pode_executar(decisao: dict) -> bool:
    if not ESCALA_ATIVA:
        return False
    if capital_disponivel() <= 0:
        return False
    if decisao.get("risco", 0) > RISCO_MAXIMO:
        return False
    return True

def executar_automatico(decisao: dict) -> dict:
    return {
        "decisao_id": decisao["id"],
        "acao": "executada_automatica",
        "valor": decisao.get("valor"),
        "resultado": "ok",
        "executado_em": datetime.utcnow().isoformat()
    }

# =====================================================
# CICLO DE ESCALA CONTROLADA
# =====================================================

@app.post("/escala/ciclo")
def ciclo_escala():
    if not ESCALA_ATIVA:
        raise HTTPException(status_code=403, detail="Escala automática desativada")

    decisoes = supabase.table("eventos_decisoes_observacao") \
        .select("*") \
        .eq("decisao", "observar_receita") \
        .eq("executado", False) \
        .limit(10) \
        .execute()

    executadas = []

    for decisao in decisoes.data:
        if not pode_executar(decisao):
            continue

        resultado = executar_automatico(decisao)

        supabase.table("eventos_execucoes_automaticas").insert({
            "decisao_id": decisao["id"],
            "acao": resultado["acao"],
            "valor": resultado.get("valor"),
            "resultado": resultado["resultado"],
            "executado_em": resultado["executado_em"]
        }).execute()

        supabase.table("eventos_decisoes_observacao") \
            .update({"executado": True}) \
            .eq("id", decisao["id"]) \
            .execute()

        executadas.append(resultado)

    return {
        "status": "ok",
        "executadas": len(executadas),
        "capital_restante": capital_disponivel(),
        "timestamp": datetime.utcnow().isoformat()
    }

# =====================================================
# CONTROLES HUMANOS
# =====================================================

@app.post("/escala/ativar")
def ativar_escala():
    return {
        "status": "ok",
        "escala": "ativa",
        "observacao": "Defina ESCALA_ATIVA=true no ambiente para efetivar"
    }

@app.post("/escala/pausar")
def pausar_escala():
    return {
        "status": "ok",
        "escala": "pausada",
        "observacao": "Defina ESCALA_ATIVA=false no ambiente para efetivar"
    }

# =====================================================
# STATUS HUMANO
# =====================================================

@app.get("/status")
def status():
    return {
        "servico": "Robo Global AI — Escala Controlada",
        "estado": "ativo",
        "escala_ativa": ESCALA_ATIVA,
        "capital_maximo": CAPITAL_MAXIMO,
        "risco_maximo": RISCO_MAXIMO,
        "timestamp": datetime.utcnow().isoformat()
    }
