# main.py — versão completa e final
# ROBO GLOBAL AI — OPERAÇÃO FINANCEIRA REAL + VISUAL HUMANO
# Backend FastAPI • Supabase • Webhooks • Decisão Econômica • Endpoint Financeiro Humano

import os
import hmac
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from supabase import create_client, Client

# =====================================================
# CONFIGURAÇÃO BÁSICA
# =====================================================

APP_NAME = "ROBO GLOBAL AI"
ENV = os.getenv("ENV", "production")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

HOTMART_SECRET = os.getenv("HOTMART_SECRET", "")
EDUZZ_SECRET = os.getenv("EDUZZ_SECRET", "")
KIWIFY_SECRET = os.getenv("KIWIFY_SECRET", "")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
    raise RuntimeError("SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY não configurados")

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
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

# =====================================================
# LOGS PADRÃO
# =====================================================

def log(origem: str, nivel: str, mensagem: str, extra: Optional[Dict] = None):
    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "origem": origem,
        "nivel": nivel,
        "mensagem": mensagem,
        "extra": extra or {},
    }
    print(payload)

# =====================================================
# SEGURANÇA HMAC
# =====================================================

def validar_hmac(body: bytes, assinatura: str, secret: str) -> bool:
    if not secret:
        return True
    mac = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, assinatura)

# =====================================================
# NORMALIZAÇÃO UNIVERSAL
# =====================================================

def normalizar_evento(origem: str, dados: Dict[str, Any]) -> Dict[str, Any]:
    valor = float(dados.get("valor", dados.get("price", dados.get("value", 0))))
    token = dados.get("token") or dados.get("transaction_id") or str(uuid.uuid4())

    return {
        "origem": origem,
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

def registrar_evento_financeiro(evento: Dict[str, Any]):
    sb = get_supabase()
    sb.table("eventos_financeiros").insert({
        "valor_total": evento["valor_total"],
        "valor_unitario": evento["valor_unitario"],
        "token": evento["token"],
        "criado_em": evento["criado_em"],
        "eu_ia": evento["eu_ia"],
        "sim": evento["sim"],
    }).execute()

# =====================================================
# DECISÃO ECONÔMICA (MVP REAL)
# =====================================================

def calcular_rentabilidade():
    sb = get_supabase()
    res = sb.table("eventos_financeiros").select("valor_total").execute()
    total = sum([r["valor_total"] for r in res.data])
    return {
        "total_recebido": total,
        "eventos": len(res.data),
        "media": total / len(res.data) if res.data else 0,
    }

def decisao_economica():
    rent = calcular_rentabilidade()
    if rent["media"] > 50:
        acao = "ESCALAR"
    else:
        acao = "MANTER"
    return {
        "rentabilidade": rent,
        "decisao": acao,
        "timestamp": datetime.utcnow().isoformat(),
    }

# =====================================================
# PIPELINE OPERACIONAL
# =====================================================

def processar_evento(origem: str, dados: Dict[str, Any]):
    evento = normalizar_evento(origem, dados)
    registrar_evento_financeiro(evento)
    log("PIPELINE", "INFO", "Evento financeiro registrado", evento)
    return evento

# =====================================================
# WEBHOOKS
# =====================================================

@app.post("/webhook/universal")
async def webhook_universal(request: Request):
    body = await request.json()
    evento = processar_evento("universal", body)
    return {"status": "ok", "evento": evento}

@app.post("/webhook/hotmart")
async def webhook_hotmart(
    request: Request,
    x_hotmart_hmac_sha256: Optional[str] = Header(None),
):
    raw = await request.body()
    if not validar_hmac(raw, x_hotmart_hmac_sha256 or "", HOTMART_SECRET):
        raise HTTPException(status_code=403, detail="HMAC inválido")
    body = await request.json()
    evento = processar_evento("hotmart", body)
    return {"status": "ok", "evento": evento}

@app.post("/webhook/eduzz")
async def webhook_eduzz(
    request: Request,
    x_eduzz_signature: Optional[str] = Header(None),
):
    raw = await request.body()
    if not validar_hmac(raw, x_eduzz_signature or "", EDUZZ_SECRET):
        raise HTTPException(status_code=403, detail="HMAC inválido")
    body = await request.json()
    evento = processar_evento("eduzz", body)
    return {"status": "ok", "evento": evento}

@app.post("/webhook/kiwify")
async def webhook_kiwify(
    request: Request,
    x_kiwify_signature: Optional[str] = Header(None),
):
    raw = await request.body()
    if not validar_hmac(raw, x_kiwify_signature or "", KIWIFY_SECRET):
        raise HTTPException(status_code=403, detail="HMAC inválido")
    body = await request.json()
    evento = processar_evento("kiwify", body)
    return {"status": "ok", "evento": evento}

# =====================================================
# ENDPOINTS OPERACIONAIS
# =====================================================

@app.get("/status")
def status():
    return {
        "app": APP_NAME,
        "env": ENV,
        "time": datetime.utcnow().isoformat(),
        "status": "online",
    }

@app.get("/capital")
def capital():
    return calcular_rentabilidade()

@app.get("/decisao")
def decisao():
    return decisao_economica()

@app.post("/ciclo")
def executar_ciclo():
    decisao = decisao_economica()
    log("CICLO", "INFO", "Ciclo executado", decisao)
    return decisao

@app.get("/resultado")
def resultado():
    return decisao_economica()

# =====================================================
# ENDPOINT FINANCEIRO HUMANO (VISUAL)
# =====================================================

@app.get("/financeiro/resumo")
def financeiro_resumo():
    sb = get_supabase()
    res = sb.table("eventos_financeiros") \
        .select("*") \
        .order("criado_em", desc=True) \
        .limit(50) \
        .execute()

    total = sum([r["valor_total"] for r in res.data])

    return {
        "total_recebido": total,
        "quantidade_eventos": len(res.data),
        "ultimos_eventos": res.data,
        "atualizado_em": datetime.utcnow().isoformat(),
    }

# =====================================================
# WIDGET RANKING (HUMANO)
# =====================================================

@app.get("/widget-ranking")
def widget_ranking():
    sb = get_supabase()
    res = sb.table("eventos_financeiros") \
        .select("token, valor_total") \
        .execute()

    ranking = sorted(res.data, key=lambda x: x["valor_total"], reverse=True)

    return {
        "ranking": ranking[:10],
        "gerado_em": datetime.utcnow().isoformat(),
    }
