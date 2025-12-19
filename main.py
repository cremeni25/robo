# main.py — versão completa e final
# ROBO GLOBAL AI — FASE 2
# Operação financeira real + visual humano
# Continuidade direta do estado anterior

import os
import hmac
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

# =====================================================
# CONFIGURAÇÃO GLOBAL
# =====================================================

APP_NAME = "ROBO GLOBAL AI"
ENV = os.getenv("ENV", "production")

SUPABASE_URL = os.getenv("SUPABASE_URL")

# 🔒 CORREÇÃO DEFINITIVA — SEM LOOPING DE VARIÁVEIS
SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_ROLE")
    or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    or os.getenv("SUPABASE_KEY")
)

HOTMART_SECRET = os.getenv("HOTMART_SECRET", "")
EDUZZ_SECRET = os.getenv("EDUZZ_SECRET", "")
KIWIFY_SECRET = os.getenv("KIWIFY_SECRET", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase não configurado no ambiente")

# =====================================================
# APP
# =====================================================

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dashboard humano
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# SUPABASE
# =====================================================

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================
# LOG PADRÃO
# =====================================================

def log(origem: str, nivel: str, mensagem: str, extra: Optional[Dict] = None):
    print({
        "ts": datetime.utcnow().isoformat(),
        "origem": origem,
        "nivel": nivel,
        "mensagem": mensagem,
        "extra": extra or {}
    })

# =====================================================
# SEGURANÇA HMAC
# =====================================================

def validar_hmac(body: bytes, assinatura: str, secret: str) -> bool:
    if not secret:
        return True
    mac = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, assinatura)

# =====================================================
# NORMALIZAÇÃO FINANCEIRA
# =====================================================

def normalizar_evento(origem: str, dados: Dict[str, Any]) -> Dict[str, Any]:
    valor = float(dados.get("valor") or dados.get("price") or dados.get("value") or 0)
    token = dados.get("token") or dados.get("transaction_id") or str(uuid.uuid4())

    return {
        "valor_total": valor,
        "valor_unitario": valor,
        "token": token,
        "criado_em": datetime.utcnow().isoformat(),
        "eu_ia": True,
        "sim": True,
    }

# =====================================================
# REGISTRO FINANCEIRO REAL
# =====================================================

def registrar_evento(evento: Dict[str, Any]):
    sb = get_supabase()
    sb.table("eventos_financeiros").insert(evento).execute()

# =====================================================
# PIPELINE
# =====================================================

def processar_evento(origem: str, dados: Dict[str, Any]):
    evento = normalizar_evento(origem, dados)
    registrar_evento(evento)
    log("PIPELINE", "INFO", f"Evento financeiro registrado ({origem})", evento)
    return evento

# =====================================================
# WEBHOOKS
# =====================================================

@app.post("/webhook/universal")
async def webhook_universal(request: Request):
    body = await request.json()
    evento = processar_evento("universal", body)
    return {"ok": True, "evento": evento}

@app.post("/webhook/hotmart")
async def webhook_hotmart(
    request: Request,
    x_hotmart_hmac_sha256: Optional[str] = Header(None),
):
    raw = await request.body()
    if not validar_hmac(raw, x_hotmart_hmac_sha256 or "", HOTMART_SECRET):
        raise HTTPException(status_code=403)
    body = await request.json()
    return processar_evento("hotmart", body)

@app.post("/webhook/eduzz")
async def webhook_eduzz(
    request: Request,
    x_eduzz_signature: Optional[str] = Header(None),
):
    raw = await request.body()
    if not validar_hmac(raw, x_eduzz_signature or "", EDUZZ_SECRET):
        raise HTTPException(status_code=403)
    body = await request.json()
    return processar_evento("eduzz", body)

# =====================================================
# MÉTRICAS FINANCEIRAS
# =====================================================

def resumo_financeiro():
    sb = get_supabase()
    res = sb.table("eventos_financeiros").select("valor_total").execute()
    total = sum(r["valor_total"] for r in res.data)
    qtd = len(res.data)
    return {
        "total_recebido": total,
        "eventos": qtd,
        "media": total / qtd if qtd else 0
    }

# =====================================================
# ENDPOINTS OPERACIONAIS
# =====================================================

@app.get("/status")
def status():
    return {
        "app": APP_NAME,
        "env": ENV,
        "status": "online",
        "ts": datetime.utcnow().isoformat()
    }

@app.get("/capital")
def capital():
    return resumo_financeiro()

@app.get("/decisao")
def decisao():
    r = resumo_financeiro()
    return {
        **r,
        "decisao": "ESCALAR" if r["media"] > 50 else "MANTER",
        "ts": datetime.utcnow().isoformat()
    }

@app.get("/resultado")
def resultado():
    return resumo_financeiro()

# =====================================================
# ENDPOINT FINANCEIRO HUMANO (FASE 2)
# =====================================================

@app.get("/financeiro/resumo")
def financeiro_resumo():
    sb = get_supabase()
    res = sb.table("eventos_financeiros") \
        .select("*") \
        .order("criado_em", desc=True) \
        .limit(50) \
        .execute()

    total = sum(r["valor_total"] for r in res.data)

    return {
        "total_recebido": total,
        "quantidade_eventos": len(res.data),
        "ultimos_eventos": res.data,
        "atualizado_em": datetime.utcnow().isoformat()
    }
