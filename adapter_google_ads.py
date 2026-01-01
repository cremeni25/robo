# adapter_google_ads.py — Adaptador Google Ads v0.1
# Objetivo: Executar ação EXTERNA mínima, reversível e auditável.
# MODO: RASCUNHO / VALIDAÇÃO (sem veiculação)

import json
from datetime import datetime, timezone
from typing import Dict, Any

# =========================
# Utilidades
# =========================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def registrar_execucao(payload: Dict[str, Any], resultado: Dict[str, Any]) -> None:
    with open("./google_ads_actions.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": utc_now_iso(),
            "payload": payload,
            "resultado": resultado
        }, ensure_ascii=False) + "\n")

# =========================
# Adaptador
# =========================

class GoogleAdsAdapter:
    def executar_rascunho(self, acao: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa uma ação mínima e reversível.
        NÃO ativa campanhas.
        """
        # ⚠️ Aqui NÃO criamos campanha ativa
        # ⚠️ Apenas simulamos/validamos estrutura

        resultado = {
            "status": "RAScunho_CRIADO",
            "acao": acao.get("type"),
            "mensagem": "Ação mínima registrada. Nenhuma veiculação ativa."
        }

        registrar_execucao(acao, resultado)
        return resultado
