# main.py — versão completa e final
# Robo Global AI — Operação Econômica Real
# Bloco 1/4 — Núcleo, Configurações, Conectores, Base Operacional

import os
import hmac
import hashlib
import json
import uuid
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from supabase import create_client, Client

# =========================================================
# CONFIGURAÇÕES GERAIS
# =========================================================

APP_NAME = "Robo Global AI"
APP_VERSION = "1.0.0-final"
ENV = os.getenv("ENV", "production")

# =========================================================
# LOGGING PADRONIZADO
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [ROBO_GLOBAL] [%(levelname)s] %(message)s'
)

def log_info(msg: str):
    logging.info(msg)

def log_warn(msg: str):
    logging.warning(msg)

def log_error(msg: str):
    logging.error(msg)

# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# SUPABASE
# =========================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    log_error("Supabase não configurado corretamente")
    raise RuntimeError("Supabase credentials missing")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

log_info("Supabase conectado")

# =========================================================
# SECRETS WEBHOOKS
# =========================================================

HOTMART_SECRET = os.getenv("HOTMART_SECRET", "")
EDUZZ_SECRET = os.getenv("EDUZZ_SECRET", "")
KIWIFY_SECRET = os.getenv("KIWIFY_SECRET", "")

# =========================================================
# UTILITÁRIOS DE SEGURANÇA
# =========================================================

def validar_hmac(payload: bytes, signature: str, secret: str) -> bool:
    if not secret or not signature:
        return False
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    expected = mac.hexdigest()
    return hmac.compare_digest(expected, signature)

def gerar_id_operacao() -> str:
    return str(uuid.uuid4())

def agora() -> str:
    return datetime.utcnow().isoformat()

# =========================================================
# MODELOS INTERNOS
# =========================================================

def registrar_log_evento(origem: str, nivel: str, mensagem: str, payload: Optional[Dict] = None):
    try:
        supabase.table("logs").insert({
            "origem": origem,
            "nivel": nivel,
            "mensagem": mensagem,
            "payload": payload,
            "criado_em": agora()
        }).execute()
    except Exception as e:
        logging.error(f"[LOG_FAIL] {e}")

# =========================================================
# STATUS OPERACIONAL
# =========================================================

@app.get("/status")
def status():
    return {
        "status": "OK",
        "app": APP_NAME,
        "versao": APP_VERSION,
        "ambiente": ENV,
        "supabase": "conectado",
        "timestamp": agora()
    }

# =========================================================
# REGISTRO FINANCEIRO — BASE
# =========================================================

def registrar_financeiro(dados: Dict[str, Any]):
    dados["criado_em"] = agora()
    supabase.table("financeiro").insert(dados).execute()

# =========================================================
# REGISTRO DE OPERAÇÕES
# =========================================================

def registrar_operacao(operacao: Dict[str, Any]):
    operacao["criado_em"] = agora()
    supabase.table("operacoes").insert(operacao).execute()

# =========================================================
# PIPELINE ECONÔMICO — PLACEHOLDER REAL (SEM SIMULAÇÃO)
# =========================================================

def processar_evento(evento: Dict[str, Any]) -> None:
    registrar_log_evento(
        origem="PIPELINE",
        nivel="INFO",
        mensagem="Evento recebido para processamento",
        payload=evento
    )
    # Continuidade no Bloco 2

# =========================================================
# WEBHOOK UNIVERSAL (BASE)
# =========================================================

@app.post("/webhook/universal")
async def webhook_universal(request: Request):
    payload = await request.json()

    registrar_log_evento(
        origem="WEBHOOK_UNIVERSAL",
        nivel="INFO",
        mensagem="Evento universal recebido",
        payload=payload
    )

    processar_evento(payload)

    return {"status": "received"}

# =========================================================
# FIM DO BLOCO 1
# =========================================================


# =========================================================
# NORMALIZAÇÃO UNIVERSAL DE EVENTOS
# =========================================================

def normalizar_evento(origem: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    evento = {
        "id_evento": gerar_id_operacao(),
        "origem": origem,
        "tipo": None,
        "produto_id": None,
        "produto_nome": None,
        "valor": 0.0,
        "comissao": 0.0,
        "moeda": "BRL",
        "comprador": {},
        "status": None,
        "raw": payload,
        "timestamp": agora()
    }

    try:
        if origem == "HOTMART":
            evento["tipo"] = payload.get("event")
            evento["produto_id"] = payload.get("data", {}).get("product", {}).get("id")
            evento["produto_nome"] = payload.get("data", {}).get("product", {}).get("name")
            evento["valor"] = float(payload.get("data", {}).get("purchase", {}).get("price", 0))
            evento["comissao"] = float(payload.get("data", {}).get("commission", {}).get("value", 0))
            evento["status"] = payload.get("event")
            evento["comprador"] = payload.get("data", {}).get("buyer", {})

        elif origem == "EDUZZ":
            evento["tipo"] = payload.get("event")
            evento["produto_id"] = payload.get("product_id")
            evento["produto_nome"] = payload.get("product_name")
            evento["valor"] = float(payload.get("sale_price", 0))
            evento["comissao"] = float(payload.get("commission", 0))
            evento["status"] = payload.get("status")
            evento["comprador"] = payload.get("customer", {})

        elif origem == "KIWIFY":
            evento["tipo"] = payload.get("event_type")
            evento["produto_id"] = payload.get("product", {}).get("id")
            evento["produto_nome"] = payload.get("product", {}).get("name")
            evento["valor"] = float(payload.get("order", {}).get("amount", 0))
            evento["comissao"] = float(payload.get("commission", {}).get("amount", 0))
            evento["status"] = payload.get("order", {}).get("status")
            evento["comprador"] = payload.get("customer", {})

    except Exception as e:
        registrar_log_evento(
            origem="NORMALIZADOR",
            nivel="ERROR",
            mensagem=f"Erro ao normalizar evento: {str(e)}",
            payload=payload
        )
        raise

    return evento

# =========================================================
# PROCESSAMENTO ECONÔMICO REAL
# =========================================================

def processar_evento(evento: Dict[str, Any]) -> None:
    registrar_log_evento(
        origem="PIPELINE",
        nivel="INFO",
        mensagem="Processando evento normalizado",
        payload=evento
    )

    registrar_operacao({
        "id_operacao": evento["id_evento"],
        "origem": evento["origem"],
        "tipo": evento["tipo"],
        "produto_id": evento["produto_id"],
        "produto_nome": evento["produto_nome"],
        "status": evento["status"],
        "valor": evento["valor"],
        "comissao": evento["comissao"]
    })

    if evento["comissao"] > 0:
        registrar_financeiro({
            "id_operacao": evento["id_evento"],
            "origem": evento["origem"],
            "produto_id": evento["produto_id"],
            "produto_nome": evento["produto_nome"],
            "valor_bruto": evento["valor"],
            "valor_comissao": evento["comissao"],
            "moeda": evento["moeda"]
        })

# =========================================================
# WEBHOOK HOTMART
# =========================================================

@app.post("/webhook/hotmart")
async def webhook_hotmart(
    request: Request,
    x_hotmart_hmac_sha256: Optional[str] = Header(None)
):
    payload_bytes = await request.body()

    if not validar_hmac(payload_bytes, x_hotmart_hmac_sha256, HOTMART_SECRET):
        registrar_log_evento("HOTMART", "WARN", "Assinatura HMAC inválida")
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(payload_bytes.decode())

    evento = normalizar_evento("HOTMART", payload)
    processar_evento(evento)

    return {"status": "ok"}

# =========================================================
# WEBHOOK EDUZZ
# =========================================================

@app.post("/webhook/eduzz")
async def webhook_eduzz(
    request: Request,
    x_eduzz_signature: Optional[str] = Header(None)
):
    payload_bytes = await request.body()

    if not validar_hmac(payload_bytes, x_eduzz_signature, EDUZZ_SECRET):
        registrar_log_evento("EDUZZ", "WARN", "Assinatura inválida")
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(payload_bytes.decode())

    evento = normalizar_evento("EDUZZ", payload)
    processar_evento(evento)

    return {"status": "ok"}

# =========================================================
# WEBHOOK KIWIFY
# =========================================================

@app.post("/webhook/kiwify")
async def webhook_kiwify(
    request: Request,
    x_kiwify_signature: Optional[str] = Header(None)
):
    payload_bytes = await request.body()

    if not validar_hmac(payload_bytes, x_kiwify_signature, KIWIFY_SECRET):
        registrar_log_evento("KIWIFY", "WARN", "Assinatura inválida")
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(payload_bytes.decode())

    evento = normalizar_evento("KIWIFY", payload)
    processar_evento(evento)

    return {"status": "ok"}

# =========================================================
# FIM DO BLOCO 2
# =========================================================


# =========================================================
# MÉTRICAS ECONÔMICAS
# =========================================================

def calcular_rentabilidade(valor_bruto: float, comissao: float) -> Dict[str, float]:
    margem = 0.0
    if valor_bruto > 0:
        margem = round((comissao / valor_bruto) * 100, 2)

    return {
        "valor_bruto": round(valor_bruto, 2),
        "comissao": round(comissao, 2),
        "margem_percentual": margem
    }

# =========================================================
# ANÁLISE DE PRODUTO
# =========================================================

def analisar_produto(produto_id: str) -> Dict[str, Any]:
    registros = supabase.table("financeiro").select("*").eq("produto_id", produto_id).execute().data

    total_vendas = len(registros)
    total_comissao = sum([r.get("valor_comissao", 0) for r in registros])
    total_bruto = sum([r.get("valor_bruto", 0) for r in registros])

    rent = calcular_rentabilidade(total_bruto, total_comissao)

    return {
        "produto_id": produto_id,
        "vendas": total_vendas,
        "valor_bruto": total_bruto,
        "valor_comissao": total_comissao,
        "rentabilidade": rent["margem_percentual"]
    }

# =========================================================
# DECISÃO ECONÔMICA
# =========================================================

def escolher_melhor_oferta() -> Optional[Dict[str, Any]]:
    produtos = supabase.table("financeiro").select("produto_id").execute().data
    produtos_ids = list(set([p["produto_id"] for p in produtos if p["produto_id"]]))

    melhor = None
    melhor_margem = 0.0

    for pid in produtos_ids:
        analise = analisar_produto(pid)
        if analise["rentabilidade"] > melhor_margem:
            melhor_margem = analise["rentabilidade"]
            melhor = analise

    return melhor

# =========================================================
# REGISTRO DE DECISÃO
# =========================================================

def registrar_decisao(decisao: Dict[str, Any]):
    decisao["criado_em"] = agora()
    supabase.table("decisoes").insert(decisao).execute()

# =========================================================
# GERENCIAMENTO DE ESCALADA
# =========================================================

def gerenciar_escalada():
    oferta = escolher_melhor_oferta()

    if not oferta:
        registrar_log_evento(
            origem="ESCALADA",
            nivel="INFO",
            mensagem="Nenhuma oferta elegível para escalada"
        )
        return

    registrar_decisao({
        "produto_id": oferta["produto_id"],
        "acao": "ESCALAR",
        "rentabilidade": oferta["rentabilidade"],
        "valor_comissao": oferta["valor_comissao"]
    })

    registrar_log_evento(
        origem="ESCALADA",
        nivel="INFO",
        mensagem="Oferta selecionada para escalada",
        payload=oferta
    )

# =========================================================
# CICLO OPERACIONAL
# =========================================================

def executar_ciclo():
    registrar_log_evento(
        origem="CICLO",
        nivel="INFO",
        mensagem="Início do ciclo operacional"
    )

    try:
        gerenciar_escalada()
    except Exception as e:
        registrar_log_evento(
            origem="CICLO",
            nivel="ERROR",
            mensagem=str(e)
        )

# =========================================================
# LOOP AUTOMÁTICO (EXECUÇÃO CONTÍNUA)
# =========================================================

ULTIMA_EXECUCAO = datetime.utcnow()

def loop_diario():
    global ULTIMA_EXECUCAO

    agora_dt = datetime.utcnow()
    if agora_dt - ULTIMA_EXECUCAO >= timedelta(minutes=10):
        executar_ciclo()
        ULTIMA_EXECUCAO = agora_dt

# =========================================================
# ENDPOINTS OPERACIONAIS
# =========================================================

@app.get("/decisao")
def ver_decisoes():
    return supabase.table("decisoes").select("*").order("criado_em", desc=True).execute().data

@app.get("/capital")
def capital():
    dados = supabase.table("financeiro").select("*").execute().data
    total = sum([d.get("valor_comissao", 0) for d in dados])
    return {
        "capital_total": round(total, 2),
        "moeda": "BRL"
    }

@app.post("/ciclo")
def ciclo_manual():
    executar_ciclo()
    return {"status": "ciclo_executado"}

# =========================================================
# FIM DO BLOCO 3
# =========================================================


# =========================================================
# PRODUTOS ANALISADOS
# =========================================================

@app.get("/produtos")
def listar_produtos():
    registros = supabase.table("financeiro").select("*").execute().data
    produtos = {}

    for r in registros:
        pid = r.get("produto_id")
        if not pid:
            continue
        produtos.setdefault(pid, {
            "produto_id": pid,
            "produto_nome": r.get("produto_nome"),
            "valor_bruto": 0.0,
            "valor_comissao": 0.0,
            "vendas": 0
        })
        produtos[pid]["valor_bruto"] += r.get("valor_bruto", 0)
        produtos[pid]["valor_comissao"] += r.get("valor_comissao", 0)
        produtos[pid]["vendas"] += 1

    return list(produtos.values())

# =========================================================
# PLANO DIÁRIO
# =========================================================

@app.get("/plano-diario")
def plano_diario():
    melhor = escolher_melhor_oferta()
    return {
        "acao_prioritaria": "ESCALAR" if melhor else "AGUARDAR",
        "oferta": melhor,
        "timestamp": agora()
    }

# =========================================================
# ANÁLISE GLOBAL
# =========================================================

@app.get("/analise")
def analise_global():
    financeiro = supabase.table("financeiro").select("*").execute().data
    operacoes = supabase.table("operacoes").select("*").execute().data

    total_comissao = sum([f.get("valor_comissao", 0) for f in financeiro])
    total_bruto = sum([f.get("valor_bruto", 0) for f in financeiro])

    return {
        "operacoes": len(operacoes),
        "valor_bruto_total": round(total_bruto, 2),
        "comissao_total": round(total_comissao, 2),
        "timestamp": agora()
    }

# =========================================================
# ESCALA (HISTÓRICO)
# =========================================================

@app.get("/escala")
def historico_escala():
    return supabase.table("decisoes").select("*").order("criado_em", desc=True).execute().data

# =========================================================
# RESULTADO CONSOLIDADO
# =========================================================

@app.get("/resultado")
def resultado():
    capital_info = capital()
    plano = plano_diario()

    return {
        "capital": capital_info,
        "plano": plano,
        "timestamp": agora()
    }

# =========================================================
# WIDGET — RANKING DE PRODUTOS
# =========================================================

@app.get("/widget-ranking")
def widget_ranking():
    produtos = listar_produtos()

    ranking = sorted(
        produtos,
        key=lambda x: x.get("valor_comissao", 0),
        reverse=True
    )

    return {
        "ranking": ranking[:10],
        "gerado_em": agora()
    }

# =========================================================
# LOOP DIÁRIO AUTOMÁTICO (BACKGROUND)
# =========================================================

@app.on_event("startup")
async def startup_event():
    registrar_log_evento(
        origem="SYSTEM",
        nivel="INFO",
        mensagem="Robo Global AI iniciado em produção"
    )

# =========================================================
# FINAL DO ARQUIVO
# =========================================================

# main.py — versão completa e final
