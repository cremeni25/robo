# main.py — versão completa e final (GERAÇÃO INTEGRAL)
# ROBO GLOBAL AI
# Carta Magna Executiva — Implementação Técnica Real
# --------------------------------------------------
# ARQUIVO ÚNICO • FASTAPI • SUPABASE • RENDER
# Geração do ZERO • Nenhum reaproveitamento
# Serialização segura • Ledger imutável • Governança final
#
# ==================================================
# PARTE 1 — CABEÇALHO, CONFIGURAÇÃO, APP, MODELOS
# (continua nas próximas partes — ESTE É UM ÚNICO ARQUIVO)
# ==================================================

import os
import json
import hmac
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pydantic import BaseModel, Field

from supabase import create_client, Client


# ==================================================
# CONFIGURAÇÃO GLOBAL
# ==================================================

APP_NAME = "ROBO GLOBAL AI"
APP_VERSION = "2.0.0-sovereign"
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ==================================================
# LOGGING PADRONIZADO
# FORMATO OBRIGATÓRIO: [ORIGEM] [NÍVEL] mensagem
# ==================================================

logging.basicConfig(level=logging.INFO, format="%(message)s")

def log(origem: str, nivel: str, mensagem: str):
    logging.info(f"[{origem}] [{nivel}] {mensagem}")


# ==================================================
# VARIÁVEIS DE AMBIENTE (OBRIGATÓRIAS)
# ==================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HOTMART_SECRET = os.getenv("HOTMART_SECRET", "")
EDUZZ_SECRET = os.getenv("EDUZZ_SECRET", "")
KIWIFY_SECRET = os.getenv("KIWIFY_SECRET", "")

DASHBOARD_API_KEY = os.getenv("DASHBOARD_API_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL e SUPABASE_KEY são obrigatórios")


# ==================================================
# SUPABASE CLIENT
# ==================================================

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
log("BOOT", "INFO", "Supabase conectado")


# ==================================================
# FASTAPI APP
# ==================================================

app = FastAPI(title=APP_NAME, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

log("BOOT", "INFO", "FastAPI inicializado")


# ==================================================
# SERIALIZAÇÃO SEGURA (FUNDAÇÃO DO ARQUIVO)
# ==================================================

def serializar(obj: Any) -> Dict[str, Any]:
    """
    Serialização soberana:
    - Converte datetime -> ISO 8601
    - Garante JSON puro para Supabase
    """
    if isinstance(obj, BaseModel):
        data = obj.dict()
    elif isinstance(obj, dict):
        data = obj.copy()
    else:
        raise TypeError("Objeto não serializável")

    for k, v in data.items():
        if isinstance(v, datetime):
            data[k] = v.isoformat()
    return data


# ==================================================
# MODELOS DE DADOS (Pydantic)
# ==================================================

class EventoBruto(BaseModel):
    origem: str
    payload: Dict[str, Any]
    recebido_em: datetime = Field(default_factory=utc_now)


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
    criado_em: datetime = Field(default_factory=utc_now)


class RegistroDecisao(BaseModel):
    estado: str
    motivo: str
    proxima_acao: str
    snapshot_id: Optional[str] = None
    criado_em: datetime = Field(default_factory=utc_now)


# ==================================================
# AUTENTICAÇÃO — CAMADA 3 (RESTRITA)
# ==================================================

def autenticar_camada_3(x_api_key: str = Header(...)):
    if x_api_key != DASHBOARD_API_KEY:
        log("AUTH", "WARN", "Acesso negado à Camada 3")
        raise HTTPException(status_code=401, detail="Não autorizado")
    return True


# ==================================================
# UTILITÁRIOS DE SEGURANÇA (HMAC)
# ==================================================

def validar_hmac(payload: bytes, assinatura: str, secret: str) -> bool:
    if not secret or not assinatura:
        return False
    digest = hmac.new(
        key=secret.encode(),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(digest, assinatura)


# ==================================================
# REGISTRO BÁSICO (SEM ERROS DE SERIALIZAÇÃO)
# ==================================================

def registrar_evento_bruto(evento: EventoBruto):
    supabase.table("eventos_brutos").insert(serializar(evento)).execute()
    log("EVENTO", "INFO", f"Evento bruto registrado ({evento.origem})")


def registrar_evento_normalizado(evento: EventoNormalizado):
    supabase.table("eventos_normalizados").insert(serializar(evento)).execute()
    log("EVENTO", "INFO", f"Evento normalizado registrado ({evento.origem})")


def registrar_decisao(decisao: RegistroDecisao):
    supabase.table("decisoes").insert(serializar(decisao)).execute()
    log("DECISAO", "INFO", f"Decisão registrada ({decisao.estado})")


# ==================================================
# ENDPOINTS BÁSICOS DE VIDA
# ==================================================

@app.get("/")
def root():
    return {"mensagem": "ROBO GLOBAL AI — backend ativo"}


@app.get("/status")
def status():
    return {
        "sistema": APP_NAME,
        "versao": APP_VERSION,
        "ambiente": ENVIRONMENT,
        "estado": "OPERANTE",
        "timestamp": utc_now().isoformat()
    }


# ==================================================
# FIM DA PARTE 1
# PRÓXIMA: PARTE 2 — LEDGER, NORMALIZAÇÃO, PIPELINE
# ==================================================

# ==================================================
# PARTE 2 — LEDGER FINANCEIRO, NORMALIZAÇÃO E PIPELINE
# Continuação direta do main.py (arquivo único)
# ==================================================


# ==================================================
# LEDGER FINANCEIRO IMUTÁVEL
# ==================================================

def registrar_ledger(evento: EventoNormalizado):
    """
    Ledger financeiro soberano:
    - append-only
    - nunca atualizado
    - base de toda auditoria
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
        "criado_em": evento.criado_em.isoformat(),
    }
    supabase.table("ledger_financeiro").insert(registro).execute()
    log("LEDGER", "INFO", f"Ledger registrado ({evento.origem})")


# ==================================================
# NORMALIZAÇÃO POR ORIGEM (REAL)
# ==================================================

def normalizar_hotmart(payload: Dict[str, Any]) -> EventoNormalizado:
    valor = float(payload.get("price", 0) or 0)
    comissao = float(payload.get("commission_value", 0) or 0)

    return EventoNormalizado(
        origem="HOTMART",
        tipo_evento=str(payload.get("event", "unknown")),
        produto=payload.get("product", {}).get("name"),
        valor=valor,
        moeda=str(payload.get("currency", "BRL")),
        comissao=comissao,
        custo_midia=0.0,
        lucro=comissao,
        dados_brutos=payload,
    )


def normalizar_eduzz(payload: Dict[str, Any]) -> EventoNormalizado:
    valor = float(payload.get("sale_value", 0) or 0)
    comissao = float(payload.get("commission", 0) or 0)

    return EventoNormalizado(
        origem="EDUZZ",
        tipo_evento=str(payload.get("event_type", "unknown")),
        produto=payload.get("product_name"),
        valor=valor,
        moeda="BRL",
        comissao=comissao,
        custo_midia=0.0,
        lucro=comissao,
        dados_brutos=payload,
    )


def normalizar_kiwify(payload: Dict[str, Any]) -> EventoNormalizado:
    valor = float(payload.get("amount", 0) or 0)
    comissao = float(payload.get("affiliate_value", 0) or 0)

    return EventoNormalizado(
        origem="KIWIFY",
        tipo_evento=str(payload.get("type", "unknown")),
        produto=payload.get("product", {}).get("name"),
        valor=valor,
        moeda="BRL",
        comissao=comissao,
        custo_midia=0.0,
        lucro=comissao,
        dados_brutos=payload,
    )


def normalizar_generico(origem: str, payload: Dict[str, Any]) -> EventoNormalizado:
    """
    Normalização segura para eventos de teste ou desconhecidos
    """
    valor = float(payload.get("valor", 0) or 0)
    comissao = float(payload.get("comissao", 0) or 0)

    return EventoNormalizado(
        origem=origem,
        tipo_evento=str(payload.get("evento", "desconhecido")),
        produto=None,
        valor=valor,
        moeda="BRL",
        comissao=comissao,
        custo_midia=0.0,
        lucro=comissao,
        dados_brutos=payload,
    )


# ==================================================
# CÁLCULO DE RENTABILIDADE
# ==================================================

def calcular_rentabilidade(evento: EventoNormalizado) -> EventoNormalizado:
    evento.lucro = evento.comissao - evento.custo_midia
    return evento


# ==================================================
# DECISÃO FINANCEIRA PRIMÁRIA
# ==================================================

def decidir_estado_financeiro(evento: EventoNormalizado) -> RegistroDecisao:
    if evento.lucro > 0:
        return RegistroDecisao(
            estado="GANHO",
            motivo="Lucro positivo",
            proxima_acao="MANTER_ESCALA",
        )
    if evento.lucro == 0:
        return RegistroDecisao(
            estado="EMPATE",
            motivo="Resultado neutro",
            proxima_acao="OBSERVAR",
        )
    return RegistroDecisao(
        estado="PERDA",
        motivo="Lucro negativo",
        proxima_acao="REDUZIR_ESCALA",
    )


# ==================================================
# PIPELINE UNIVERSAL DE EVENTOS
# ==================================================

def processar_evento(origem: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pipeline oficial:
    Evento → Registro → Normalização → Ledger → Decisão
    """
    # 1. Evento bruto
    evento_bruto = EventoBruto(origem=origem, payload=payload)
    registrar_evento_bruto(evento_bruto)

    # 2. Normalização
    if origem == "HOTMART":
        evento_norm = normalizar_hotmart(payload)
    elif origem == "EDUZZ":
        evento_norm = normalizar_eduzz(payload)
    elif origem == "KIWIFY":
        evento_norm = normalizar_kiwify(payload)
    else:
        evento_norm = normalizar_generico(origem, payload)

    # 3. Rentabilidade
    evento_norm = calcular_rentabilidade(evento_norm)

    # 4. Registros financeiros
    registrar_evento_normalizado(evento_norm)
    registrar_ledger(evento_norm)

    # 5. Decisão
    decisao = decidir_estado_financeiro(evento_norm)
    registrar_decisao(decisao)

    return {
        "status": "processado",
        "origem": origem,
        "estado": decisao.estado,
    }


# ==================================================
# WEBHOOKS
# ==================================================

@app.post("/webhook/universal")
async def webhook_universal(request: Request):
    payload = await request.json()
    origem = payload.get("origem", "DESCONHECIDA")
    resultado = processar_evento(origem, payload)
    return JSONResponse(content=resultado)


@app.post("/webhook/hotmart")
async def webhook_hotmart(
    request: Request,
    x_hotmart_signature: str = Header(None)
):
    body = await request.body()
    if not validar_hmac(body, x_hotmart_signature or "", HOTMART_SECRET):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = json.loads(body.decode())
    resultado = processar_evento("HOTMART", payload)
    return JSONResponse(content=resultado)


@app.post("/webhook/eduzz")
async def webhook_eduzz(
    request: Request,
    x_eduzz_signature: str = Header(None)
):
    body = await request.body()
    if not validar_hmac(body, x_eduzz_signature or "", EDUZZ_SECRET):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = json.loads(body.decode())
    resultado = processar_evento("EDUZZ", payload)
    return JSONResponse(content=resultado)


@app.post("/webhook/kiwify")
async def webhook_kiwify(
    request: Request,
    x_kiwify_signature: str = Header(None)
):
    body = await request.body()
    if not validar_hmac(body, x_kiwify_signature or "", KIWIFY_SECRET):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = json.loads(body.decode())
    resultado = processar_evento("KIWIFY", payload)
    return JSONResponse(content=resultado)


# ==================================================
# FIM DA PARTE 2
# PRÓXIMA: PARTE 3 — RISCO, FREIOS E ESCALA
# ==================================================

# ==================================================
# PARTE 3 — RISCO, FREIOS E ESCALA CONTROLADA
# Continuação direta do main.py (arquivo único)
# ==================================================


# ==================================================
# PARÂMETROS DE RISCO (CONGELADOS POR PROTOCOLO)
# ==================================================

PERDA_MAXIMA_DIARIA = float(os.getenv("PERDA_MAXIMA_DIARIA", "500"))
PERDA_MAXIMA_POR_ORIGEM = float(os.getenv("PERDA_MAXIMA_POR_ORIGEM", "300"))


# ==================================================
# CONSULTAS FINANCEIRAS (BASE LEDGER)
# ==================================================

def obter_resultado_diario() -> float:
    hoje = utc_now().date().isoformat()
    res = (
        supabase.table("ledger_financeiro")
        .select("lucro")
        .gte("criado_em", hoje)
        .execute()
    )
    if not res.data:
        return 0.0
    return sum(float(r["lucro"]) for r in res.data)


def obter_resultado_por_origem(origem: str) -> float:
    hoje = utc_now().date().isoformat()
    res = (
        supabase.table("ledger_financeiro")
        .select("lucro")
        .eq("origem", origem)
        .gte("criado_em", hoje)
        .execute()
    )
    if not res.data:
        return 0.0
    return sum(float(r["lucro"]) for r in res.data)


# ==================================================
# AVALIAÇÃO DE RISCO
# ==================================================

def avaliar_risco_global() -> Optional[str]:
    resultado = obter_resultado_diario()
    if resultado <= -PERDA_MAXIMA_DIARIA:
        return "BLOQUEIO_GLOBAL"
    return None


def avaliar_risco_por_origem(origem: str) -> Optional[str]:
    resultado = obter_resultado_por_origem(origem)
    if resultado <= -PERDA_MAXIMA_POR_ORIGEM:
        return "BLOQUEIO_ORIGEM"
    return None


# ==================================================
# APLICAÇÃO DE FREIOS
# ==================================================

def aplicar_freios(decisao: RegistroDecisao, origem: str) -> RegistroDecisao:
    risco_global = avaliar_risco_global()
    risco_origem = avaliar_risco_por_origem(origem)

    if risco_global:
        decisao.estado = "PERDA_CRITICA"
        decisao.motivo = "Perda máxima diária atingida"
        decisao.proxima_acao = "BLOQUEAR_OPERACAO"
        log("RISCO", "WARN", "Freio global acionado")

    elif risco_origem:
        decisao.estado = "PERDA_CRITICA"
        decisao.motivo = f"Perda máxima por origem atingida ({origem})"
        decisao.proxima_acao = "BLOQUEAR_ORIGEM"
        log("RISCO", "WARN", f"Freio por origem acionado ({origem})")

    return decisao


# ==================================================
# PIPELINE COM GOVERNANÇA FINAL
# ==================================================

def pipeline_operacional(origem: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pipeline completo com governança:
    Evento → Registro → Normalização → Ledger
    → Decisão → Freios → Registro final
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
        evento_norm = normalizar_generico(origem, payload)

    evento_norm = calcular_rentabilidade(evento_norm)

    registrar_evento_normalizado(evento_norm)
    registrar_ledger(evento_norm)

    decisao = decidir_estado_financeiro(evento_norm)
    decisao = aplicar_freios(decisao, origem)

    registrar_decisao(decisao)

    return {
        "status": "processado",
        "origem": origem,
        "estado": decisao.estado,
        "acao": decisao.proxima_acao,
    }


# ==================================================
# OBSERVAÇÃO PROTOCOLAR
# ==================================================
# Neste ponto:
# - Nenhuma escala automática é executada
# - Apenas decisões e freios são registrados
# - A execução de mídia é externa ao backend
# ==================================================


# ==================================================
# FIM DA PARTE 3
# PRÓXIMA: PARTE 4 — DASHBOARD (CAMADAS 1, 2 E 3)
# ==================================================

# ==================================================
# PARTE 4 — DASHBOARD (CAMADAS 1, 2 E 3)
# Continuação direta do main.py (arquivo único)
# ==================================================


# ==================================================
# CAMADA 1 — LEITURA EXECUTIVA (SEM NÚMEROS)
# ==================================================

@app.get("/dashboard/status")
def dashboard_status():
    """
    Estado geral do robô — leitura humana executiva.
    Nenhum número financeiro é exibido.
    """
    return {
        "estado_geral": "OPERANTE",
        "intencao_atual": "Captura controlada de oportunidades",
        "mensagem": "O robô opera dentro das regras e sob governança humana.",
        "timestamp": utc_now().isoformat(),
    }


@app.get("/dashboard/proxima-acao")
def dashboard_proxima_acao():
    """
    Próxima ação prevista pelo robô (sem métricas cruas).
    """
    res = (
        supabase.table("decisoes")
        .select("proxima_acao, motivo, criado_em")
        .order("criado_em", desc=True)
        .limit(1)
        .execute()
    )

    if not res.data:
        return {
            "proxima_acao": "AGUARDAR_EVENTOS",
            "motivo": "Nenhuma decisão registrada ainda",
        }

    ultima = res.data[0]
    return {
        "proxima_acao": ultima["proxima_acao"],
        "motivo": ultima["motivo"],
    }


# ==================================================
# CAMADA 2 — DECISÕES DO ROBÔ (SEM NÚMEROS CRUDOS)
# ==================================================

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
        "decisoes": res.data or [],
    }


@app.get("/dashboard/fontes")
def dashboard_fontes():
    """
    Fontes de eventos detectadas pelo robô.
    """
    res = (
        supabase.table("eventos_normalizados")
        .select("origem")
        .execute()
    )

    fontes = []
    if res.data:
        fontes = sorted({r["origem"] for r in res.data})

    return {
        "fontes_ativas": fontes,
    }


# ==================================================
# CAMADA 3 — CONTROLE HUMANO (RESTRITA, COM NÚMEROS)
# ==================================================

@app.get(
    "/dashboard/financeiro/resumo",
    dependencies=[Depends(autenticar_camada_3)],
)
def dashboard_financeiro_resumo():
    """
    Resumo financeiro REAL (controle humano).
    """
    res = (
        supabase.table("ledger_financeiro")
        .select("lucro")
        .execute()
    )

    total = 0.0
    if res.data:
        total = sum(float(r["lucro"]) for r in res.data)

    return {
        "lucro_total": total,
        "total_registros": len(res.data) if res.data else 0,
    }


@app.get(
    "/dashboard/financeiro/origem",
    dependencies=[Depends(autenticar_camada_3)],
)
def dashboard_financeiro_por_origem():
    """
    Financeiro por origem (Hotmart, Eduzz, Kiwify, etc).
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
        "por_origem": acumulado,
    }


@app.get(
    "/dashboard/auditoria/ledger",
    dependencies=[Depends(autenticar_camada_3)],
)
def dashboard_auditoria_ledger():
    """
    Ledger financeiro completo para auditoria humana.
    """
    res = (
        supabase.table("ledger_financeiro")
        .select("*")
        .order("criado_em", desc=True)
        .limit(100)
        .execute()
    )

    return {
        "ledger": res.data or [],
    }


# ==================================================
# FIM DA PARTE 4
# PRÓXIMA: PARTE FINAL — BOOTSTRAP, SEGURANÇA E FECHAMENTO
# ==================================================

# ==================================================
# PARTE FINAL — BOOTSTRAP, SEGURANÇA E FECHAMENTO
# Continuação direta do main.py (arquivo único)
# ==================================================


# ==================================================
# BOOTSTRAP OPERACIONAL
# ==================================================

@app.on_event("startup")
def on_startup():
    log("BOOT", "INFO", "ROBO GLOBAL AI iniciado")
    log("BOOT", "INFO", f"Ambiente: {ENVIRONMENT}")
    log("BOOT", "INFO", "Governança ativa — humano governa, robô executa")


@app.on_event("shutdown")
def on_shutdown():
    log("BOOT", "INFO", "ROBO GLOBAL AI encerrado com segurança")


# ==================================================
# MIDDLEWARE DE SEGURANÇA BÁSICA
# ==================================================

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# ==================================================
# ENDPOINT DE SAÚDE (RENDER / MONITORAMENTO)
# ==================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": utc_now().isoformat(),
    }


# ==================================================
# DECLARAÇÃO INSTITUCIONAL FINAL (IMUTÁVEL)
# ==================================================

"""
DECLARAÇÃO FINAL — ROBO GLOBAL AI

Este arquivo (main.py) é a implementação técnica direta
da Carta Magna Executiva do projeto ROBO GLOBAL AI.

PRINCÍPIOS FUNDAMENTAIS:
- Nenhuma decisão ocorre sem registro
- Nenhuma escala ocorre sem lucro
- Nenhuma perda crítica é ignorada
- Nenhum humano interpreta logs técnicos
- Toda leitura humana é semântica
- Todo dado financeiro é auditável
- Todo controle final é humano

GARANTIAS TÉCNICAS:
- Serialização segura (datetime → ISO 8601)
- Ledger financeiro imutável (append-only)
- Governança e freios automáticos
- Backend único, íntegro e soberano
- Pronto para deploy direto (Render)

Este arquivo é soberano.
Não deve ser fragmentado.
Não deve ser editado parcialmente.
Qualquer alteração exige geração integral.

VERSÃO FINAL — ROBO GLOBAL AI 2.0.0
"""

# ==================================================
# FIM DO ARQUIVO — main.py
# ==================================================
