# main.py — versão completa e final PROATIVA
# Robo Global AI
# Arquitetura: Autônoma, Proativa, Geradora de Renda
# Modo: Produção Real
# NÃO compactar | NÃO omitir | NÃO refatorar sem autorização

import os
import json
import time
import hmac
import hashlib
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import requests
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# =========================================================
# CONFIGURAÇÕES DE AMBIENTE
# =========================================================

APP_NAME = "Robo Global AI"
ENV = os.getenv("ENV", "production")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HOTMART_SECRET = os.getenv("HOTMART_SECRET")
EDUZZ_SECRET = os.getenv("EDUZZ_SECRET")
KIWIFY_SECRET = os.getenv("KIWIFY_SECRET")

SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "300"))  # 5 min
DECISION_INTERVAL_SECONDS = int(os.getenv("DECISION_INTERVAL_SECONDS", "180"))
LOOP_INTERVAL_SECONDS = int(os.getenv("LOOP_INTERVAL_SECONDS", "60"))

# =========================================================
# LOGGER PADRONIZADO
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] [%(levelname)s] %(message)s"
)

logger = logging.getLogger("ROBO_GLOBAL")

def log_info(msg: str):
    logger.info(msg)

def log_warn(msg: str):
    logger.warning(msg)

def log_error(msg: str):
    logger.error(msg)

# =========================================================
# APP FASTAPI
# =========================================================

app = FastAPI(
    title=APP_NAME,
    version="3.0.0",
    description="Robô Global Autônomo de Afiliados — Proativo e Gerador de Renda"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# MODELOS BASE
# =========================================================

class EventoUniversal(BaseModel):
    origem: str
    evento: str
    payload: Dict[str, Any]
    recebido_em: datetime = datetime.utcnow()

class DecisaoRobo(BaseModel):
    acao: str
    justificativa: str
    score: float
    data: datetime = datetime.utcnow()

# =========================================================
# ESTADO GLOBAL DO ROBÔ (MEMÓRIA OPERACIONAL)
# =========================================================

ESTADO_ROBO = {
    "ultimo_scan": None,
    "ultima_decisao": None,
    "ciclo_ativo": True,
    "modo": "PROATIVO",
    "operacoes_registradas": 0
}

log_info("Robo Global AI inicializado em modo PROATIVO.")


# =========================================================
# CONECTOR SUPABASE
# =========================================================

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None
    log_warn("Supabase SDK não disponível. Operando em modo degradado.")

supabase: Optional["Client"] = None

def conectar_supabase():
    global supabase
    if not SUPABASE_URL or not SUPABASE_KEY:
        log_error("Supabase URL/KEY não configurados.")
        return None
    if create_client is None:
        log_error("SDK Supabase ausente.")
        return None
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    log_info("Supabase conectado com sucesso.")
    return supabase

conectar_supabase()

# =========================================================
# FUNÇÕES UTILITÁRIAS INTERNAS
# =========================================================

def agora_iso():
    return datetime.utcnow().isoformat()

def gerar_hash(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()

def registrar_evento_universal(evento: EventoUniversal):
    if not supabase:
        log_warn("Evento não persistido (Supabase indisponível).")
        return
    try:
        supabase.table("eventos").insert({
            "origem": evento.origem,
            "evento": evento.evento,
            "payload": evento.payload,
            "hash": gerar_hash(evento.payload),
            "recebido_em": evento.recebido_em.isoformat()
        }).execute()
        log_info(f"Evento registrado: {evento.origem} | {evento.evento}")
    except Exception as e:
        log_error(f"Falha ao registrar evento: {e}")

def registrar_decisao(decisao: DecisaoRobo):
    if not supabase:
        log_warn("Decisão não persistida (Supabase indisponível).")
        return
    try:
        supabase.table("decisoes").insert({
            "acao": decisao.acao,
            "justificativa": decisao.justificativa,
            "score": decisao.score,
            "data": decisao.data.isoformat()
        }).execute()
        ESTADO_ROBO["ultima_decisao"] = decisao.data
        log_info(f"Decisão registrada: {decisao.acao}")
    except Exception as e:
        log_error(f"Erro ao registrar decisão: {e}")

def registrar_operacao(descricao: str, dados: Dict[str, Any]):
    if not supabase:
        log_warn("Operação não persistida (Supabase indisponível).")
        return
    try:
        supabase.table("operacoes").insert({
            "descricao": descricao,
            "dados": dados,
            "data": agora_iso()
        }).execute()
        ESTADO_ROBO["operacoes_registradas"] += 1
        log_info(f"Operação registrada: {descricao}")
    except Exception as e:
        log_error(f"Erro ao registrar operação: {e}")


# =========================================================
# NÚCLEO INTELIGENTE DO ROBÔ
# =========================================================

def normalizar_evento(origem: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte eventos de qualquer plataforma para um formato universal
    """
    evento = {
        "origem": origem,
        "produto": payload.get("product_name") or payload.get("produto"),
        "valor": float(payload.get("price", 0) or payload.get("valor", 0)),
        "comissao": float(payload.get("commission", 0) or payload.get("comissao", 0)),
        "status": payload.get("status", "desconhecido"),
        "timestamp": agora_iso()
    }
    log_info(f"Evento normalizado: {evento}")
    return evento

def calcular_comissao(evento: Dict[str, Any]) -> float:
    valor = evento.get("valor", 0)
    taxa = evento.get("comissao", 0)
    comissao = valor * taxa if taxa <= 1 else taxa
    return round(comissao, 2)

def calcular_rentabilidade(evento: Dict[str, Any]) -> float:
    """
    Score interno de atratividade do produto
    """
    comissao = calcular_comissao(evento)
    score = comissao * 0.7
    if evento.get("status") == "aprovado":
        score *= 1.2
    return round(score, 2)

def analisar_produto(evento: Dict[str, Any]) -> DecisaoRobo:
    score = calcular_rentabilidade(evento)

    if score > 50:
        acao = "ESCALAR"
        justificativa = "Alta rentabilidade esperada"
    elif score > 10:
        acao = "TESTAR"
        justificativa = "Rentabilidade moderada"
    else:
        acao = "DESCARTAR"
        justificativa = "Baixa atratividade"

    decisao = DecisaoRobo(
        acao=acao,
        justificativa=justificativa,
        score=score
    )
    log_info(f"Decisão gerada: {decisao.acao} | Score {decisao.score}")
    return decisao

def escolher_melhor_oferta(eventos: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not eventos:
        return None
    eventos_ordenados = sorted(
        eventos,
        key=lambda e: calcular_rentabilidade(e),
        reverse=True
    )
    melhor = eventos_ordenados[0]
    log_info(f"Melhor oferta selecionada: {melhor.get('produto')}")
    return melhor


# =========================================================
# PIPELINE OPERACIONAL PROATIVO
# =========================================================

def pipeline_operacional(evento_normalizado: Dict[str, Any]):
    """
    Pipeline completo:
    normaliza → analisa → decide → registra
    """
    decisao = analisar_produto(evento_normalizado)
    registrar_decisao(decisao)
    registrar_operacao(
        descricao=f"Pipeline executado | {decisao.acao}",
        dados={
            "produto": evento_normalizado.get("produto"),
            "score": decisao.score
        }
    )
    return decisao

# =========================================================
# CICLO AUTÔNOMO DE DECISÃO (SEM ESTÍMULO EXTERNO)
# =========================================================

async def ciclo_autonomo():
    """
    Loop contínuo do robô:
    varre, decide e registra mesmo sem vendas
    """
    while ESTADO_ROBO["ciclo_ativo"]:
        try:
            log_info("Ciclo autônomo iniciado.")

            # Simulação de varredura ativa (placeholder real)
            eventos_detectados = []

            if supabase:
                try:
                    resp = supabase.table("eventos").select("*").limit(10).execute()
                    for e in resp.data or []:
                        eventos_detectados.append(e)
                except Exception as e:
                    log_error(f"Erro ao varrer eventos: {e}")

            melhor_oferta = escolher_melhor_oferta(eventos_detectados)

            if melhor_oferta:
                pipeline_operacional(melhor_oferta)
                ESTADO_ROBO["ultima_decisao"] = datetime.utcnow()
            else:
                log_info("Nenhuma oferta relevante no ciclo.")

            ESTADO_ROBO["ultimo_scan"] = datetime.utcnow()
            await asyncio.sleep(DECISION_INTERVAL_SECONDS)

        except Exception as e:
            log_error(f"Erro no ciclo autônomo: {e}")
            await asyncio.sleep(10)


# =========================================================
# SEGURANÇA — VALIDAÇÃO HMAC
# =========================================================

def validar_hmac(secret: str, payload: bytes, assinatura: str) -> bool:
    if not secret or not assinatura:
        return False
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    esperado = mac.hexdigest()
    return hmac.compare_digest(esperado, assinatura)

# =========================================================
# WEBHOOK UNIVERSAL
# =========================================================

@app.post("/webhook/universal")
async def webhook_universal(request: Request):
    payload = await request.json()
    evento = EventoUniversal(
        origem="universal",
        evento=payload.get("event", "desconhecido"),
        payload=payload
    )
    registrar_evento_universal(evento)

    evento_norm = normalizar_evento("universal", payload)
    pipeline_operacional(evento_norm)

    return {"status": "OK"}

# =========================================================
# WEBHOOK HOTMART
# =========================================================

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    raw = await request.body()
    assinatura = request.headers.get("X-Hotmart-Signature")

    if not validar_hmac(HOTMART_SECRET, raw, assinatura):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = json.loads(raw)
    evento = EventoUniversal(
        origem="hotmart",
        evento=payload.get("event"),
        payload=payload
    )
    registrar_evento_universal(evento)

    evento_norm = normalizar_evento("hotmart", payload)
    pipeline_operacional(evento_norm)

    return {"status": "OK"}

# =========================================================
# WEBHOOK EDUZZ
# =========================================================

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    raw = await request.body()
    assinatura = request.headers.get("X-Eduzz-Signature")

    if not validar_hmac(EDUZZ_SECRET, raw, assinatura):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = json.loads(raw)
    evento = EventoUniversal(
        origem="eduzz",
        evento=payload.get("event"),
        payload=payload
    )
    registrar_evento_universal(evento)

    evento_norm = normalizar_evento("eduzz", payload)
    pipeline_operacional(evento_norm)

    return {"status": "OK"}

# =========================================================
# WEBHOOK KIWIFY
# =========================================================

@app.post("/webhook/kiwify")
async def webhook_kiwify(request: Request):
    raw = await request.body()
    assinatura = request.headers.get("X-Kiwify-Signature")

    if not validar_hmac(KIWIFY_SECRET, raw, assinatura):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = json.loads(raw)
    evento = EventoUniversal(
        origem="kiwify",
        evento=payload.get("event"),
        payload=payload
    )
    registrar_evento_universal(evento)

    evento_norm = normalizar_evento("kiwify", payload)
    pipeline_operacional(evento_norm)

    return {"status": "OK"}


# =========================================================
# ENDPOINTS OPERACIONAIS
# =========================================================

@app.get("/status")
async def status():
    return {
        "status": "OK",
        "modo": ESTADO_ROBO["modo"],
        "ciclo_ativo": ESTADO_ROBO["ciclo_ativo"],
        "ultimo_scan": ESTADO_ROBO["ultimo_scan"],
        "ultima_decisao": ESTADO_ROBO["ultima_decisao"],
        "operacoes_registradas": ESTADO_ROBO["operacoes_registradas"],
        "supabase": "conectado" if supabase else "indisponivel"
    }

@app.get("/decisao")
async def decisao_atual():
    if not supabase:
        return {"decisao": None}
    try:
        resp = supabase.table("decisoes").select("*").order("data", desc=True).limit(1).execute()
        return resp.data[0] if resp.data else {"decisao": None}
    except Exception as e:
        log_error(f"Erro ao buscar decisão: {e}")
        return {"erro": "falha ao buscar decisão"}

@app.get("/analise")
async def analise_geral():
    """
    Visão macro do robô: eventos, decisões e performance
    """
    if not supabase:
        return {"erro": "supabase indisponivel"}
    try:
        eventos = supabase.table("eventos").select("*").limit(50).execute().data
        decisoes = supabase.table("decisoes").select("*").limit(20).execute().data
        return {
            "eventos_recentes": eventos,
            "decisoes_recentes": decisoes
        }
    except Exception as e:
        log_error(f"Erro na análise geral: {e}")
        return {"erro": "falha na analise"}

@app.get("/plano-diario")
async def plano_diario():
    """
    Plano gerado automaticamente pelo robô
    """
    return {
        "data": agora_iso(),
        "acoes_previstas": [
            "Varredura ativa de ofertas",
            "Análise de rentabilidade",
            "Decisão autônoma de escala"
        ],
        "modo": ESTADO_ROBO["modo"]
    }


# =========================================================
# INICIALIZAÇÃO AUTOMÁTICA DO ROBÔ (STARTUP)
# =========================================================

@app.on_event("startup")
async def iniciar_robo():
    """
    Ao subir a API, o robô entra automaticamente em modo PROATIVO
    """
    log_info("Startup detectado. Ativando ciclo autônomo do Robo Global AI.")
    ESTADO_ROBO["ciclo_ativo"] = True
    asyncio.create_task(ciclo_autonomo())

# =========================================================
# CONTROLE MANUAL (EMERGÊNCIA)
# =========================================================

@app.post("/ciclo/parar")
async def parar_ciclo():
    ESTADO_ROBO["ciclo_ativo"] = False
    log_warn("Ciclo autônomo interrompido manualmente.")
    return {"status": "ciclo_parado"}

@app.post("/ciclo/iniciar")
async def iniciar_ciclo():
    if not ESTADO_ROBO["ciclo_ativo"]:
        ESTADO_ROBO["ciclo_ativo"] = True
        asyncio.create_task(ciclo_autonomo())
        log_info("Ciclo autônomo reiniciado manualmente.")
    return {"status": "ciclo_ativo"}

# =========================================================
# FINAL DO ARQUIVO
# =========================================================

log_info("main.py carregado completamente. Robo Global AI OPERACIONAL.")


# =========================================================
# MÓDULO 1 — VARREDURA REAL DE MARKETPLACES
# =========================================================

MARKETPLACES = {
    "hotmart": {
        "catalog_url": "https://api.hotmart.com/v2/products",
        "headers": lambda: {"Authorization": f"Bearer {os.getenv('HOTMART_TOKEN', '')}"}
    },
    "eduzz": {
        "catalog_url": "https://api.eduzz.com/catalog",
        "headers": lambda: {"Authorization": f"Bearer {os.getenv('EDUZZ_TOKEN', '')}"}
    },
    "kiwify": {
        "catalog_url": "https://api.kiwify.com.br/products",
        "headers": lambda: {"Authorization": f"Bearer {os.getenv('KIWIFY_TOKEN', '')}"}
    }
}

def varrer_marketplace(nome: str, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    produtos = []
    try:
        r = requests.get(cfg["catalog_url"], headers=cfg["headers"](), timeout=15)
        if r.status_code == 200:
            data = r.json() or {}
            itens = data.get("items") or data.get("data") or []
            for it in itens:
                produtos.append({
                    "origem": nome,
                    "produto": it.get("name") or it.get("title"),
                    "valor": float(it.get("price", 0) or 0),
                    "comissao": float(it.get("commission", 0) or it.get("commission_rate", 0)),
                    "status": "catalogo",
                    "timestamp": agora_iso()
                })
        log_info(f"Varredura {nome}: {len(produtos)} produtos")
    except Exception as e:
        log_error(f"Erro varrendo {nome}: {e}")
    return produtos

async def loop_varredura_marketplaces():
    while ESTADO_ROBO["ciclo_ativo"]:
        for nome, cfg in MARKETPLACES.items():
            produtos = varrer_marketplace(nome, cfg)
            for p in produtos:
                pipeline_operacional(p)
        await asyncio.sleep(SCAN_INTERVAL_SECONDS)

@app.on_event("startup")
async def iniciar_varredura_marketplaces():
    asyncio.create_task(loop_varredura_marketplaces())
    log_info("Varredura real de marketplaces ATIVA.")


# =========================================================
# MÓDULO 2 — GERAÇÃO AUTOMÁTICA DE CONTEÚDO
# =========================================================

TIPOS_CONTEUDO = ["headline", "copy_curta", "cta"]

def gerar_headline(produto: str) -> str:
    return f"Descubra agora por que {produto} está mudando o jogo."

def gerar_copy_curta(produto: str, score: float) -> str:
    return (
        f"{produto} foi analisado pelo Robo Global AI e atingiu score {score}. "
        f"Alta atratividade detectada. Veja por que tanta gente está entrando."
    )

def gerar_cta() -> str:
    return "Acesse agora e confira os detalhes."

def gerar_conteudo(decisao: DecisaoRobo, produto: str) -> Dict[str, Any]:
    conteudo = {
        "produto": produto,
        "headline": gerar_headline(produto),
        "copy": gerar_copy_curta(produto, decisao.score),
        "cta": gerar_cta(),
        "score": decisao.score,
        "status": "READY",
        "gerado_em": agora_iso()
    }
    log_info(f"Conteúdo gerado para {produto}")
    return conteudo

def registrar_conteudo(conteudo: Dict[str, Any]):
    if not supabase:
        return
    try:
        supabase.table("conteudos").insert(conteudo).execute()
        log_info("Conteúdo registrado no Supabase.")
    except Exception as e:
        log_error(f"Erro ao registrar conteúdo: {e}")

def pipeline_conteudo(evento_normalizado: Dict[str, Any], decisao: DecisaoRobo):
    produto = evento_normalizado.get("produto") or "Produto"
    conteudo = gerar_conteudo(decisao, produto)
    registrar_conteudo(conteudo)

# Hook no pipeline principal
_original_pipeline = pipeline_operacional

def pipeline_operacional(evento_normalizado: Dict[str, Any]):
    decisao = analisar_produto(evento_normalizado)
    registrar_decisao(decisao)
    registrar_operacao(
        descricao=f"Pipeline executado | {decisao.acao}",
        dados={
            "produto": evento_normalizado.get("produto"),
            "score": decisao.score
        }
    )
    if decisao.acao in ("ESCALAR", "TESTAR"):
        pipeline_conteudo(evento_normalizado, decisao)
    return decisao


# =========================================================
# MÓDULO 3 — ESCALA ORGÂNICA (SOCIAL)
# =========================================================

REDES_SOCIAIS = ["instagram", "tiktok", "youtube", "facebook"]

def priorizar_conteudos():
    if not supabase:
        return []
    try:
        resp = (
            supabase
            .table("conteudos")
            .select("*")
            .eq("status", "READY")
            .order("score", desc=True)
            .limit(10)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        log_error(f"Erro ao priorizar conteúdos: {e}")
        return []

def planejar_publicacao(conteudo: Dict[str, Any]) -> Dict[str, Any]:
    plano = {
        "produto": conteudo.get("produto"),
        "headline": conteudo.get("headline"),
        "copy": conteudo.get("copy"),
        "cta": conteudo.get("cta"),
        "redes": REDES_SOCIAIS,
        "status": "SCHEDULED",
        "agendado_em": agora_iso()
    }
    log_info(f"Conteúdo planejado para escala orgânica: {conteudo.get('produto')}")
    return plano

def registrar_plano_publicacao(plano: Dict[str, Any]):
    if not supabase:
        return
    try:
        supabase.table("publicacoes").insert(plano).execute()
        supabase.table("conteudos").update(
            {"status": "SCHEDULED"}
        ).eq("produto", plano.get("produto")).execute()
        log_info("Plano de publicação registrado.")
    except Exception as e:
        log_error(f"Erro ao registrar plano de publicação: {e}")

async def loop_escala_organica():
    while ESTADO_ROBO["ciclo_ativo"]:
        conteudos = priorizar_conteudos()
        for c in conteudos:
            plano = planejar_publicacao(c)
            registrar_plano_publicacao(plano)
        await asyncio.sleep(600)  # a cada 10 min

@app.on_event("startup")
async def iniciar_escala_organica():
    asyncio.create_task(loop_escala_organica())
    log_info("Escala orgânica ATIVA (modo planejamento).")


# =========================================================
# MÓDULO 4 — ESCALA PAGA CONTROLADA
# =========================================================

CAPITAL_CONFIG = {
    "capital_total": float(os.getenv("CAPITAL_TOTAL", "1000")),
    "risco_max_por_acao": float(os.getenv("RISCO_MAX_POR_ACAO", "0.02")),  # 2%
    "cpa_max": float(os.getenv("CPA_MAX", "50")),
}

def simular_roi(conteudo: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulação conservadora de ROI antes de qualquer gasto real
    """
    score = conteudo.get("score", 0)
    investimento = CAPITAL_CONFIG["capital_total"] * CAPITAL_CONFIG["risco_max_por_acao"]
    retorno_estimado = investimento * (score / 50)  # heurística interna

    roi = (retorno_estimado - investimento) / investimento if investimento > 0 else 0

    simulacao = {
        "produto": conteudo.get("produto"),
        "investimento_sugerido": round(investimento, 2),
        "retorno_estimado": round(retorno_estimado, 2),
        "roi_estimado": round(roi, 2),
        "cpa_max": CAPITAL_CONFIG["cpa_max"],
        "status": "SIMULADO",
        "simulado_em": agora_iso()
    }
    log_info(f"ROI simulado para {conteudo.get('produto')} | ROI {simulacao['roi_estimado']}")
    return simulacao

def registrar_simulacao(simulacao: Dict[str, Any]):
    if not supabase:
        return
    try:
        supabase.table("escala_paga").insert(simulacao).execute()
        log_info("Simulação de escala paga registrada.")
    except Exception as e:
        log_error(f"Erro ao registrar simulação paga: {e}")

async def loop_escala_paga_controlada():
    """
    NÃO gasta dinheiro.
    Apenas prepara e registra cenários matematicamente viáveis.
    """
    while ESTADO_ROBO["ciclo_ativo"]:
        if not supabase:
            await asyncio.sleep(300)
            continue

        try:
            resp = (
                supabase
                .table("conteudos")
                .select("*")
                .eq("status", "SCHEDULED")
                .order("score", desc=True)
                .limit(5)
                .execute()
            )
            for c in resp.data or []:
                simulacao = simular_roi(c)
                if simulacao["roi_estimado"] > 0:
                    registrar_simulacao(simulacao)
        except Exception as e:
            log_error(f"Erro no loop de escala paga: {e}")

        await asyncio.sleep(900)  # a cada 15 min

@app.on_event("startup")
async def iniciar_escala_paga():
    asyncio.create_task(loop_escala_paga_controlada())
    log_info("Escala paga CONTROLADA ATIVA (somente simulação).")

# =========================================================
# SISTEMA 100% ATIVO
# =========================================================

log_info("🔥 Robo Global AI OPERANDO EM CAPACIDADE MÁXIMA 🔥")
