# main.py — Camada de Análise e Consolidação HUMANA
# Sequencial ao Plano Diretor
# Escopo: tornar decisões e eventos interpretáveis para humanos
# Sem execução • Sem escala • Sem Robo • Sem dashboard complexo

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

app = FastAPI(title="Robo Global AI — Análise e Consolidação Humana")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# FUNÇÕES DE CONSOLIDAÇÃO HUMANA
# =====================================================

def consolidar_eventos():
    eventos = supabase.table("eventos_afiliados_normalizados") \
        .select("plataforma, tipo_evento, valor") \
        .execute()

    total_eventos = len(eventos.data)
    total_valor = sum(e.get("valor") or 0 for e in eventos.data)

    por_plataforma = {}
    for e in eventos.data:
        plat = e.get("plataforma")
        por_plataforma.setdefault(plat, {"quantidade": 0, "valor": 0})
        por_plataforma[plat]["quantidade"] += 1
        por_plataforma[plat]["valor"] += e.get("valor") or 0

    return {
        "total_eventos": total_eventos,
        "total_valor": total_valor,
        "por_plataforma": por_plataforma,
    }

def consolidar_decisoes():
    decisoes = supabase.table("eventos_decisoes_observacao") \
        .select("decisao") \
        .execute()

    resumo = {}
    for d in decisoes.data:
        chave = d.get("decisao")
        resumo[chave] = resumo.get(chave, 0) + 1

    return resumo

# =====================================================
# ENDPOINTS HUMANOS (INTERPRETÁVEIS)
# =====================================================

@app.get("/analise/resumo")
def resumo_humano():
    eventos = consolidar_eventos()
    decisoes = consolidar_decisoes()

    return {
        "status": "ok",
        "resumo_eventos": eventos,
        "resumo_decisoes": decisoes,
        "gerado_em": datetime.utcnow().isoformat(),
        "interpretacao": "Visão consolidada para análise humana"
    }

@app.get("/status")
def status():
    return {
        "servico": "Robo Global AI — Análise Humana",
        "estado": "ativo",
        "timestamp": datetime.utcnow().isoformat()
    }
