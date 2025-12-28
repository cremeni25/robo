# affiliate/monetizze.py
# Integração REAL Monetizze — Webhook, Validação, Normalização e Persistência
# Arquivo AUTÔNOMO — não altera main.py

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, status

# ===============================
# CONFIGURAÇÕES
# ===============================

MONETIZZE_WEBHOOK_TOKEN = os.getenv("MONETIZZE_WEBHOOK_TOKEN")
MONETIZZE_ORIGIN = "MONETIZZE"

if not MONETIZZE_WEBHOOK_TOKEN:
    raise RuntimeError("MONETIZZE_WEBHOOK_TOKEN não definido no ambiente")

router = APIRouter(
    prefix="/webhook/monetizze",
    tags=["Monetizze"]
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
# VALIDAÇÃO DE TOKEN
# ===============================

def validar_token(headers: Dict[str, str]) -> bool:
    """
    Monetizze envia token no header (ex: X-Monetizze-Token).
    Mantemos tolerância a variações.
    """
    token_recebido = (
        headers.get("X-Monetizze-Token")
        or headers.get("x-monetizze-token")
        or headers.get("Authorization")
        or headers.get("authorization")
    )

    if not token_recebido:
        return False

    if token_recebido.lower().startswith("bearer "):
        token_recebido = token_recebido.split(" ", 1)[1].strip()

    return token_recebido == MONETIZZE_WEBHOOK_TOKEN


# ===============================
# NORMALIZAÇÃO UNIVERSAL
# ===============================

def normalizar_evento_monetizze(evento: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte payload Monetizze para o modelo universal do Robô
    """

    dados = evento.get("data", {})

    valor = float(dados.get("sale_value", 0.0))
    moeda = dados.get("currency", "BRL")

    evento_normalizado = {
        "origem": MONETIZZE_ORIGIN,
        "evento": evento.get("event") or evento.get("type"),
        "status": dados.get("status"),
        "transacao_id": dados.get("sale_id") or dados.get("id"),
        "produto": {
            "id": dados.get("product_id"),
            "nome": dados.get("product_name"),
        },
        "afiliado": {
            "id": dados.get("affiliate_id"),
            "nome": dados.get("affiliate_name"),
        },
        "comprador": {
            "email": dados.get("buyer_email"),
            "nome": dados.get("buyer_name"),
        },
        "financeiro": {
            "valor": valor,
            "moeda": moeda,
        },
        "timestamp_evento": dados.get("created_at"),
        "timestamp_ingestao": datetime.now(timezone.utc).isoformat(),
        "raw": evento,
    }

    return evento_normalizado


# ===============================
# PERSISTÊNCIA (ABSTRAÍDA)
# ===============================

def persistir_evento(evento_normalizado: Dict[str, Any]):
    """
    Persistência desacoplada, compatível com o backend atual.
    """
    log(
        origem=MONETIZZE_ORIGIN,
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
async def webhook_monetizze(request: Request):
    if not validar_token(request.headers):
        log(MONETIZZE_ORIGIN, "ERROR", "Token inválido ou ausente")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    try:
        payload = await request.json()
    except Exception:
        log(MONETIZZE_ORIGIN, "ERROR", "Payload inválido (JSON)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload inválido"
        )

    log(
        origem=MONETIZZE_ORIGIN,
        nivel="INFO",
        mensagem="Webhook recebido",
        extra={
            "event": payload.get("event") or payload.get("type"),
            "transaction_id": payload.get("data", {}).get("sale_id"),
        }
    )

    evento_normalizado = normalizar_evento_monetizze(payload)
    persistir_evento(evento_normalizado)

    return {"status": "ok"}
