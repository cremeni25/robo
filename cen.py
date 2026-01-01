# cen.py — Camada de Eventos Neutra (CEN) v1.0
# Objetivo: Receber eventos neutros, validar, registrar e encaminhar ao Robô Global.
# Princípios: neutro, burro, auditável, desacoplado.

import os
import json
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Literal, Optional, Dict, Any

from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# =========================
# Configurações básicas
# =========================

CEN_API_KEY = os.getenv("CEN_API_KEY", "CHANGE_ME")
ROBO_ENDPOINT = os.getenv("ROBO_ENDPOINT", "http://robo-interno/event")
LOG_PATH = os.getenv("CEN_LOG_PATH", "./cen_events.log")

ALLOWED_EVENT_TYPES = {"presence", "intent", "action", "result"}
ALLOWED_SOURCES = {"web", "api", "platform"}

# =========================
# App
# =========================

app = FastAPI(
    title="CEN — Camada de Eventos Neutra",
    version="1.0.0",
    description="Recebe eventos neutros, valida, registra e encaminha ao Robô Global."
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

def write_log(entry: Dict[str, Any]) -> None:
    line = json.dumps(entry, ensure_ascii=False)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

async def forward_to_robo(event: Dict[str, Any]) -> None:
    """
    Encaminhamento assíncrono.
    IMPORTANTE: a CEN não espera resposta do Robô.
    """
    try:
        # Simulação de envio assíncrono desacoplado.
        # Aqui você pode substituir por httpx/aiohttp futuramente,
        # mantendo a regra: não bloquear resposta da CEN.
        await asyncio.sleep(0)  # yield ao loop
        # Exemplo (desativado por neutralidade):
        # async with httpx.AsyncClient(timeout=2.0) as client:
        #     await client.post(ROBO_ENDPOINT, json=event)
    except Exception:
        # Falha no encaminhamento NÃO invalida aceitação do evento
        pass

# =========================
# Endpoints
# =========================

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/event")
async def receive_event(
    payload: EventPayload,
    background_tasks: BackgroundTasks,
    x_cen_key: Optional[str] = Header(None)
):
    # Autenticação simples
    if x_cen_key != CEN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    received_at = utc_now_iso()

    # Registro de aceitação
    log_entry = {
        "received_at": received_at,
        "event_id": payload.event_id,
        "event_type": payload.event_type,
        "event_name": payload.event_name,
        "source": payload.source,
        "status": "accepted"
    }

    write_log(log_entry)

    # Encaminhamento assíncrono ao Robô
    background_tasks.add_task(
        forward_to_robo,
        {
            "event_id": payload.event_id,
            "event_type": payload.event_type,
            "event_name": payload.event_name,
            "source": payload.source,
            "timestamp_utc": payload.timestamp_utc,
            "context": payload.context.dict()
        }
    )

    return JSONResponse(status_code=202, content={"accepted": True})
