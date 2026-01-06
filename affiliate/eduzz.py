# webhook_eduzz.py
from fastapi import APIRouter, Request
import hmac
import hashlib
import os
import json

router = APIRouter()

EDUZZ_WEBHOOK_SECRET = os.getenv("EDUZZ_WEBHOOK_SECRET", "")

# eventos que REALMENTE importam financeiramente
EVENTOS_VENDA_APROVADA = {
    "myeduzz.invoice_paid",
    "myeduzz.sale_approved",
    "myeduzz.payment_approved",
}

def validar_assinatura(body: bytes, signature: str) -> bool:
    if not EDUZZ_WEBHOOK_SECRET:
        return False
    expected = hmac.new(
        EDUZZ_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def identificar_evento(payload: dict) -> str:
    # Eduzz pode enviar o tipo em locais diferentes
    return (
        payload.get("event")
        or payload.get("type")
        or payload.get("name")
        or ""
    )


@router.post("/webhook/eduzz")
async def eduzz_webhook(request: Request):
    """
    Webhook Eduzz – modo PRODUÇÃO
    - NUNCA retorna 500
    - Ignora eventos irrelevantes
    - Processa apenas venda aprovada
    """

    try:
        body = await request.body()
        signature = request.headers.get("X-Eduzz-Signature", "")

        # valida assinatura (se falhar, ignora mas responde 200)
        if signature and EDUZZ_WEBHOOK_SECRET:
            if not validar_assinatura(body, signature):
                print("[EDUZZ] [WARN] Assinatura inválida – evento ignorado")
                return {"status": "ignored", "reason": "invalid_signature"}

        payload = json.loads(body.decode("utf-8"))
        event_type = identificar_evento(payload)

        # evento que NÃO é venda → ignora
        if event_type not in EVENTOS_VENDA_APROVADA:
            print(f"[EDUZZ] [INFO] Evento ignorado: {event_type}")
            return {"status": "ignored", "event": event_type}

        # =============================
        # VENDA REAL (ÚNICO PONTO CRÍTICO)
        # =============================

        print("[EDUZZ] [INFO] Venda aprovada recebida")

        # EXTRACAO DEFENSIVA (não assume estrutura fixa)
        venda = payload.get("data", payload)

        valor = (
            venda.get("value")
            or venda.get("amount")
            or venda.get("price")
        )

        comissao = (
            venda.get("commission")
            or venda.get("commission_value")
        )

        produto = venda.get("product_id") or venda.get("product", {}).get("id")

        # aqui você pode integrar com Supabase / pipeline interno
        print(f"[EDUZZ] [INFO] Produto={produto} Valor={valor} Comissão={comissao}")

        return {
            "status": "processed",
            "platform": "eduzz",
            "event": event_type
        }

    except Exception as e:
        # REGRA DE OURO: webhook NUNCA quebra
        print("[EDUZZ] [ERROR] Erro tratado:", str(e))
        return {"status": "error_handled"}
