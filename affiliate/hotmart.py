from fastapi import APIRouter, Request, HTTPException
import hmac
import hashlib
import base64
import json
import os
import logging

router = APIRouter()
logger = logging.getLogger("ROBO-GLOBAL-AI")

HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET")

@router.post("/webhook/hotmart")
async def hotmart_webhook(request: Request):
    if not HOTMART_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Secret ausente")

    signature = request.headers.get("X-Hotmart-Hmac-SHA256")
    if not signature:
        raise HTTPException(status_code=401, detail="Assinatura ausente")

    payload = await request.json()

    # Hotmart assina o JSON normalizado, não o body cru
    message = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    digest = hmac.new(
        HOTMART_WEBHOOK_SECRET.encode(),
        message,
        hashlib.sha256
    ).digest()

    expected = base64.b64encode(digest).decode()

    if not hmac.compare_digest(expected, signature):
        logger.error("HMAC inválido")
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    logger.info(f"HOTMART OK | event={payload.get('event')}")

    return {"status": "ok"}
