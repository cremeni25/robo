# main.py — ROBO GLOBAL AI
# ESTADO DECISÓRIO • VALIDAÇÃO HUMANA • WEBHOOKS • SNAPSHOT
# ----------------------------------------------------------
# PASSO 5 IMPLEMENTADO
# Persistência usada apenas como MEMÓRIA segura.
# Nenhuma decisão ocorre no banco.
# ----------------------------------------------------------

from fastapi import FastAPI, HTTPException, Request
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import hashlib
import os

# ==================================================
# CONFIGURAÇÃO SUPABASE (DEPENDÊNCIA FRACA)
# ==================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None

# ==================================================
# ENUMERAÇÕES
# ==================================================

class EstadoEnum(str, Enum):
    OBSERVACAO = "OBSERVACAO"
    ANALISE = "ANALISE"
    EXECUCAO = "EXECUCAO"
    AGUARDANDO_VALIDACAO = "AGUARDANDO_VALIDACAO"
    BLOQUEADO = "BLOQUEADO"


class ClasseAcao(str, Enum):
    CAPTAR = "CAPTAR"
    ANALISAR = "ANALISAR"
    INVESTIR = "INVESTIR"
    ESCALAR = "ESCALAR"
    PAUSAR = "PAUSAR"
    RECUAR = "RECUAR"
    DESCARTAR = "DESCARTAR"


class RespostaHumana(str, Enum):
    APROVAR = "APROVAR"
    NEGAR = "NEGAR"
    SOLICITAR_AJUSTE = "SOLICITAR_AJUSTE"
    ADIAR = "ADIAR"


class TipoEvento(str, Enum):
    VENDA = "VENDA"
    REEMBOLSO = "REEMBOLSO"
    CANCELAMENTO = "CANCELAMENTO"
    OUTRO = "OUTRO"

# ==================================================
# MATRIZ DE PERMISSÕES
# ==================================================

PERMISSOES_POR_ESTADO = {
    EstadoEnum.OBSERVACAO: [ClasseAcao.CAPTAR],
    EstadoEnum.ANALISE: [ClasseAcao.CAPTAR, ClasseAcao.ANALISAR, ClasseAcao.DESCARTAR],
    EstadoEnum.EXECUCAO: [ClasseAcao.INVESTIR],
    EstadoEnum.AGUARDANDO_VALIDACAO: [],
    EstadoEnum.BLOQUEADO: []
}

# ==================================================
# FUNÇÕES DE SNAPSHOT (MEMÓRIA)
# ==================================================

def gerar_hash_estado(snapshot: dict) -> str:
    bruto = str(snapshot)
    return hashlib.sha256(bruto.encode()).hexdigest()


def salvar_snapshot(snapshot: dict):
    if not supabase:
        return False

    snapshot["hash_logico"] = gerar_hash_estado(snapshot)
    snapshot["criado_em"] = datetime.utcnow().isoformat()

    supabase.table("estado_snapshot").insert(snapshot).execute()
    return True


def carregar_ultimo_snapshot() -> Optional[dict]:
    if not supabase:
        return None

    result = (
        supabase
        .table("estado_snapshot")
        .select("*")
        .order("criado_em", desc=True)
        .limit(1)
        .execute()
    )

    if result.data:
        return result.data[0]
    return None

# ==================================================
# ESTADO DECISÓRIO SOBERANO
# ==================================================

class EstadoDecisorio:
    def __init__(self):
        snapshot = carregar_ultimo_snapshot()

        if snapshot:
            self.estado_id = snapshot["estado_id"]
            self.versao_estado = snapshot["versao_estado"]
            self.estado_atual = EstadoEnum(snapshot["estado_atual"])
            self.justificativa_humana_atual = snapshot["justificativa_humana"]
            self.historico = snapshot.get("historico", [])
            self.validacao_pendente = snapshot.get("validacao_pendente", False)
        else:
            self.estado_id = str(uuid.uuid4())
            self.versao_estado = 1
            self.estado_atual = EstadoEnum.OBSERVACAO
            self.justificativa_humana_atual = (
                "Estado inicial criado. Nenhum snapshot anterior encontrado."
            )
            self.historico = []
            self.validacao_pendente = False
            self._registrar("Estado inicial sem snapshot")

            if supabase:
                self.estado_atual = EstadoEnum.BLOQUEADO
                self.justificativa_humana_atual = (
                    "Snapshot inexistente ou inválido. "
                    "Sistema bloqueado aguardando validação humana."
                )
                self._registrar("Sistema bloqueado por ausência de snapshot")

        self._persistir()

    # -----------------------------
    # UTIL
    # -----------------------------

    def _registrar(self, motivo: str):
        self.historico.append({
            "timestamp": datetime.utcnow().isoformat(),
            "estado": self.estado_atual.value,
            "motivo": motivo
        })

    def _persistir(self):
        snapshot = {
            "estado_id": self.estado_id,
            "versao_estado": self.versao_estado,
            "estado_atual": self.estado_atual.value,
            "justificativa_humana": self.justificativa_humana_atual,
            "historico": self.historico,
            "validacao_pendente": self.validacao_pendente
        }
        salvar_snapshot(snapshot)

    # -----------------------------
    # LEITURA
    # -----------------------------

    def obter_estado(self):
        return {
            "estado_id": self.estado_id,
            "versao_estado": self.versao_estado,
            "estado_atual": self.estado_atual,
            "acoes_permitidas": PERMISSOES_POR_ESTADO[self.estado_atual],
            "validacao_pendente": self.validacao_pendente,
            "explicacao_humana": self.justificativa_humana_atual
        }

    # -----------------------------
    # TRANSIÇÃO
    # -----------------------------

    def transicionar(self, novo_estado: EstadoEnum, motivo: str):
        if self.estado_atual == EstadoEnum.AGUARDANDO_VALIDACAO:
            raise ValueError("Estado congelado aguardando validação humana.")

        self.estado_atual = novo_estado
        self.versao_estado += 1
        self.justificativa_humana_atual = (
            f"Estado alterado para {novo_estado.value}. Motivo: {motivo}"
        )
        self._registrar(motivo)
        self._persistir()

# ==================================================
# REGISTRO DE EVENTOS (WEBHOOKS)
# ==================================================

EVENTOS_REGISTRADOS: Dict[str, Dict] = {}

def gerar_hash_evento(origem: str, payload: dict) -> str:
    return hashlib.sha256(f"{origem}-{payload}".encode()).hexdigest()

def registrar_evento(origem: str, tipo: TipoEvento, payload: dict):
    h = gerar_hash_evento(origem, payload)
    if h in EVENTOS_REGISTRADOS:
        return {"status": "EVENTO_DUPLICADO", "hash": h}

    EVENTOS_REGISTRADOS[h] = {
        "evento_id": str(uuid.uuid4()),
        "origem": origem,
        "tipo": tipo.value,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat()
    }
    return {"status": "EVENTO_REGISTRADO", "hash": h}

# ==================================================
# FASTAPI
# ==================================================

app = FastAPI(
    title="Robo Global AI — Arquitetura Completa",
    version="1.3.0"
)

ESTADO = EstadoDecisorio()

# ==================================================
# ENDPOINTS
# ==================================================

@app.get("/estado")
def estado():
    return ESTADO.obter_estado()

@app.get("/estado/explicacao")
def explicacao():
    return {
        "explicacao": ESTADO.justificativa_humana_atual,
        "historico": ESTADO.historico
    }

@app.post("/webhook/{origem}")
async def webhook(origem: str, request: Request):
    payload = await request.json()
    resultado = registrar_evento(origem, TipoEvento.OUTRO, payload)

    return {
        "mensagem": "Evento registrado",
        "resultado": resultado,
        "estado_atual": ESTADO.estado_atual,
        "explicacao": ESTADO.justificativa_humana_atual
    }

# ==================================================
# FIM DO ARQUIVO
# ==================================================
