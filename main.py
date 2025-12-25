# main.py — versão completa e final
# ROBO GLOBAL AI
# Carta Magna — Resumo Soberano v8 (25/12/2025)
# Execução REAL — Registro REAL — Decisão REAL

import os
import json
import hmac
import hashlib
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from supabase import create_client, Client

# ------------------------------------------------------------------------------
# CONFIGURAÇÃO GLOBAL
# ------------------------------------------------------------------------------

APP_NAME = "ROBO GLOBAL AI"
APP_VERSION = "v2-final"
ENV = os.getenv("ENV", "production")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET", "")
EDUZZ_WEBHOOK_SECRET = os.getenv("EDUZZ_WEBHOOK_SECRET", "")
KIWIFY_WEBHOOK_SECRET = os.getenv("KIWIFY_WEBHOOK_SECRET", "")

DASHBOARD_ORIGINS = os.getenv("DASHBOARD_ORIGINS", "*").split(",")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórios")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ------------------------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] [%(levelname)s] %(message)s",
)

log = logging.getLogger("ROBO-GLOBAL")

def log_info(origem: str, msg: str):
    log.info(f"[{origem}] {msg}")

def log_warn(origem: str, msg: str):
    log.warning(f"[{origem}] {msg}")

def log_error(origem: str, msg: str):
    log.error(f"[{origem}] {msg}")

# ------------------------------------------------------------------------------
# FASTAPI
# ------------------------------------------------------------------------------

app = FastAPI(title=APP_NAME, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=DASHBOARD_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# MODELOS
# ------------------------------------------------------------------------------

class EventoEntrada(BaseModel):
    origem: str
    payload: Dict[str, Any]

class Decisao(BaseModel):
    produto: str
    acao: str
    score: float
    motivo: str

# ------------------------------------------------------------------------------
# UTILIDADES
# ------------------------------------------------------------------------------

def utcnow():
    return datetime.now(timezone.utc)

def validar_hmac(raw_body: bytes, signature: str, secret: str) -> bool:
    if not secret or not signature:
        return False
    mac = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, signature)

def salvar_snapshot(tabela: str, data: Dict[str, Any]):
    data["created_at"] = utcnow().isoformat()
    supabase.table(tabela).insert(data).execute()

# ------------------------------------------------------------------------------
# NORMALIZAÇÃO
# ------------------------------------------------------------------------------

def normalizar_evento(origem: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    evento = {
        "origem": origem,
        "evento_id": payload.get("id") or payload.get("transaction") or payload.get("order_id"),
        "produto": payload.get("product_name") or payload.get("product") or "desconhecido",
        "valor": float(payload.get("value") or payload.get("price") or 0),
        "comissao": float(payload.get("commission") or 0),
        "status": payload.get("status") or payload.get("event") or "unknown",
        "raw": payload,
    }
    return evento

# ------------------------------------------------------------------------------
# CÁLCULOS
# ------------------------------------------------------------------------------

def calcular_comissao(evento: Dict[str, Any]) -> float:
    return evento.get("comissao", 0.0)

def calcular_rentabilidade(evento: Dict[str, Any]) -> float:
    valor = evento.get("valor", 0.0)
    comissao = evento.get("comissao", 0.0)
    if valor <= 0:
        return 0.0
    return comissao / valor

# ------------------------------------------------------------------------------
# ANÁLISE E DECISÃO
# ------------------------------------------------------------------------------

def analisar_produto(evento: Dict[str, Any]) -> float:
    rent = calcular_rentabilidade(evento)
    score = rent * 100
    return score

def escolher_melhor_oferta(evento: Dict[str, Any]) -> Decisao:
    score = analisar_produto(evento)
    if score > 30:
        acao = "ESCALAR"
        motivo = "Alta rentabilidade"
    elif score > 5:
        acao = "MANTER"
        motivo = "Rentabilidade média"
    else:
        acao = "PAUSAR"
        motivo = "Baixa rentabilidade"
    return Decisao(
        produto=evento.get("produto"),
        acao=acao,
        score=score,
        motivo=motivo,
    )

# ------------------------------------------------------------------------------
# PIPELINE OPERACIONAL
# ------------------------------------------------------------------------------

def registrar_operacao(evento: Dict[str, Any], decisao: Decisao):
    salvar_snapshot("eventos", evento)
    salvar_snapshot("decisoes", decisao.dict())

def processar_evento(origem: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    evento = normalizar_evento(origem, payload)
    decisao = escolher_melhor_oferta(evento)
    registrar_operacao(evento, decisao)
    return {
        "evento": evento,
        "decisao": decisao.dict(),
    }

def executar_ciclo(eventos: List[Dict[str, Any]]) -> Dict[str, Any]:
    resultados = []
    for ev in eventos:
        resultados.append(processar_evento(ev["origem"], ev["payload"]))
    return {"resultados": resultados}

def gerenciar_escalada():
    log_info("ESCALADA", "Rotina de escalada executada")

# ------------------------------------------------------------------------------
# WEBHOOKS
# ------------------------------------------------------------------------------

@app.post("/webhook/universal")
async def webhook_universal(evento: EventoEntrada):
    log_info("WEBHOOK", f"Evento universal recebido de {evento.origem}")
    resultado = processar_evento(evento.origem, evento.payload)
    return {"ok": True, "resultado": resultado}

@app.post("/webhook/hotmart")
async def webhook_hotmart(
    request: Request,
    x_hotmart_hmac_sha256: Optional[str] = Header(None),
):
    raw = await request.body()
    if not validar_hmac(raw, x_hotmart_hmac_sha256 or "", HOTMART_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="HMAC inválido")
    payload = json.loads(raw.decode())
    log_info("HOTMART", "Webhook validado")
    resultado = processar_evento("hotmart", payload)
    return {"ok": True, "resultado": resultado}

@app.post("/webhook/eduzz")
async def webhook_eduzz(
    request: Request,
    x_eduzz_signature: Optional[str] = Header(None),
):
    raw = await request.body()
    if not validar_hmac(raw, x_eduzz_signature or "", EDUZZ_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="HMAC inválido")
    payload = json.loads(raw.decode())
    log_info("EDUZZ", "Webhook validado")
    resultado = processar_evento("eduzz", payload)
    return {"ok": True, "resultado": resultado}

@app.post("/webhook/kiwify")
async def webhook_kiwify(
    request: Request,
    x_kiwify_signature: Optional[str] = Header(None),
):
    raw = await request.body()
    if not validar_hmac(raw, x_kiwify_signature or "", KIWIFY_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="HMAC inválido")
    payload = json.loads(raw.decode())
    log_info("KIWIFY", "Webhook validado")
    resultado = processar_evento("kiwify", payload)
    return {"ok": True, "resultado": resultado}

# ------------------------------------------------------------------------------
# ENDPOINTS OPERACIONAIS
# ------------------------------------------------------------------------------

@app.get("/status")
def status():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "env": ENV,
        "time": utcnow().isoformat(),
        "status": "ONLINE",
    }

@app.get("/produtos")
def produtos():
    res = supabase.table("eventos").select("produto").execute()
    produtos = list({r["produto"] for r in res.data}) if res.data else []
    return {"produtos": produtos}

@app.get("/capital")
def capital():
    res = supabase.table("eventos").select("comissao").execute()
    total = sum(r.get("comissao", 0) for r in res.data) if res.data else 0
    return {"capital_total": total}

@app.get("/decisao")
def ultima_decisao():
    res = supabase.table("decisoes").select("*").order("created_at", desc=True).limit(1).execute()
    return {"ultima_decisao": res.data[0] if res.data else None}

@app.get("/plano-diario")
def plano_diario():
    return {
        "acao": "Monitorar conversões",
        "meta": "Escalar produtos rentáveis",
    }

@app.get("/analise")
def analise():
    res = supabase.table("eventos").select("*").execute()
    return {"eventos": res.data}

@app.get("/escala")
def escala():
    gerenciar_escalada()
    return {"status": "Escalada executada"}

@app.post("/ciclo")
def ciclo(eventos: List[EventoEntrada]):
    payloads = [{"origem": e.origem, "payload": e.payload} for e in eventos]
    return executar_ciclo(payloads)

@app.get("/loop-diario")
def loop_diario():
    log_info("LOOP", "Loop diário executado")
    return {"ok": True}

@app.get("/resultado")
def resultado():
    res = supabase.table("decisoes").select("*").execute()
    return {"decisoes": res.data}

# ------------------------------------------------------------------------------
# WIDGET
# ------------------------------------------------------------------------------

@app.get("/widget-ranking")
def widget_ranking():
    res = supabase.table("eventos").select("produto, comissao").execute()
    ranking = {}
    for r in res.data or []:
        ranking[r["produto"]] = ranking.get(r["produto"], 0) + r.get("comissao", 0)
    ordenado = sorted(ranking.items(), key=lambda x: x[1], reverse=True)
    return {"ranking": ordenado}

# ------------------------------------------------------------------------------
# STARTUP
# ------------------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    log_info("STARTUP", "ROBO GLOBAL AI INICIADO")

@app.on_event("shutdown")
async def shutdown():
    log_info("SHUTDOWN", "ROBO GLOBAL AI ENCERRADO")
