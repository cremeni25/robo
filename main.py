# ============================================================
# main.py — ROBO GLOBAL AI
# VERSÃO: EXECUÇÃO REAL / DASHBOARD SOBERANO
# STACK: FastAPI + Supabase + Render
# AUTORIDADE: CARTA SOBERANA — INDEX DO DASHBOARD + MAIN.PY
# ============================================================

import os
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import (
    FastAPI,
    Depends,
    Header,
    HTTPException,
    status,
    Request
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pydantic import BaseModel

# ============================================================
# CONFIGURAÇÕES DE AMBIENTE (OBRIGATÓRIO)
# ============================================================

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

FINANCIAL_API_KEY = os.getenv("FINANCIAL_API_KEY")  # Camada 3 (humano)

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("SUPABASE_URL e SUPABASE_SERVICE_KEY são obrigatórios")

if not FINANCIAL_API_KEY:
    raise RuntimeError("FINANCIAL_API_KEY (Camada 3) é obrigatória")

# ============================================================
# APP FASTAPI
# ============================================================

app = FastAPI(
    title="Robo Global AI — Dashboard Operacional",
    description="Dashboard soberano com controle humano e execução real",
    version="1.0.0"
)

# ============================================================
# CORS (LIBERADO PARA DASHBOARD)
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dashboard institucional
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# UTILITÁRIOS GERAIS
# ============================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_audit_id() -> str:
    return str(uuid.uuid4())


def json_response(data: Any, status_code: int = 200):
    return JSONResponse(content=data, status_code=status_code)


# ============================================================
# MODELOS BASE (Pydantic)
# ============================================================

class StatusResponse(BaseModel):
    estado: str
    frase: str
    intencao: str
    atualizado_em: datetime


class PerformanceResponse(BaseModel):
    atencao: str
    eficiencia: str
    observacao: str
    atualizado_em: datetime


class FonteStatus(BaseModel):
    nome: str
    status: str


class DecisaoItem(BaseModel):
    data: datetime
    acao: str
    motivo: str


class ProximaAcaoResponse(BaseModel):
    texto: str
    atualizado_em: datetime


# ============================================================
# DEPENDÊNCIA — AUTENTICAÇÃO CAMADA 3
# ============================================================

def financial_auth(x_api_key: Optional[str] = Header(None)):
    if x_api_key != FINANCIAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso não autorizado à Camada 3"
        )
    return True


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/status")
def health_check():
    return {
        "service": "Robo Global AI",
        "status": "online",
        "environment": ENVIRONMENT,
        "timestamp": utc_now().isoformat()
    }

# ============================================================
# FIM DA PARTE 1
# ============================================================

# ============================================================
# PARTE 2 — CONEXÃO SUPABASE + MODELOS PERSISTENTES
# ============================================================

from supabase import create_client, Client

# ============================================================
# CLIENTE SUPABASE
# ============================================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)

# ============================================================
# MODELOS DE PERSISTÊNCIA (INTERNOS)
# ============================================================

class DashboardStatusDB(BaseModel):
    id: str
    estado: str
    frase: str
    intencao: str
    atualizado_em: datetime


class DashboardPerformanceDB(BaseModel):
    id: str
    atencao: str
    eficiencia: str
    observacao: str
    atualizado_em: datetime


class DashboardFonteDB(BaseModel):
    id: str
    nome: str
    status: str
    atualizado_em: datetime


class DashboardDecisaoDB(BaseModel):
    id: str
    data: datetime
    acao: str
    motivo: str


class DashboardProximaAcaoDB(BaseModel):
    id: str
    texto: str
    atualizado_em: datetime


class FinancialLedgerDB(BaseModel):
    id: str
    origem: str
    tipo: str  # gasto | receita
    valor: float
    referencia: str
    criado_em: datetime


class FinancialSnapshotDB(BaseModel):
    id: str
    capital_total: float
    capital_alocado: float
    resultado_liquido: float
    criado_em: datetime


class FinancialAuditDB(BaseModel):
    id: str
    origem: str
    ip: str
    user_agent: str
    acessado_em: datetime


# ============================================================
# FUNÇÕES DE ACESSO AO BANCO — DASHBOARD (CAMADAS 1 E 2)
# ============================================================

def get_dashboard_status() -> Optional[DashboardStatusDB]:
    response = supabase.table("dashboard_status") \
        .select("*") \
        .order("atualizado_em", desc=True) \
        .limit(1) \
        .execute()

    if response.data:
        return DashboardStatusDB(**response.data[0])
    return None


def get_dashboard_performance() -> Optional[DashboardPerformanceDB]:
    response = supabase.table("dashboard_performance") \
        .select("*") \
        .order("atualizado_em", desc=True) \
        .limit(1) \
        .execute()

    if response.data:
        return DashboardPerformanceDB(**response.data[0])
    return None


def get_dashboard_fontes() -> List[DashboardFonteDB]:
    response = supabase.table("dashboard_fontes") \
        .select("*") \
        .order("nome") \
        .execute()

    return [DashboardFonteDB(**item) for item in response.data or []]


def get_dashboard_decisoes(limit: int = 20) -> List[DashboardDecisaoDB]:
    response = supabase.table("dashboard_decisoes") \
        .select("*") \
        .order("data", desc=True) \
        .limit(limit) \
        .execute()

    return [DashboardDecisaoDB(**item) for item in response.data or []]


def get_dashboard_proxima_acao() -> Optional[DashboardProximaAcaoDB]:
    response = supabase.table("dashboard_proxima_acao") \
        .select("*") \
        .order("atualizado_em", desc=True) \
        .limit(1) \
        .execute()

    if response.data:
        return DashboardProximaAcaoDB(**response.data[0])
    return None


# ============================================================
# FUNÇÕES DE ACESSO AO BANCO — FINANCEIRO (CAMADA 3)
# ============================================================

def get_financial_ledger() -> List[FinancialLedgerDB]:
    response = supabase.table("financial_ledger") \
        .select("*") \
        .order("criado_em", desc=True) \
        .execute()

    return [FinancialLedgerDB(**item) for item in response.data or []]


def get_latest_financial_snapshot() -> Optional[FinancialSnapshotDB]:
    response = supabase.table("financial_snapshot") \
        .select("*") \
        .order("criado_em", desc=True) \
        .limit(1) \
        .execute()

    if response.data:
        return FinancialSnapshotDB(**response.data[0])
    return None


def register_financial_audit(
    origem: str,
    ip: str,
    user_agent: str
):
    supabase.table("financial_audit").insert({
        "id": generate_audit_id(),
        "origem": origem,
        "ip": ip,
        "user_agent": user_agent,
        "acessado_em": utc_now().isoformat()
    }).execute()


# ============================================================
# FIM DA PARTE 2
# ============================================================

# ============================================================
# PARTE 3 — ROTAS DO DASHBOARD (CAMADAS 1 E 2)
# ============================================================

# ============================================================
# CAMADA 1 — STATUS DO ROBÔ
# ============================================================

@app.get("/dashboard/status", response_model=StatusResponse)
def dashboard_status():
    status_db = get_dashboard_status()

    if not status_db:
        return StatusResponse(
            estado="OFF",
            frase="Robô aguardando inicialização operacional",
            intencao="Nenhuma ação em execução",
            atualizado_em=utc_now()
        )

    return StatusResponse(
        estado=status_db.estado,
        frase=status_db.frase,
        intencao=status_db.intencao,
        atualizado_em=status_db.atualizado_em
    )


# ============================================================
# CAMADA 2 — PERFORMANCE (SEM NÚMEROS)
# ============================================================

@app.get("/dashboard/performance", response_model=PerformanceResponse)
def dashboard_performance():
    perf_db = get_dashboard_performance()

    if not perf_db:
        return PerformanceResponse(
            atencao="baixa",
            eficiencia="abaixo",
            observacao="Nenhum ciclo completo executado",
            atualizado_em=utc_now()
        )

    return PerformanceResponse(
        atencao=perf_db.atencao,
        eficiencia=perf_db.eficiencia,
        observacao=perf_db.observacao,
        atualizado_em=perf_db.atualizado_em
    )


# ============================================================
# CAMADA 2 — FONTES (SEM NÚMEROS)
# ============================================================

@app.get("/dashboard/fontes", response_model=List[FonteStatus])
def dashboard_fontes():
    fontes_db = get_dashboard_fontes()

    if not fontes_db:
        return []

    return [
        FonteStatus(
            nome=fonte.nome,
            status=fonte.status
        )
        for fonte in fontes_db
    ]


# ============================================================
# CAMADA 2 — DECISÕES
# ============================================================

@app.get("/dashboard/decisoes", response_model=List[DecisaoItem])
def dashboard_decisoes():
    decisoes_db = get_dashboard_decisoes()

    return [
        DecisaoItem(
            data=decisao.data,
            acao=decisao.acao,
            motivo=decisao.motivo
        )
        for decisao in decisoes_db
    ]


# ============================================================
# CAMADA 2 — PRÓXIMA AÇÃO
# ============================================================

@app.get("/dashboard/proxima-acao", response_model=ProximaAcaoResponse)
def dashboard_proxima_acao():
    proxima_db = get_dashboard_proxima_acao()

    if not proxima_db:
        return ProximaAcaoResponse(
            texto="Aguardando condições para próxima ação",
            atualizado_em=utc_now()
        )

    return ProximaAcaoResponse(
        texto=proxima_db.texto,
        atualizado_em=proxima_db.atualizado_em
    )


# ============================================================
# FIM DA PARTE 3
# ============================================================

# ============================================================
# PARTE 4 — CAMADA 3 (FINANCEIRO REAL + AUTH + AUDITORIA)
# ============================================================

# ============================================================
# MODELOS DE RESPOSTA — FINANCEIRO
# ============================================================

class FinancialResumoResponse(BaseModel):
    capital_total: float
    capital_alocado: float
    resultado_liquido: float
    atualizado_em: datetime


class FinancialOrigemItem(BaseModel):
    origem: str
    gasto_total: float
    receita_total: float
    resultado: float


class FinancialResponse(BaseModel):
    resumo: FinancialResumoResponse
    por_origem: List[FinancialOrigemItem]


# ============================================================
# ROTA FINANCEIRA (PROTEGIDA)
# ============================================================

@app.get(
    "/dashboard/financeiro",
    response_model=FinancialResponse,
    dependencies=[Depends(financial_auth)]
)
def dashboard_financeiro(request: Request):
    # --------------------------------------------------------
    # AUDITORIA DE ACESSO (OBRIGATÓRIA)
    # --------------------------------------------------------
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    register_financial_audit(
        origem="dashboard_financeiro",
        ip=client_ip,
        user_agent=user_agent
    )

    # --------------------------------------------------------
    # SNAPSHOT FINANCEIRO
    # --------------------------------------------------------
    snapshot = get_latest_financial_snapshot()

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot financeiro inexistente"
        )

    resumo = FinancialResumoResponse(
        capital_total=snapshot.capital_total,
        capital_alocado=snapshot.capital_alocado,
        resultado_liquido=snapshot.resultado_liquido,
        atualizado_em=snapshot.criado_em
    )

    # --------------------------------------------------------
    # CONSOLIDAÇÃO POR ORIGEM
    # --------------------------------------------------------
    ledger = get_financial_ledger()
    consolidado: Dict[str, Dict[str, float]] = {}

    for item in ledger:
        if item.origem not in consolidado:
            consolidado[item.origem] = {
                "gasto": 0.0,
                "receita": 0.0
            }

        if item.tipo == "gasto":
            consolidado[item.origem]["gasto"] += item.valor
        elif item.tipo == "receita":
            consolidado[item.origem]["receita"] += item.valor

    por_origem: List[FinancialOrigemItem] = []

    for origem, valores in consolidado.items():
        gasto = valores["gasto"]
        receita = valores["receita"]
        resultado = receita - gasto

        por_origem.append(
            FinancialOrigemItem(
                origem=origem,
                gasto_total=gasto,
                receita_total=receita,
                resultado=resultado
            )
        )

    return FinancialResponse(
        resumo=resumo,
        por_origem=por_origem
    )


# ============================================================
# FIM DA PARTE 4
# ============================================================

# ============================================================
# PARTE 5 — PIPELINE FINANCEIRO + DECISÕES + CONSISTÊNCIA
# ============================================================

# ============================================================
# PIPELINE FINANCEIRO (IMUTÁVEL)
# ============================================================

def registrar_ledger(
    origem: str,
    tipo: str,  # gasto | receita
    valor: float,
    referencia: str
):
    supabase.table("financial_ledger").insert({
        "id": str(uuid.uuid4()),
        "origem": origem,
        "tipo": tipo,
        "valor": float(valor),
        "referencia": referencia,
        "criado_em": utc_now().isoformat()
    }).execute()


def gerar_snapshot_financeiro():
    ledger = get_financial_ledger()

    capital_total = 0.0
    capital_alocado = 0.0

    for item in ledger:
        if item.tipo == "receita":
            capital_total += item.valor
        elif item.tipo == "gasto":
            capital_total -= item.valor
            capital_alocado += item.valor

    resultado_liquido = capital_total

    supabase.table("financial_snapshot").insert({
        "id": str(uuid.uuid4()),
        "capital_total": capital_total,
        "capital_alocado": capital_alocado,
        "resultado_liquido": resultado_liquido,
        "criado_em": utc_now().isoformat()
    }).execute()


# ============================================================
# DECISÕES OPERACIONAIS (SEM MÉTRICAS CRUAS)
# ============================================================

def registrar_decisao(acao: str, motivo: str):
    supabase.table("dashboard_decisoes").insert({
        "id": str(uuid.uuid4()),
        "data": utc_now().isoformat(),
        "acao": acao,
        "motivo": motivo
    }).execute()


def atualizar_proxima_acao(texto: str):
    supabase.table("dashboard_proxima_acao").insert({
        "id": str(uuid.uuid4()),
        "texto": texto,
        "atualizado_em": utc_now().isoformat()
    }).execute()


# ============================================================
# CONSISTÊNCIA DE ESTADO DO ROBÔ
# ============================================================

def atualizar_status(
    estado: str,
    frase: str,
    intencao: str
):
    supabase.table("dashboard_status").insert({
        "id": str(uuid.uuid4()),
        "estado": estado,
        "frase": frase,
        "intencao": intencao,
        "atualizado_em": utc_now().isoformat()
    }).execute()


def atualizar_performance(
    atencao: str,
    eficiencia: str,
    observacao: str
):
    supabase.table("dashboard_performance").insert({
        "id": str(uuid.uuid4()),
        "atencao": atencao,
        "eficiencia": eficiencia,
        "observacao": observacao,
        "atualizado_em": utc_now().isoformat()
    }).execute()


def atualizar_fonte(nome: str, status: str):
    supabase.table("dashboard_fontes").upsert({
        "id": f"fonte_{nome.lower()}",
        "nome": nome,
        "status": status,
        "atualizado_em": utc_now().isoformat()
    }).execute()


# ============================================================
# BOOTSTRAP INICIAL (SE NECESSÁRIO)
# ============================================================

def bootstrap_inicial():
    status_existente = get_dashboard_status()

    if not status_existente:
        atualizar_status(
            estado="TESTE",
            frase="Dashboard operacional iniciado",
            intencao="Aguardando primeiro ciclo financeiro"
        )

        atualizar_performance(
            atencao="baixa",
            eficiencia="abaixo",
            observacao="Nenhum ciclo financeiro registrado"
        )

        atualizar_fonte("Meta Ads", "ativo")
        atualizar_fonte("Hotmart", "ativo")

        atualizar_proxima_acao(
            "Validar dashboard e iniciar retomada das campanhas"
        )


# ============================================================
# EVENTO DE STARTUP
# ============================================================

@app.on_event("startup")
def on_startup():
    bootstrap_inicial()


# ============================================================
# FIM DA PARTE 5 — MAIN.PY COMPLETO
# ============================================================
