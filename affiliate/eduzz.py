# affiliate/eduzz.py


import json
import os
from datetime import datetime, timezone
from typing import Dict, Any


from fastapi import APIRouter, Request, HTTPException, status


EDUZZ_WEBHOOK_TOKEN = os.getenv("EDUZZ_WEBHOOK_TOKEN")
EDUZZ_ORIGIN = "EDUZZ"


router = APIRouter(
prefix="/webhook/eduzz",
tags=["Eduzz"],
)




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




def validar_token(headers: Dict[str, str]) -> bool:
token = headers.get("Authorization") or headers.get("X-Eduzz-Token")
if not token:
return False
return token.replace("Bearer ", "") == EDUZZ_WEBHOOK_TOKEN




def normalizar_evento(evento: Dict[str, Any]) -> Dict[str, Any]:
data = evento.get("data", {})
return {
"origem": EDUZZ_ORIGIN,
"evento": evento.get("event"),
"status": data.get("status"),
"transacao_id": data.get("transaction_id"),
"financeiro": {
"valor": float(data.get("value", 0)),
"moeda": data.get("currency", "BRL"),
},
"timestamp_ingestao": datetime.now(timezone.utc).isoformat(),
"raw": evento,
}




@router.post("", status_code=status.HTTP_200_OK)
async def webhook_eduzz(request: Request):
if not EDUZZ_WEBHOOK_TOKEN:
raise HTTPException(status_code=503, detail="EDUZZ_WEBHOOK_TOKEN não configurado")


if not validar_token(request.headers):
raise HTTPException(status_code=401, detail="Token EDUZZ inválido")


payload = await request.json()
evento = normalizar_evento(payload)


log(EDUZZ_ORIGIN, "INFO", "Evento recebido", {"transacao_id": evento["transacao_id"]})


return {"status": "ok"}
