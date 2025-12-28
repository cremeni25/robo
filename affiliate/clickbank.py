import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, status

CLICKBANK_SECRET_KEY = os.getenv("CLICKBANK_SECRET_KEY")
CLICKBANK_ORIGIN = "CLICKBANK"

router = APIRouter(
    prefix="/postback/clickbank",
    tags=["ClickBank"]
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

def normalizar_evento(query: Dict[str, str]) -> Dict[str, Any]:
    return {
        "origem": CLICKBANK_ORIGIN,
        "evento": query.get("transactionType"),
        "transacao_id": query.get("receipt"),
        "financeiro": {
            "valor": float(query.get("amount", 0)),
            "moeda": query.get("currency", "USD"),
        },
        "timestamp_ingestao": datetime.now(timezone.utc).isoformat(),
        "raw": dict(query),
    }

@router.get("")
async def postback_clickbank(request: Request):
    if not CLICKBANK_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Postback ClickBank não habilitado")

    secret = request.query_params.get("secretKey")
    if secret != CLICKBANK_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Postback inválido")

    evento = normalizar_evento(dict(request.query_params))
    log(CLICKBANK_ORIGIN, "INFO", "Evento recebido", {"id": evento["transacao_id"]})
    return {"status": "ok"}
