# main.py — ROBO GLOBAL AI
# ESTADO DECISÓRIO • VALIDAÇÃO HUMANA EXTERNA
# --------------------------------------------------
# Implementação soberana do Estado Decisório com
# Validação Humana Formal (PASSO 3)
# --------------------------------------------------

from fastapi import FastAPI, HTTPException
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
import uuid

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

# ==================================================
# MATRIZ DURA DE PERMISSÕES
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
            "Apenas coleta informações."
        )

        self.historico: List[Dict] = []

        # ----- Validação Humana -----
        self.validacao_pendente: bool = False
        self.pedido_humano: Optional[Dict] = None
        self.estado_proposto: Optional[EstadoEnum] = None

        self._registrar("Estado inicial criado")

    # -----------------------------
    # UTIL
    # -----------------------------

    def _registrar(self, motivo: str):
        self.historico.append({
            "timestamp": datetime.utcnow().isoformat(),
            "estado": self.estado_atual.value,
            "motivo": motivo
        })

    # -----------------------------
    # LEITURA
    # -----------------------------

    def obter_estado(self):
        return {
            "estado_id": self.estado_id,
            "versao_estado": self.versao_estado,
            "estado_atual": self.estado_atual,
            "acoes_permitidas": PERMISSOES_POR_ESTADO[self.estado_atual],
            "explicacao_humana": self.justificativa_humana_atual,
            "validacao_pendente": self.validacao_pendente
        }

    # -----------------------------
    # TRANSIÇÃO NORMAL
    # -----------------------------

    def transicionar(self, novo_estado: EstadoEnum, motivo: str):
        if self.estado_atual == EstadoEnum.AGUARDANDO_VALIDACAO:
            raise ValueError("Estado congelado aguardando validação humana.")

        self.estado_atual = novo_estado
        self.versao_estado += 1

        self.justificativa_humana_atual = (
            f"O Robô mudou para {novo_estado.value}. "
            f"Motivo: {motivo}"
        )

        self._registrar(motivo)

    # -----------------------------
    # SOLICITAÇÃO DE VALIDAÇÃO HUMANA
    # -----------------------------

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
            "o_que": f"Transitar para {estado_proposto.value}",
            "por_que": motivo,
            "risco": risco,
            "capital_envolvido": capital,
            "consequencia_se_aprovado": f"O Robô entrará em {estado_proposto.value}",
            "consequencia_se_negado": "O Robô não avançará e recuará para análise"
        }

        self.justificativa_humana_atual = (
            "O Robô está aguardando validação humana para avançar."
        )

        self._registrar("Validação humana solicitada")

    # -----------------------------
    # RESPOSTA HUMANA
    # -----------------------------

    def responder_validacao(self, resposta: RespostaHumana, motivo: Optional[str] = None):
        if not self.validacao_pendente:
            raise ValueError("Não existe validação pendente.")

        if resposta == RespostaHumana.APROVAR:
            self.estado_atual = self.estado_proposto
            self.justificativa_humana_atual = (
                f"O humano aprovou a transição para {self.estado_proposto.value}."
            )

        elif resposta == RespostaHumana.NEGAR:
            self.estado_atual = EstadoEnum.ANALISE
            self.justificativa_humana_atual = (
                f"O humano negou a transição. Motivo: {motivo}"
            )

        elif resposta == RespostaHumana.SOLICITAR_AJUSTE:
            self.estado_atual = EstadoEnum.ANALISE
            self.justificativa_humana_atual = (
                f"O humano solicitou ajustes. Motivo: {motivo}"
            )

        elif resposta == RespostaHumana.ADIAR:
            self.justificativa_humana_atual = (
                "O humano optou por adiar a decisão. Estado permanece congelado."
            )
            return  # mantém congelado

        self.validacao_pendente = False
        self.estado_proposto = None
        self.pedido_humano = None
        self.versao_estado += 1

        self._registrar(f"Resposta humana: {resposta.value}")

# ==================================================
# INSTÂNCIA ÚNICA
# ==================================================

ESTADO = EstadoDecisorio()

# ==================================================
# FASTAPI
# ==================================================

app = FastAPI(
    title="Robo Global AI — Estado Decisório + Validação Humana",
    version="1.1.0"
)

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


@app.post("/estado/solicitar-validacao")
def solicitar_validacao(
    estado_proposto: EstadoEnum,
    motivo: str,
    risco: str,
    capital: float
):
    try:
        ESTADO.solicitar_validacao_humana(
            estado_proposto=estado_proposto,
            motivo=motivo,
            risco=risco,
            capital=capital
        )
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

    return {
        "mensagem": "Validação humana solicitada",
        "pedido": ESTADO.pedido_humano
    }


@app.post("/estado/responder-validacao")
def responder_validacao(resposta: RespostaHumana, motivo: Optional[str] = None):
    try:
        ESTADO.responder_validacao(resposta, motivo)
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

    return {
        "mensagem": "Resposta humana registrada",
        "estado_atual": ESTADO.estado_atual,
        "explicacao": ESTADO.justificativa_humana_atual
    }

# ==================================================
# FIM DO ARQUIVO
# ==================================================
