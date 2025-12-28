import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, status

MONETIZZE_WEBHOOK_TOKEN = os.getenv("MONETIZZE_WEBHOOK_TOKEN")
MONETIZZE_ORIGIN = "MONETIZZE"

router = APIRouter(
    prefix="/webhook/monetizze",
    tags=["Monetizze"]
)

def log(origem: str, nivel: str, mensagem: str, extra: Dict[str, Any] | None = None):
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "origem": origem,
        "nivel": nivel,
        "mensagem": mensagem,
    }
    if extra:
        payload["extra"] = extra
    print(json.dumps(payload, ensure_ascii=False))

def validar_token(headers: Dict[str, str]) -> bool:
    token = headers.get("X-Monetizze-Token") or headers.get("Authorization")
    if not token:
        return False
    return token.replace("Bearer ", "") == MONETIZZE_WEBHOOK_TOKEN

def normalizar_evento(evento: Dict[str, Any]) -> Dict[str, Any]:
    data = evento.get("data", {})
    return {
        "origem": MONETIZZE_ORIGIN,
        "evento": evento.get("event"),
        "status": data.get("status"),
        "transacao_id": data.get("sale_id"),
        "financeiro": {
            "valor": float(data.get("sale_value", 0)),
            "moeda": data.get("currency", "BRL"),
        },
        "timestamp_ingestao": datetime.now(timezone.utc).isoformat(),
        "raw": evento,
    }

@router.post("")
async def webhook_monetizze(request: Request):
    if not MONETIZZE_WEBHOOK_TOKEN:
        raise HTTPException(status_code=503, detail="Webhook Monetizze não habilitado")

    if not validar_token(request.headers):
        raise HTTPException(status_code=401, detail="Token inválido")

    payload = await request.json()
    evento = normalizar_evento(payload)

    log(MONETIZZE_ORIGIN, "INFO", "Evento recebido", {"id": evento["transacao_id"]})
    return {"status": "ok"}
