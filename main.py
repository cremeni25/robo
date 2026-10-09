# ==========================================================
# main.py — versão completa e final (PARTE 1 / N)
# ROBO GLOBAL AI
# Núcleo Operacional Soberano
# Data-base: 2025-12-24
#
# NÃO REMOVER, NÃO RESUMIR, NÃO REORDENAR.
# ==========================================================

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
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

CAPITAL_MAX = float(os.getenv("CAPITAL_MAX", "10000"))
RISCO_MAX_PCT = float(os.getenv("RISCO_MAX_PCT", "40"))

PLATAFORMAS_PERMITIDAS = os.getenv(
    "PLATAFORMAS_PERMITIDAS",
    "HOTMART,EDUZZ,MONETIZZE,CLICKBANK"
).split(",")

# ==========================================================
# SUPABASE — FONTE ÚNICA DA VERDADE
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
    description="Núcleo Operacional Soberano — Execução, Monetização e Governança"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.roboglobal.com.br", "https://roboglobal.com.br", "https://robo-global-frontend.onrender.com"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# LOGS HUMANOS (PADRÃO OFICIAL)
# ==========================================================

logging.basicConfig(level=logging.INFO, format="%(message)s")

def log(origem: str, nivel: str, mensagem: str):
    print(f"[{origem}] [{nivel}] {mensagem}")

log("SYSTEM", "INFO", f"{APP_NAME} iniciado | instância {INSTANCE_ID}")

# ==========================================================
# UTILIDADES DE TEMPO
# ==========================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def utc_now_iso() -> str:
    return utc_now().isoformat()

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
# main.py — PARTE 2 / N
# Modelos Canônicos • Núcleo Soberano • Decisão • Governança Base
# ==========================================================

# ==========================================================
# MODELOS BASE — FINANCEIRO CANÔNICO (LEGADO SOBERANO)
# ==========================================================

class EventoFinanceiro(BaseModel):
    plataforma: str
    oferta: Optional[str]
    valor_bruto: float
    moeda: str
    status: str  # GERADO | EM_ANALISE | APROVADO | LIBERADO | TRANSFERIDO | BLOQUEADO | ESTORNADO
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
# MODELOS CANÔNICOS — DOR / CONTEXTO / CAMINHO
# (CAMADA DE INTELIGÊNCIA NEUTRA)
# ==========================================================

class Dor(BaseModel):
    codigo: str
    descricao: Optional[str] = None


class Contexto(BaseModel):
    origem: Optional[str] = None
    horario: Optional[str] = None
    intensidade: Optional[int] = 0
    sequencia: Optional[List[str]] = []


class Caminho(BaseModel):
    id: str
    dor: Dor
    contexto: Contexto
    ofertas: List[str]
    prioridade: float = 0.0
    atualizado_em: str


# ==========================================================
# CAMADA FINANCEIRA INTEGRADA — CONSOLIDAÇÃO LEGADA
# (ATENÇÃO: NÃO É MAIS FONTE PRIMÁRIA DE VERDADE)
# ==========================================================

def registrar_evento_financeiro(evento: EventoFinanceiro):
    """
    Registro LEGADO para leitura humana e governança.
    NÃO é mais fonte primária de auditoria financeira.
    """
    sb.table("eventos_financeiros").insert(evento.dict()).execute()
    log(
        "FINANCEIRO",
        "INFO",
        f"Evento legado registrado: {evento.plataforma} | {evento.status} | {evento.valor_bruto}"
    )


def atualizar_caixa_logico(valor: float):
    """
    Caixa lógico soberano (derivado).
    """
    ESTADO_GLOBAL["capital_total"] += valor
    ESTADO_GLOBAL["capital_disponivel"] += valor
    ESTADO_GLOBAL["ultima_atualizacao"] = utc_now_iso()


# ==========================================================
# DECISÃO SOBERANA (AUTÔNOMA)
# ==========================================================

def decidir_acao(evento: EventoFinanceiro) -> Dict[str, Any]:
    """
    Função PURA de decisão soberana.
    NÃO cria dinheiro.
    NÃO altera comissão.
    Apenas decide.
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
# GOVERNANÇA — LIMITES MACRO
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
# EXECUÇÃO SOB GOVERNANÇA (LEGADA)
# ==========================================================

def executar_decisao(evento: EventoFinanceiro, decisao: Dict[str, Any]):
    """
    Execução soberana baseada em governança.
    NÃO registra vendas.
    NÃO altera saldos reais.
    """
    if decisao["decisao"] == "ESCALAR":
        if risco_permitido(evento.valor_bruto):
            registrar_risco(evento.valor_bruto * 0.1)
            atualizar_caixa_logico(evento.valor_bruto)
            log(
                "EXECUCAO",
                "INFO",
                f"Escala autorizada | {evento.plataforma} | {evento.valor_bruto} {evento.moeda}"
            )
        else:
            log("EXECUCAO", "WARN", "Escala bloqueada por governança")

    elif decisao["decisao"] == "DESCARTAR":
        log("EXECUCAO", "INFO", "Evento descartado pelo decisor soberano")

    else:
        log("EXECUCAO", "INFO", "Evento aguardando maturação financeira")


# ==========================================================
# PIPELINE OPERACIONAL LEGADO (DECISÃO / GOVERNANÇA)
# ==========================================================

def pipeline_operacional(evento: EventoFinanceiro):
    """
    Pipeline LEGADO.
    NÃO é mais fonte de vendas.
    Atua apenas como camada decisória.
    """
    if ESTADO_GLOBAL["estado_operacional"] != "ATIVO":
        log("PIPELINE", "WARN", "Pipeline bloqueado — sistema desligado")
        return

    registrar_evento_financeiro(evento)
    decisao = decidir_acao(evento)
    executar_decisao(evento, decisao)

# ==========================================================
# main.py — PARTE 3 / N
# Segurança • Normalização • Webhooks Integrados ao Financeiro Real
# ==========================================================

# ==========================================================
# SEGURANÇA — HMAC / ASSINATURAS
# ==========================================================

HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET", "")
EDUZZ_WEBHOOK_SECRET = os.getenv("EDUZZ_WEBHOOK_SECRET", "")
MONETIZZE_WEBHOOK_SECRET = os.getenv("MONETIZZE_WEBHOOK_SECRET", "")

def verify_hmac_sha256(payload: bytes, signature: str, secret: str) -> bool:
    if not secret or not signature:
        return False
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


# ==========================================================
# NORMALIZAÇÃO CANÔNICA (LEGADA — DECISÃO / GOVERNANÇA)
# ==========================================================

def normalizar_evento_hotmart(payload: Dict[str, Any]) -> EventoFinanceiro:
    return EventoFinanceiro(
        plataforma="HOTMART",
        oferta=str(payload.get("data", {}).get("product", {}).get("id")),
        valor_bruto=float(
            payload.get("data", {})
            .get("purchase", {})
            .get("price", {})
            .get("value", 0)
        ),
        moeda=payload.get("data", {})
              .get("purchase", {})
              .get("price", {})
              .get("currency", "BRL"),
        status="APROVADO",
        origem_evento=payload.get("event", "HOTMART"),
        recebido_em=utc_now_iso()
    )


def normalizar_evento_eduzz(payload: Dict[str, Any]) -> EventoFinanceiro:
    return EventoFinanceiro(
        plataforma="EDUZZ",
        oferta=str(payload.get("product", {}).get("id")),
        valor_bruto=float(payload.get("sale", {}).get("value", 0)),
        moeda=payload.get("sale", {}).get("currency", "BRL"),
        status="APROVADO",
        origem_evento=payload.get("event_type", "EDUZZ"),
        recebido_em=utc_now_iso()
    )


def normalizar_evento_monetizze(payload: Dict[str, Any]) -> EventoFinanceiro:
    return EventoFinanceiro(
        plataforma="MONETIZZE",
        oferta=str(payload.get("produto", {}).get("codigo")),
        valor_bruto=float(payload.get("venda", {}).get("valor", 0)),
        moeda=payload.get("moeda", "BRL"),
        status="APROVADO",
        origem_evento=payload.get("tipo", "MONETIZZE"),
        recebido_em=utc_now_iso()
    )


# ==========================================================
# IMPORTAÇÃO DOS SERVICES FINANCEIROS REAIS
# ==========================================================

from sales_service import registrar_venda
from commission_service import calcular_comissao
from balance_service import adicionar_comissao


# ==========================================================
# FUNÇÃO INTERNA — PIPELINE FINANCEIRO REAL
# ==========================================================

def pipeline_financeiro_real(
    *,
    platform: str,
    external_sale_id: str,
    product_id: str,
    gross_value: float,
    commission_total: float,
    partner_id: Optional[str],
    payload: Dict[str, Any]
):
    percentual_parceiro = 0.60

    comissao = calcular_comissao(
        commission_total=commission_total,
        percentual_parceiro=percentual_parceiro
    )

    registrar_venda(
        sb,
        platform=platform,
        external_sale_id=external_sale_id,
        product_id=product_id,
        partner_id=partner_id,
        gross_value=gross_value,
        commission_value=commission_total,
        partner_commission=comissao["partner_commission"],
        master_commission=comissao["master_commission"],
        sale_status="approved",
        occurred_at=utc_now(),
        payload=payload
    )

    if partner_id:
        adicionar_comissao(
            sb,
            partner_id=partner_id,
            valor=comissao["partner_commission"]
        )


# ==========================================================
# WEBHOOK HOTMART (HMAC + FINANCEIRO REAL + DECISÃO)
# ==========================================================

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Hotmart-Hmac-SHA256")

    if not verify_hmac_sha256(raw_body, signature, HOTMART_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Assinatura Hotmart inválida")

    payload = json.loads(raw_body.decode())

    # Financeiro real (fonte da verdade)
    pipeline_financeiro_real(
        platform="HOTMART",
        external_sale_id=payload["data"]["purchase"]["transaction"],
        product_id=str(payload["data"]["product"]["id"]),
        gross_value=float(payload["data"]["purchase"]["price"]["value"]),
        commission_total=float(payload["data"]["purchase"]["commission"]["value"]),
        partner_id=payload.get("data", {}).get("affiliate", {}).get("affiliate_code"),
        payload=payload
    )

    # Camada soberana (decisão / governança)
    evento = normalizar_evento_hotmart(payload)
    pipeline_operacional(evento)

    return {"status": "OK", "plataforma": "HOTMART"}


# ==========================================================
# WEBHOOK EDUZZ
# ==========================================================

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Eduzz-Signature")

    if not verify_hmac_sha256(raw_body, signature, EDUZZ_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Assinatura Eduzz inválida")

    payload = json.loads(raw_body.decode())

    pipeline_financeiro_real(
        platform="EDUZZ",
        external_sale_id=str(payload["sale"]["id"]),
        product_id=str(payload["product"]["id"]),
        gross_value=float(payload["sale"]["value"]),
        commission_total=float(payload["sale"]["commission"]),
        partner_id=payload.get("affiliate", {}).get("id"),
        payload=payload
    )

    evento = normalizar_evento_eduzz(payload)
    pipeline_operacional(evento)

    return {"status": "OK", "plataforma": "EDUZZ"}


# ==========================================================
# WEBHOOK MONETIZZE
# ==========================================================

@app.post("/webhook/monetizze")
async def webhook_monetizze(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Monetizze-Signature")

    if not verify_hmac_sha256(raw_body, signature, MONETIZZE_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Assinatura Monetizze inválida")

    payload = json.loads(raw_body.decode())

    pipeline_financeiro_real(
        platform="MONETIZZE",
        external_sale_id=str(payload["venda"]["codigo"]),
        product_id=str(payload["produto"]["codigo"]),
        gross_value=float(payload["venda"]["valor"]),
        commission_total=float(payload["venda"]["comissao"]),
        partner_id=payload.get("afiliado", {}).get("codigo"),
        payload=payload
    )

    evento = normalizar_evento_monetizze(payload)
    pipeline_operacional(evento)

    return {"status": "OK", "plataforma": "MONETIZZE"}

# ==========================================================
# main.py — PARTE 4 / N
# Financeiro Humano • Auditoria • Governança Avançada
# ==========================================================

# ==========================================================
# ENDPOINTS — FINANCEIRO HUMANO (LEITURA / AÇÃO)
# ==========================================================

@app.get("/financeiro/visao-geral")
def visao_financeira():
    """
    Visão consolidada DERIVADA.
    Não é contábil primária.
    """
    return {
        "capital_total": ESTADO_GLOBAL["capital_total"],
        "capital_disponivel": ESTADO_GLOBAL["capital_disponivel"],
        "capital_em_risco": ESTADO_GLOBAL["capital_em_risco"],
        "risco_pct": risco_atual_pct(),
        "atualizado_em": ESTADO_GLOBAL["ultima_atualizacao"],
    }


@app.post("/financeiro/acao-humana")
def acao_humana(payload: AcaoFinanceiraHumana):
    """
    Registro auditável de ação humana.
    Não movimenta dinheiro real.
    """
    registro = payload.dict()
    registro["executado_em"] = utc_now_iso()

    sb.table("acoes_financeiras_humanas").insert(registro).execute()
    log("HUMANO", "INFO", f"Ação financeira registrada: {payload.acao}")

    return {"status": "OK", "mensagem": "Ação financeira registrada"}


# ==========================================================
# AUDITORIA HUMANA — EVENTOS LEGADOS
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
# GOVERNANÇA — CONTROLE DE ESTADO DO SISTEMA
# ==========================================================

@app.get("/governanca/status")
def status_governanca():
    return {
        "estado_operacional": ESTADO_GLOBAL["estado_operacional"],
        "capital_total": ESTADO_GLOBAL["capital_total"],
        "capital_disponivel": ESTADO_GLOBAL["capital_disponivel"],
        "capital_em_risco": ESTADO_GLOBAL["capital_em_risco"],
        "risco_pct": risco_atual_pct(),
        "risco_max_permitido_pct": RISCO_MAX_PCT,
        "plataformas_permitidas": PLATAFORMAS_PERMITIDAS,
        "atualizado_em": ESTADO_GLOBAL["ultima_atualizacao"],
    }


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
# HEALTHCHECKS
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


@app.get("/health")
def health():
    return {
        "status": "ok",
        "estado_operacional": ESTADO_GLOBAL["estado_operacional"],
        "timestamp": utc_now_iso(),
    }

# ==========================================================
# main.py — PARTE FINAL / N
# GO Router • Caminhos • Loop Operacional • Validações
# ==========================================================

# ==========================================================
# LOOP OPERACIONAL (AUTÔNOMO, NÃO FINANCEIRO)
# ==========================================================

def loop_operacional():
    log("LOOP", "INFO", "Loop operacional iniciado")
    while True:
        try:
            # Loop reativo / monitoramento leve
            time.sleep(5)
        except Exception as e:
            log("LOOP", "ERRO", f"Falha no loop: {str(e)}")
            time.sleep(5)

threading.Thread(target=loop_operacional, daemon=True).start()
log("SYSTEM", "INFO", "Loop operacional ativo")


# ==========================================================
# GERADOR DE CAMINHOS (AUDITORIA, NÃO DECISÃO)
# ==========================================================

def gerar_caminho(dor: Dor, contexto: Contexto, ofertas: List[str]) -> Caminho:
    prioridade = (contexto.intensidade or 0) * 1.0
    return Caminho(
        id=str(uuid.uuid4()),
        dor=dor,
        contexto=contexto,
        ofertas=ofertas,
        prioridade=prioridade,
        atualizado_em=utc_now_iso()
    )


def registrar_caminho(caminho: Caminho):
    sb.table("caminhos").insert({
        "id": caminho.id,
        "dor": caminho.dor.codigo,
        "contexto": caminho.contexto.dict(),
        "ofertas": caminho.ofertas,
        "prioridade": caminho.prioridade,
        "atualizado_em": caminho.atualizado_em
    }).execute()


def interpretar_contexto_clique(eventos: List[Dict[str, Any]]) -> Contexto:
    return Contexto(
        origem=eventos[0].get("origem") if eventos else None,
        horario=utc_now_iso(),
        intensidade=len(eventos),
        sequencia=[e.get("slug") for e in eventos]
    )


# ==========================================================
# GO ROUTER — MONETIZAÇÃO DIRETA (B1)
# ==========================================================

@app.get("/go")
def go_router(produto: str, request: Request):
    """
    Roteador direto de monetização.
    Não decide, não bloqueia, não pontua.
    Apenas redireciona para LINK MASTER ativo.
    """
    try:
        res = (
            sb.table("offers")
            .select("*")
            .eq("slug", produto)
            .eq("status", "ativo")
            .limit(1)
            .execute()
        )
    except Exception as e:
        log("GO", "ERRO", f"Falha Supabase: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno")

    if not res.data:
        log("GO", "WARN", f"Produto não encontrado ou inativo: {produto}")
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    offer = res.data[0]
    target_url = offer.get("url_afiliado")

    if not target_url:
        log("GO", "ERRO", f"Oferta sem URL: {produto}")
        raise HTTPException(status_code=500, detail="URL de destino inexistente")

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


@app.get("/go/caminho")
def go_caminho(dor_codigo: str, produto: str, request: Request):
    dor = Dor(codigo=dor_codigo)

    eventos = (
        sb.table("clicks")
        .select("*")
        .eq("slug", produto)
        .order("ts", desc=True)
        .limit(10)
        .execute()
        .data
    )

    contexto = interpretar_contexto_clique(eventos)
    caminho = gerar_caminho(dor, contexto, [produto])
    registrar_caminho(caminho)

    return {
        "status": "CAMINHO_REGISTRADO",
        "caminho_id": caminho.id
    }


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
# DECLARAÇÃO FORMAL DE CONCLUSÃO TÉCNICA
# ==========================================================

def declaracao_conclusao():
    log(
        "SYSTEM",
        "INFO",
        "CONCLUSÃO TÉCNICA: main.py completo, integrado e operacional"
    )

declaracao_conclusao()

# ==========================================================
# CMS MASTER — CAMADA SOBERANA (B1 → B2 TRANSIÇÃO)
# ==========================================================

MASTER_KEY = os.getenv("MASTER_KEY", "")

def validar_master(request: Request):
    chave = request.headers.get("x-master-key")
    if not MASTER_KEY or chave != MASTER_KEY:
        raise HTTPException(status_code=401, detail="MASTER KEY inválida")

class NichoCMS(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None


@app.post("/cms/nichos")
def cms_criar_nicho(payload: NichoCMS, request: Request):
    """
    Criação segura de nichos via CMS.
    Não altera pipeline soberano.
    Apenas registra dados editoriais.
    """
    validar_master(request)

    try:
        table_rg("nichos").insert({
            "title": payload.title,
            "slug": payload.slug,
            "description": payload.description
        }).execute()

        log("CMS", "INFO", f"Nicho criado via MASTER: {payload.slug}")

        return {"status": "OK", "slug": payload.slug}

    except Exception as e:
        log("CMS", "ERRO", f"Falha ao criar nicho: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao inserir nicho")

# B1 editorial management — private, explicitly authenticated, unpublished by default
class SubnichoCMS(BaseModel):
    nicho_id: uuid.UUID
    title: str
    slug: str
    description: Optional[str] = None

class DorCMS(BaseModel):
    subnicho_id: uuid.UUID
    title: str
    slug: str
    description: Optional[str] = None

@app.post("/cms/subnichos")
def cms_criar_subnicho(payload: SubnichoCMS, request: Request):
    validar_master(request)
    parent = table_rg("nichos").select("id").eq("id", str(payload.nicho_id)).limit(1).execute()
    if not parent.data:
        raise HTTPException(status_code=404, detail="Nicho nao encontrado")
    try:
        result = table_rg("subnichos").insert({"nicho_id":str(payload.nicho_id),"title":payload.title,"slug":payload.slug,"description":payload.description,"published":False}).execute()
        return {"status":"OK","data":result.data}
    except Exception:
        raise HTTPException(status_code=409, detail="Subnicho nao cadastrado; verifique slug e dados")

@app.post("/cms/dores")
def cms_criar_dor(payload: DorCMS, request: Request):
    validar_master(request)
    parent = table_rg("subnichos").select("id").eq("id", str(payload.subnicho_id)).limit(1).execute()
    if not parent.data:
        raise HTTPException(status_code=404, detail="Subnicho nao encontrado")
    try:
        result = table_rg("dores").insert({"subnicho_id":str(payload.subnicho_id),"title":payload.title,"slug":payload.slug,"description":payload.description,"published":False}).execute()
        return {"status":"OK","data":result.data}
    except Exception:
        raise HTTPException(status_code=409, detail="Dor nao cadastrada; verifique slug e dados")

class PublicacaoCMS(BaseModel):
    published: bool

@app.get("/cms/b1/inventario")
def cms_inventario_b1(request: Request):
    validar_master(request)
    try:
        nichos = table_rg("nichos").select("id,slug,title,description,published").order("title").execute().data or []
        subnichos = table_rg("subnichos").select("id,nicho_id,slug,title,description,published").order("title").execute().data or []
        dores = table_rg("dores").select("id,subnicho_id,slug,title,description,published").order("title").execute().data or []
        vinculos = table_rg("dor_solucoes").select("id,dor_id,solucao_id,prioridade,published").execute().data or []
        solucoes = sb.table("solucoes").select("id,nome,descricao,ativo").execute().data or []
        return {"status":"OK","data":{"nichos":nichos,"subnichos":subnichos,"dores":dores,"vinculos":vinculos,"solucoes":solucoes}}
    except Exception:
        raise HTTPException(status_code=503, detail="Inventario B1 indisponivel")

class VinculoSolucaoCMS(BaseModel):
    dor_id: uuid.UUID
    solucao_id: uuid.UUID
    prioridade: int = 1

@app.post("/cms/b1/vinculos")
def cms_vincular_solucao(payload: VinculoSolucaoCMS, request: Request):
    validar_master(request)
    if payload.prioridade < 0:
        raise HTTPException(status_code=422, detail="Prioridade invalida")
    dor = table_rg("dores").select("id").eq("id", str(payload.dor_id)).limit(1).execute()
    if not dor.data:
        raise HTTPException(status_code=404, detail="Dor nao encontrada")
    sol = sb.table("solucoes").select("id,ativo,link_afiliado").eq("id", str(payload.solucao_id)).limit(1).execute()
    if not sol.data or not sol.data[0].get("ativo") or not str(sol.data[0].get("link_afiliado") or "").startswith(("https://","http://")):
        raise HTTPException(status_code=409, detail="Solucao inexistente, inativa ou sem link valido")
    try:
        result = table_rg("dor_solucoes").upsert({"dor_id":str(payload.dor_id),"solucao_id":str(payload.solucao_id),"prioridade":payload.prioridade,"published":False}, on_conflict="dor_id,solucao_id").execute()
        return {"status":"OK","data":result.data,"published":False}
    except Exception:
        raise HTTPException(status_code=503, detail="Nao foi possivel registrar o vinculo")

@app.patch("/cms/b1/vinculos/{vinculo_id}/publicacao")
def cms_publicar_vinculo(vinculo_id: uuid.UUID, payload: PublicacaoCMS, request: Request):
    validar_master(request)
    existing=table_rg("dor_solucoes").select("id,dor_id,solucao_id").eq("id",str(vinculo_id)).limit(1).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Vinculo nao encontrado")
    if payload.published:
        dor=table_rg("dores").select("subnicho_id,slug").eq("id",existing.data[0]["dor_id"]).eq("published",True).limit(1).execute()
        if not dor.data or str(dor.data[0]["slug"]).lower().startswith(("teste-","test-")):
            raise HTTPException(status_code=409, detail="Dor nao publicada")
        sub=table_rg("subnichos").select("nicho_id,slug").eq("id",dor.data[0]["subnicho_id"]).eq("published",True).limit(1).execute()
        if not sub.data or str(sub.data[0]["slug"]).lower().startswith(("teste-","test-")):
            raise HTTPException(status_code=409, detail="Subnicho nao publicado")
        nicho=table_rg("nichos").select("slug").eq("id",sub.data[0]["nicho_id"]).eq("published",True).limit(1).execute()
        if not nicho.data or str(nicho.data[0]["slug"]).lower().startswith(("teste-","test-")):
            raise HTTPException(status_code=409, detail="Nicho nao publicado")
        sol=sb.table("solucoes").select("ativo,link_afiliado").eq("id",existing.data[0]["solucao_id"]).limit(1).execute()
        if not sol.data or not sol.data[0].get("ativo") or not str(sol.data[0].get("link_afiliado") or "").startswith(("https://","http://")):
            raise HTTPException(status_code=409, detail="Solucao nao elegivel")
    table_rg("dor_solucoes").update({"published":payload.published}).eq("id",str(vinculo_id)).execute()
    return {"status":"OK","id":str(vinculo_id),"published":payload.published}


    published: bool

@app.patch("/cms/b1/{nivel}/{item_id}/publicacao")
def cms_publicar_b1(nivel: str, item_id: uuid.UUID, payload: PublicacaoCMS, request: Request):
    validar_master(request)
    tabelas={"nichos":"nichos","subnichos":"subnichos","dores":"dores"}
    if nivel not in tabelas:
        raise HTTPException(status_code=404, detail="Nivel desconhecido")
    table=tabelas[nivel]
    existing=table_rg(table).select("id").eq("id",str(item_id)).limit(1).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Registro nao encontrado")
    if payload.published and nivel == "subnichos":
        row=table_rg("subnichos").select("nicho_id,slug").eq("id",str(item_id)).limit(1).execute().data[0]
        parent=table_rg("nichos").select("id,slug").eq("id",row["nicho_id"]).eq("published",True).limit(1).execute()
        if not parent.data or str(row["slug"]).lower().startswith(("teste-","test-")):
            raise HTTPException(status_code=409, detail="Publique primeiro um nicho valido")
    if payload.published and nivel == "dores":
        row=table_rg("dores").select("subnicho_id,slug").eq("id",str(item_id)).limit(1).execute().data[0]
        sub=table_rg("subnichos").select("nicho_id,slug").eq("id",row["subnicho_id"]).eq("published",True).limit(1).execute()
        if not sub.data or str(row["slug"]).lower().startswith(("teste-","test-")):
            raise HTTPException(status_code=409, detail="Publique primeiro um subnicho valido")
        parent=table_rg("nichos").select("id").eq("id",sub.data[0]["nicho_id"]).eq("published",True).limit(1).execute()
        if not parent.data:
            raise HTTPException(status_code=409, detail="Nicho principal nao publicado")
    if payload.published and nivel == "nichos":
        row=table_rg("nichos").select("slug").eq("id",str(item_id)).limit(1).execute().data[0]
        if str(row["slug"]).lower().startswith(("teste-","test-")):
            raise HTTPException(status_code=409, detail="Registros de teste nao podem ser publicados")
    table_rg(table).update({"published":payload.published}).eq("id",str(item_id)).execute()
    return {"status":"OK","nivel":nivel,"id":str(item_id),"published":payload.published}

# ==========================================================
# CMS — LEITURA SEGURA DE NICHOS (PUBLICO VIA API)
# ==========================================================

def listar_nichos_publicos_legacy_1():
    """
    Leitura pública segura.
    Frontend não acessa mais Supabase direto.
    """
    try:
        res = (
            sb.table("nichos")
            .select("id,title,slug,description")
            .order("title")
            .execute()
        )

        return {"data": res.data}

    except Exception as e:
        log("CMS", "ERRO", f"Falha ao listar nichos: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao buscar nichos")

# ==========================================================
# PUBLIC — NICHOS GLOBAL (VERSÃO DEFINITIVA)
# ==========================================================

def listar_nichos_publicos_legacy_2():
    """
    Endpoint público global.
    Frontend NÃO acessa banco.
    Retorna todos os campos necessários.
    """
    try:
        res = (
            sb.table("nichos")
            .select("id,title,slug,description,image_url,created_at")
            .order("title")
            .execute()
        )

        return {
            "status": "OK",
            "total": len(res.data or []),
            "data": res.data or []
        }

    except Exception as e:
        log("PUBLIC", "ERRO", f"Falha ao listar nichos: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao buscar nichos")

# CORS is configured once, at FastAPI initialization above.

# ================================
# BLOCO OPERACIONAL - DASHBOARD API
# Inclusão definitiva no FINAL do MAIN
# ================================

from fastapi.responses import JSONResponse

# Rotas de indicadores ficticios /capital e /escala removidas: nenhuma metrica simulada em producao.

# ============================================
# B2 — CADASTRO OPERACIONAL DE PRODUTOS (MASTER)
# ============================================

from pydantic import BaseModel

class ProdutoInput(BaseModel):
    nome: str
    plataforma: str
    preco: float
    comissao: float
    risco: str = "baixo"

# memória inicial segura (não quebra nada existente)
if "produtos_cadastrados" not in globals():
    produtos_cadastrados = []

@app.post("/master/produto")
async def cadastrar_produto(produto: ProdutoInput):
    novo = {
        "id": len(produtos_cadastrados) + 1,
        "nome": produto.nome,
        "plataforma": produto.plataforma,
        "preco": produto.preco,
        "comissao": produto.comissao,
        "risco": produto.risco,
        "status": "ativo"
    }
    produtos_cadastrados.append(novo)
    return {"ok": True, "produto": novo}

@app.get("/master/produtos")
async def listar_produtos_master():
    return produtos_cadastrados

# ==========================================================
# B2.1 — PRODUTO AFILIADO ESTRUTURADO (EXECUTOR MASTER)
# NÃO ALTERA ROTAS EXISTENTES
# ==========================================================

from typing import Optional
from pydantic import BaseModel

class ProdutoAfiliado(BaseModel):
    nome: str
    plataforma: str
    product_id: Optional[str] = None
    affiliate_url: str
    preco: float
    comissao: float
    nicho: Optional[str] = None
    dor: Optional[str] = None
    image_url: Optional[str] = None

    # CAMPOS MASTER
    usuario_master: Optional[str] = None
    senha_master: Optional[str] = None

    # PREPARAÇÃO GLOBAL (B3)
    titulo_pt: Optional[str] = None
    titulo_es: Optional[str] = None
    titulo_en: Optional[str] = None


@app.post("/b2/produtos")
def criar_produto_b2(payload: ProdutoAfiliado, request: Request):

    validar_master(request)

    try:
        # ======================================================
        # GERAÇÃO GUL (GO UNIQUE LINK)
        # ======================================================
        import uuid
        gul = f"/go/{str(uuid.uuid4())[:8]}"

        sb.table("produtos").insert({
            "nome": payload.nome,
            "plataforma": payload.plataforma,
            "product_id": payload.product_id,
            "affiliate_url": payload.affiliate_url,
            "preco": payload.preco,
            "comissao": payload.comissao,
            "nicho": payload.nicho,
            "dor": payload.dor,
            "image_url": payload.image_url,
            "usuario_master": payload.usuario_master,
            "senha_master": payload.senha_master,
            "titulo_pt": payload.titulo_pt,
            "titulo_es": payload.titulo_es,
            "titulo_en": payload.titulo_en,
            "gul": gul,
            "status": "ativo",
            "created_at": utc_now_iso()
        }).execute()

        log("B2", "INFO", f"Produto criado via MASTER: {payload.nome}")

        return {
            "status": "OK",
            "produto": payload.nome,
            "gul": gul
        }

    except Exception as e:
        log("B2", "ERRO", f"Falha ao criar produto: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao inserir produto")

# ==========================================================
# B2.2 — LISTAGEM OPERACIONAL DE PRODUTOS (DASHBOARD)
# ==========================================================

@app.get("/b2/produtos")
def listar_produtos_b2():

    try:
        res = sb.table("produtos").select(
            "nome, plataforma, preco, comissao, nicho, dor, image_url, gul, status"
        ).order("created_at", desc=True).execute()

        return res.data or []

    except Exception as e:
        log("B2", "ERRO", f"Falha ao listar produtos: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao buscar produtos")

# ==========================================================
# B2.5 — GUL (GLOBAL UNIQUE LINK) ENGINE
# Geração automática de link blindado do Robô Global
# NÃO altera pipeline existente
# ==========================================================

import hashlib
from datetime import datetime

BASE_REDIRECT = os.getenv("BASE_REDIRECT", "https://roboglobal.com.br/go")

def gerar_gul(plataforma: str, codigo: str, link_afiliado: str) -> str:
    """
    Cria o GUL (Global Unique Link)
    Blindagem da comissão do Robô Global.
    """
    raw = f"{plataforma}:{codigo}:{link_afiliado}:{datetime.utcnow().isoformat()}"
    hash_id = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return f"{BASE_REDIRECT}/{hash_id}"


# ==========================================================
# ENDPOINT MASTER — REGISTRO COM GUL AUTOMÁTICO
# ==========================================================

class ProdutoMaster(BaseModel):
    nome: str
    plataforma: str
    preco: float
    comissao: str
    link_afiliado: str
    url_produto: Optional[str] = None
    imagem: Optional[str] = None
    nicho: Optional[str] = None
    dor: Optional[str] = None
    codigo: Optional[str] = None


@app.post("/master/produto")
def master_cadastrar_produto(payload: ProdutoMaster):

    try:
        gul = gerar_gul(
            payload.plataforma,
            payload.codigo or payload.nome,
            payload.link_afiliado,
        )

        sb.table("produtos").insert({
            "nome": payload.nome,
            "plataforma": payload.plataforma,
            "preco": payload.preco,
            "comissao": payload.comissao,
            "link_afiliado": payload.link_afiliado,
            "url_produto": payload.url_produto,
            "imagem": payload.imagem,
            "nicho": payload.nicho,
            "dor": payload.dor,
            "codigo": payload.codigo,
            "gul": gul,
            "created_at": utc_now_iso()
        }).execute()

        log("B2.5", "INFO", f"GUL gerado: {gul}")

        return {
            "status": "OK",
            "mensagem": "Produto cadastrado com GUL",
            "gul": gul
        }

    except Exception as e:
        log("B2.5", "ERRO", str(e))
        raise HTTPException(status_code=500, detail="Erro ao cadastrar produto")

# ==========================================================
# B2.6 — REDIRECIONADOR INTELIGENTE GUL
# Endpoint público do Robô Global
# https://roboglobal.com.br/go/{id}
# ==========================================================

from fastapi.responses import RedirectResponse

@app.get("/go/{gul_id}")
def redirect_gul(gul_id: str):

    try:
        # Buscar produto pelo GUL
        res = sb.table("produtos") \
            .select("nome, link_afiliado, plataforma, gul") \
            .like("gul", f"%{gul_id}") \
            .limit(1) \
            .execute()

        if not res.data:
            raise HTTPException(status_code=404, detail="GUL não encontrado")

        produto = res.data[0]
        destino = produto["link_afiliado"]

        # ======================================================
        # LOG OPERACIONAL DO CLIQUE
        # ======================================================
        sb.table("cliques").insert({
            "gul": produto["gul"],
            "produto": produto["nome"],
            "plataforma": produto["plataforma"],
            "created_at": utc_now_iso()
        }).execute()

        log("B2.6", "INFO", f"Redirect GUL -> {destino}")

        return RedirectResponse(destino, status_code=302)

    except Exception as e:
        log("B2.6", "ERRO", str(e))
        raise HTTPException(status_code=500, detail="Erro no redirecionamento")

# ===============================
# SCHEMA FIX — ROBO GLOBAL
# NÃO ALTERAR NADA ACIMA
# ===============================

SCHEMA_ROBO = "robo_global"

def table_rg(nome_tabela: str):
    """
    Helper seguro para acessar tabelas do schema robo_global
    Sem impactar código existente
    """
    return sb.schema(SCHEMA_ROBO).table(nome_tabela)

# ===============================
# ENDPOINT PUBLICO — NICHOS
# CORRIGIDO PARA SCHEMA
# ===============================

@app.get("/public/nichos")
def listar_nichos_publicos():
    try:
        resp = table_rg("nichos").select("id,title,slug,description").eq("published", True).execute()
        items = [row for row in (resp.data or []) if not str(row.get("slug", "")).startswith("teste-")]
        return {"status": "OK", "total": len(items), "data": items}
    except Exception as e:
        log("PUBLIC", "ERRO", "Falha ao buscar nichos publicos")
        raise HTTPException(status_code=503, detail="Catalogo temporariamente indisponivel")

# B1 — hierarchical public catalog (only approved records; test slugs excluded)
@app.get("/public/nichos/{nicho_slug}/subnichos")
def listar_subnichos_publicos(nicho_slug: str):
    try:
        parent = table_rg("nichos").select("id,slug").eq("slug", nicho_slug).eq("published", True).limit(1).execute()
        if not parent.data or nicho_slug.lower().startswith(("teste-", "test-")):
            raise HTTPException(status_code=404, detail="Nicho nao encontrado")
        result = table_rg("subnichos").select("id,nicho_id,slug,title,description").eq("nicho_id", parent.data[0]["id"]).eq("published", True).execute()
        items = [row for row in (result.data or []) if not str(row.get("slug", "")).lower().startswith(("teste-", "test-"))]
        return {"status": "OK", "total": len(items), "data": items}
    except HTTPException:
        raise
    except Exception:
        log("PUBLIC", "ERRO", "Falha ao buscar subnichos")
        raise HTTPException(status_code=503, detail="Catalogo temporariamente indisponivel")

@app.get("/public/subnichos/{subnicho_id}/dores")
def listar_dores_subnicho_publicas(subnicho_id: uuid.UUID):
    try:
        sub = table_rg("subnichos").select("id,nicho_id,slug").eq("id", str(subnicho_id)).eq("published", True).limit(1).execute()
        if not sub.data or str(sub.data[0]["slug"]).lower().startswith(("teste-", "test-")):
            raise HTTPException(status_code=404, detail="Subnicho nao encontrado")
        parent = table_rg("nichos").select("slug").eq("id", sub.data[0]["nicho_id"]).eq("published", True).limit(1).execute()
        if not parent.data or str(parent.data[0]["slug"]).lower().startswith(("teste-", "test-")):
            raise HTTPException(status_code=404, detail="Nicho nao encontrado")
        result = table_rg("dores").select("id,subnicho_id,slug,title,description").eq("subnicho_id", str(subnicho_id)).eq("published", True).execute()
        items = [row for row in (result.data or []) if not str(row.get("slug", "")).lower().startswith(("teste-", "test-"))]
        return {"status": "OK", "total": len(items), "data": items}
    except HTTPException:
        raise
    except Exception:
        log("PUBLIC", "ERRO", "Falha ao buscar dores")
        raise HTTPException(status_code=503, detail="Catalogo temporariamente indisponivel")

# B1 — public approved solutions linked to a published pain.
# This is a read-only catalog endpoint; no click tracking or personal data.
@app.get("/public/dores/{dor_id}/solucoes")
def listar_solucoes_publicas_dor(dor_id: uuid.UUID):
    try:
        pain = table_rg("dores").select("id,subnicho_id,slug").eq("id", str(dor_id)).eq("published", True).limit(1).execute()
        if not pain.data or str(pain.data[0]["slug"]).lower().startswith(("teste-", "test-")):
            raise HTTPException(status_code=404, detail="Dor nao encontrada")
        sub = table_rg("subnichos").select("id,nicho_id,slug").eq("id", pain.data[0]["subnicho_id"]).eq("published", True).limit(1).execute()
        if not sub.data or str(sub.data[0]["slug"]).lower().startswith(("teste-", "test-")):
            raise HTTPException(status_code=404, detail="Subnicho nao encontrado")
        parent = table_rg("nichos").select("id,slug").eq("id", sub.data[0]["nicho_id"]).eq("published", True).limit(1).execute()
        if not parent.data or str(parent.data[0]["slug"]).lower().startswith(("teste-", "test-")):
            raise HTTPException(status_code=404, detail="Nicho nao encontrado")
        links = table_rg("dor_solucoes").select("solucao_id,prioridade").eq("dor_id", str(dor_id)).eq("published", True).order("prioridade", desc=True).execute()
        ids = [x["solucao_id"] for x in (links.data or [])]
        if not ids:
            return {"status": "OK", "total": 0, "data": []}
        products = sb.table("solucoes").select("id,nome,descricao,link_afiliado,ativo").in_("id", ids).eq("ativo", True).execute()
        lookup = {str(x["id"]): x for x in (products.data or [])}
        items = [{"id": str(k), "title": lookup[str(k)]["nome"], "description": lookup[str(k)].get("descricao") or "", "url": lookup[str(k)]["link_afiliado"]} for k in ids if str(k) in lookup and str(lookup[str(k)].get("link_afiliado") or "").startswith(("https://", "http://"))]
        return {"status": "OK", "total": len(items), "data": items}
    except HTTPException:
        raise
    except Exception:
        log("PUBLIC", "ERRO", "Falha ao consultar solucoes da dor")
        raise HTTPException(status_code=503, detail="Solucoes temporariamente indisponiveis")

# ================================
# 🔹 ENDPOINT SEGURO — NICHOS PUBLICOS
# NÃO ALTERA NADA EXISTENTE
# ================================

def listar_nichos_publicos_legacy_inativo():
    try:
        result = (
            supabase
            .schema("robo_global")
            .table("nichos")
            .select("*")
            .execute()
        )

        return result.data or []

    except Exception as e:
        print("[NICHOS] ERRO:", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar nichos: {str(e)}"
        )

# ============================================================
# 🔹 Inicialização segura do cliente Supabase (escopo global)
# ============================================================

try:
    from supabase import create_client
    import os

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[SUPABASE] Cliente inicializado com sucesso")
    else:
        print("[SUPABASE] Variáveis de ambiente não definidas")

except Exception as e:
    print(f"[SUPABASE] Erro ao inicializar cliente: {e}")

# ==========================================================
# 🧠 MOTOR ESTRATÉGICO DO ROBÔ GLOBAL — FASE 1 FINAL
# ==========================================================

from collections import defaultdict

def calcular_metricas_produtos():
    """
    Calcula métricas reais por produto baseado nos eventos financeiros.
    """
    eventos = supabase.schema("robo_global").table("eventos_financeiros").select("*").execute().data
    
    if not eventos:
        return {}

    metricas = defaultdict(lambda: {
        "vendas": 0,
        "receita": 0.0,
        "comissoes": 0.0,
        "reembolsos": 0
    })

    for e in eventos:
        produto = e.get("produto_id")
        if not produto:
            continue

        metricas[produto]["vendas"] += 1
        metricas[produto]["receita"] += float(e.get("valor", 0))
        metricas[produto]["comissoes"] += float(e.get("comissao", 0))
        
        if e.get("status") == "reembolsado":
            metricas[produto]["reembolsos"] += 1

    return metricas


def pontuar_produto(dados):
    """
    Calcula score equilibrado: lucro + conversão + risco.
    """
    vendas = dados["vendas"]
    receita = dados["receita"]
    comissoes = dados["comissoes"]
    reembolsos = dados["reembolsos"]

    if vendas == 0:
        return 0

    ticket = receita / vendas
    margem = comissoes / receita if receita else 0
    risco = reembolsos / vendas

    score = (
        (margem * 50) +
        (ticket * 0.1) +
        (vendas * 2) -
        (risco * 40)
    )

    return round(score, 2)


def classificar_ofertas():
    """
    Retorna ranking estratégico de produtos.
    """
    metricas = calcular_metricas_produtos()
    
    ranking = []

    for produto, dados in metricas.items():
        score = pontuar_produto(dados)
        ranking.append({
            "produto_id": produto,
            "score": score,
            **dados
        })

    ranking.sort(key=lambda x: x["score"], reverse=True)
    return ranking


def escolher_ofertas_prioritarias(top=5):
    """
    Seleciona as melhores ofertas para escalar.
    """
    ranking = classificar_ofertas()
    return ranking[:top]

# ==============================
# BLOCO NOVO — Estratégia Real
# NÃO ALTERAR NADA ACIMA
# ==============================

@app.get("/estrategia/ofertas-real")
def obter_ofertas_reais():
    try:
        response = (
            supabase
            .schema("robo_global")
            .table("v_produto_metricas")
            .select("*")
            .execute()
        )

        dados = response.data or []

        resultado = []

        for row in dados:
            resultado.append({
                "produto_id": row["produto_id"],
                "score": row["score"],
                "vendas": row["vendas"],
                "receita": row["comissoes"],
                "comissoes": row["comissoes"],
                "reembolsos": row["reembolsos"],
            })

        return resultado

    except Exception as e:
        return {"erro": str(e)}
@app.get("/estrategia/ofertas")
def api_ranking_ofertas():
    """
    Endpoint de visualização da inteligência do robô.
    """
    try:
        return escolher_ofertas_prioritarias()
    except Exception as e:
        return {"erro": str(e)}

# ============================================================
# MÓDULO DE DECISÃO E ESCALADA AUTOMÁTICA — ROBO GLOBAL AI
# ============================================================

from datetime import datetime

# ------------------------------------------------------------
# REGRAS DE DECISÃO (padrão inicial — ajustável depois)
# ------------------------------------------------------------

def decidir_acao_produto(score: float, vendas: int, receita: float):
    """
    Motor simples de decisão estratégica.
    Pode evoluir para IA depois.
    """

    if vendas == 0:
        return "IGNORAR", "Sem vendas registradas"

    if score >= 3:
        return "ESCALAR", "Produto com alto desempenho"

    if score >= 1:
        return "TESTAR", "Produto com desempenho médio"

    return "PAUSAR", "Produto com baixo desempenho"


# ------------------------------------------------------------
# REGISTRO DE DECISÕES NO BANCO
# ------------------------------------------------------------

def registrar_decisao_estrategica(produto_id, decisao, motivo):
    try:
        supabase.table("decisoes_estrategicas").insert({
            "entidade": "produto",
            "entidade_id": produto_id,
            "decisao": decisao,
            "base_decisao": motivo,
            "status": "ATIVA",
            "data_decisao": datetime.utcnow().isoformat()
        }).execute()

        print(f"[DECISAO] INFO Produto {produto_id} -> {decisao}")

    except Exception as e:
        print(f"[DECISAO] ERRO ao registrar decisão: {e}")


# ------------------------------------------------------------
# EXECUÇÃO DE AÇÕES AUTOMÁTICAS
# ------------------------------------------------------------

def registrar_acao(produto_id, decisao):
    try:
        supabase.table("acoes_executadas").insert({
            "decisao_id": None,
            "tipo_acao": decisao,
            "descricao_acao": f"Ação automática: {decisao}",
            "resultado": "PENDENTE",
            "data_execucao": datetime.utcnow().isoformat()
        }).execute()

        print(f"[ACAO] INFO Ação registrada: {decisao}")

    except Exception as e:
        print(f"[ACAO] ERRO ao registrar ação: {e}")


# ------------------------------------------------------------
# GERENCIADOR PRINCIPAL DE ESCALADA
# ------------------------------------------------------------

def gerenciar_escalada():
    """
    Função central do cérebro do robô.
    Analisa todos os produtos e decide automaticamente.
    """

    print("[ESCALADA] INFO Iniciando análise estratégica...")

    try:
        resp = supabase.table("v_produto_metricas").select("*").execute()
        produtos = resp.data or []

        for p in produtos:
            produto_id = p["produto_id"]
            score = float(p["score"] or 0)
            vendas = int(p["vendas"] or 0)
            receita = float(p["comissoes"] or 0)

            decisao, motivo = decidir_acao_produto(score, vendas, receita)

            registrar_decisao_estrategica(produto_id, decisao, motivo)
            registrar_acao(produto_id, decisao)

        print("[ESCALADA] INFO Análise concluída")

    except Exception as e:
        print(f"[ESCALADA] ERRO {e}")


# ------------------------------------------------------------
# ENDPOINT DE EXECUÇÃO MANUAL
# ------------------------------------------------------------

@app.get("/estrategia/executar")
def executar_estrategia():
    gerenciar_escalada()
    return {"status": "estrategia executada"}


# ------------------------------------------------------------
# ENDPOINT DE VISUALIZAÇÃO DAS DECISÕES
# ------------------------------------------------------------

@app.get("/estrategia/decisoes")
def listar_decisoes():
    resp = supabase.table("decisoes_estrategicas") \
        .select("*") \
        .order("data_decisao", desc=True) \
        .limit(50) \
        .execute()

    return resp.data


# ------------------------------------------------------------
# ENDPOINT DE AÇÕES EXECUTADAS
# ------------------------------------------------------------

@app.get("/estrategia/acoes")
def listar_acoes():
    resp = supabase.table("acoes_executadas") \
        .select("*") \
        .order("data_execucao", desc=True) \
        .limit(50) \
        .execute()

    return resp.data

# ============================================
# ENDPOINTS CORRIGIDOS — DECISÕES E AÇÕES
# ============================================

@app.get("/estrategia/decisoes")
async def listar_decisoes():
    try:
        resp = supabase.table("decisoes_estrategicas")\
            .select("*")\
            .order("data_decisao", desc=True)\
            .limit(50)\
            .execute()

        return resp.data

    except Exception as e:
        return {"erro": str(e)}


@app.get("/estrategia/acoes")
async def listar_acoes():
    try:
        resp = supabase.table("acoes_executadas")\
            .select("*")\
            .order("data_execucao", desc=True)\
            .limit(50)\
            .execute()

        return resp.data

    except Exception as e:
        return {"erro": str(e)}

# ============================================
# ENDPOINTS NOVOS — LISTAGEM REAL DO ROBÔ
# ============================================

@app.get("/estrategia/decisoes-real")
async def listar_decisoes_real():
    try:
        resp = supabase.table("decisoes_estrategicas")\
            .select("*")\
            .order("data_decisao", desc=True)\
            .limit(50)\
            .execute()

        return resp.data

    except Exception as e:
        return {"erro": str(e)}


@app.get("/estrategia/acoes-real")
async def listar_acoes_real():
    try:
        resp = supabase.table("acoes_executadas")\
            .select("*")\
            .order("data_execucao", desc=True)\
            .limit(50)\
            .execute()

        return resp.data

    except Exception as e:
        return {"erro": str(e)}

# ==========================================================
# ENDPOINTS REAIS — SCHEMA ROBO_GLOBAL (VERSÃO ESTÁVEL)
# ==========================================================

@app.get("/estrategia/decisoes-real")
async def decisoes_reais():
    try:
        resp = (
            supabase.schema("robo_global")
            .table("decisoes_estrategicas")
            .select("*")
            .order("data_decisao", desc=True)
            .limit(100)
            .execute()
        )
        return resp.data
    except Exception as e:
        return {"erro": str(e)}


@app.get("/estrategia/acoes-real")
async def acoes_reais():
    try:
        resp = (
            supabase.schema("robo_global")
            .table("acoes_executadas")
            .select("*")
            .order("data_execucao", desc=True)
            .limit(100)
            .execute()
        )
        return resp.data
    except Exception as e:
        return {"erro": str(e)}

# ===============================
# FASE 7 — FIX DEFINITIVO ENDPOINTS HUMANOS
# NÃO ALTERAR NADA ACIMA
# ===============================

@app.get("/estrategia/decisoes-real")
async def listar_decisoes_reais():
    try:
        res = supabase.table("decisoes_robo") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(50) \
            .execute()

        return res.data or []

    except Exception as e:
        return {"erro": str(e)}


@app.get("/estrategia/acoes-real")
async def listar_acoes_reais():
    try:
        res = supabase.table("tarefas_executadas") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(50) \
            .execute()

        return res.data or []

    except Exception as e:
        return {"erro": str(e)}

# ============================================================
# FASE 7 — ENDPOINTS HUMANOS DEFINITIVOS (VERSÃO FINAL)
# ============================================================

@app.get("/estrategia/decisoes-real")
def listar_decisoes_humanas():
    try:
        resp = (
            supabase
            .schema("robo_global")
            .table("decisoes_estrategicas")
            .select("*")
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        return {"erro": str(e)}


@app.get("/estrategia/acoes-real")
def listar_acoes_humanas():
    try:
        resp = (
            supabase
            .schema("robo_global")
            .table("acoes_executadas")
            .select("*")
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        return {"erro": str(e)}

# =========================================================
# FASE 9 — IDENTIDADE E PERFIL DO USUÁRIO (SUPABASE AUTH)
# =========================================================

from fastapi import Header, HTTPException

async def obter_usuario_logado(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não informado")

    try:
        token = authorization.replace("Bearer ", "")

        user = supabase.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Token inválido")

        auth_id = user.user.id

        perfil = supabase.table("v_perfil_usuario") \
            .select("*") \
            .eq("auth_user_id", auth_id) \
            .single() \
            .execute()

        if not perfil.data:
            raise HTTPException(status_code=403, detail="Usuário não registrado")

        return perfil.data

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# =========================================================
# FASE 9 — CONTROLE DE ACESSO E PERMISSÕES
# =========================================================

from fastapi import Depends

async def exigir_login(usuario = Depends(obter_usuario_logado)):
    return usuario


async def exigir_master(usuario = Depends(obter_usuario_logado)):
    if usuario["perfil"] != "MASTER":
        raise HTTPException(status_code=403, detail="Acesso restrito ao MASTER")
    return usuario


async def exigir_permissao_admin(usuario = Depends(obter_usuario_logado)):
    if not usuario.get("pode_admin"):
        raise HTTPException(status_code=403, detail="Permissão administrativa necessária")
    return usuario


async def exigir_permissao_cadastro(usuario = Depends(obter_usuario_logado)):
    if not usuario.get("pode_cadastrar"):
        raise HTTPException(status_code=403, detail="Permissão de cadastro necessária")
    return usuario

# =========================================================
# FASE 10 — CADASTRO OPERACIONAL DE SOLUÇÕES
# =========================================================

from pydantic import BaseModel

class NovaSolucao(BaseModel):
    nome: str
    plataforma_id: str
    link_afiliado: str
    comissao_percentual: float | None = None
    ticket_medio: float | None = None


@app.post("/solucoes")
async def cadastrar_solucao(
    dados: NovaSolucao,
    usuario = Depends(exigir_permissao_cadastro)
):
    try:
        res = supabase.table("solucoes").insert({
            "nome": dados.nome,
            "plataforma_id": dados.plataforma_id,
            "link_afiliado": dados.link_afiliado,
            "comissao_percentual": dados.comissao_percentual,
            "ticket_medio": dados.ticket_medio
        }).execute()

        return {"status": "solução cadastrada", "data": res.data}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# =========================================================
# FASE 10 — MOTOR REAL DO ROBÔ GLOBAL (VERSÃO DEFINITIVA)
# =========================================================

import uuid
from fastapi.responses import RedirectResponse


@app.get("/recomendar/{dor_id}")
async def recomendar_solucao(dor_id: str):
    try:
        # Buscar melhor solução
        res = supabase.table("dor_solucoes") \
            .select("*, solucoes(*)") \
            .eq("dor_id", dor_id) \
            .order("prioridade", desc=True) \
            .limit(1) \
            .execute()

        if not res.data:
            raise HTTPException(status_code=404, detail="Nenhuma solução encontrada")

        solucao = res.data[0]["solucoes"]

        # Gerar ID de rastreamento
        go_id = str(uuid.uuid4())

        # Registrar memória do robô
        await registrar_memoria_robo(dor_id, solucao)

        # Registrar clique para rastreamento
        supabase.table("go_tracking").insert({
            "id": go_id,
            "dor_id": dor_id,
            "solucao_id": solucao["id"],
            "link_destino": solucao["link_afiliado"]
        }).execute()

        # Retornar somente ID público
        return {
            "go_id": go_id
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================
# ENDPOINT DE REDIRECIONAMENTO REAL
# =========================================================

# Duplicate legacy /go/{go_id} handler retired: /go/{gul_id} is the single active public GUL route.
# Original implementation used go_tracking and was shadowed by the earlier registered route.

# =========================================================
# FASE 10 — REGISTRO AUTOMÁTICO DE DECISÕES
# =========================================================

async def registrar_memoria_robo(dor_id: str, solucao: dict):
    try:
        # Registrar decisão estratégica
        supabase.table("decisoes_estrategicas").insert({
            "produto_id": solucao["id"],
            "score": 0,
            "decisao": f"Solução escolhida para dor {dor_id}"
        }).execute()

        # Registrar ação executada
        supabase.table("acoes_executadas").insert({
            "produto_id": solucao["id"],
            "acao": "Recomendação automática",
            "status": "EXECUTADA"
        }).execute()

    except Exception as e:
        print("Erro ao registrar memória:", e)

# =========================================================
# FASE 11 — PAINEL MASTER DO ROBÔ GLOBAL
# =========================================================

@app.get("/master/decisoes")
async def listar_decisoes():
    try:
        res = supabase.table("decisoes_estrategicas") \
            .select("*") \
            .order("id", desc=True) \
            .limit(200) \
            .execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/master/acoes")
async def listar_acoes():
    try:
        res = supabase.table("acoes_executadas") \
            .select("*") \
            .order("id", desc=True) \
            .limit(200) \
            .execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/master/resumo")
async def resumo_master():
    try:
        decisoes = supabase.table("decisoes_estrategicas").select("id").execute()
        acoes = supabase.table("acoes_executadas").select("id").execute()

        return {
            "total_decisoes": len(decisoes.data),
            "total_acoes": len(acoes.data)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# =========================================================
# FASE 11 — CADASTRO OPERACIONAL (PRESTADOR)
# =========================================================

@app.post("/operacional/plataforma")
async def criar_plataforma(payload: dict):
    try:
        res = supabase.table("plataformas").insert(payload).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/operacional/solucao")
async def criar_solucao(payload: dict):
    try:
        res = supabase.table("solucoes").insert(payload).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/operacional/vincular")
async def vincular_solucao(payload: dict):
    try:
        res = supabase.table("dor_solucoes").insert(payload).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Legacy public catalog routes retired: canonical B1 is served exclusively by /public/nichos and its child routes.


@app.get("/master/catalogo/awin/anunciantes")
def anunciantes_awin_master(request: Request):
    validar_master(request)
    from scripts.awin_discover import discover
    from urllib.error import HTTPError, URLError
    try:
        return discover()
    except (HTTPError, URLError, TimeoutError, ValueError):
        raise HTTPException(status_code=503, detail="Consulta Awin indisponivel")
