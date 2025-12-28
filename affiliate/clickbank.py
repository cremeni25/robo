# affiliate/clickbank.py
# Integração REAL ClickBank — Postback (GET) + Modelo Pull Opcional
# Arquivo AUTÔNOMO — não altera main.py

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, status

# ===============================
# CONFIGURAÇÕES
# ===============================

CLICKBANK_SECRET_KEY = os.getenv("CLICKBANK_SECRET_KEY")  # recomendado usar a Secret Key do postback
CLICKBANK_ORIGIN = "CLICKBANK"

if not CLICKBANK_SECRET_KEY:
    raise RuntimeError("CLICKBANK_SECRET_KEY não definido no ambiente")

router = APIRouter(
    prefix="/postback/clickbank",
    tags=["ClickBank"]
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
# VALIDAÇÃO DE POSTBACK
# ===============================

def validar_postback(query: Dict[str, str]) -> bool:
    """
    ClickBank permite validar via Secret Key enviada como parâmetro customizado.
    Exemplo comum: ?secretKey=XXXX
    """
    secret_recebida = query.get("secretKey") or query.get("secret_key")
    return secret_recebida == CLICKBANK_SECRET_KEY


# ===============================
# NORMALIZAÇÃO UNIVERSAL
# ===============================

def normalizar_evento_clickbank(query: Dict[str, str]) -> Dict[str, Any]:
    """
    Converte parâmetros GET do ClickBank para o modelo universal do Robô
    Campos comuns:
    - receipt
    - itemNo
    - itemTitle
    - amount
    - currency
    - affiliate
    - customerEmail
    - transactionType (SALE, BILL, RFND, CGBK)
    """

    valor = float(query.get("amount", "0") or 0)
    moeda = query.get("currency", "USD")

    evento_normalizado = {
        "origem": CLICKBANK_ORIGIN,
        "evento": query.get("transactionType"),
        "status": query.get("transactionType"),
        "transacao_id": query.get("receipt"),
        "produto": {
            "id": query.get("itemNo"),
            "nome": query.get("itemTitle"),
        },
        "afiliado": {
            "id": query.get("affiliate"),
            "nome": query.get("affiliate"),
        },
        "comprador": {
            "email": query.get("customerEmail"),
            "nome": None,
        },
        "financeiro": {
            "valor": valor,
            "moeda": moeda,
        },
        "timestamp_evento": query.get("time") or datetime.now(timezone.utc).isoformat(),
        "timestamp_ingestao": datetime.now(timezone.utc).isoformat(),
        "raw": dict(query),
    }

    return evento_normalizado


# ===============================
# PERSISTÊNCIA (ABSTRAÍDA)
# ===============================

def persistir_evento(evento_normalizado: Dict[str, Any]):
    log(
        origem=CLICKBANK_ORIGIN,
        nivel="INFO",
        mensagem="Evento persistido (camada de persistência abstrata)",
        extra={
            "transacao_id": evento_normalizado.get("transacao_id"),
            "evento": evento_normalizado.get("evento"),
            "valor": evento_normalizado.get("financeiro", {}).get("valor"),
        }
    )


# ===============================
# ENDPOINT POSTBACK (GET)
# ===============================

@router.get("")
async def postback_clickbank(request: Request):
    query_params = dict(request.query_params)

    if not validar_postback(query_params):
        log(CLICKBANK_ORIGIN, "ERROR", "Postback inválido — secret incorreta")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Postback inválido"
        )

    log(
        origem=CLICKBANK_ORIGIN,
        nivel="INFO",
        mensagem="Postback recebido",
        extra={
            "receipt": query_params.get("receipt"),
            "transactionType": query_params.get("transactionType"),
        }
    )

    evento_normalizado = normalizar_evento_clickbank(query_params)
    persistir_evento(evento_normalizado)

    # ClickBank espera HTTP 200 simples
    return {"status": "ok"}


# ===============================
# MODELO PULL (OPCIONAL / DESATIVADO)
# ===============================

def pull_clickbank_events(since: Optional[str] = None):
    """
    MODELO de pull para relatórios da ClickBank.
    Não executa automaticamente.
    Mantido apenas para compatibilidade futura.
    """
    log(
        origem=CLICKBANK_ORIGIN,
        nivel="INFO",
        mensagem="Pull ClickBank chamado (modelo, não executado)",
        extra={"since": since}
    )
