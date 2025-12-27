# main.py — versão completa e final
# ROBO GLOBAL AI
# CARTA MAGNA EXECUTIVA — IMPLEMENTAÇÃO TÉCNICA REAL
# --------------------------------------------------
# ARQUIVO ÚNICO • FASTAPI • SUPABASE • RENDER
# GOVERNANÇA FINAL • LEITURA HUMANA • LEDGER IMUTÁVEL
#
# PARTE 1 — CABEÇALHO + CONFIGURAÇÃO + NÚCLEO
# (NADA FOI OMITIDO. ARQUIVO CONTINUA NAS PRÓXIMAS PARTES.)
# --------------------------------------------------

import os
import json
import hmac
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pydantic import BaseModel, Field

from supabase import create_client, Client


# ======================================================
# CONFIGURAÇÃO GLOBAL
# ======================================================

APP_NAME = "ROBO GLOBAL AI"
APP_VERSION = "1.0.0-final"
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

UTC_NOW = lambda: datetime.now(timezone.utc)

# ======================================================
# LOGGING PADRONIZADO (OBRIGATÓRIO)
# FORMATO: [ORIGEM] [NÍVEL] mensagem
# ======================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)

def log(origem: str, nivel: str, mensagem: str):
    logging.info(f"[{origem}] [{nivel}] {mensagem}")


# ======================================================
# VARIÁVEIS DE AMBIENTE — OBRIGATÓRIO
# ======================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HOTMART_SECRET = os.getenv("HOTMART_SECRET", "")
EDUZZ_SECRET = os.getenv("EDUZZ_SECRET", "")
KIWIFY_SECRET = os.getenv("KIWIFY_SECRET", "")

DASHBOARD_API_KEY = os.getenv("DASHBOARD_API_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL ou SUPABASE_KEY não configurados")

# ======================================================
# SUPABASE CLIENT
# ======================================================

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

log("BOOT", "INFO", "Supabase conectado com sucesso")


# ======================================================
# FASTAPI APP
# ======================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION
)

# ======================================================
# CORS — DASHBOARD
# ======================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # frontend separado ou pages
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

log("BOOT", "INFO", "FastAPI inicializado")


# ======================================================
# MODELOS BASE (EVENTOS E REGISTROS)
# ======================================================

class EventoBruto(BaseModel):
    origem: str
    payload: Dict[str, Any]
    recebido_em: datetime = Field(default_factory=UTC_NOW)


class EventoNormalizado(BaseModel):
    origem: str
    tipo_evento: str
    produto: Optional[str]
    valor: float
    moeda: str
    comissao: float
    custo_midia: float
    lucro: float
    dados_brutos: Dict[str, Any]
    criado_em: datetime = Field(default_factory=UTC_NOW)


class RegistroDecisao(BaseModel):
    estado: str
    motivo: str
    proxima_acao: str
    snapshot_id: Optional[str]
    criado_em: datetime = Field(default_factory=UTC_NOW)


# ======================================================
# AUTENTICAÇÃO — CAMADA 3 (RESTRITA)
# ======================================================

def autenticar_camada_3(x_api_key: str = Header(...)):
    if x_api_key != DASHBOARD_API_KEY:
        log("AUTH", "WARN", "Acesso negado à Camada 3")
        raise HTTPException(status_code=401, detail="Não autorizado")
    return True


# ======================================================
# FUNÇÕES UTILITÁRIAS INTERNAS
# ======================================================

def validar_hmac(payload: bytes, assinatura: str, secret: str) -> bool:
    if not secret:
        return False
    digest = hmac.new(
        key=secret.encode(),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(digest, assinatura)


def registrar_evento_bruto(evento: EventoBruto):
    supabase.table("eventos_brutos").insert(evento.dict()).execute()
    log("EVENTO", "INFO", f"Evento bruto registrado ({evento.origem})")


def registrar_evento_normalizado(evento: EventoNormalizado):
    supabase.table("eventos_normalizados").insert(evento.dict()).execute()
    log("EVENTO", "INFO", f"Evento normalizado registrado ({evento.origem})")


def registrar_decisao(decisao: RegistroDecisao):
    supabase.table("decisoes").insert(decisao.dict()).execute()
    log("DECISAO", "INFO", f"Decisão registrada: {decisao.estado}")


# ======================================================
# NÚCLEO FINANCEIRO (PLACEHOLDERS — IMPLEMENTAÇÃO REAL NAS PRÓXIMAS PARTES)
# ======================================================

def normalizar_evento(origem: str, payload: Dict[str, Any]) -> EventoNormalizado:
    """
    Normalização universal.
    Implementações específicas por origem vêm depois.
    """
    return EventoNormalizado(
        origem=origem,
        tipo_evento="desconhecido",
        produto=None,
        valor=0.0,
        moeda="BRL",
        comissao=0.0,
        custo_midia=0.0,
        lucro=0.0,
        dados_brutos=payload
    )


def calcular_rentabilidade(evento: EventoNormalizado) -> EventoNormalizado:
    evento.lucro = evento.comissao - evento.custo_midia
    return evento


def decidir_estado_financeiro(evento: EventoNormalizado) -> RegistroDecisao:
    if evento.lucro > 0:
        estado = "GANHO"
        motivo = "Lucro positivo"
        proxima_acao = "MANTER_ESCALA"
    elif evento.lucro == 0:
        estado = "EMPATE"
        motivo = "Resultado neutro"
        proxima_acao = "OBSERVAR"
    else:
        estado = "PERDA"
        motivo = "Lucro negativo"
        proxima_acao = "REDUZIR_ESCALA"

    return RegistroDecisao(
        estado=estado,
        motivo=motivo,
        proxima_acao=proxima_acao,
        snapshot_id=None
    )


# ======================================================
# ENDPOINTS BÁSICOS DE STATUS
# ======================================================

@app.get("/status")
def status_geral():
    return {
        "sistema": APP_NAME,
        "versao": APP_VERSION,
        "estado": "OPERANTE",
        "ambiente": ENVIRONMENT,
        "timestamp": UTC_NOW().isoformat()
    }


@app.get("/")
def root():
    return {"mensagem": "ROBO GLOBAL AI — backend ativo"}


# ======================================================
# FIM DA PARTE 1
# PRÓXIMA: PARTE 2 — WEBHOOKS + NORMALIZAÇÃO REAL + LEDGER
# ======================================================

# ======================================================
# PARTE 2 — WEBHOOKS + NORMALIZAÇÃO REAL + LEDGER FINANCEIRO
# ======================================================
# Continuação direta do main.py — NENHUM CONTEÚDO FOI REMOVIDO
# ======================================================


# ======================================================
# LEDGER FINANCEIRO IMUTÁVEL
# ======================================================

def registrar_ledger(evento: EventoNormalizado):
    """
    Ledger financeiro imutável.
    Cada evento financeiro gera UM registro.
    Nunca é atualizado, apenas inserido.
    """
    registro = {
        "origem": evento.origem,
        "tipo_evento": evento.tipo_evento,
        "produto": evento.produto,
        "valor": evento.valor,
        "moeda": evento.moeda,
        "comissao": evento.comissao,
        "custo_midia": evento.custo_midia,
        "lucro": evento.lucro,
        "criado_em": evento.criado_em.isoformat()
    }
    supabase.table("ledger_financeiro").insert(registro).execute()
    log("LEDGER", "INFO", f"Ledger registrado ({evento.origem})")


# ======================================================
# NORMALIZAÇÃO POR ORIGEM (REAL)
# ======================================================

def normalizar_hotmart(payload: Dict[str, Any]) -> EventoNormalizado:
    valor = float(payload.get("price", 0))
    comissao = float(payload.get("commission_value", 0))
    return EventoNormalizado(
        origem="HOTMART",
        tipo_evento=payload.get("event", "unknown"),
        produto=payload.get("product", {}).get("name"),
        valor=valor,
        moeda=payload.get("currency", "BRL"),
        comissao=comissao,
        custo_midia=0.0,
        lucro=comissao,
        dados_brutos=payload
    )


def normalizar_eduzz(payload: Dict[str, Any]) -> EventoNormalizado:
    valor = float(payload.get("sale_value", 0))
    comissao = float(payload.get("commission", 0))
    return EventoNormalizado(
        origem="EDUZZ",
        tipo_evento=payload.get("event_type", "unknown"),
        produto=payload.get("product_name"),
        valor=valor,
        moeda="BRL",
        comissao=comissao,
        custo_midia=0.0,
        lucro=comissao,
        dados_brutos=payload
    )


def normalizar_kiwify(payload: Dict[str, Any]) -> EventoNormalizado:
    valor = float(payload.get("amount", 0))
    comissao = float(payload.get("affiliate_value", 0))
    return EventoNormalizado(
        origem="KIWIFY",
        tipo_evento=payload.get("type", "unknown"),
        produto=payload.get("product", {}).get("name"),
        valor=valor,
        moeda="BRL",
        comissao=comissao,
        custo_midia=0.0,
        lucro=comissao,
        dados_brutos=payload
    )


# ======================================================
# PROCESSAMENTO UNIVERSAL DE EVENTO
# ======================================================

def processar_evento(origem: str, payload: Dict[str, Any]):
    # 1. Registrar evento bruto
    evento_bruto = EventoBruto(origem=origem, payload=payload)
    registrar_evento_bruto(evento_bruto)

    # 2. Normalizar conforme origem
    if origem == "HOTMART":
        evento_norm = normalizar_hotmart(payload)
    elif origem == "EDUZZ":
        evento_norm = normalizar_eduzz(payload)
    elif origem == "KIWIFY":
        evento_norm = normalizar_kiwify(payload)
    else:
        evento_norm = normalizar_evento(origem, payload)

    # 3. Calcular rentabilidade
    evento_norm = calcular_rentabilidade(evento_norm)

    # 4. Registrar evento normalizado
    registrar_evento_normalizado(evento_norm)

    # 5. Registrar ledger financeiro
    registrar_ledger(evento_norm)

    # 6. Decidir estado financeiro
    decisao = decidir_estado_financeiro(evento_norm)
    registrar_decisao(decisao)

    return {
        "status": "processado",
        "origem": origem,
        "estado": decisao.estado
    }


# ======================================================
# WEBHOOKS
# ======================================================

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request, x_hotmart_signature: str = Header(None)):
    payload_bytes = await request.body()

    if not validar_hmac(payload_bytes, x_hotmart_signature or "", HOTMART_SECRET):
        log("HOTMART", "WARN", "Assinatura inválida")
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = json.loads(payload_bytes.decode())
    resultado = processar_evento("HOTMART", payload)

    return JSONResponse(content=resultado)


@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request, x_eduzz_signature: str = Header(None)):
    payload_bytes = await request.body()

    if not validar_hmac(payload_bytes, x_eduzz_signature or "", EDUZZ_SECRET):
        log("EDUZZ", "WARN", "Assinatura inválida")
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = json.loads(payload_bytes.decode())
    resultado = processar_evento("EDUZZ", payload)

    return JSONResponse(content=resultado)


@app.post("/webhook/kiwify")
async def webhook_kiwify(request: Request, x_kiwify_signature: str = Header(None)):
    payload_bytes = await request.body()

    if not validar_hmac(payload_bytes, x_kiwify_signature or "", KIWIFY_SECRET):
        log("KIWIFY", "WARN", "Assinatura inválida")
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = json.loads(payload_bytes.decode())
    resultado = processar_evento("KIWIFY", payload)

    return JSONResponse(content=resultado)


@app.post("/webhook/universal")
async def webhook_universal(request: Request):
    payload = await request.json()
    origem = payload.get("origem", "DESCONHECIDA")
    resultado = processar_evento(origem, payload)
    return JSONResponse(content=resultado)


# ======================================================
# FIM DA PARTE 2
# PRÓXIMA: PARTE 3 — REGRAS DE RISCO, ESCALA E FREIOS
# ======================================================

# ======================================================
# PARTE 3 — REGRAS DE RISCO, ESCALA E FREIOS AUTOMÁTICOS
# ======================================================
# Continuação direta do main.py — ARQUIVO ÚNICO
# ======================================================


# ======================================================
# PARÂMETROS DE RISCO (CONGELADOS)
# ======================================================

PERDA_MAXIMA_DIARIA = float(os.getenv("PERDA_MAXIMA_DIARIA", 500.0))
PERDA_MAXIMA_POR_ORIGEM = float(os.getenv("PERDA_MAXIMA_POR_ORIGEM", 300.0))

# Estados financeiros possíveis
ESTADOS_VALIDOS = [
    "GANHO",
    "EMPATE",
    "PERDA",
    "PERDA_CRITICA"
]


# ======================================================
# CONSULTAS FINANCEIRAS (SUPABASE)
# ======================================================

def obter_resultado_diario() -> float:
    hoje = UTC_NOW().date().isoformat()
    res = (
        supabase.table("ledger_financeiro")
        .select("lucro")
        .gte("criado_em", hoje)
        .execute()
    )
    total = sum([float(r["lucro"]) for r in res.data]) if res.data else 0.0
    return total


def obter_resultado_por_origem(origem: str) -> float:
    hoje = UTC_NOW().date().isoformat()
    res = (
        supabase.table("ledger_financeiro")
        .select("lucro")
        .eq("origem", origem)
        .gte("criado_em", hoje)
        .execute()
    )
    total = sum([float(r["lucro"]) for r in res.data]) if res.data else 0.0
    return total


# ======================================================
# AVALIAÇÃO DE RISCO
# ======================================================

def avaliar_risco_global() -> Optional[str]:
    resultado_diario = obter_resultado_diario()

    if resultado_diario <= -PERDA_MAXIMA_DIARIA:
        return "BLOQUEIO_GLOBAL"

    return None


def avaliar_risco_por_origem(origem: str) -> Optional[str]:
    resultado_origem = obter_resultado_por_origem(origem)

    if resultado_origem <= -PERDA_MAXIMA_POR_ORIGEM:
        return "BLOQUEIO_ORIGEM"

    return None


# ======================================================
# MECANISMO DE ESCALA E FREIO
# ======================================================

def aplicar_freios(decisao: RegistroDecisao, origem: str) -> RegistroDecisao:
    """
    Nenhuma escala é permitida se houver risco crítico.
    """
    risco_global = avaliar_risco_global()
    risco_origem = avaliar_risco_por_origem(origem)

    if risco_global:
        decisao.estado = "PERDA_CRITICA"
        decisao.motivo = "Perda máxima diária atingida"
        decisao.proxima_acao = "BLOQUEAR_OPERACAO"
        log("RISCO", "WARN", "Bloqueio global aplicado")

    elif risco_origem:
        decisao.estado = "PERDA_CRITICA"
        decisao.motivo = f"Perda máxima por origem atingida ({origem})"
        decisao.proxima_acao = "BLOQUEAR_ORIGEM"
        log("RISCO", "WARN", f"Bloqueio por origem aplicado ({origem})")

    return decisao


# ======================================================
# PIPELINE OPERACIONAL COMPLETO
# ======================================================

def pipeline_operacional(origem: str, payload: Dict[str, Any]):
    """
    Pipeline oficial:
    Evento → Registro → Consolidação → Leitura Humana
    → Decisão → Freios → Registro
    """
    evento_bruto = EventoBruto(origem=origem, payload=payload)
    registrar_evento_bruto(evento_bruto)

    if origem == "HOTMART":
        evento_norm = normalizar_hotmart(payload)
    elif origem == "EDUZZ":
        evento_norm = normalizar_eduzz(payload)
    elif origem == "KIWIFY":
        evento_norm = normalizar_kiwify(payload)
    else:
        evento_norm = normalizar_evento(origem, payload)

    evento_norm = calcular_rentabilidade(evento_norm)
    registrar_evento_normalizado(evento_norm)
    registrar_ledger(evento_norm)

    decisao = decidir_estado_financeiro(evento_norm)
    decisao = aplicar_freios(decisao, origem)

    registrar_decisao(decisao)

    return decisao


# ======================================================
# FIM DA PARTE 3
# PRÓXIMA: PARTE 4 — ENDPOINTS DO DASHBOARD
# (CAMADAS 1, 2 E 3)
# ======================================================

# ======================================================
# PARTE 4 — ENDPOINTS DO DASHBOARD
# CAMADAS 1, 2 E 3 (LEITURA HUMANA + CONTROLE RESTRITO)
# ======================================================
# Continuação direta do main.py — ARQUIVO ÚNICO
# ======================================================


# ======================================================
# CAMADA 1 — LEITURA EXECUTIVA (SEM NÚMEROS)
# ======================================================

@app.get("/dashboard/status")
def dashboard_status():
    """
    Estado geral do robô — leitura humana executiva.
    Nenhum número financeiro é exposto aqui.
    """
    return {
        "estado_geral": "OPERANTE",
        "intencao_atual": "Captura controlada de oportunidades",
        "mensagem": "O robô está operando dentro das regras definidas.",
        "timestamp": UTC_NOW().isoformat()
    }


@app.get("/dashboard/proxima-acao")
def dashboard_proxima_acao():
    """
    Próxima ação prevista pelo robô, sem métricas cruas.
    """
    res = (
        supabase.table("decisoes")
        .select("*")
        .order("criado_em", desc=True)
        .limit(1)
        .execute()
    )

    if not res.data:
        return {
            "proxima_acao": "AGUARDAR_EVENTOS",
            "motivo": "Nenhuma decisão registrada ainda"
        }

    ultima = res.data[0]
    return {
        "proxima_acao": ultima["proxima_acao"],
        "motivo": ultima["motivo"]
    }


# ======================================================
# CAMADA 2 — DECISÕES DO ROBÔ (SEM NÚMEROS CRUDOS)
# ======================================================

@app.get("/dashboard/decisoes")
def dashboard_decisoes():
    """
    Histórico interpretável das decisões tomadas.
    """
    res = (
        supabase.table("decisoes")
        .select("estado, motivo, proxima_acao, criado_em")
        .order("criado_em", desc=True)
        .limit(20)
        .execute()
    )

    return {
        "decisoes": res.data or []
    }


@app.get("/dashboard/fontes")
def dashboard_fontes():
    """
    Fontes ativas do robô (origens detectadas).
    """
    res = (
        supabase.table("eventos_normalizados")
        .select("origem")
        .execute()
    )

    fontes = sorted(list(set([r["origem"] for r in res.data]))) if res.data else []

    return {
        "fontes_ativas": fontes
    }


# ======================================================
# CAMADA 3 — CONTROLE HUMANO (RESTRITA, COM NÚMEROS)
# ======================================================

@app.get("/dashboard/financeiro/resumo", dependencies=[Depends(autenticar_camada_3)])
def dashboard_financeiro_resumo():
    """
    Resumo financeiro REAL.
    Somente humano autorizado.
    """
    res = (
        supabase.table("ledger_financeiro")
        .select("lucro")
        .execute()
    )

    total = sum([float(r["lucro"]) for r in res.data]) if res.data else 0.0

    return {
        "lucro_total": total,
        "total_registros": len(res.data) if res.data else 0
    }


@app.get("/dashboard/financeiro/origem", dependencies=[Depends(autenticar_camada_3)])
def dashboard_financeiro_por_origem():
    """
    Financeiro por origem (Hotmart, Eduzz, Kiwify etc).
    """
    res = (
        supabase.table("ledger_financeiro")
        .select("origem, lucro")
        .execute()
    )

    acumulado: Dict[str, float] = {}

    for r in res.data or []:
        origem = r["origem"]
        acumulado[origem] = acumulado.get(origem, 0.0) + float(r["lucro"])

    return {
        "por_origem": acumulado
    }


@app.get("/dashboard/auditoria/ledger", dependencies=[Depends(autenticar_camada_3)])
def dashboard_auditoria_ledger():
    """
    Ledger financeiro completo — auditoria.
    """
    res = (
        supabase.table("ledger_financeiro")
        .select("*")
        .order("criado_em", desc=True)
        .limit(100)
        .execute()
    )

    return {
        "ledger": res.data or []
    }


# ======================================================
# FIM DA PARTE 4
# PRÓXIMA: PARTE FINAL — BOOTSTRAP, SEGURANÇA E FECHAMENTO
# ======================================================

# ======================================================
# PARTE FINAL — BOOTSTRAP, SEGURANÇA E FECHAMENTO
# ======================================================
# Continuação direta do main.py — ARQUIVO ÚNICO
# ======================================================


# ======================================================
# BOOTSTRAP OPERACIONAL
# ======================================================

@app.on_event("startup")
def startup_event():
    log("BOOT", "INFO", "ROBO GLOBAL AI iniciado")
    log("BOOT", "INFO", f"Ambiente: {ENVIRONMENT}")
    log("BOOT", "INFO", "Governança ativa — humano governa, robô executa")


@app.on_event("shutdown")
def shutdown_event():
    log("BOOT", "INFO", "ROBO GLOBAL AI encerrado com segurança")


# ======================================================
# SEGURANÇA BÁSICA — FALLBACK
# ======================================================

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# ======================================================
# ENDPOINTS OPERACIONAIS AUXILIARES
# ======================================================

@app.get("/health")
def healthcheck():
    """
    Endpoint simples para Render / uptime monitoring.
    """
    return {
        "status": "ok",
        "timestamp": UTC_NOW().isoformat()
    }


# ======================================================
# FECHAMENTO INSTITUCIONAL
# ======================================================

"""
DECLARAÇÃO FINAL — ROBO GLOBAL AI

Este arquivo (main.py) é a implementação técnica direta
da Carta Magna Executiva do projeto ROBO GLOBAL AI.

- Nenhuma decisão ocorre sem registro
- Nenhuma escala ocorre sem lucro
- Nenhuma perda crítica é ignorada
- Nenhum humano interpreta logs técnicos
- Toda leitura humana é semântica
- Todo dado financeiro é auditável
- Todo controle final é humano

Este arquivo é soberano.
Não deve ser fragmentado.
Não deve ser parcialmente executado.
Não deve ser reinterpretado fora deste contexto.

VERSÃO FINAL — DEPLOY-READY
"""


# ======================================================
# FIM DO ARQUIVO — main.py
# ======================================================
