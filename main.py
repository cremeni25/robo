# main.py — ROBO GLOBAL AI
# ESTADO DECISÓRIO • VALIDAÇÃO HUMANA • WEBHOOKS COMO EVENTOS
# ----------------------------------------------------------
# PASSO 4 IMPLEMENTADO
# Webhooks são tratados exclusivamente como eventos externos.
# Nenhum webhook executa ação ou altera estado diretamente.
# ----------------------------------------------------------

from fastapi import FastAPI, HTTPException, Request
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import hashlib

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
# ESTADO DECISÓRIO SOBERANO
# ==================================================

class EstadoDecisorio:
    def __init__(self):
        self.estado_id = str(uuid.uuid4())
        self.versao_estado = 1
        self.estado_atual = EstadoEnum.OBSERVACAO

        self.justificativa_humana_atual = (
            "O Robô iniciou em OBSERVAÇÃO. "
            "Webhooks apenas registram fatos."
        )

        self.historico: List[Dict] = []

        # Validação humana
        self.validacao_pendente = False
        self.estado_proposto: Optional[EstadoEnum] = None
        self.pedido_humano: Optional[Dict] = None

        self._registrar("Estado inicial criado")

    def _registrar(self, motivo: str):
        self.historico.append({
            "timestamp": datetime.utcnow().isoformat(),
            "estado": self.estado_atual.value,
            "motivo": motivo
        })

    def obter_estado(self):
        return {
            "estado_id": self.estado_id,
            "versao_estado": self.versao_estado,
            "estado_atual": self.estado_atual,
            "acoes_permitidas": PERMISSOES_POR_ESTADO[self.estado_atual],
            "validacao_pendente": self.validacao_pendente,
            "explicacao_humana": self.justificativa_humana_atual
        }

    def solicitar_validacao_humana(
        self,
        estado_proposto: EstadoEnum,
        motivo: str,
        risco: str,
        capital: float
    ):
        self.validacao_pendente = True
        self.estado_proposto = estado_proposto
        self.estado_atual = EstadoEnum.AGUARDANDO_VALIDACAO
        self.versao_estado += 1

        self.pedido_humano = {
            "acao_proposta": estado_proposto.value,
            "motivo": motivo,
            "risco": risco,
            "capital": capital
        }

        self.justificativa_humana_atual = (
            "O Robô está aguardando validação humana para uma decisão crítica."
        )

        self._registrar("Validação humana solicitada")

    def responder_validacao(self, resposta: RespostaHumana, motivo: Optional[str] = None):
        if not self.validacao_pendente:
            raise ValueError("Nenhuma validação pendente.")

        if resposta == RespostaHumana.APROVAR:
            self.estado_atual = self.estado_proposto
            self.justificativa_humana_atual = (
                f"Humano aprovou a transição para {self.estado_proposto.value}."
            )

        elif resposta == RespostaHumana.NEGAR:
            self.estado_atual = EstadoEnum.ANALISE
            self.justificativa_humana_atual = f"Humano negou a decisão. Motivo: {motivo}"

        elif resposta == RespostaHumana.SOLICITAR_AJUSTE:
            self.estado_atual = EstadoEnum.ANALISE
            self.justificativa_humana_atual = f"Humano solicitou ajustes. Motivo: {motivo}"

        elif resposta == RespostaHumana.ADIAR:
            self.justificativa_humana_atual = "Humano adiou a decisão."
            return

        self.validacao_pendente = False
        self.estado_proposto = None
        self.pedido_humano = None
        self.versao_estado += 1

        self._registrar(f"Resposta humana: {resposta.value}")

# ==================================================
# REGISTRO DE EVENTOS (WEBHOOKS)
# ==================================================

EVENTOS_REGISTRADOS: Dict[str, Dict] = {}

def gerar_hash_evento(origem: str, payload: dict) -> str:
    bruto = f"{origem}-{payload}"
    return hashlib.sha256(bruto.encode()).hexdigest()

def registrar_evento(origem: str, tipo: TipoEvento, payload: dict) -> Dict:
    hash_evento = gerar_hash_evento(origem, payload)

    if hash_evento in EVENTOS_REGISTRADOS:
        return {
            "status": "EVENTO_DUPLICADO",
            "hash_evento": hash_evento
        }

    EVENTOS_REGISTRADOS[hash_evento] = {
        "evento_id": str(uuid.uuid4()),
        "origem": origem,
        "tipo": tipo.value,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat()
    }

    return {
        "status": "EVENTO_REGISTRADO",
        "hash_evento": hash_evento
    }

# ==================================================
# FASTAPI
# ==================================================

app = FastAPI(
    title="Robo Global AI — Estado + Webhooks",
    version="1.2.0"
)

ESTADO = EstadoDecisorio()

# ==================================================
# ENDPOINTS DO ESTADO
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

@app.post("/estado/responder-validacao")
def responder_validacao(resposta: RespostaHumana, motivo: Optional[str] = None):
    try:
        ESTADO.responder_validacao(resposta, motivo)
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

    return {
        "mensagem": "Resposta humana registrada",
        "estado": ESTADO.estado_atual
    }

# ==================================================
# WEBHOOKS COMO EVENTOS
# ==================================================

@app.post("/webhook/{origem}")
async def receber_webhook(origem: str, request: Request):
    payload = await request.json()

    tipo = TipoEvento.OUTRO
    if "venda" in payload.get("evento", "").lower():
        tipo = TipoEvento.VENDA
    elif "reembolso" in payload.get("evento", "").lower():
        tipo = TipoEvento.REEMBOLSO

    resultado = registrar_evento(origem, tipo, payload)

    # Nenhuma decisão ocorre aqui
    return {
        "mensagem": "Webhook recebido como evento",
        "resultado": resultado,
        "estado_atual": ESTADO.estado_atual,
        "explicacao": ESTADO.justificativa_humana_atual
    }

# ==================================================
# FIM DO ARQUIVO
# ==================================================
