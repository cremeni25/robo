from fastapi import APIRouter, Request, HTTPException
import hmac
import hashlib
import os
import logging

router = APIRouter()

HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET")

@router.post("/webhook/hotmart")
async def hotmart_webhook(request: Request):

    if not HOTMART_WEBHOOK_SECRET:
        logging.error("HOTMART_WEBHOOK_SECRET não definido")
        raise HTTPException(status_code=500, detail="Missing secret")

    signature = request.headers.get("X-Hotmart-Signature")

    if not signature:
        logging.warning("Hotmart não enviou assinatura")
        raise HTTPException(status_code=401, detail="Missing signature")

    body = await request.body()

    expected = hmac.new(
        HOTMART_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        logging.warning("Assinatura Hotmart inválida")
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()

    logging.info(f"[HOTMART] Evento: {payload.get('event')}")

    return {"status": "ok"}
