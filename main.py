# main.py — ROBO GLOBAL AI
# ESTADO DECISÓRIO • IMPLEMENTAÇÃO FORMAL • AUTORIDADE SOBERANA
# -------------------------------------------------------------
# Este arquivo implementa o Estado Decisório como entidade
# persistente, explicável e bloqueadora de ações.
# Nenhuma ação do sistema pode ocorrer sem validação do Estado.
# -------------------------------------------------------------

from fastapi import FastAPI, HTTPException
from enum import Enum
from datetime import datetime
from typing import List, Dict, Optional
import uuid

# =====================================================
# ENUMERAÇÕES FORMALIZADAS
# =====================================================

class EstadoEnum(str, Enum):
    OBSERVACAO = "OBSERVACAO"
    ANALISE = "ANALISE"
    EXECUCAO = "EXECUCAO"
    AGUARDANDO_VALIDACAO = "AGUARDANDO_VALIDACAO"
    BLOQUEADO = "BLOQUEADO"


class ClasseAcao(str, Enum):
    CAPTAR = "CAPTAR"
    INVESTIR = "INVESTIR"
    ESCALAR = "ESCALAR"
    PAUSAR = "PAUSAR"
    RECUAR = "RECUAR"
    DESCARTAR = "DESCARTAR"
    REPROCESSAR = "REPROCESSAR"


# =====================================================
# MATRIZ DE PERMISSÕES (REGRA DURA)
# =====================================================

PERMISSOES_POR_ESTADO: Dict[EstadoEnum, List[ClasseAcao]] = {
    EstadoEnum.OBSERVACAO: [ClasseAcao.CAPTAR],
    EstadoEnum.ANALISE: [ClasseAcao.CAPTAR, ClasseAcao.DESCARTAR],
    EstadoEnum.EXECUCAO: [ClasseAcao.INVESTIR],
    EstadoEnum.AGUARDANDO_VALIDACAO: [],
    EstadoEnum.BLOQUEADO: []
}

# =====================================================
# ESTADO DECISÓRIO (ENTIDADE SOBERANA)
# =====================================================

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
            "O Robô iniciou em estado de OBSERVAÇÃO. "
            "Neste estado, ele apenas coleta informações e não executa investimentos."
        )

        self.historico_decisorio_resumido: List[Dict] = []

        self._registrar_historico("Estado inicial criado")

    # -------------------------------------------------
    # MÉTODOS DE LEITURA
    # -------------------------------------------------

    def obter_estado_atual(self) -> EstadoEnum:
        return self.estado_atual

    def obter_acoes_permitidas(self) -> List[ClasseAcao]:
        return PERMISSOES_POR_ESTADO[self.estado_atual]

    def obter_restricoes(self) -> List[str]:
        return self.restricoes_ativas

    def obter_explicacao_humana(self) -> str:
        return self.justificativa_humana_atual

    # -------------------------------------------------
    # VALIDAÇÕES
    # -------------------------------------------------

    def acao_eh_permitida(self, acao: ClasseAcao) -> bool:
        return acao in self.obter_acoes_permitidas()

    def transicao_eh_valida(self, novo_estado: EstadoEnum) -> bool:
        if self.estado_atual == EstadoEnum.BLOQUEADO:
            return False
        return True

    # -------------------------------------------------
    # TRANSIÇÕES DE ESTADO
    # -------------------------------------------------

    def solicitar_transicao(self, novo_estado: EstadoEnum, motivo: str):
        if not self.transicao_eh_valida(novo_estado):
            raise ValueError("Transição de estado não permitida")

        self.estado_atual = novo_estado
        self.versao_estado += 1

        self.justificativa_humana_atual = (
            f"O Robô entrou no estado {novo_estado.value} pelo seguinte motivo: {motivo}"
        )

        self._registrar_historico(motivo)

    # -------------------------------------------------
    # HISTÓRICO HUMANO
    # -------------------------------------------------

    def _registrar_historico(self, motivo: str):
        self.historico_decisorio_resumido.append({
            "data": datetime.utcnow().isoformat(),
            "estado": self.estado_atual.value,
            "motivo": motivo
        })


# =====================================================
# INSTÂNCIA ÚNICA DO ESTADO (FONTE DA VERDADE)
# =====================================================

ESTADO_DECISORIO = EstadoDecisorio()

# =====================================================
# FASTAPI
# =====================================================

app = FastAPI(
    title="Robo Global AI — Estado Decisório",
    description="Implementação formal do Estado Decisório soberano",
    version="1.0.0"
)

# =====================================================
# ENDPOINTS OPERACIONAIS DO ESTADO
# =====================================================

@app.get("/estado")
def obter_estado():
    return {
        "estado_id": ESTADO_DECISORIO.estado_id,
        "versao": ESTADO_DECISORIO.versao_estado,
        "estado_atual": ESTADO_DECISORIO.estado_atual,
        "acoes_permitidas": ESTADO_DECISORIO.obter_acoes_permitidas(),
        "explicacao_humana": ESTADO_DECISORIO.obter_explicacao_humana()
    }


@app.post("/estado/acao/{acao}")
def solicitar_acao(acao: ClasseAcao):
    if not ESTADO_DECISORIO.acao_eh_permitida(acao):
        raise HTTPException(
            status_code=403,
            detail={
                "mensagem": "Ação bloqueada pelo Estado Decisório",
                "estado_atual": ESTADO_DECISORIO.estado_atual,
                "explicacao": ESTADO_DECISORIO.obter_explicacao_humana()
            }
        )

    return {
        "mensagem": f"Ação {acao.value} permitida pelo Estado Decisório",
        "estado_atual": ESTADO_DECISORIO.estado_atual
    }


@app.post("/estado/transicao/{novo_estado}")
def solicitar_transicao(novo_estado: EstadoEnum, motivo: str):
    try:
        ESTADO_DECISORIO.solicitar_transicao(novo_estado, motivo)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return {
        "mensagem": "Transição realizada com sucesso",
        "novo_estado": ESTADO_DECISORIO.estado_atual,
        "explicacao_humana": ESTADO_DECISORIO.obter_explicacao_humana()
    }


@app.get("/estado/explicacao")
def explicacao_humana():
    return {
        "explicacao_humana": ESTADO_DECISORIO.obter_explicacao_humana(),
        "historico": ESTADO_DECISORIO.historico_decisorio_resumido
    }

# -----------------------------------------------------
# FIM DO ARQUIVO
# -----------------------------------------------------
