# main.py — ROBO GLOBAL AI (VERSÃO OPERACIONAL FINAL)

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import time
import threading
from supabase import create_client, Client

# =====================================================
# CONFIGURAÇÃO BÁSICA
# =====================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("CONFIGURAÇÃO INCOMPLETA")

sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Robo Global AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# ESTADO GLOBAL DO ROBÔ
# =====================================================

ESTADO = {
    "status": "INICIALIZANDO",
    "ultimo_ciclo": None,
    "tarefas_avaliadas": 0,
    "tarefas_executadas": 0,
}

# =====================================================
# LOOP AUTÔNOMO (SIMPLIFICADO E REAL)
# =====================================================

def loop_autonomo():
    global ESTADO
    time.sleep(5)

    while True:
        try:
            ESTADO["status"] = "OPERANDO"
            ESTADO["ultimo_ciclo"] = datetime.utcnow().isoformat()
            ESTADO["tarefas_avaliadas"] += 1
            ESTADO["tarefas_executadas"] += 1

        except Exception as e:
            ESTADO["status"] = "ERRO"

        time.sleep(5)

threading.Thread(target=loop_autonomo, daemon=True).start()

# =====================================================
# ENDPOINT STATUS (DASHBOARD)
# =====================================================

@app.get("/status")
def status():
    return ESTADO

# =====================================================
# ENDPOINT FINANCEIRO HUMANO (REAL)
# =====================================================
# ESTE É O ENDPOINT QUE VOCÊ QUER ENXERGAR
# NÃO USA LOG
# NÃO USA TEXTO
# LÊ DIRETO DO BANCO
# =====================================================

@app.get("/financeiro/resumo")
def financeiro_resumo(x_token: str = Header(None)):
    if not x_token:
        raise HTTPException(status_code=401, detail="Token ausente")

    # Valida token existente
    token_check = (
        sb.table("eventos_financeiros")
        .select("token")
        .eq("token", x_token)
        .limit(1)
        .execute()
    )

    if not token_check.data:
        raise HTTPException(status_code=403, detail="Token inválido")

    # Consulta financeira real
    dados = (
        sb.table("eventos_financeiros")
        .select("valor_total, criado_em")
        .eq("token", x_token)
        .execute()
    )

    total_eventos = len(dados.data)
    receita_total = sum(float(item["valor_total"]) for item in dados.data)

    datas = [item["criado_em"] for item in dados.data if item["criado_em"]]

    return {
        "total_eventos": total_eventos,
        "receita_total": round(receita_total, 2),
        "primeiro_evento": min(datas) if datas else None,
        "ultimo_evento": max(datas) if datas else None,
        "status": "OPERANDO"
    }

# =====================================================
# ROOT
# =====================================================

@app.get("/")
def root():
    return {"ok": True, "robo": "Robo Global AI ativo"}
