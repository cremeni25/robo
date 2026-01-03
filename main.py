# main.py — ROBO GLOBAL AI
# VERSÃO FINAL BOOT-SAFE
# COMPATÍVEL COM RENDER (WEB SERVICE)
# COEXISTE COM WORKER (operational_loop.py)
# PYTHON 3.13 | FASTAPI 0.110 | PYDANTIC v2
# SUBSTITUIÇÃO INTEGRAL DO ARQUIVO

from __future__ import annotations

import os
import sys
import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# ==============================
# Affiliate Platforms Routers
# ==============================
from affiliate.hotmart import router as hotmart_router
from affiliate.eduzz import router as eduzz_router
from affiliate.monetizze import router as monetizze_router
from affiliate.clickbank import router as clickbank_router
from controlador_acao_externa import router as acquisition_router

# =========================================================
# SETTINGS — BOOT SAFE (NUNCA QUEBRA NO IMPORT)
# =========================================================

class Settings(BaseSettings):
    ENV: str = "production"

    # CHAVES — OPCIONAIS NO BOOT
    DASHBOARD_API_KEY: Optional[str] = None
    FINANCEIRO_API_KEY: Optional[str] = None

    META_ACCESS_TOKEN: Optional[str] = None
    META_AD_ACCOUNT_ID: Optional[str] = None

    STRIPE_API_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="[%(name)s] [%(levelname)s] %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger("ROBO-GLOBAL-AI")
logger.info("BOOT OK — ROBO GLOBAL AI (WEB SERVICE)")
# =========================================================
# FASTAPI APP (WEB SERVICE)
# =========================================================

app = FastAPI(
    title="Robo Global AI",
    version="2025.12.29",
)

# ==============================
# Affiliate Platforms
# ==============================
app.include_router(hotmart_router)
app.include_router(eduzz_router)
app.include_router(monetizze_router)
app.include_router(clickbank_router)
app.include_router(acquisition_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# =========================================================
# SEGURANÇA — BOOT SAFE
# Validação ocorre SOMENTE ao acessar rotas protegidas
# =========================================================

dashboard_key = APIKeyHeader(
    name="X-DASHBOARD-API-KEY",
    auto_error=False
)

financeiro_key = APIKeyHeader(
    name="X-FINANCEIRO-API-KEY",
    auto_error=False
)


def require_dashboard_key(key: Optional[str] = Depends(dashboard_key)):
    if not settings.DASHBOARD_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DASHBOARD_API_KEY não configurada no ambiente"
        )
    if key != settings.DASHBOARD_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de dashboard inválida"
        )
    return True


def require_financeiro_key(key: Optional[str] = Depends(financeiro_key)):
    if not settings.FINANCEIRO_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="FINANCEIRO_API_KEY não configurada no ambiente"
        )
    if key != settings.FINANCEIRO_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave financeira inválida"
        )
    return True
# =========================================================
# SUPABASE — BOOT SAFE (opcional no boot)
# =========================================================

try:
    from supabase import create_client
except Exception:
    create_client = None

supabase = None

if (
    create_client
    and settings.SUPABASE_URL
    and settings.SUPABASE_SERVICE_ROLE_KEY
):
    try:
        supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        logger.info("SUPABASE OK — cliente inicializado")
    except Exception as e:
        supabase = None
        logger.error(f"SUPABASE ERRO — cliente não inicializado: {e}")
else:
    logger.warning("SUPABASE — variáveis ausentes ou cliente indisponível")


# =========================================================
# MODELOS BASE
# =========================================================

class RegistroBase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EstadoSistema(RegistroBase):
    estado: str
    mensagem: str
    intencao_atual: str


class DecisaoEstrategica(RegistroBase):
    acao: str
    motivo: str
    origem: Optional[str] = None
    proxima_acao: Optional[str] = None
# =========================================================
# ROTAS PÚBLICAS — STATUS INSTITUCIONAL
# =========================================================

@app.get("/status")
async def status_root():
    return {
        "sistema": "ROBO GLOBAL AI",
        "estado": "ATIVO",
        "modo": "WEB_SERVICE",
        "boot_safe": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
# =========================================================
# DASHBOARD HUMANO — CAMADA 1 (LEITURA EXECUTIVA)
# =========================================================

@app.get("/dashboard/status")
async def dashboard_status():
    return {
        "estado_geral": "OPERACIONAL",
        "mensagem": "Sistema operacional sob governança ativa",
        "intencao_atual": "Estabilizar núcleo e avançar Meta Ads"
    }
# =========================================================
# DASHBOARD HUMANO — CAMADA 2 (DECISÃO)
# =========================================================

@app.get("/dashboard/proxima-acao")
async def dashboard_proxima_acao():
    return {
        "proxima_acao": "Retomar execução Meta Ads após validação do núcleo",
        "motivo": "Infraestrutura estabilizada e dashboard operacional"
    }
@app.get("/dashboard/decisoes")
async def dashboard_decisoes():
    # leitura simples — não técnica
    return {
        "decisoes": []
    }
@app.get("/dashboard/fontes")
async def dashboard_fontes():
    return {
        "fontes_ativas": [
            "Meta Ads",
            "Hotmart",
            "Eduzz",
            "Kiwify"
        ]
    }
# =========================================================
# DASHBOARD — CAMADA 3 (FINANCEIRO) — PROTEGIDA
# =========================================================

@app.get(
    "/dashboard/financeiro",
    dependencies=[Depends(require_financeiro_key)]
)
async def dashboard_financeiro():
    # leitura financeira resumida (governança)
    return {
        "capital_total": 0,
        "capital_alocado": 0,
        "receita_total": 0,
        "custo_total": 0,
        "resultado_liquido": 0,
        "status": "CAMADA_PROTEGIDA_OK"
    }
# =========================================================
# ENCERRAMENTO
# =========================================================

logger.info(
    "MAIN.PY CARREGADO COM SUCESSO — "
    "WEB SERVICE ATIVO | WORKER PRESERVADO | BOOT-SAFE OK"
)
# =========================================================
# FASE 3 — CAMADA FINANCEIRA / ESTRATÉGICA (LEITURA GOVERNADA)
# ROBO GLOBAL AI — BACKEND
# Parte 1/2 — Endpoints + Contratos Humanos
# =========================================================

from fastapi import Depends, HTTPException
from datetime import datetime
from typing import Dict, Any

# ------------------------------------------------------------------
# DEPENDÊNCIA DE GOVERNANÇA (somente leitura)
# ------------------------------------------------------------------
def governanca_read_only():
    # Hook institucional — aqui não existe escrita nem execução
    return True


# ------------------------------------------------------------------
# HELPERS INTERNOS (SAFE)
# ------------------------------------------------------------------
def _safe_number(v):
    try:
        return float(v)
    except Exception:
        return 0.0


# ------------------------------------------------------------------
# FASE 3 — STATUS FINANCEIRO GLOBAL (LEITURA HUMANA)
# ------------------------------------------------------------------
@app.get("/dashboard/fase3/status", dependencies=[Depends(governanca_read_only)])
def fase3_status():
    """
    Visão executiva do estado financeiro do Robô.
    Nenhuma métrica técnica, apenas leitura humana.
    """
    try:
        # tabela: publico.estado_economico
        res = supabase.table("estado_economico").select("*").order("created_at", desc=True).limit(1).execute()
        row = res.data[0] if res.data else {}

        return {
            "fase": "FASE_3_FINANCEIRA",
            "estado_financeiro": row.get("estado", "INDEFINIDO"),
            "capital_atual": _safe_number(row.get("capital_atual")),
            "capital_maximo": _safe_number(row.get("capital_maximo")),
            "resultado_acumulado": _safe_number(row.get("resultado_acumulado")),
            "risco_atual": row.get("risco_atual", "N/A"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# FASE 3 — PLANO FINANCEIRO ATIVO
# ------------------------------------------------------------------
@app.get("/dashboard/fase3/plano", dependencies=[Depends(governanca_read_only)])
def fase3_plano_financeiro():
    """
    Plano financeiro vigente (leitura estratégica).
    """
    try:
        res = supabase.table("plano_diario").select("*").order("created_at", desc=True).limit(1).execute()
        row = res.data[0] if res.data else {}

        return {
            "plano": row.get("nome_plano", "SEM_PLANO_ATIVO"),
            "objetivo": row.get("objetivo", "N/A"),
            "limite_risco": row.get("limite_risco"),
            "estrategia": row.get("estrategia"),
            "status": row.get("status", "INDEFINIDO"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# FASE 3 — ESCALA FINANCEIRA
# ------------------------------------------------------------------
@app.get("/dashboard/fase3/escala", dependencies=[Depends(governanca_read_only)])
def fase3_escala():
    """
    Estado da escala financeira do robô.
    """
    try:
        res = supabase.table("escala_financeira").select("*").order("created_at", desc=True).limit(1).execute()
        row = res.data[0] if res.data else {}

        return {
            "escala_ativa": row.get("escala_ativa", False),
            "nivel_escala": row.get("nivel", 0),
            "criterio": row.get("criterio", "N/A"),
            "ultima_decisao": row.get("ultima_decisao", "N/A"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# =========================
# FASE 3 — DASHBOARD FINANCEIRO (LEITURA HUMANA)
# =========================

from fastapi import Depends

@app.get(
    "/dashboard/fase3/overview",
    dependencies=[Depends(require_financeiro_key)]
)
def dashboard_fase3_overview():

    """
    FASE 3 — Leitura humana financeira e estratégica
    Sem métricas técnicas, sem logs brutos
    """

    try:
        # Exemplos de leitura a partir do Supabase (ajuste se nomes divergirem)
        estado = supabase.table("estado_economico").select("*").order("created_at", desc=True).limit(1).execute()
        escala = supabase.table("escala_financeira").select("*").order("created_at", desc=True).limit(1).execute()
        plano = supabase.table("plano_diario").select("*").order("created_at", desc=True).limit(1).execute()

        return {
            "fase": "FASE_3",
            "status_financeiro": estado.data[0] if estado.data else {},
            "escala": escala.data[0] if escala.data else {},
            "plano_ativo": plano.data[0] if plano.data else {},
            "mensagem": "Leitura financeira sob governança ativa"
        }

    except Exception as e:
        return {
            "fase": "FASE_3",
            "erro": "Falha ao compor leitura financeira",
            "detalhe": str(e)
        }
