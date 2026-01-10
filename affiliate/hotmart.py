from fastapi import APIRouter, Request, HTTPException
import hmac
import hashlib
import base64
import os
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger("ROBO-GLOBAL-AI")

HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET")

@router.post("/webhook/hotmart")
async def hotmart_webhook(request: Request):
    # 1️⃣ Garantia de segredo
    if not HOTMART_WEBHOOK_SECRET:
        logger.error("HOTMART_WEBHOOK_SECRET ausente")
        raise HTTPException(status_code=500, detail="Webhook não configurado")

    # 2️⃣ Header correto da Hotmart
    signature = request.headers.get("X-Hotmart-Hmac-SHA256")
    if not signature:
        logger.warning("Header X-Hotmart-Hmac-SHA256 ausente")
        raise HTTPException(status_code=401, detail="Assinatura ausente")

    # 3️⃣ Corpo bruto (RAW BODY)
    body = await request.body()

    # 4️⃣ Geração correta do HMAC (BASE64)
    digest = hmac.new(
        HOTMART_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).digest()

    expected_signature = base64.b64encode(digest).decode()

    if not hmac.compare_digest(expected_signature, signature):
        logger.warning("Assinatura inválida da Hotmart")
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    # 5️⃣ Payload válido
    payload = await request.json()

    logger.info(
        f"HOTMART WEBHOOK OK | evento={payload.get('event')} | "
        f"timestamp={datetime.utcnow().isoformat()}"
    )

    # ⚠️ Aqui propositalmente só confirmamos recebimento
    # Normalização + Supabase vêm no próximo passo

    return {"status": "ok"}
