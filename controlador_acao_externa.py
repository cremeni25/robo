# controlador_acao_externa.py — CAE v1.0
# Objetivo: Avaliar decisões internas e SIMULAR autorização de ação externa.
# Nenhuma integração com Ads. Nenhuma execução real.

import json
from datetime import datetime, timezone
from typing import Dict, Any

# =========================
# Configurações
# =========================

CAE_LOG_PATH = "./robo_external_actions.log"

# Limites conservadores (governança)
MAX_AUTORIZACOES_POR_CICLO = 3
CONFIDENCE_MINIMA = 0.6

# =========================
# Utilidades
# =========================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def write_log(entry: Dict[str, Any]) -> None:
    with open(CAE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# =========================
# Controlador
# =========================

class ControladorAcaoExterna:
    def __init__(self):
        self.autorizacoes_no_ciclo = 0

    def avaliar(self, decisao: Dict[str, Any]) -> Dict[str, Any]:
        """
        Avalia se uma decisão interna é AUTORIZÁVEL para ação externa.
        """
        decision_type = decisao.get("decision")
        confidence = decisao.get("confidence", 0.0)

        # Regra 1 — decisões ignoradas nunca viram ação
        if decision_type == "ignore":
            return self._bloqueada("decision_ignored")

        # Regra 2 — limite por ciclo
        if self.autorizacoes_no_ciclo >= MAX_AUTORIZACOES_POR_CICLO:
            return self._bloqueada("cycle_limit_reached")

        # Regra 3 — confiança mínima
        if confidence < CONFIDENCE_MINIMA:
            return self._bloqueada("low_confidence")

        # Se passou por tudo, é AUTORIZÁVEL (não executada)
        self.autorizacoes_no_ciclo += 1
        return self._autorizavel()

    def _autorizavel(self) -> Dict[str, Any]:
        return {
            "status": "AUTORIZAVEL",
            "executed": False
        }

    def _bloqueada(self, reason: str) -> Dict[str, Any]:
        return {
            "status": "BLOQUEADA",
            "executed": False,
            "reason": reason
        }

    def registrar(self, decisao: Dict[str, Any], resultado: Dict[str, Any]) -> None:
        write_log({
            "timestamp": utc_now_iso(),
            "decision": decisao,
            "result": resultado
        })
