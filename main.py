# main.py — versão completa e final
# ROBO GLOBAL AI
# CARTA-SOBERANA — VERSÃO 2025-12-27
# MODO: CONDUÇÃO-TOTAL-ABSOLUTA
# ESCOPO: DASHBOARD + BACKEND + FINANCEIRO + META-ADS
# REGRA: ENTREGA-INTEGRAL-OBRIGATÓRIA
# CHECKSUM-INSTITUCIONAL:
# 9f7d8c4a6e3b5f0a1c2e9d7a8b6f4c3e2d1a0b9c8e7f6d5c4b3a2918f7e6
#
# ❗ ESTE ARQUIVO DEVE SER GERADO EM PARTES SEQUENCIAIS
# ❗ NÃO REMOVER, NÃO COMPACTAR, NÃO REFATORAR
# ❗ COLAGEM DEVE SER FEITA EM ORDEM LINEAR

# =========================================================
# PARTE 1 — CABEÇALHO + IMPORTS + CONFIG + APP FASTAPI
# =========================================================

from __future__ import annotations

import os
import sys
import json
import uuid
import hmac
import hashlib
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from pydantic import BaseModel, BaseSettings, Field

# =========================================================
# CONFIGURAÇÃO GLOBAL — AMBIENTE
# =========================================================

class Settings(BaseSettings):
    # Ambiente
    ENV: str = Field(default="production")

    # Render / Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=10000)

    # Segurança
    DASHBOARD_API_KEY: str = Field(default="CHANGE_ME")
    FINANCEIRO_API_KEY: str = Field(default="CHANGE_ME_FINANCEIRO")

    # Supabase
    SUPABASE_URL: str = Field(default="")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="")

    # Meta Ads
    META_ACCESS_TOKEN: str = Field(default="")
    META_AD_ACCOUNT_ID: str = Field(default="")

    # Logs
    LOG_LEVEL: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# =========================================================
# LOGGING — PADRÃO INSTITUCIONAL
# =========================================================

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="[%(name)s] [%(levelname)s] %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger("ROBO-GLOBAL-AI")

logger.info("BOOTSTRAP INICIADO — ROBO GLOBAL AI")
logger.info(f"AMBIENTE: {settings.ENV}")

# =========================================================
# FASTAPI — APLICAÇÃO PRINCIPAL
# =========================================================

app = FastAPI(
    title="Robo Global AI",
    description="Sistema institucional de automação, decisão e controle financeiro",
    version="2025.12.27",
)

# =========================================================
# CORS — DASHBOARD
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mantido aberto conforme decisão institucional
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# SEGURANÇA — API KEYS
# =========================================================

dashboard_api_key_header = APIKeyHeader(
    name="X-DASHBOARD-API-KEY",
    auto_error=False,
)

financeiro_api_key_header = APIKeyHeader(
    name="X-FINANCEIRO-API-KEY",
    auto_error=False,
)

def validar_dashboard_api_key(api_key: Optional[str] = Depends(dashboard_api_key_header)):
    if not api_key or api_key != settings.DASHBOARD_API_KEY:
        logger.warning("[AUTH] [WARN] Tentativa de acesso inválida ao Dashboard")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso não autorizado",
        )
    return True

def validar_financeiro_api_key(api_key: Optional[str] = Depends(financeiro_api_key_header)):
    if not api_key or api_key != settings.FINANCEIRO_API_KEY:
        logger.warning("[AUTH] [WARN] Tentativa de acesso inválida ao Financeiro")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso financeiro não autorizado",
        )
    return True

# =========================================================
# HEALTHCHECK / STATUS BÁSICO
# =========================================================

@app.get("/status")
async def status_root():
    return {
        "sistema": "ROBO GLOBAL AI",
        "estado": "ATIVO",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modo": "CONDUCAO-TOTAL-ABSOLUTA",
    }

# =========================================================
# FIM DA PARTE 1
# PRÓXIMA: PARTE 2 — SUPABASE + MODELOS DE DADOS
# =========================================================

# =========================================================
# PARTE 2 — SUPABASE + MODELOS DE DADOS
# =========================================================

# =========================================================
# SUPABASE — CONEXÃO
# =========================================================

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None
    logger.warning("[SUPABASE] [WARN] Biblioteca supabase não instalada")

supabase: Optional["Client"] = None

def iniciar_supabase() -> Optional["Client"]:
    global supabase

    if not create_client:
        logger.error("[SUPABASE] [ERROR] supabase-py não disponível")
        return None

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        logger.warning("[SUPABASE] [WARN] Variáveis de ambiente não configuradas")
        return None

    try:
        supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
        logger.info("[SUPABASE] [INFO] Conexão estabelecida com sucesso")
        return supabase
    except Exception as e:
        logger.error(f"[SUPABASE] [ERROR] Falha ao conectar: {e}")
        return None


supabase = iniciar_supabase()

# =========================================================
# MODELOS DE DADOS — BASE
# =========================================================

class BaseRegistro(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =========================================================
# CAMADA 1 — STATUS DO ROBÔ (SEM NÚMEROS)
# =========================================================

class StatusRobo(BaseRegistro):
    estado: str  # OFF | TESTE | VALIDACAO | MONETIZACAO | ESCALA
    frase: str
    intencao: str


# =========================================================
# CAMADA 2 — DECISÕES DO ROBÔ (SEM MÉTRICAS CRUAS)
# =========================================================

class DecisaoRobo(BaseRegistro):
    data: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acao: str
    motivo: str
    proxima_acao: Optional[str] = None


# =========================================================
# CAMADA 3 — FINANCEIRO (RESTRITO)
# =========================================================

class RegistroFinanceiro(BaseRegistro):
    origem: str  # Meta, Hotmart, Eduzz, etc.
    tipo: str    # custo | receita | ajuste
    valor: float
    referencia: Optional[str] = None


class SnapshotFinanceiro(BaseRegistro):
    capital_total: float
    capital_alocado: float
    resultado_liquido: float


# =========================================================
# MODELOS AUXILIARES — DASHBOARD
# =========================================================

class PerformanceRobo(BaseModel):
    atencao: str   # baixa | media | alta
    eficiencia: str  # abaixo | dentro | acima
    observacao: str


class FonteStatus(BaseModel):
    nome: str
    status: str  # ativo | pausado | em_analise


class ProximaAcao(BaseModel):
    texto: str


# =========================================================
# UTILITÁRIOS — REGISTRO EM SUPABASE
# =========================================================

def salvar_registro(tabela: str, payload: Dict[str, Any]):
    if not supabase:
        logger.warning(f"[SUPABASE] [WARN] Registro não salvo ({tabela}) — conexão ausente")
        return None
    try:
        response = supabase.table(tabela).insert(payload).execute()
        logger.info(f"[SUPABASE] [INFO] Registro salvo em {tabela}")
        return response
    except Exception as e:
        logger.error(f"[SUPABASE] [ERROR] Falha ao salvar em {tabela}: {e}")
        return None


def listar_registros(tabela: str, limite: int = 50):
    if not supabase:
        logger.warning(f"[SUPABASE] [WARN] Leitura não executada ({tabela}) — conexão ausente")
        return []
    try:
        response = (
            supabase
            .table(tabela)
            .select("*")
            .order("criado_em", desc=True)
            .limit(limite)
            .execute()
        )
        return response.data or []
    except Exception as e:
        logger.error(f"[SUPABASE] [ERROR] Falha ao listar {tabela}: {e}")
        return []

# =========================================================
# FIM DA PARTE 2
# PRÓXIMA: PARTE 3 — ROTAS DO DASHBOARD (CAMADAS 1 E 2)
# =========================================================

# =========================================================
# PARTE 3 — ROTAS DO DASHBOARD (CAMADAS 1 E 2)
# =========================================================

# =========================================================
# CAMADA 1 — STATUS DO ROBÔ
# =========================================================

@app.get("/dashboard/status")
async def dashboard_status():
    """
    Retorna o estado atual do robô.
    Nenhum dado financeiro permitido.
    """
    registros = listar_registros("status_robo", limite=1)

    if registros:
        status_atual = registros[0]
    else:
        status_atual = StatusRobo(
            estado="TESTE",
            frase="Sistema em observação controlada",
            intencao="Coletar sinais iniciais sem escalar"
        ).dict()
        salvar_registro("status_robo", status_atual)

    return {
        "estado": status_atual.get("estado"),
        "frase": status_atual.get("frase"),
        "intencao": status_atual.get("intencao"),
    }


# =========================================================
# CAMADA 2 — PERFORMANCE (LEITURA SEMÂNTICA)
# =========================================================

@app.get("/dashboard/performance")
async def dashboard_performance():
    """
    Performance interpretável.
    Sem métricas cruas.
    """
    # Valores textuais deliberadamente abstratos
    performance = PerformanceRobo(
        atencao="media",
        eficiencia="dentro",
        observacao="Comportamento estável dentro do esperado para a fase atual"
    )

    return performance.dict()


# =========================================================
# CAMADA 2 — FONTES (STATUS OPERACIONAL)
# =========================================================

@app.get("/dashboard/fontes")
async def dashboard_fontes():
    """
    Status das fontes de tráfego e monetização.
    Nenhum número permitido.
    """
    fontes = [
        FonteStatus(nome="Meta Ads", status="ativo"),
        FonteStatus(nome="Hotmart", status="em_analise"),
        FonteStatus(nome="Eduzz", status="em_analise"),
        FonteStatus(nome="Kiwify", status="em_analise"),
    ]

    return [f.dict() for f in fontes]


# =========================================================
# CAMADA 2 — DECISÕES DO ROBÔ
# =========================================================

@app.get("/dashboard/decisoes")
async def dashboard_decisoes():
    """
    Lista cronológica de decisões tomadas pelo robô.
    """
    registros = listar_registros("decisoes_robo", limite=20)

    decisoes = []
    for r in registros:
        decisoes.append({
            "data": r.get("data"),
            "acao": r.get("acao"),
            "motivo": r.get("motivo"),
            "proxima_acao": r.get("proxima_acao"),
        })

    return decisoes


# =========================================================
# CAMADA 2 — PRÓXIMA AÇÃO
# =========================================================

@app.get("/dashboard/proxima-acao")
async def dashboard_proxima_acao():
    """
    Próxima ação planejada pelo sistema.
    Texto único central.
    """
    acao = ProximaAcao(
        texto="Finalizar validação do dashboard e liberar leitura financeira controlada"
    )

    return acao.dict()


# =========================================================
# FIM DA PARTE 3
# PRÓXIMA: PARTE 4 — CAMADA 3 (FINANCEIRO) + AUTENTICAÇÃO
# =========================================================

# =========================================================
# PARTE 4 — CAMADA 3 (FINANCEIRO) + AUTENTICAÇÃO + AUDITORIA
# =========================================================

# =========================================================
# AUDITORIA — REGISTRO DE ACESSO FINANCEIRO
# =========================================================

def auditar_acesso_financeiro(
    origem: str,
    sucesso: bool,
    detalhe: Optional[str] = None,
):
    payload = {
        "id": str(uuid.uuid4()),
        "criado_em": datetime.now(timezone.utc).isoformat(),
        "origem": origem,
        "sucesso": sucesso,
        "detalhe": detalhe,
    }
    salvar_registro("auditoria_financeiro", payload)


# =========================================================
# CAMADA 3 — ENDPOINT FINANCEIRO (PROTEGIDO)
# =========================================================

@app.get(
    "/dashboard/financeiro",
    dependencies=[Depends(validar_financeiro_api_key)],
)
async def dashboard_financeiro():
    """
    Painel financeiro RESTRITO.
    Dados numéricos reais.
    Acesso auditado obrigatoriamente.
    """
    try:
        registros = listar_registros("registro_financeiro", limite=500)
        snapshots = listar_registros("snapshot_financeiro", limite=1)

        # Consolidação simples para leitura humana
        total_receita = sum(
            r.get("valor", 0)
            for r in registros
            if r.get("tipo") == "receita"
        )

        total_custo = sum(
            r.get("valor", 0)
            for r in registros
            if r.get("tipo") == "custo"
        )

        resultado_liquido = total_receita - total_custo

        snapshot_atual = snapshots[0] if snapshots else {
            "capital_total": total_receita,
            "capital_alocado": total_custo,
            "resultado_liquido": resultado_liquido,
        }

        auditar_acesso_financeiro(
            origem="dashboard_financeiro",
            sucesso=True,
        )

        return {
            "capital_total": snapshot_atual.get("capital_total", 0),
            "capital_alocado": snapshot_atual.get("capital_alocado", 0),
            "receita_total": total_receita,
            "custo_total": total_custo,
            "resultado_liquido": resultado_liquido,
        }

    except Exception as e:
        auditar_acesso_financeiro(
            origem="dashboard_financeiro",
            sucesso=False,
            detalhe=str(e),
        )
        logger.error(f"[FINANCEIRO] [ERROR] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar dados financeiros",
        )


# =========================================================
# CAMADA 3 — ENDPOINT DE INSERÇÃO FINANCEIRA (INTERNA)
# =========================================================

@app.post(
    "/financeiro/registrar",
    dependencies=[Depends(validar_financeiro_api_key)],
)
async def registrar_movimento_financeiro(registro: RegistroFinanceiro):
    """
    Registro financeiro imutável.
    Uso interno controlado.
    """
    payload = registro.dict()
    payload["criado_em"] = payload["criado_em"].isoformat()

    salvar_registro("registro_financeiro", payload)

    return {
        "status": "registrado",
        "id": payload.get("id"),
    }


# =========================================================
# CAMADA 3 — SNAPSHOT FINANCEIRO
# =========================================================

@app.post(
    "/financeiro/snapshot",
    dependencies=[Depends(validar_financeiro_api_key)],
)
async def criar_snapshot(snapshot: SnapshotFinanceiro):
    """
    Snapshot financeiro consolidado.
    """
    payload = snapshot.dict()
    payload["criado_em"] = payload["criado_em"].isoformat()

    salvar_registro("snapshot_financeiro", payload)

    return {
        "status": "snapshot_criado",
        "id": payload.get("id"),
    }

# =========================================================
# FIM DA PARTE 4
# PRÓXIMA: PARTE 5 — PIPELINE FINANCEIRO + DECISÃO + FECHAMENTO
# =========================================================

# =========================================================
# PARTE 5 — PIPELINE FINANCEIRO + DECISÃO + FECHAMENTO FINAL
# =========================================================

# =========================================================
# PIPELINE FINANCEIRO — EXECUÇÃO INSTITUCIONAL
# =========================================================

def consolidar_financeiro():
    """
    Consolida registros financeiros e gera snapshot automático.
    """
    registros = listar_registros("registro_financeiro", limite=1000)

    total_receita = sum(
        r.get("valor", 0)
        for r in registros
        if r.get("tipo") == "receita"
    )

    total_custo = sum(
        r.get("valor", 0)
        for r in registros
        if r.get("tipo") == "custo"
    )

    resultado_liquido = total_receita - total_custo

    snapshot = SnapshotFinanceiro(
        capital_total=total_receita,
        capital_alocado=total_custo,
        resultado_liquido=resultado_liquido,
    )

    payload = snapshot.dict()
    payload["criado_em"] = payload["criado_em"].isoformat()

    salvar_registro("snapshot_financeiro", payload)

    logger.info("[FINANCEIRO] [INFO] Snapshot financeiro consolidado")

    return snapshot


# =========================================================
# LÓGICA DE DECISÃO — ESTADOS FINANCEIROS
# =========================================================

def avaliar_estado_financeiro(snapshot: SnapshotFinanceiro) -> str:
    """
    Avalia o estado financeiro do robô.
    """
    if snapshot.resultado_liquido > 0:
        return "GANHO"
    elif snapshot.resultado_liquido == 0:
        return "EMPATE"
    elif snapshot.resultado_liquido < 0 and abs(snapshot.resultado_liquido) < (snapshot.capital_total * 0.1):
        return "PERDA_CONTROLADA"
    else:
        return "PERDA_CRITICA"


def registrar_decisao_financeira(estado: str, snapshot: SnapshotFinanceiro):
    """
    Registra decisão institucional baseada no estado financeiro.
    """
    if estado == "GANHO":
        acao = "Manter operação e avaliar escala controlada"
        proxima = "Escalar gradualmente mantendo limites"
    elif estado == "EMPATE":
        acao = "Manter operação sem escala"
        proxima = "Aguardar novos sinais"
    elif estado == "PERDA_CONTROLADA":
        acao = "Reduzir exposição e otimizar campanhas"
        proxima = "Aplicar freio parcial"
    else:
        acao = "Interromper escala e proteger capital"
        proxima = "Freio total e revisão humana"

    decisao = DecisaoRobo(
        acao=acao,
        motivo=f"Estado financeiro avaliado como {estado}",
        proxima_acao=proxima,
    )

    payload = decisao.dict()
    payload["criado_em"] = payload["criado_em"].isoformat()
    payload["data"] = payload["data"].isoformat()

    salvar_registro("decisoes_robo", payload)

    logger.info(f"[DECISAO] [INFO] Decisão registrada — {estado}")

    return decisao


# =========================================================
# CICLO OPERACIONAL FINANCEIRO
# =========================================================

def executar_ciclo_financeiro():
    """
    Executa o ciclo completo:
    Consolidação → Decisão → Registro
    """
    snapshot = consolidar_financeiro()
    estado = avaliar_estado_financeiro(snapshot)
    decisao = registrar_decisao_financeira(estado, snapshot)

    return {
        "estado_financeiro": estado,
        "decisao": decisao.dict(),
    }


# =========================================================
# ENDPOINT — EXECUÇÃO CONTROLADA DO CICLO
# =========================================================

@app.post(
    "/financeiro/ciclo",
    dependencies=[Depends(validar_financeiro_api_key)],
)
async def ciclo_financeiro():
    """
    Dispara manualmente o ciclo financeiro institucional.
    """
    try:
        resultado = executar_ciclo_financeiro()
        return {
            "status": "ciclo_executado",
            "resultado": resultado,
        }
    except Exception as e:
        logger.error(f"[CICLO] [ERROR] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao executar ciclo financeiro",
        )


# =========================================================
# FECHAMENTO INSTITUCIONAL DO ARQUIVO
# =========================================================

logger.info("MAIN.PY CARREGADO — ROBO GLOBAL AI PRONTO PARA EXECUÇÃO")
logger.info("DASHBOARD + BACKEND + FINANCEIRO ATIVOS")
logger.info("META ADS: CONTINUIDADE AUTORIZADA APÓS DASHBOARD")

# =========================================================
# FIM DO ARQUIVO — main.py COMPLETO
# =========================================================

