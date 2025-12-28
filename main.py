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
