# main.py — Camada de Integração Mínima (FastAPI)
# Objetivo: ingestão externa controlada → Supabase
# Escopo: mínimo absoluto, conforme Plano Diretor
# Sem Robo • Sem decisão • Sem webhook • Sem dashboard

import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
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

app = FastAPI(title="Robo Global AI — Camada de Integração Mínima")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# ENDPOINT DE INGESTÃO MÍNIMA
# =====================================================

@app.post("/ingestao")
async def ingestao(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload JSON inválido")

    registro = {
        "plataforma_origem": payload.get("plataforma_origem", "ingestao_externa"),
        "payload_original": payload,
        "hash_evento": payload.get("hash_evento", f"hash_{datetime.utcnow().isoformat()}"),
    }

    try:
        result = supabase.table("eventos_afiliados_brutos").insert(registro).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not result.data:
        raise HTTPException(status_code=500, detail="Falha ao persistir registro")

    return {
        "status": "ok",
        "mensagem": "Ingestão realizada com sucesso",
        "registro_id": result.data[0].get("id")
    }

# =====================================================
# ENDPOINT DE STATUS (HUMANO)
# =====================================================

@app.get("/status")
def status():
    return {
        "servico": "Robo Global AI — Integração Mínima",
        "estado": "ativo",
        "timestamp": datetime.utcnow().isoformat()
    }
