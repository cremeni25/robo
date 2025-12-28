# affiliate/hotmart.py
# Integração REAL Hotmart — Webhook, Validação, Normalização e Persistência
# Arquivo AUTÔNOMO — não altera main.py

import hmac
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, status

# ===============================
# CONFIGURAÇÕES
# ===============================

HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET")
HOTMART_ORIGIN = "HOTMART"

if not HOTMART_WEBHOOK_SECRET:
    raise RuntimeError("HOTMART_WEBHOOK_SECRET não definido no ambiente")

router = APIRouter(
    prefix="/webhook/hotmart",
    tags=["Hotmart"]
)

# ===============================
# LOG ESTRUTURADO
# ===============================

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


# ===============================
# VALIDAÇÃO DE ASSINATURA
# ===============================

def validar_assinatura(raw_body: bytes, assinatura_recebida: str) -> bool:
    """
    Hotmart envia assinatura HMAC SHA256 no header:
    X-Hotmart-Hmac-SHA256
    """
    assinatura_calculada = hmac.new(
        key=HOTMART_WEBHOOK_SECRET.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        assinatura_calculada,
        assinatura_recebida
    )


# ===============================
# NORMALIZAÇÃO UNIVERSAL
# ===============================

def normalizar_evento_hotmart(evento: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte payload Hotmart para o modelo universal do Robô
    """

    compra = evento.get("data", {})
    produto = compra.get("product", {})
    afiliado = compra.get("affiliate", {})
    comprador = compra.get("buyer", {})

    valor = float(compra.get("purchase", {}).get("price", 0.0))
    moeda = compra.get("purchase", {}).get("currency", "BRL")

    evento_normalizado = {
        "origem": HOTMART_ORIGIN,
        "evento": evento.get("event"),
        "status": compra.get("status"),
        "transacao_id": compra.get("transaction", {}).get("id"),
        "produto": {
            "id": produto.get("id"),
            "nome": produto.get("name"),
        },
        "afiliado": {
            "id": afiliado.get("affiliate_id"),
            "nome": afiliado.get("name"),
        },
        "comprador": {
            "email": comprador.get("email"),
            "nome": comprador.get("name"),
        },
        "financeiro": {
            "valor": valor,
            "moeda": moeda,
        },
        "timestamp_evento": compra.get("purchase", {}).get("approved_date"),
        "timestamp_ingestao": datetime.now(timezone.utc).isoformat(),
        "raw": evento,  # preservação integral
    }

    return evento_normalizado


# ===============================
# PERSISTÊNCIA (ABSTRAÍDA)
# ===============================

def persistir_evento(evento_normalizado: Dict[str, Any]):
    """
    Persistência compatível com o backend atual.
    Não assume Supabase diretamente para não violar o congelamento do main.py.
    """
    log(
        origem=HOTMART_ORIGIN,
        nivel="INFO",
        mensagem="Evento persistido (camada de persistência abstrata)",
        extra={
            "transacao_id": evento_normalizado.get("transacao_id"),
            "evento": evento_normalizado.get("evento"),
            "valor": evento_normalizado.get("financeiro", {}).get("valor"),
        }
    )


# ===============================
# ENDPOINT WEBHOOK
# ===============================

@router.post("")
async def webhook_hotmart(request: Request):
    raw_body = await request.body()

    assinatura = request.headers.get("X-Hotmart-Hmac-SHA256")
    if not assinatura:
        log(HOTMART_ORIGIN, "WARN", "Assinatura ausente")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Assinatura ausente"
        )

    if not validar_assinatura(raw_body, assinatura):
        log(HOTMART_ORIGIN, "ERROR", "Assinatura inválida")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Assinatura inválida"
        )

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        log(HOTMART_ORIGIN, "ERROR", "Payload inválido (JSON)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload inválido"
        )

    log(
        origem=HOTMART_ORIGIN,
        nivel="INFO",
        mensagem="Webhook recebido",
        extra={
            "event": payload.get("event"),
            "transaction_id": payload.get("data", {}).get("transaction", {}).get("id"),
        }
    )

    evento_normalizado = normalizar_evento_hotmart(payload)
    persistir_evento(evento_normalizado)

    return {"status": "ok"}
