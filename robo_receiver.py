# robo_receiver.py — Receptor Oficial do Robô Global (RR) v1.0
# Objetivo: Receber eventos da CEN, validar, registrar e preparar para processamento futuro.
# Princípios: seguro, auditável, idempotente, sem decisão.

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional, Dict, Any, Set

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# =========================
# Configurações
# =========================

ROBO_API_KEY = os.getenv("ROBO_API_KEY", "CHANGE_ME_ROBO")
ROBO_LOG_PATH = os.getenv("ROBO_EVENT_LOG_PATH", "./robo_events.log")
ROBO_SEEN_PATH = os.getenv("ROBO_SEEN_EVENTS_PATH", "./robo_seen_events.log")

ALLOWED_EVENT_TYPES = {"presence", "intent", "action", "result"}
ALLOWED_SOURCES = {"web", "api", "platform"}

# =========================
# App
# =========================

app = FastAPI(
    title="Robô Global — Receptor de Eventos",
    version="1.0.0",
    description="Receptor oficial de eventos provenientes da CEN."
)

# =========================
# Modelos
# =========================

class EventContext(BaseModel):
    page: Optional[str] = None
    session_id: Optional[str] = None
    anonymous_id: Optional[str] = None

class EventPayload(BaseModel):
    event_id: str = Field(..., description="UUID v4")
    event_type: Literal["presence", "intent", "action", "result"]
    event_name: str
    source: Literal["web", "api", "platform"]
    timestamp_utc: str
    context: EventContext

    @validator("event_id")
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except Exception:
            raise ValueError("event_id must be a valid UUID")
        return v

    @validator("timestamp_utc")
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except Exception:
            raise ValueError("timestamp_utc must be ISO-8601")
        return v

# =========================
# Utilidades
# =========================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def write_log(path: str, entry: Dict[str, Any]) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def has_seen_event(event_id: str) -> bool:
    try:
        with open(ROBO_SEEN_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() == event_id:
                    return True
    except FileNotFoundError:
        pass
    return False

def mark_event_seen(event_id: str) -> None:
    with open(ROBO_SEEN_PATH, "a", encoding="utf-8") as f:
        f.write(event_id + "\n")

# =========================
# Endpoint
# =========================

@app.post("/robo/event")
def receive_from_cen(
    payload: EventPayload,
    x_robo_key: Optional[str] = Header(None)
):
    # Autenticação da CEN
    if x_robo_key != ROBO_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid ROBÔ API key")

    received_at = utc_now_iso()

    # Idempotência
    if has_seen_event(payload.event_id):
        write_log(ROBO_LOG_PATH, {
            "received_at": received_at,
            "event_id": payload.event_id,
            "status": "duplicate_ignored"
        })
        return JSONResponse(status_code=202, content={"accepted": True, "duplicate": True})

    # Registro principal
    write_log(ROBO_LOG_PATH, {
        "received_at": received_at,
        "event_id": payload.event_id,
        "event_type": payload.event_type,
        "event_name": payload.event_name,
        "source": payload.source,
        "timestamp_utc": payload.timestamp_utc,
        "context": payload.context.dict(),
        "status": "accepted"
    })

    mark_event_seen(payload.event_id)

    return JSONResponse(status_code=202, content={"accepted": True})
