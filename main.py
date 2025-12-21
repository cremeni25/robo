# main.py — Camada de Decisão Econômica MÍNIMA (Modo Observação)
# Sequencial ao Plano Diretor
# Escopo: leitura de eventos normalizados → decisão registrada
# Sem execução • Sem escala • Sem Robo • Sem dashboard

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

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Variáveis SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórias")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# =====================================================
# APP
# =====================================================

app = FastAPI(title="Robo Global AI — Decisão Econômica Mínima (Observação)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# LÓGICA DE DECISÃO MÍNIMA
# =====================================================

def decidir_evento(evento: dict) -> dict:
    """
    Decisão econômica mínima (modo observação):
    Não executa ações — apenas classifica.
    """
    valor = evento.get("valor")
    tipo = evento.get("tipo_evento")
    plataforma = evento.get("plataforma")

    if tipo in ["PURCHASE_APPROVED", "approved", "sale"] and valor:
        decisao = "observar_receita"
    elif tipo in ["refund", "chargeback", "canceled"]:
        decisao = "observar_risco"
    else:
        decisao = "ignorar"

    return {
        "plataforma": plataforma,
        "tipo_evento": tipo,
        "valor": valor,
        "decisao": decisao,
        "referencia": evento.get("referencia"),
        "criado_em": datetime.utcnow().isoformat(),
    }

def processar_decisoes():
    """
    Lê eventos normalizados ainda não avaliados
    e registra decisão econômica mínima.
    """
    eventos = supabase.table("eventos_afiliados_normalizados") \
        .select("*") \
        .eq("avaliado", False) \
        .limit(50) \
        .execute()

    if not eventos.data:
        return 0

    for evento in eventos.data:
        decisao = decidir_evento(evento)

        supabase.table("eventos_decisoes_observacao").insert(decisao).execute()

        supabase.table("eventos_afiliados_normalizados") \
            .update({"avaliado": True}) \
            .eq("id", evento["id"]) \
            .execute()

    return len(eventos.data)

# =====================================================
# ENDPOINT DE CICLO (HUMANO / MANUAL)
# =====================================================

@app.post("/ciclo/decisao")
def ciclo_decisao():
    quantidade = processar_decisoes()
    return {
        "status": "ok",
        "eventos_processados": quantidade,
        "modo": "observacao",
        "timestamp": datetime.utcnow().isoformat()
    }

# =====================================================
# STATUS HUMANO
# =====================================================

@app.get("/status")
def status():
    return {
        "servico": "Robo Global AI — Decisão Econômica Mínima",
        "estado": "ativo",
        "modo": "observacao",
        "timestamp": datetime.utcnow().isoformat()
    }
