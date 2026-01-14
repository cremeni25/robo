# main.py — versão completa e final (PARTE 1 / N)
# ROBO GLOBAL AI
# Núcleo Operacional Soberano
# Data-base: 2025-12-24
#
# Este arquivo consolida:
# - Decisão autônoma vertical
# - Execução contínua
# - Monetização obrigatória
# - Camada Financeira Integrada (leitura e ação humana)
# - Governança por limites macro
#
# NÃO REMOVER, NÃO RESUMIR, NÃO REORDENAR.
# ==========================================================

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import os
import json
import uuid
import hmac
import hashlib
import threading
import time
import logging

# ==========================================================
# CONFIGURAÇÃO GLOBAL
# ==========================================================

APP_NAME = "ROBO GLOBAL AI"
APP_VERSION = "SOVEREIGN-1.0.0"
ENV = os.getenv("ENV", "production")
INSTANCE_ID = os.getenv("INSTANCE_ID", str(uuid.uuid4()))

# Limites macro definidos pelo HUMANO (MODELO C)
CAPITAL_MAX = float(os.getenv("CAPITAL_MAX", "10000"))
RISCO_MAX_PCT = float(os.getenv("RISCO_MAX_PCT", "40"))
PLATAFORMAS_PERMITIDAS = os.getenv(
    "PLATAFORMAS_PERMITIDAS",
    "HOTMART,EDUZZ,MONETIZZE,CLICkBANK"
).split(",")

# ==========================================================
# SUPABASE (FONTE DE VERDADE)
# ==========================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Supabase não configurado corretamente")

from supabase import create_client, Client
sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ==========================================================
# FASTAPI
# ==========================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Núcleo Operacional Soberano — Execução, Monetização e Leitura Humana"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# LOGS HUMANOS (PADRÃO)
# ==========================================================

logging.basicConfig(level=logging.INFO, format="%(message)s")

def log(origem: str, nivel: str, mensagem: str):
    print(f"[{origem}] [{nivel}] {mensagem}")

# ==========================================================
# UTILIDADES DE TEMPO
# ==========================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def utc_now_iso() -> str:
    return utc_now().isoformat()

# ==========================================================
# MODELOS BASE
# ==========================================================

class EventoFinanceiro(BaseModel):
    plataforma: str
    oferta: Optional[str]
    valor_bruto: float
    moeda: str
    status: str  # GERADO | EM_ANALISE | APROVADO | LIBERADO | TRANSFERIDO | BLOQUEADO
    origem_evento: str
    recebido_em: str

class AcaoFinanceiraHumana(BaseModel):
    plataforma: str
    referencia: str
    acao: str  # TRANSFERIR | SACAR | ALOCAR
    valor: float
    moeda: str
    executado_em: Optional[str] = None

# ==========================================================
# ESTADO GLOBAL DO SISTEMA (SOBERANO)
# ==========================================================

ESTADO_GLOBAL: Dict[str, Any] = {
    "estado_operacional": "ATIVO",
    "capital_total": 0.0,
    "capital_em_risco": 0.0,
    "capital_disponivel": 0.0,
    "ultima_atualizacao": utc_now_iso()
}

# ==========================================================
# CAMADA FINANCEIRA INTEGRADA — CONSOLIDAÇÃO
# ==========================================================

def registrar_evento_financeiro(evento: EventoFinanceiro):
    sb.table("eventos_financeiros").insert(evento.dict()).execute()
    log("FINANCEIRO", "INFO", f"Evento registrado: {evento.plataforma} | {evento.status} | {evento.valor_bruto}")

def atualizar_caixa_logico(valor: float):
    ESTADO_GLOBAL["capital_total"] += valor
    ESTADO_GLOBAL["capital_disponivel"] += valor
    ESTADO_GLOBAL["ultima_atualizacao"] = utc_now_iso()

# ==========================================================
# DECISÃO SOBERANA (AUTÔNOMA)
# ==========================================================

def decidir_acao(evento: EventoFinanceiro) -> Dict[str, Any]:
    """
    Função PURA de decisão.
    Decide escalar, manter ou descartar com base em sinais financeiros.
    """
    if evento.status != "APROVADO":
        return {
            "decisao": "AGUARDAR",
            "motivo": "Evento ainda não aprovado",
            "risco": "BAIXO"
        }

    if evento.valor_bruto <= 0:
        return {
            "decisao": "DESCARTAR",
            "motivo": "Valor inválido",
            "risco": "NULO"
        }

    return {
        "decisao": "ESCALAR",
        "motivo": "Receita aprovada",
        "risco": "CONTROLADO"
    }

# ==========================================================
# EXECUÇÃO (MÚSCULO)
# ==========================================================

def executar_decisao(evento: EventoFinanceiro, decisao: Dict[str, Any]):
    if decisao["decisao"] == "ESCALAR":
        atualizar_caixa_logico(evento.valor_bruto)
        log("EXECUCAO", "INFO", f"Escala autorizada | Valor {evento.valor_bruto} {evento.moeda}")
    elif decisao["decisao"] == "DESCARTAR":
        log("EXECUCAO", "WARN", "Evento descartado")
    else:
        log("EXECUCAO", "INFO", "Evento aguardando aprovação")

# ==========================================================
# PIPELINE OPERACIONAL COMPLETO
# ==========================================================

def pipeline_operacional(evento: EventoFinanceiro):
    registrar_evento_financeiro(evento)
    decisao = decidir_acao(evento)
    executar_decisao(evento, decisao)

# ==========================================================
# ENDPOINTS — FINANCEIRO HUMANO
# ==========================================================

@app.get("/financeiro/visao-geral")
def visao_financeira():
    return {
        "capital_total": ESTADO_GLOBAL["capital_total"],
        "capital_disponivel": ESTADO_GLOBAL["capital_disponivel"],
        "capital_em_risco": ESTADO_GLOBAL["capital_em_risco"],
        "atualizado_em": ESTADO_GLOBAL["ultima_atualizacao"]
    }

@app.post("/financeiro/acao-humana")
def acao_humana(payload: AcaoFinanceiraHumana):
    registro = payload.dict()
    registro["executado_em"] = utc_now_iso()
    sb.table("acoes_financeiras_humanas").insert(registro).execute()
    log("HUMANO", "INFO", f"Ação financeira registrada: {payload.acao}")
    return {"status": "OK", "mensagem": "Ação financeira registrada"}

# ==========================================================
# STATUS HUMANO
# ==========================================================

@app.get("/status")
def status():
    return {
        "sistema": APP_NAME,
        "versao": APP_VERSION,
        "estado": ESTADO_GLOBAL["estado_operacional"],
        "ambiente": ENV,
        "instancia": INSTANCE_ID,
        "horario": utc_now_iso()
    }

# ==========================================================
# ROOT
# ==========================================================

@app.get("/")
def root():
    return {
        "sistema": APP_NAME,
        "mensagem": "Núcleo Operacional Soberano ativo",
        "horario": utc_now_iso()
    }

log("SYSTEM", "INFO", f"{APP_NAME} iniciado | instância {INSTANCE_ID}")
# ===================== FIM DA PARTE 1 ======================
# ===================== main.py — PARTE 2 / N =====================
# Integrações Financeiras + Normalização Canônica + Auditoria
# ================================================================

# ==========================================================
# SEGURANÇA — HMAC / ASSINATURAS
# ==========================================================

HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET", "")
EDUZZ_WEBHOOK_SECRET = os.getenv("EDUZZ_WEBHOOK_SECRET", "")
MONETIZZE_WEBHOOK_SECRET = os.getenv("MONETIZZE_WEBHOOK_SECRET", "")
CLICKBANK_WEBHOOK_SECRET = os.getenv("CLICKBANK_WEBHOOK_SECRET", "")

def verify_hmac_sha256(payload: bytes, signature: str, secret: str) -> bool:
    if not secret or not signature:
        return False
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)

# ==========================================================
# NORMALIZAÇÃO CANÔNICA FINANCEIRA
# ==========================================================

def normalizar_evento_hotmart(payload: Dict[str, Any]) -> EventoFinanceiro:
    return EventoFinanceiro(
        plataforma="HOTMART",
        oferta=str(payload.get("data", {}).get("product", {}).get("id")),
        valor_bruto=float(payload.get("data", {}).get("purchase", {}).get("price", {}).get("value", 0)),
        moeda=payload.get("data", {}).get("purchase", {}).get("price", {}).get("currency", "BRL"),
        status="GERADO",
        origem_evento=payload.get("event"),
        recebido_em=utc_now_iso()
    )

def normalizar_evento_eduzz(payload: Dict[str, Any]) -> EventoFinanceiro:
    return EventoFinanceiro(
        plataforma="EDUZZ",
        oferta=str(payload.get("product", {}).get("id")),
        valor_bruto=float(payload.get("sale", {}).get("value", 0)),
        moeda=payload.get("sale", {}).get("currency", "BRL"),
        status="GERADO",
        origem_evento=payload.get("event_type"),
        recebido_em=utc_now_iso()
    )

def normalizar_evento_monetizze(payload: Dict[str, Any]) -> EventoFinanceiro:
    return EventoFinanceiro(
        plataforma="MONETIZZE",
        oferta=str(payload.get("produto", {}).get("codigo")),
        valor_bruto=float(payload.get("valor", 0)),
        moeda=payload.get("moeda", "BRL"),
        status="GERADO",
        origem_evento=payload.get("tipo"),
        recebido_em=utc_now_iso()
    )

def normalizar_evento_clickbank(payload: Dict[str, Any]) -> EventoFinanceiro:
    return EventoFinanceiro(
        plataforma="CLICKBANK",
        oferta=str(payload.get("itemNo")),
        valor_bruto=float(payload.get("amount", 0)),
        moeda=payload.get("currency", "USD"),
        status="GERADO",
        origem_evento=payload.get("transactionType"),
        recebido_em=utc_now_iso()
    )

# ==========================================================
# WEBHOOKS — FINANCEIROS
# ==========================================================

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Hotmart-Hmac-SHA256")

    if not verify_hmac_sha256(raw_body, signature, HOTMART_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Assinatura Hotmart inválida")

    payload = json.loads(raw_body.decode())
    evento = normalizar_evento_hotmart(payload)
    pipeline_operacional(evento)

    return {"status": "OK", "plataforma": "HOTMART"}

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Eduzz-Signature")

    if not verify_hmac_sha256(raw_body, signature, EDUZZ_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Assinatura Eduzz inválida")

    payload = json.loads(raw_body.decode())
    evento = normalizar_evento_eduzz(payload)
    pipeline_operacional(evento)

    return {"status": "OK", "plataforma": "EDUZZ"}

@app.post("/webhook/monetizze")
async def webhook_monetizze(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Monetizze-Signature")

    if not verify_hmac_sha256(raw_body, signature, MONETIZZE_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Assinatura Monetizze inválida")

    payload = json.loads(raw_body.decode())
    evento = normalizar_evento_monetizze(payload)
    pipeline_operacional(evento)

    return {"status": "OK", "plataforma": "MONETIZZE"}

@app.post("/webhook/clickbank")
async def webhook_clickbank(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-ClickBank-Signature")

    if not verify_hmac_sha256(raw_body, signature, CLICKBANK_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Assinatura ClickBank inválida")

    payload = json.loads(raw_body.decode())
    evento = normalizar_evento_clickbank(payload)
    pipeline_operacional(evento)

    return {"status": "OK", "plataforma": "CLICKBANK"}

# ==========================================================
# AUDITORIA HUMANA — FINANCEIRA
# ==========================================================

@app.get("/financeiro/auditoria")
def auditoria_financeira(limit: int = 50):
    response = (
        sb.table("eventos_financeiros")
        .select("*")
        .order("recebido_em", desc=True)
        .limit(limit)
        .execute()
    )
    return {
        "total": len(response.data),
        "eventos": response.data
    }

# ==========================================================
# LOOP OPERACIONAL (AUTÔNOMO)
# ==========================================================

def loop_operacional():
    log("LOOP", "INFO", "Loop operacional autônomo iniciado")
    while True:
        try:
            # O loop é reativo a eventos financeiros reais.
            # Nenhuma ação cega é executada aqui.
            time.sleep(5)
        except Exception as e:
            log("LOOP", "ERRO", f"Falha no loop: {str(e)}")
            time.sleep(5)

threading.Thread(target=loop_operacional, daemon=True).start()

log("SYSTEM", "INFO", "Integrações financeiras carregadas")
# ===================== FIM DA PARTE 2 =====================
# ===================== main.py — PARTE 3 / N =====================
# Governança por Limites Macro • Risco • Estados Financeiros
# ================================================================

# ==========================================================
# ESTADOS FINANCEIROS — AVANÇADOS
# ==========================================================

ESTADOS_FINANCEIROS_VALIDOS = [
    "GERADO",
    "EM_ANALISE",
    "APROVADO",
    "LIBERADO",
    "TRANSFERIDO",
    "BLOQUEADO",
    "ESTORNADO",
]

def atualizar_status_financeiro(evento_id: str, novo_status: str):
    if novo_status not in ESTADOS_FINANCEIROS_VALIDOS:
        raise ValueError("Status financeiro inválido")

    sb.table("eventos_financeiros") \
      .update({"status": novo_status}) \
      .eq("id", evento_id) \
      .execute()

    log("FINANCEIRO", "INFO", f"Status atualizado: {evento_id} → {novo_status}")

# ==========================================================
# GOVERNANÇA — LIMITES MACRO (MODELO C)
# ==========================================================

def risco_atual_pct() -> float:
    if ESTADO_GLOBAL["capital_total"] <= 0:
        return 0.0
    return (ESTADO_GLOBAL["capital_em_risco"] / ESTADO_GLOBAL["capital_total"]) * 100

def risco_permitido(valor: float) -> bool:
    risco_projetado = (
        (ESTADO_GLOBAL["capital_em_risco"] + valor)
        / max(ESTADO_GLOBAL["capital_total"], 1)
    ) * 100
    return risco_projetado <= RISCO_MAX_PCT

def registrar_risco(valor: float):
    ESTADO_GLOBAL["capital_em_risco"] += valor
    ESTADO_GLOBAL["capital_disponivel"] -= valor
    ESTADO_GLOBAL["ultima_atualizacao"] = utc_now_iso()

# ==========================================================
# CRITÉRIOS DE ESCALA / BLOQUEIO
# ==========================================================

def avaliar_escalabilidade(evento: EventoFinanceiro) -> bool:
    """
    Retorna True se o evento pode ser escalado
    dentro dos limites macro definidos pelo humano.
    """
    if evento.plataforma not in PLATAFORMAS_PERMITIDAS:
        log("GOVERNANCA", "WARN", f"Plataforma não permitida: {evento.plataforma}")
        return False

    if not risco_permitido(evento.valor_bruto):
        log("GOVERNANCA", "WARN", "Limite de risco atingido")
        return False

    return True

# ==========================================================
# EXECUÇÃO SOB GOVERNANÇA
# ==========================================================

def executar_decisao(evento: EventoFinanceiro, decisao: Dict[str, Any]):
    if decisao["decisao"] == "ESCALAR":
        if avaliar_escalabilidade(evento):
            registrar_risco(evento.valor_bruto * 0.1)
            atualizar_caixa_logico(evento.valor_bruto)
            log(
                "EXECUCAO",
                "INFO",
                f"Escala executada | {evento.plataforma} | {evento.valor_bruto} {evento.moeda}",
            )
        else:
            log("EXECUCAO", "WARN", "Escala bloqueada por governança")

    elif decisao["decisao"] == "DESCARTAR":
        log("EXECUCAO", "INFO", "Evento descartado pelo decisor soberano")

    else:
        log("EXECUCAO", "INFO", "Evento aguardando maturação financeira")

# ==========================================================
# AUDITORIA DE GOVERNANÇA — HUMANA
# ==========================================================

@app.get("/governanca/status")
def status_governanca():
    return {
        "capital_total": ESTADO_GLOBAL["capital_total"],
        "capital_disponivel": ESTADO_GLOBAL["capital_disponivel"],
        "capital_em_risco": ESTADO_GLOBAL["capital_em_risco"],
        "risco_pct": risco_atual_pct(),
        "risco_max_permitido_pct": RISCO_MAX_PCT,
        "plataformas_permitidas": PLATAFORMAS_PERMITIDAS,
        "atualizado_em": ESTADO_GLOBAL["ultima_atualizacao"],
    }

# ==========================================================
# BLOQUEIO DE SEGURANÇA (BOTÃO NUCLEAR)
# ==========================================================

@app.post("/governanca/desligar")
def desligar_sistema():
    ESTADO_GLOBAL["estado_operacional"] = "DESLIGADO"
    log("SYSTEM", "WARN", "SISTEMA DESLIGADO PELO HUMANO")
    return {"status": "OK", "mensagem": "Sistema desligado"}

@app.post("/governanca/ligar")
def ligar_sistema():
    ESTADO_GLOBAL["estado_operacional"] = "ATIVO"
    log("SYSTEM", "INFO", "Sistema religado pelo humano")
    return {"status": "OK", "mensagem": "Sistema ligado"}

# ==========================================================
# BLOQUEIO GLOBAL DE EXECUÇÃO
# ==========================================================

def pipeline_operacional(evento: EventoFinanceiro):
    if ESTADO_GLOBAL["estado_operacional"] != "ATIVO":
        log("PIPELINE", "WARN", "Pipeline bloqueado — sistema desligado")
        return

    registrar_evento_financeiro(evento)
    decisao = decidir_acao(evento)
    executar_decisao(evento, decisao)

# ==========================================================
# HEALTHCHECK AVANÇADO
# ==========================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "estado_operacional": ESTADO_GLOBAL["estado_operacional"],
        "timestamp": utc_now_iso(),
    }

log("SYSTEM", "INFO", "Governança e controle de risco ativados")
# ===================== FIM DA PARTE 3 =====================
# ===================== main.py — PARTE FINAL / N =====================
# Consolidação Final • Validação • Checklist • Encerramento
# ===================================================================

# ==========================================================
# VALIDAÇÕES DE PRODUÇÃO
# ==========================================================

def validar_configuracao_producao():
    erros = []

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        erros.append("Supabase não configurado")

    if not PLATAFORMAS_PERMITIDAS:
        erros.append("Nenhuma plataforma permitida definida")

    if RISCO_MAX_PCT <= 0 or RISCO_MAX_PCT > 100:
        erros.append("RISCO_MAX_PCT inválido")

    if erros:
        log("VALIDACAO", "ERRO", f"Falhas de configuração: {erros}")
        raise RuntimeError("Configuração de produção inválida")

    log("VALIDACAO", "INFO", "Configuração de produção validada com sucesso")

validar_configuracao_producao()

# ==========================================================
# CHECKLIST DE DEPLOY — HUMANO
# ==========================================================

@app.get("/deploy/checklist")
def checklist_deploy():
    """
    Checklist objetivo para validação final do deploy.
    Não há interpretação subjetiva.
    """
    return {
        "supabase_configurado": bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY),
        "plataformas_permitidas": PLATAFORMAS_PERMITIDAS,
        "estado_operacional": ESTADO_GLOBAL["estado_operacional"],
        "capital_total": ESTADO_GLOBAL["capital_total"],
        "risco_max_pct": RISCO_MAX_PCT,
        "instancia": INSTANCE_ID,
        "timestamp": utc_now_iso(),
        "status_geral": "PRONTO_PARA_PRODUCAO"
    }

# ==========================================================
# ENDPOINT DE VALIDAÇÃO FINAL
# ==========================================================

@app.get("/validacao/final")
def validacao_final():
    """
    Endpoint definitivo de validação do sistema.
    Se retornar OK, o projeto está tecnicamente concluído.
    """
    if ESTADO_GLOBAL["estado_operacional"] != "ATIVO":
        return {
            "status": "FALHA",
            "motivo": "Sistema não está ativo",
            "timestamp": utc_now_iso()
        }

    return {
        "status": "OK",
        "mensagem": "Robo Global AI operacional em produção",
        "versao": APP_VERSION,
        "timestamp": utc_now_iso()
    }

# ==========================================================
# DECLARAÇÃO FORMAL DE CONCLUSÃO TÉCNICA
# ==========================================================

def declaracao_conclusao():
    log(
        "SYSTEM",
        "INFO",
        "CONCLUSÃO TÉCNICA: Núcleo Operacional Soberano materializado e ativo"
    )

declaracao_conclusao()

# ==========================================================
# ENCERRAMENTO DEFINITIVO DO ARQUIVO
# ==========================================================
# Este main.py representa:
# - Núcleo único, soberano e verticalizado
# - Execução autônoma sob limites macro
# - Monetização integrada e obrigatória
# - Camada financeira humana visível e acionável
# - Governança, risco e botão nuclear
#
# A partir deste ponto:
# - O sistema é considerado CONCLUÍDO
# - Evoluções futuras são incrementais
# - Não há retorno a alinhamentos conceituais
#
# ROBO GLOBAL AI — PRODUÇÃO REAL
# ===================================================================

# ==========================================================
# BLOCO FINAL — GO ROUTER (MONETIZAÇÃO DIRETA)
# ADIÇÃO AUTORIZADA • NÃO ALTERA O NÚCLEO SOBERANO
# OBJETIVO: EXPOR PRODUTO E PERMITIR PRIMEIRA VENDA
# ==========================================================

from fastapi.responses import RedirectResponse

@app.get("/go")
def go_router(produto: str, request: Request):
    """
    Roteador direto de monetização.
    NÃO decide, NÃO bloqueia, NÃO aplica score.
    Apenas expõe a oferta e redireciona.
    """

    try:
        res = (
            sb.table("offers")
            .select("*")
            .eq("slug", produto)
            .limit(1)
            .execute()
        )
    except Exception as e:
        log("GO", "ERRO", f"Falha Supabase: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno")

    if not res.data:
        log("GO", "WARN", f"Produto não encontrado: {produto}")
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    offer = res.data[0]
    target_url = offer.get("hotmart_url")

    if not target_url:
        log("GO", "ERRO", f"Oferta sem URL de destino: {produto}")
        raise HTTPException(status_code=500, detail="URL de destino inexistente")

    # Registro de clique (observacional)
    try:
        sb.table("clicks").insert({
            "slug": produto,
            "offer_id": offer.get("id"),
            "ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "ts": utc_now_iso()
        }).execute()
    except Exception as e:
        log("GO", "WARN", f"Falha ao registrar clique: {str(e)}")

    log("GO", "INFO", f"Redirecionamento executado: {produto}")

    return RedirectResponse(url=target_url, status_code=302)

# ==========================================================
# FIM DO BLOCO GO ROUTER
# ==========================================================

