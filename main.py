# main.py — versão completa e final

import os
import hmac
import hashlib
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from supabase import create_client, Client

# =========================
# CONFIGURAÇÕES GERAIS
# =========================

APP_NAME = "Robo Global AI"
ENV = os.getenv("ENV", "production")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")

HOTMART_SECRET = os.getenv("HOTMART_SECRET", "")
EDUZZ_SECRET = os.getenv("EDUZZ_SECRET", "")
KIWIFY_SECRET = os.getenv("KIWIFY_SECRET", "")

INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", "0"))

# =========================
# APP
# =========================

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

# =========================
# LOGS
# =========================

def log(origem: str, nivel: str, mensagem: str, extra: Optional[Dict[str, Any]] = None):
    registro = {
        "id": str(uuid.uuid4()),
        "origem": origem,
        "nivel": nivel,
        "mensagem": mensagem,
        "extra": extra or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    supabase.table("logs").insert(registro).execute()

# =========================
# SEGURANÇA
# =========================

def validar_hmac(payload: bytes, signature: str, secret: str) -> bool:
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)

# =========================
# NORMALIZAÇÃO
# =========================

def normalizar_evento(origem: str, data: Dict[str, Any]) -> Dict[str, Any]:
    evento = {
        "id": str(uuid.uuid4()),
        "origem": origem,
        "produto_id": data.get("product_id") or data.get("productId"),
        "produto_nome": data.get("product_name") or data.get("productName"),
        "valor": float(data.get("value") or data.get("price") or 0),
        "comissao": float(data.get("commission") or 0),
        "moeda": data.get("currency", "BRL"),
        "status": data.get("status", "unknown"),
        "raw": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    return evento

# =========================
# FINANCEIRO
# =========================

def registrar_operacao(evento: Dict[str, Any]):
    supabase.table("operacoes").insert(evento).execute()

def calcular_comissao(evento: Dict[str, Any]) -> float:
    return evento.get("comissao", 0.0)

def calcular_rentabilidade() -> float:
    result = supabase.table("operacoes").select("comissao").execute()
    total = sum([float(r["comissao"]) for r in result.data])
    return total

def capital_atual() -> float:
    return INITIAL_CAPITAL + calcular_rentabilidade()

# =========================
# ANÁLISE E DECISÃO
# =========================

def analisar_produto(produto_id: str) -> Dict[str, Any]:
    vendas = supabase.table("operacoes").select("*").eq("produto_id", produto_id).execute().data
    total = sum([v["comissao"] for v in vendas])
    return {
        "produto_id": produto_id,
        "total_comissao": total,
        "quantidade": len(vendas)
    }

def escolher_melhor_oferta() -> Optional[str]:
    produtos = supabase.table("operacoes").select("produto_id").execute().data
    ranking = {}
    for p in produtos:
        pid = p["produto_id"]
        if pid not in ranking:
            ranking[pid] = analisar_produto(pid)["total_comissao"]
    if not ranking:
        return None
    return max(ranking, key=ranking.get)

def gerenciar_escalada():
    melhor = escolher_melhor_oferta()
    if melhor:
        supabase.table("escaladas").insert({
            "id": str(uuid.uuid4()),
            "produto_id": melhor,
            "timestamp": datetime.utcnow().isoformat()
        }).execute()

# =========================
# PIPELINE
# =========================

def processar_evento(origem: str, data: Dict[str, Any]):
    evento = normalizar_evento(origem, data)
    registrar_operacao(evento)
    gerenciar_escalada()

def executar_ciclo():
    gerenciar_escalada()

# =========================
# WEBHOOKS
# =========================

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    payload = await request.body()
    signature = request.headers.get("X-HOTMART-HMAC-SHA256", "")
    if not validar_hmac(payload, signature, HOTMART_SECRET):
        log("HOTMART", "ERROR", "HMAC inválido")
        raise HTTPException(status_code=401)
    data = json.loads(payload)
    processar_evento("HOTMART", data)
    return {"status": "ok"}

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    payload = await request.body()
    signature = request.headers.get("X-Eduzz-Signature", "")
    if not validar_hmac(payload, signature, EDUZZ_SECRET):
        log("EDUZZ", "ERROR", "HMAC inválido")
        raise HTTPException(status_code=401)
    data = json.loads(payload)
    processar_evento("EDUZZ", data)
    return {"status": "ok"}

@app.post("/webhook/kiwify")
async def webhook_kiwify(request: Request):
    payload = await request.body()
    signature = request.headers.get("X-Kiwify-Signature", "")
    if not validar_hmac(payload, signature, KIWIFY_SECRET):
        log("KIWIFY", "ERROR", "HMAC inválido")
        raise HTTPException(status_code=401)
    data = json.loads(payload)
    processar_evento("KIWIFY", data)
    return {"status": "ok"}

@app.post("/webhook/universal")
async def webhook_universal(request: Request):
    data = await request.json()
    origem = data.get("origem", "UNIVERSAL")
    processar_evento(origem, data)
    return {"status": "ok"}

# =========================
# ENDPOINTS OPERACIONAIS
# =========================

@app.get("/status")
def status():
    return {
        "app": APP_NAME,
        "env": ENV,
        "capital": capital_atual(),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/capital")
def capital():
    return {"capital": capital_atual()}

@app.get("/decisao")
def decisao():
    return {"melhor_oferta": escolher_melhor_oferta()}

@app.post("/ciclo")
def ciclo():
    executar_ciclo()
    return {"status": "executado"}

@app.get("/resultado")
def resultado():
    return {
        "rentabilidade": calcular_rentabilidade(),
        "capital": capital_atual()
    }

@app.get("/produtos")
def produtos():
    return supabase.table("operacoes").select("produto_id").execute().data

@app.get("/analise")
def analise():
    produtos = supabase.table("operacoes").select("produto_id").execute().data
    return [analisar_produto(p["produto_id"]) for p in produtos]

@app.get("/escala")
def escala():
    return supabase.table("escaladas").select("*").execute().data

@app.get("/loop-diario")
def loop_diario():
    executar_ciclo()
    return {"status": "loop executado"}

@app.get("/widget-ranking")
def widget_ranking():
    produtos = supabase.table("operacoes").select("produto_id").execute().data
    ranking = []
    for p in produtos:
        ranking.append(analisar_produto(p["produto_id"]))
    ranking.sort(key=lambda x: x["total_comissao"], reverse=True)
    return ranking
