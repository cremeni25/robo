# controlador_acao_externa.py
# ROBO GLOBAL AI — CONTROLE DE AÇÕES EXTERNAS
# Função: Ponte de aquisição (Google → Robô → Plataforma)
# Arquivo único, seguro para deploy
# Python 3.13 | FastAPI

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from datetime import datetime, timezone
import logging

# Router dedicado às ações externas
router = APIRouter()

# Logger institucional
logger = logging.getLogger("ROBO-ACQUISITION")


@router.get("/go/eduzz/produtividade")
async def go_eduzz_produtividade(request: Request):
    """
    Endpoint de aquisição:
    - Recebe clique do tráfego (Google Ads)
    - Registra evento
    - Redireciona imediatamente para o checkout Eduzz
    """

    evento = {
        "evento": "clique",
        "origem": "google_ads",
        "plataforma_destino": "eduzz",
        "produto": "produtividade_autentica",
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Log estruturado (não bloqueante)
    logger.info(f"[ACQUISITION] {evento}")

    # Redirecionamento imediato para o checkout Eduzz
    return RedirectResponse(
        url="https://chk.eduzz.com/801EB01RW7",
        status_code=302
    )
