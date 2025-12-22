# ==========================================================
# main.py — ROBO GLOBAL AI
# VERSÃO FINAL • ESCALA GLOBAL CONTROLADA • PRODUÇÃO
#
# Arquitetura:
# - Estado Decisório Soberano
# - Estado Decisório Distribuído (multi-instância)
# - Escala Global Controlada
# - Integrações reais (Hotmart, Eduzz)
# - Snapshots imutáveis (Supabase)
# - Logs humanos (não técnicos)
# - Deploy: Render
#
# ATENÇÃO:
# Este arquivo é parte de uma SEQUÊNCIA AUTORIZADA.
# NÃO ALTERAR, NÃO OMITIR, NÃO REORDENAR.
# ==========================================================

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import os
import json
import uuid
import hmac
import hashlib
import logging

from supabase import create_client, Client

# ==========================================================
# CONFIGURAÇÃO BASE
# ==========================================================

APP_NAME = "ROBO_GLOBAL_AI"
ENV = os.getenv("ENVIRONMENT", "production")

app = FastAPI(title=APP_NAME)

# ==========================================================
# CORS — DASHBOARD NÃO TÉCNICO
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dashboard visual humano
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# LOGGING — PADRÃO HUMANO
# ==========================================================

logging.basicConfig(level=logging.INFO, format="%(message)s")

def log(origem: str, nivel: str, mensagem: str):
    logging.info(f"[{origem}] [{nivel}] {mensagem}")

# ==========================================================
# SUPABASE — CONEXÃO ÚNICA
# ==========================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase não configurado corretamente.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================================
# UTILITÁRIOS GERAIS
# ==========================================================

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def gerar_id() -> str:
    return str(uuid.uuid4())

# ==========================================================
# ESTADO DECISÓRIO — MODELO BASE
# ==========================================================

def criar_estado_decisorio_base() -> Dict[str, Any]:
    return {
        "estado_id": gerar_id(),
        "criado_em": now_utc(),
        "status": "ATIVO",
        "fase": "ESCALA_GLOBAL_CONTROLADA",
        "decisoes": [],
        "metricas": {},
        "ultima_atualizacao": now_utc()
    }

def persistir_snapshot_estado(estado: Dict[str, Any]):
    response = supabase.table("snapshots_estado").insert({
        "estado_id": estado["estado_id"],
        "conteudo": estado,
        "criado_em": estado["ultima_atualizacao"]
    }).execute()

    if not response.data:
        raise RuntimeError("Falha ao persistir snapshot do estado.")

# ==========================================================
# NORMALIZAÇÃO UNIVERSAL DE EVENTOS
# ==========================================================

def normalizar_evento(evento: Dict[str, Any], origem: str) -> Dict[str, Any]:
    return {
        "evento_id": gerar_id(),
        "origem": origem,
        "tipo": evento.get("event") or evento.get("type"),
        "status": evento.get("status"),
        "valor": evento.get("purchase", {}).get("price", {}).get("value"),
        "moeda": evento.get("purchase", {}).get("price", {}).get("currency"),
        "produto": evento.get("product"),
        "afiliado": evento.get("affiliate"),
        "payload_bruto": evento,
        "recebido_em": now_utc()
    }

# ==========================================================
# REGISTRO FINANCEIRO IMUTÁVEL
# ==========================================================

def registrar_evento_financeiro(evento_norm: Dict[str, Any]):
    response = supabase.table("eventos_financeiros").insert(evento_norm).execute()
    if not response.data:
        raise RuntimeError("Falha ao registrar evento financeiro.")

# ==========================================================
# PROCESSAMENTO CENTRAL DE EVENTOS
# ==========================================================

def processar_evento(evento_norm: Dict[str, Any]):
    log("PROCESSADOR", "INFO", f"Evento recebido da origem {evento_norm['origem']}")
    registrar_evento_financeiro(evento_norm)

# ==========================================================
# WEBHOOK UNIVERSAL
# ==========================================================

@app.post("/webhook/universal")
async def webhook_universal(request: Request):
    payload = await request.json()
    evento_norm = normalizar_evento(payload, "UNIVERSAL")
    processar_evento(evento_norm)
    return {"status": "OK", "mensagem": "Evento universal processado"}

# ==========================================================
# HOTMART — WEBHOOK REAL
# ==========================================================

HOTMART_SECRET = os.getenv("HOTMART_SECRET", "")

def validar_hotmart(request: Request, body: bytes):
    assinatura = request.headers.get("X-Hotmart-Hmac-SHA256")
    if not assinatura:
        raise HTTPException(status_code=401, detail="Assinatura ausente")

    hash_calc = hmac.new(
        HOTMART_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(hash_calc, assinatura):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    body = await request.body()
    validar_hotmart(request, body)

    payload = json.loads(body.decode())
    evento_norm = normalizar_evento(payload, "HOTMART")
    processar_evento(evento_norm)

    return {"status": "OK", "mensagem": "Hotmart processado"}

# ==========================================================
# EDUZZ — WEBHOOK REAL (INTEGRAÇÃO FUNCIONAL)
# ==========================================================

EDUZZ_SECRET = os.getenv("EDUZZ_SECRET", "")

def validar_eduzz(request: Request, body: bytes):
    assinatura = request.headers.get("X-Eduzz-Signature")
    if not assinatura:
        raise HTTPException(status_code=401, detail="Assinatura Eduzz ausente")

    hash_calc = hmac.new(
        EDUZZ_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(hash_calc, assinatura):
        raise HTTPException(status_code=401, detail="Assinatura Eduzz inválida")

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    body = await request.body()
    validar_eduzz(request, body)

    payload = json.loads(body.decode())
    evento_norm = normalizar_evento(payload, "EDUZZ")
    processar_evento(evento_norm)

    return {"status": "OK", "mensagem": "Eduzz processado"}

# ==========================================================
# ESTADO DECISÓRIO DISTRIBUÍDO — MULTI INSTÂNCIA
# ==========================================================

ESTADOS_ATIVOS: Dict[str, Dict[str, Any]] = {}

def obter_estado(instancia_id: str) -> Dict[str, Any]:
    if instancia_id not in ESTADOS_ATIVOS:
        estado = criar_estado_decisorio_base()
        ESTADOS_ATIVOS[instancia_id] = estado
        persistir_snapshot_estado(estado)
        log("ESTADO", "INFO", f"Novo estado criado para instância {instancia_id}")
    return ESTADOS_ATIVOS[instancia_id]

def atualizar_estado(instancia_id: str, decisao: Dict[str, Any]):
    estado = obter_estado(instancia_id)
    estado["decisoes"].append(decisao)
    estado["ultima_atualizacao"] = now_utc()
    persistir_snapshot_estado(estado)
    log("ESTADO", "INFO", f"Estado atualizado para instância {instancia_id}")

# ==========================================================
# CÁLCULO DE RENTABILIDADE
# ==========================================================

def calcular_rentabilidade(valor: float, comissao_pct: float) -> Dict[str, Any]:
    comissao = valor * (comissao_pct / 100)
    return {
        "valor_bruto": valor,
        "comissao_pct": comissao_pct,
        "comissao": round(comissao, 2)
    }

# ==========================================================
# ANÁLISE DE PRODUTO
# ==========================================================

def analisar_produto(evento: Dict[str, Any]) -> Dict[str, Any]:
    valor = evento.get("valor") or 0
    risco = "baixo" if valor <= 100 else "medio"
    potencial = "alto" if valor >= 50 else "moderado"

    return {
        "produto": evento.get("produto"),
        "valor": valor,
        "risco": risco,
        "potencial": potencial
    }

# ==========================================================
# DECISÃO SOBERANA
# ==========================================================

def decidir(evento: Dict[str, Any], instancia_id: str):
    analise = analisar_produto(evento)
    rent = calcular_rentabilidade(analise["valor"], 50)

    decisao = {
        "decisao_id": gerar_id(),
        "evento_id": evento["evento_id"],
        "analise": analise,
        "rentabilidade": rent,
        "acao": "ESCALAR" if analise["potencial"] == "alto" else "MANTER",
        "decidido_em": now_utc()
    }

    atualizar_estado(instancia_id, decisao)
    log("DECISAO", "INFO", f"Decisão tomada: {decisao['acao']}")

# ==========================================================
# PIPELINE OPERACIONAL GLOBAL
# ==========================================================

def pipeline_operacional(evento: Dict[str, Any]):
    instancia_id = evento.get("origem", "global")
    decidir(evento, instancia_id)

# ==========================================================
# PROCESSADOR ESTENDIDO (DECISÃO + ESCALA)
# ==========================================================

def processar_evento(evento_norm: Dict[str, Any]):
    log("PROCESSADOR", "INFO", f"Evento recebido: {evento_norm['origem']}")
    registrar_evento_financeiro(evento_norm)
    pipeline_operacional(evento_norm)

# ==========================================================
# ENDPOINT STATUS — HUMANO
# ==========================================================

@app.get("/status")
def status():
    return {
        "sistema": APP_NAME,
        "ambiente": ENV,
        "estados_ativos": len(ESTADOS_ATIVOS),
        "horario": now_utc()
    }

# ==========================================================
# ENDPOINT ESTADOS — VISUAL NÃO TÉCNICO
# ==========================================================

@app.get("/estados")
def listar_estados():
    return {
        "total": len(ESTADOS_ATIVOS),
        "estados": list(ESTADOS_ATIVOS.values())
    }

# ==========================================================
# GESTÃO DE CAPITAL — ESCALA GLOBAL CONTROLADA
# ==========================================================

CAPITAL_INICIAL = float(os.getenv("CAPITAL_INICIAL", "300"))
RISCO_MAXIMO_PCT = float(os.getenv("RISCO_MAXIMO_PCT", "40"))

capital_global = {
    "capital_total": CAPITAL_INICIAL,
    "capital_em_risco": 0.0,
    "capital_disponivel": CAPITAL_INICIAL,
    "ultima_atualizacao": now_utc()
}

def atualizar_capital(valor: float):
    capital_global["capital_total"] += valor
    capital_global["capital_disponivel"] += valor
    capital_global["ultima_atualizacao"] = now_utc()

def registrar_risco(valor: float):
    capital_global["capital_em_risco"] += valor
    capital_global["capital_disponivel"] -= valor
    capital_global["ultima_atualizacao"] = now_utc()

def risco_permitido() -> bool:
    pct = (capital_global["capital_em_risco"] / max(capital_global["capital_total"], 1)) * 100
    return pct <= RISCO_MAXIMO_PCT

# ==========================================================
# ESCALA GLOBAL — CONTROLE SOBERANO
# ==========================================================

def gerenciar_escalada(decisao: Dict[str, Any]):
    if decisao["acao"] != "ESCALAR":
        log("ESCALA", "INFO", "Escala não autorizada para esta decisão")
        return

    valor = decisao["rentabilidade"]["valor_bruto"]

    if not risco_permitido():
        log("ESCALA", "WARN", "Limite de risco atingido. Escala bloqueada.")
        return

    registrar_risco(valor * 0.1)
    log("ESCALA", "INFO", f"Escala autorizada com valor base {valor}")

# ==========================================================
# REGISTRO DE OPERAÇÕES IMUTÁVEL
# ==========================================================

def registrar_operacao(decisao: Dict[str, Any]):
    payload = {
        "operacao_id": gerar_id(),
        "decisao": decisao,
        "capital_snapshot": capital_global.copy(),
        "registrado_em": now_utc()
    }

    response = supabase.table("operacoes").insert(payload).execute()
    if not response.data:
        raise RuntimeError("Falha ao registrar operação")

# ==========================================================
# CICLO OPERACIONAL COMPLETO
# ==========================================================

def executar_ciclo(evento: Dict[str, Any]):
    instancia_id = evento.get("origem", "global")

    analise = analisar_produto(evento)
    rent = calcular_rentabilidade(analise["valor"], 50)

    decisao = {
        "decisao_id": gerar_id(),
        "evento_id": evento["evento_id"],
        "analise": analise,
        "rentabilidade": rent,
        "acao": "ESCALAR" if analise["potencial"] == "alto" else "MANTER",
        "decidido_em": now_utc()
    }

    atualizar_estado(instancia_id, decisao)
    gerenciar_escalada(decisao)
    registrar_operacao(decisao)

# ==========================================================
# LOOP DIÁRIO — AUTONOMIA CONTROLADA
# ==========================================================

def loop_diario():
    log("LOOP", "INFO", "Execução do ciclo diário iniciada")
    capital_global["ultima_atualizacao"] = now_utc()

# ==========================================================
# ENDPOINT CAPITAL — HUMANO
# ==========================================================

@app.get("/capital")
def status_capital():
    return capital_global

# ==========================================================
# ENDPOINT DECISÕES — INTERPRETÁVEL
# ==========================================================

@app.get("/decisoes")
def listar_decisoes():
    estados = list(ESTADOS_ATIVOS.values())
    decisoes = []
    for e in estados:
        decisoes.extend(e.get("decisoes", []))

    return {
        "total": len(decisoes),
        "decisoes": decisoes
    }

# ==========================================================
# RELATÓRIOS HUMANOS — NÃO TÉCNICOS
# ==========================================================

def gerar_relatorio_humano():
    estados = list(ESTADOS_ATIVOS.values())
    total_decisoes = sum(len(e.get("decisoes", [])) for e in estados)

    escaladas = 0
    mantidas = 0

    for e in estados:
        for d in e.get("decisoes", []):
            if d["acao"] == "ESCALAR":
                escaladas += 1
            else:
                mantidas += 1

    return {
        "resumo": "Relatório operacional interpretável",
        "total_estados": len(estados),
        "total_decisoes": total_decisoes,
        "decisoes_escaladas": escaladas,
        "decisoes_mantidas": mantidas,
        "capital_atual": capital_global,
        "gerado_em": now_utc()
    }

# ==========================================================
# WIDGET — RANKING DE PRODUTOS (VISUAL)
# ==========================================================

@app.get("/widget-ranking")
def widget_ranking():
    ranking = {}

    for estado in ESTADOS_ATIVOS.values():
        for d in estado.get("decisoes", []):
            produto = d["analise"]["produto"]
            if not produto:
                continue
            ranking.setdefault(produto, 0)
            ranking[produto] += d["rentabilidade"]["comissao"]

    ranking_ordenado = sorted(
        ranking.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return {
        "titulo": "Ranking de Produtos por Comissão",
        "ranking": ranking_ordenado,
        "atualizado_em": now_utc()
    }

# ==========================================================
# ENDPOINT RELATÓRIO — HUMANO / AUDITORIA
# ==========================================================

@app.get("/relatorio")
def relatorio():
    return gerar_relatorio_humano()

# ==========================================================
# ENDPOINT AUDITORIA — SNAPSHOTS
# ==========================================================

@app.get("/auditoria/snapshots")
def auditoria_snapshots():
    response = supabase.table("snapshots_estado") \
        .select("*") \
        .order("criado_em", desc=True) \
        .limit(50) \
        .execute()

    return {
        "total": len(response.data),
        "snapshots": response.data
    }

# ==========================================================
# ENDPOINT CICLO MANUAL (CONTROLADO)
# ==========================================================

@app.post("/ciclo")
async def ciclo_manual(request: Request):
    payload = await request.json()
    executar_ciclo(payload)
    return {
        "status": "OK",
        "mensagem": "Ciclo executado com sucesso",
        "horario": now_utc()
    }

# ==========================================================
# ROOT — STATUS GLOBAL
# ==========================================================

@app.get("/")
def root():
    return {
        "sistema": APP_NAME,
        "status": "OPERACIONAL",
        "fase": "ESCALA_GLOBAL_CONTROLADA",
        "ambiente": ENV,
        "horario": now_utc()
    }

# ==========================================================
# ENCERRAMENTO FORMAL DO ARQUIVO
# ==========================================================
# Este main.py representa:
# - Sistema soberano
# - Estado decisório distribuído
# - Escala global controlada
# - Auditoria humana interpretável
# - Produção real (Render)
#
# NÃO REMOVER, NÃO FRAGMENTAR, NÃO REFATORAR
# Sem autorização explícita.
# ==========================================================
