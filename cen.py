# cen.py — Camada de Eventos Neutra (CEN) v1.1
# OBJETIVO:
# Receber eventos neutros, validar, registrar e encaminhar ASSÍNCRONAMENTE ao Robô Global.
#
# PRINCÍPIOS:
# - Neutra (não decide)
# - Burra (não interpreta)
# - Auditável
# - Desacoplada
# - Sem Ads
# - Sem testes humanos

import os
import json
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Literal

import httpx
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# ======================================================
# CONFIGURAÇÕES (OBRIGATÓRIAS VIA ENVIRONMENT - RENDER)
# ======================================================

CEN_API_KEY = os.getenv("CEN_API_KEY", "CHANGE_ME")
ROBO_ENDPOINT = os.getenv("ROBO_ENDPOINT")        # https://robo-global-api-v2.onrender.com/robo/event
ROBO_API_KEY = os.getenv("ROBO_API_KEY")          # chave exclusiva CEN -> Robô
LOG_PATH = os.getenv("CEN_LOG_PATH", "./cen_events.log")

if not ROBO_ENDPOINT or not ROBO_API_KEY:
    raise RuntimeError("ROBO_ENDPOINT e ROBO_API_KEY são obrigatórios")

# ======================================================
# APLICAÇÃO
# ======================================================

app = FastAPI(
    title="CEN — Camada de Eventos Neutra",
    version="1.1.0",
    description="Recebe eventos neutros, valida, registra e encaminha ao Robô Global."
)

# ======================================================
# MODELOS
# ======================================================

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

# ======================================================
# UTILIDADES
# ======================================================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def write_log(entry: Dict[str, Any]) -> None:
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

async def forward_to_robo(event: Dict[str, Any]) -> None:
    """
    Encaminhamento assíncrono e não bloqueante.
    A CEN NÃO espera resposta do Robô.
    """
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                ROBO_ENDPOINT,
                json=event,
                headers={
                    "X-ROBO-KEY": ROBO_API_KEY,
                    "Content-Type": "application/json"
                }
            )
    except Exception:
        # Falha de envio NÃO invalida o evento
        pass

# ======================================================
# ENDPOINTS
# ======================================================

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/event")
async def receive_event(
    payload: EventPayload,
    background_tasks: BackgroundTasks,
    x_cen_key: Optional[str] = Header(None)
):
    # Autenticação da origem
    if x_cen_key != CEN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid CEN API key")

    received_at = utc_now_iso()

    # Registro imutável
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
