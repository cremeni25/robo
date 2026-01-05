from fastapi import APIRouter, Request, HTTPException
import hmac
import hashlib
import os

router = APIRouter()

EDUZZ_WEBHOOK_SECRET = os.getenv("EDUZZ_WEBHOOK_SECRET")

@router.post("/webhook/eduzz")
async def eduzz_webhook(request: Request):
    if not EDUZZ_WEBHOOK_SECRET:
        raise HTTPException(status_code=500)
    signature = request.headers.get("X-Eduzz-Signature")
    if not signature:
        raise HTTPException(status_code=401)
    body = await request.body()
    expected = hmac.new(EDUZZ_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401)
    payload = await request.json()
    return {"status": "ok", "platform": "eduzz", "event": payload}
