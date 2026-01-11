from fastapi import APIRouter, Request, HTTPException
import os
import logging

router = APIRouter()

HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET")

@router.post("/webhook/hotmart")
async def hotmart_webhook(request: Request):
    # 1️⃣ Verifica se a chave existe no ambiente
    if not HOTMART_WEBHOOK_SECRET:
        logging.error("HOTMART_WEBHOOK_SECRET não configurado no ambiente")
        raise HTTPException(status_code=500, detail="Hotmart secret not configured")

    # 2️⃣ Lê o header Authorization
    auth = request.headers.get("Authorization")

    if not auth or not auth.startswith("Bearer "):
        logging.warning("Hotmart sem header Authorization")
        raise HTTPException(status_code=401, detail="Missing Authorization")

    # 3️⃣ Extrai o token enviado pela Hotmart
    token = auth.replace("Bearer ", "").strip()

    # 4️⃣ Valida o token contra o Client Secret
    if token != HOTMART_WEBHOOK_SECRET:
        logging.warning("Hotmart token inválido")
        raise HTTPException(status_code=401, detail="Invalid token")

    # 5️⃣ Lê o payload
    payload = await request.json()

    logging.info(f"[HOTMART] Evento recebido: {payload.get('event')}")

    # 6️⃣ Retorno de sucesso
    return {
        "status": "ok",
        "platform": "hotmart",
        "event": payload.get("event"),
        "transaction": payload.get("data", {}).get("purchase", {}).get("transaction")
    }
