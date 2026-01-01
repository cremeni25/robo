# motor_interno.py — Motor Interno do Robô (MIR) v1.0
# Objetivo: interpretar eventos, manter memória e registrar decisões internas.
# Princípios: determinístico, explicável, auditável, sem ações externas.

import json
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Dict, Any, Deque, List, Optional

# =========================
# Configurações
# =========================

MEMORY_WINDOW_SECONDS = 300        # 5 minutos
MAX_EVENTS_PER_WINDOW = 20
DECISION_LOG_PATH = "./robo_decisions.log"

# =========================
# Utilidades
# =========================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def write_decision(entry: Dict[str, Any]) -> None:
    with open(DECISION_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# =========================
# Normalizador
# =========================

def normalize(event: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "event_id": event["event_id"],
        "type": event["event_type"],
        "name": event["event_name"],
        "source": event["source"],
        "timestamp": event["timestamp_utc"],
        "session_id": event.get("context", {}).get("session_id"),
        "anonymous_id": event.get("context", {}).get("anonymous_id"),
    }

# =========================
# Memória (curto prazo)
# =========================

class ShortTermMemory:
    def __init__(self):
        self.events: Dict[str, Deque[Dict[str, Any]]] = defaultdict(deque)

    def _key(self, e: Dict[str, Any]) -> str:
        return e.get("anonymous_id") or e.get("session_id") or "unknown"

    def add(self, e: Dict[str, Any]) -> None:
        key = self._key(e)
        now = time.time()
        dq = self.events[key]
        dq.append((now, e))
        # limpar janela
        while dq and now - dq[0][0] > MEMORY_WINDOW_SECONDS:
            dq.popleft()

    def count(self, e: Dict[str, Any]) -> int:
        key = self._key(e)
        return len(self.events[key])

    def last_sequence(self, e: Dict[str, Any], n: int = 3) -> List[str]:
        key = self._key(e)
        return [item[1]["name"] for item in list(self.events[key])[-n:]]

# =========================
# Motor de Regras v0
# =========================

class RuleEngineV0:
    def decide(self, mem: ShortTermMemory, e: Dict[str, Any]) -> Dict[str, Any]:
        cnt = mem.count(e)
        seq = mem.last_sequence(e)

        # Regra 1: excesso de eventos no curto prazo
        if cnt > MAX_EVENTS_PER_WINDOW:
            return {
                "decision": "ignore",
                "reason": "excessive_events_short_window",
                "count": cnt
            }

        # Regra 2: repetição imediata do mesmo evento
        if len(seq) >= 2 and seq[-1] == seq[-2]:
            return {
                "decision": "group",
                "reason": "repeated_event",
                "sequence": seq[-2:]
            }

        # Regra 3: sequência simples de intenção → ação
        if len(seq) >= 2 and seq[-2].startswith("intent.") and seq[-1].startswith("action."):
            return {
                "decision": "register_pattern",
                "reason": "intent_to_action",
                "sequence": seq[-2:]
            }

        # Padrão: registrar
        return {
            "decision": "register",
            "reason": "default"
        }

# =========================
# Orquestrador
# =========================

class MotorInterno:
    def __init__(self):
        self.memory = ShortTermMemory()
        self.rules = RuleEngineV0()

    def process(self, raw_event: Dict[str, Any]) -> None:
        e = normalize(raw_event)
        self.memory.add(e)
        decision = self.rules.decide(self.memory, e)

        write_decision({
            "decided_at": utc_now_iso(),
            "event_id": e["event_id"],
            "event_name": e["name"],
            "decision": decision["decision"],
            "reason": decision["reason"],
            "meta": {k: v for k, v in decision.items() if k not in ("decision", "reason")}
        })
