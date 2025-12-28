import json
import os
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, status

HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET")
HOTMART_ORIGIN = "HOTMART"

router = APIRouter(
    prefix="/webhook/hotmart",
    tags=["Hotmart"]
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

def validar_assinatura(raw_body: bytes, assinatura_recebida: str) -> bool:
    assinatura_calculada = hmac.new(
        key=HOTMART_WEBHOOK_SECRET.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(assinatura_calculada, assinatura_recebida)

def normalizar_evento(evento: Dict[str, Any]) -> Dict[str, Any]:
    data = evento.get("data", {})
    purchase = data.get("purchase", {})

    return {
        "origem": HOTMART_ORIGIN,
        "evento": evento.get("event"),
        "status": data.get("status"),
        "transacao_id": data.get("transaction", {}).get("id"),
        "financeiro": {
            "valor": float(purchase.get("price", 0)),
            "moeda": purchase.get("currency", "BRL"),
        },
        "timestamp_ingestao": datetime.now(timezone.utc).isoformat(),
        "raw": evento,
    }

@router.post("")
async def webhook_hotmart(request: Request):
    if not HOTMART_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook Hotmart não habilitado")

    raw_body = await request.body()
    assinatura = request.headers.get("X-Hotmart-Hmac-SHA256")

    if not assinatura or not validar_assinatura(raw_body, assinatura):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = json.loads(raw_body.decode())
    evento = normalizar_evento(payload)

    log(HOTMART_ORIGIN, "INFO", "Evento recebido", {"id": evento["transacao_id"]})
    return {"status": "ok"}
