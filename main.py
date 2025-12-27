# main.py — ROBO GLOBAL AI
# VERSÃO COMPLETA • FASE E • CARTA MAGNA EXECUTIVA
# Backend único | FastAPI | Governança ativa
# Robô executa • Humano governa • Sistema audita

import os
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# =========================================================
# CONFIGURAÇÃO GERAL
# =========================================================

APP_NAME = "ROBO GLOBAL AI — Backend Institucional"
ENV = os.getenv("ENV", "production")

FINANCE_API_KEY = os.getenv("FINANCE_API_KEY")

if not FINANCE_API_KEY:
    raise RuntimeError("FINANCE_API_KEY não configurada")

logging.basicConfig(
    level=logging.INFO,
    format="[BACKEND] [%(levelname)s] %(message)s"
)

logger = logging.getLogger(APP_NAME)

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dashboard público
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# MODELOS
# =========================================================

class StatusResponse(BaseModel):
    status: str
    intencao: str
    mensagem: str


class ProximaAcaoResponse(BaseModel):
    acao: str
    motivo: str


class FontesResponse(BaseModel):
    fontes: List[str]


class LedgerItem(BaseModel):
    data: str
    origem: str
    tipo: str
    valor: float


class LedgerResponse(BaseModel):
    registros: List[LedgerItem]


# =========================================================
# MIDDLEWARE DE AUTENTICAÇÃO FINANCEIRA
# =========================================================

def validar_api_key(authorization: Optional[str]):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header ausente")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de autorização inválido")

    token = authorization.replace("Bearer ", "").strip()

    if token != FINANCE_API_KEY:
        raise HTTPException(status_code=403, detail="Acesso financeiro negado")


def auditar_acesso(request: Request, sucesso: bool):
    logger.info(
        f"[AUDITORIA] acesso_financeiro | ip={request.client.host} "
        f"| path={request.url.path} | sucesso={sucesso}"
    )


# =========================================================
# CAMADA 1 — ESTADO EXECUTIVO (PÚBLICA)
# =========================================================

@app.get("/dashboard/status", response_model=StatusResponse)
def dashboard_status():
    return StatusResponse(
        status="OPERANTE",
        intencao="ESCALA CONTROLADA",
        mensagem="Sistema em execução conforme governança institucional"
    )


# =========================================================
# CAMADA 2 — DECISÃO DO ROBÔ (PÚBLICA)
# =========================================================

@app.get("/dashboard/proxima-acao", response_model=ProximaAcaoResponse)
def dashboard_proxima_acao():
    return ProximaAcaoResponse(
        acao="MANTER_ESCALA",
        motivo="Resultados estáveis dentro das regras de risco"
    )


@app.get("/dashboard/fontes", response_model=FontesResponse)
def dashboard_fontes():
    return FontesResponse(
        fontes=["META_ADS", "HOTMART"]
    )


# =========================================================
# CAMADA 3 — FINANCEIRO (RESTRITA • AUTH REAL)
# =========================================================

@app.get("/finance/ledger", response_model=LedgerResponse)
def finance_ledger(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    try:
        validar_api_key(authorization)
        auditar_acesso(request, sucesso=True)

        # 🔒 Dados financeiros reais / simulados
        registros = [
            LedgerItem(
                data="2025-01-10",
                origem="META_ADS",
                tipo="CUSTO",
                valor=-320.50
            ),
            LedgerItem(
                data="2025-01-10",
                origem="HOTMART",
                tipo="RECEITA",
                valor=980.00
            ),
            LedgerItem(
                data="2025-01-11",
                origem="META_ADS",
                tipo="CUSTO",
                valor=-410.00
            ),
            LedgerItem(
                data="2025-01-11",
                origem="HOTMART",
                tipo="RECEITA",
                valor=1250.00
            ),
        ]

        return LedgerResponse(registros=registros)

    except HTTPException:
        auditar_acesso(request, sucesso=False)
        raise


# =========================================================
# STATUS GERAL
# =========================================================

@app.get("/status")
def status():
    return {
        "service": APP_NAME,
        "env": ENV,
        "timestamp": datetime.utcnow().isoformat(),
        "governanca": "ATIVA"
    }


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "ROBO GLOBAL AI — Backend ativo",
        "camadas": {
            "1": "Executiva",
            "2": "Decisão",
            "3": "Financeiro (Restrito)"
        }
    }
