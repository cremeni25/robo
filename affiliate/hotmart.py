from fastapi import APIRouter, Request, HTTPException
import hmac
import hashlib
import os

router = APIRouter()

HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET")

@router.post("/webhook/hotmart")
async def hotmart_webhook(request: Request):
    if not HOTMART_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Missing HOTMART_WEBHOOK_SECRET")

    header = request.headers.get("X-Hotmart-Hmac-SHA256")
    if not header:
        raise HTTPException(status_code=401, detail="Missing HMAC header")

    body = await request.body()

    calculated = hmac.new(
        HOTMART_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    received = header.replace("sha256=", "")

    if not hmac.compare_digest(calculated, received):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()

    return {
        "status": "ok",
        "platform": "hotmart",
        "event": payload
    }
