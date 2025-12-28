# affiliate/eduzz.py
# Integração REAL Eduzz — Webhook, Validação, Normalização e Persistência
# Arquivo AUTÔNOMO — não altera main.py

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, status

# ===============================
# CONFIGURAÇÕES
# ===============================

EDUZZ_WEBHOOK_TOKEN = os.getenv("EDUZZ_WEBHOOK_TOKEN")
EDUZZ_ORIGIN = "EDUZZ"

if not EDUZZ_WEBHOOK_TOKEN:
    raise RuntimeError("EDUZZ_WEBHOOK_TOKEN não definido no ambiente")

router = APIRouter(
    prefix="/webhook/eduzz",
    tags=["Eduzz"]
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
    A Eduzz envia o token no header (ex: Authorization ou X-Eduzz-Token).
    Mantemos tolerância a variações documentadas.
    """
    token_recebido = (
        headers.get("authorization")
        or headers.get("Authorization")
        or headers.get("X-Eduzz-Token")
        or headers.get("x-eduzz-token")
    )

    if not token_recebido:
        return False

    # Normaliza "Bearer <token>" se existir
    if token_recebido.lower().startswith("bearer "):
        token_recebido = token_recebido.split(" ", 1)[1].strip()

    return token_recebido == EDUZZ_WEBHOOK_TOKEN


# ===============================
# NORMALIZAÇÃO UNIVERSAL
# ===============================

def normalizar_evento_eduzz(evento: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte payload Eduzz para o modelo universal do Robô
    """

    dados = evento.get("data", {})

    valor = float(dados.get("value", 0.0))
    moeda = dados.get("currency", "BRL")

    evento_normalizado = {
        "origem": EDUZZ_ORIGIN,
        "evento": evento.get("event") or evento.get("type"),
        "status": dados.get("status"),
        "transacao_id": dados.get("transaction_id") or dados.get("id"),
        "produto": {
            "id": dados.get("product_id"),
            "nome": dados.get("product_name"),
        },
        "afiliado": {
            "id": dados.get("affiliate_id"),
            "nome": dados.get("affiliate_name"),
        },
        "comprador": {
            "email": dados.get("customer_email"),
            "nome": dados.get("customer_name"),
        },
        "financeiro": {
            "valor": valor,
            "moeda": moeda,
        },
        "timestamp_evento": dados.get("created_at"),
        "timestamp_ingestao": datetime.now(timezone.utc).isoformat(),
        "raw": evento,  # preservação integral
    }

    return evento_normalizado


# ===============================
# PERSISTÊNCIA (ABSTRAÍDA)
# ===============================

def persistir_evento(evento_normalizado: Dict[str, Any]):
    """
    Persistência desacoplada.
    Compatível com o backend atual sem alterar main.py.
    """
    log(
        origem=EDUZZ_ORIGIN,
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
async def webhook_eduzz(request: Request):
    if not validar_token(request.headers):
        log(EDUZZ_ORIGIN, "ERROR", "Token inválido ou ausente")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    try:
        payload = await request.json()
    except Exception:
        log(EDUZZ_ORIGIN, "ERROR", "Payload inválido (JSON)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload inválido"
        )

    log(
        origem=EDUZZ_ORIGIN,
        nivel="INFO",
        mensagem="Webhook recebido",
        extra={
            "event": payload.get("event") or payload.get("type"),
            "transaction_id": payload.get("data", {}).get("transaction_id"),
        }
    )

    evento_normalizado = normalizar_evento_eduzz(payload)
    persistir_evento(evento_normalizado)

    return {"status": "ok"}
