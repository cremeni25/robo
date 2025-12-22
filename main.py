# main.py — ROBO GLOBAL AI
# IMPLEMENTAÇÃO FORMAL DO ESTADO DECISÓRIO
# ---------------------------------------
# Este arquivo implementa o núcleo soberano do Robo Global AI.
# Nenhuma ação ocorre fora do Estado Decisório.
# Nenhuma decisão ocorre sem explicação humana.
# ---------------------------------------

from fastapi import FastAPI, HTTPException
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
import uuid

# =========================================================
# ENUMERAÇÕES FORMAIS
# =========================================================

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


# =========================================================
# MATRIZ DURA DE PERMISSÕES
# =========================================================

PERMISSOES_POR_ESTADO: Dict[EstadoEnum, List[ClasseAcao]] = {
    EstadoEnum.OBSERVACAO: [ClasseAcao.CAPTAR],
    EstadoEnum.ANALISE: [ClasseAcao.CAPTAR, ClasseAcao.ANALISAR, ClasseAcao.DESCARTAR],
    EstadoEnum.EXECUCAO: [ClasseAcao.INVESTIR],
    EstadoEnum.AGUARDANDO_VALIDACAO: [],
    EstadoEnum.BLOQUEADO: []
}

# =========================================================
# ENTIDADE SOBERANA — ESTADO DECISÓRIO
# =========================================================

class EstadoDecisorio:
    def __init__(self):
        self.estado_id: str = str(uuid.uuid4())
        self.versao_estado: int = 1

        self.estado_atual: EstadoEnum = EstadoEnum.OBSERVACAO
        self.subestado: Optional[str] = None

        self.objetivo_ativo: Optional[str] = None
        self.restricoes_ativas: List[str] = []
        self.riscos_assumidos: Optional[str] = None
        self.capital_exposto: float = 0.0
        self.plataformas_permitidas: List[str] = []

        self.justificativa_humana_atual: str = (
            "O Robô iniciou em OBSERVAÇÃO. "
            "Neste estado, apenas coleta informações. "
            "Nenhuma execução é permitida."
        )

        self.historico_decisorio: List[Dict] = []
        self._registrar_historico("Estado inicial criado")

    # ---------------------------
    # LEITURA
    # ---------------------------

    def obter_estado(self) -> Dict:
        return {
            "estado_id": self.estado_id,
            "versao_estado": self.versao_estado,
            "estado_atual": self.estado_atual,
            "acoes_permitidas": PERMISSOES_POR_ESTADO[self.estado_atual],
            "explicacao_humana": self.justificativa_humana_atual
        }

    def obter_explicacao_humana(self) -> str:
        return self.justificativa_humana_atual

    # ---------------------------
    # VALIDAÇÕES
    # ---------------------------

    def acao_permitida(self, acao: ClasseAcao) -> bool:
        return acao in PERMISSOES_POR_ESTADO[self.estado_atual]

    def transicao_permitida(self, novo_estado: EstadoEnum) -> bool:
        if self.estado_atual == EstadoEnum.BLOQUEADO:
            return False
        return True

    # ---------------------------
    # TRANSIÇÕES
    # ---------------------------

    def transicionar_estado(self, novo_estado: EstadoEnum, motivo: str):
        if not self.transicao_permitida(novo_estado):
            raise ValueError("Transição não permitida a partir do estado atual.")

        self.estado_atual = novo_estado
        self.versao_estado += 1

        self.justificativa_humana_atual = (
            f"O Robô mudou para o estado {novo_estado.value}. "
            f"Motivo: {motivo}"
        )

        self._registrar_historico(motivo)

    # ---------------------------
    # HISTÓRICO HUMANO
    # ---------------------------

    def _registrar_historico(self, motivo: str):
        self.historico_decisorio.append({
            "timestamp": datetime.utcnow().isoformat(),
            "estado": self.estado_atual.value,
            "motivo": motivo
        })


# =========================================================
# INSTÂNCIA ÚNICA DO ESTADO (FONTE DA VERDADE)
# =========================================================

ESTADO = EstadoDecisorio()

# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Robo Global AI — Estado Decisório",
    description="Núcleo soberano do Robo Global AI",
    version="1.0.0"
)

# =========================================================
# ENDPOINTS DO ESTADO
# =========================================================

@app.get("/estado")
def consultar_estado():
    return ESTADO.obter_estado()


@app.get("/estado/explicacao")
def explicacao_humana():
    return {
        "explicacao": ESTADO.obter_explicacao_humana(),
        "historico": ESTADO.historico_decisorio
    }


@app.post("/estado/acao/{acao}")
def solicitar_acao(acao: ClasseAcao):
    if not ESTADO.acao_permitida(acao):
        raise HTTPException(
            status_code=403,
            detail={
                "mensagem": "Ação bloqueada pelo Estado Decisório.",
                "estado_atual": ESTADO.estado_atual,
                "explicacao": ESTADO.obter_explicacao_humana()
            }
        )

    return {
        "mensagem": f"Ação {acao.value} permitida pelo Estado.",
        "estado_atual": ESTADO.estado_atual
    }


@app.post("/estado/transicao/{novo_estado}")
def solicitar_transicao(novo_estado: EstadoEnum, motivo: str):
    try:
        ESTADO.transicionar_estado(novo_estado, motivo)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return {
        "mensagem": "Transição realizada com sucesso.",
        "novo_estado": ESTADO.estado_atual,
        "explicacao": ESTADO.obter_explicacao_humana()
    }

# =========================================================
# FIM DO ARQUIVO
# =========================================================
