# main.py — ROBO GLOBAL AI
# Versão compatível com Python 3.13 + Pydantic v2
# Arquivo soberano — substituição integral

from __future__ import annotations

import sys
import uuid
import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
# =========================================================
# CONFIGURAÇÕES
# =========================================================

class Settings(BaseSettings):
    ENV: str = "production"

    DASHBOARD_API_KEY: str
    FINANCEIRO_API_KEY: str

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
logger.info("BOOT — ROBO GLOBAL AI")
# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Robo Global AI",
    version="2025.12.27",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# =========================================================
# SEGURANÇA
# =========================================================

dashboard_key = APIKeyHeader(name="X-DASHBOARD-API-KEY", auto_error=False)
financeiro_key = APIKeyHeader(name="X-FINANCEIRO-API-KEY", auto_error=False)


def auth_dashboard(key: Optional[str] = Depends(dashboard_key)):
    if key != settings.DASHBOARD_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return True


def auth_financeiro(key: Optional[str] = Depends(financeiro_key)):
    if key != settings.FINANCEIRO_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return True
# =========================================================
# SUPABASE
# =========================================================

try:
    from supabase import create_client
except ImportError:
    create_client = None

supabase = None

if (
    create_client
    and settings.SUPABASE_URL
    and settings.SUPABASE_SERVICE_ROLE_KEY
):
    supabase = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY,
    )
# =========================================================
# MODELOS
# =========================================================

class BaseRegistro(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusRobo(BaseRegistro):
    estado: str
    frase: str
    intencao: str


class DecisaoRobo(BaseRegistro):
    acao: str
    motivo: str
    proxima_acao: Optional[str] = None
@app.get("/status")
async def status_root():
    return {
        "sistema": "ROBO GLOBAL AI",
        "estado": "ATIVO",
        "modo": "CONDUCAO-TOTAL-ABSOLUTA",
    }
@app.get("/dashboard/status")
async def dashboard_status():
    return {
        "estado": "TESTE",
        "frase": "Sistema operacional sob governança",
        "intencao": "Validar leitura humana antes da escala",
    }
@app.get("/dashboard/proxima-acao")
async def dashboard_proxima_acao():
    return {
        "texto": "Finalizar validação do dashboard e retomar Meta Ads",
    }
@app.get("/dashboard/decisoes")
async def dashboard_decisoes():
    return []
@app.get("/dashboard/fontes")
async def dashboard_fontes():
    return [
        {"nome": "Meta Ads", "status": "ativo"},
        {"nome": "Hotmart", "status": "em_analise"},
        {"nome": "Eduzz", "status": "em_analise"},
    ]
@app.get(
    "/dashboard/financeiro",
    dependencies=[Depends(auth_financeiro)],
)
async def dashboard_financeiro():
    return {
        "capital_total": 0,
        "capital_alocado": 0,
        "receita_total": 0,
        "custo_total": 0,
        "resultado_liquido": 0,
    }
logger.info(
    "MAIN.PY CARREGADO COM SUCESSO — "
    "PYDANTIC V2 / PYTHON 3.13 / RENDER OK"
)
