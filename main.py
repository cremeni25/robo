# main.py — versão completa e final
# ROBO GLOBAL AI — ENGINE OPERACIONAL REAL
# Substituição TOTAL do arquivo
# Data: 25/12/2025

import os
import time
import threading
from typing import Optional, Dict

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ======================================================
# CONFIGURAÇÕES VIA ENV (RENDER)
# ======================================================

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
META_AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID")  # somente número (sem act_)
HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET")

META_API_VERSION = "v19.0"

if not META_ACCESS_TOKEN or not META_AD_ACCOUNT_ID:
    # Não levanta exceção aqui para não matar o deploy;
    # os endpoints de engine validarão em tempo de uso.
    pass

# ======================================================
# ESTADO GLOBAL DO ENGINE
# ======================================================

ENGINE_STATE: Dict[str, Optional[str]] = {
    "status": "IDLE",          # IDLE | RUNNING | PAUSED | KILLED
    "campaign_id": None,
    "last_action": None,
}

ENGINE_LOCK = threading.Lock()
ENGINE_THREAD: Optional[threading.Thread] = None
ENGINE_STOP_EVENT = threading.Event()

# ======================================================
# FASTAPI APP
# ======================================================

app = FastAPI(
    title="Robo Global AI — Engine Operacional",
    version="1.0.0",
)

# ======================================================
# MODELOS
# ======================================================

class EngineResponse(BaseModel):
    status: str
    detail: str
    campaign_id: Optional[str] = None

# ======================================================
# META ADS — FUNÇÕES REAIS (GRAPH API)
# ======================================================

def _meta_headers():
    return {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
    }

def create_meta_campaign() -> str:
    if not META_ACCESS_TOKEN or not META_AD_ACCOUNT_ID:
        raise RuntimeError("META_ACCESS_TOKEN ou META_AD_ACCOUNT_ID não configurados")

    url = f"https://graph.facebook.com/{META_API_VERSION}/act_{META_AD_ACCOUNT_ID}/campaigns"

    payload = {
        "name": "RoboGlobalAI_Campaign",
        "objective": "TRAFFIC",
        "status": "PAUSED",
        "special_ad_categories": [],
    }

    response = requests.post(url, data=payload, headers=_meta_headers(), timeout=30)

    if response.status_code != 200:
        raise RuntimeError(f"Erro ao criar campanha Meta Ads: {response.text}")

    data = response.json()
    return data["id"]

def set_campaign_status(campaign_id: str, status: str):
    url = f"https://graph.facebook.com/{META_API_VERSION}/{campaign_id}"
    payload = {"status": status}

    response = requests.post(url, data=payload, headers=_meta_headers(), timeout=30)

    if response.status_code != 200:
        raise RuntimeError(f"Erro ao alterar status da campanha: {response.text}")

# ======================================================
# LOOP OPERACIONAL (SIMPLIFICADO)
# ======================================================

def engine_loop():
    """
    Loop contínuo do engine.
    Neste MVP real, o loop apenas mantém o estado vivo.
    A lógica de escala/corte será evoluída a partir daqui.
    """
    while not ENGINE_STOP_EVENT.is_set():
        time.sleep(5)

# ======================================================
# ENDPOINTS DE CONTROLE DO ENGINE
# ======================================================

@app.post("/engine/start", response_model=EngineResponse)
def engine_start():
    global ENGINE_THREAD

    with ENGINE_LOCK:
        if ENGINE_STATE["status"] == "KILLED":
            raise HTTPException(status_code=403, detail="Engine encerrada definitivamente")

        if ENGINE_STATE["status"] == "RUNNING":
            return EngineResponse(
                status="RUNNING",
                detail="Engine já está em execução",
                campaign_id=ENGINE_STATE["campaign_id"],
            )

        try:
            campaign_id = create_meta_campaign()
            set_campaign_status(campaign_id, "ACTIVE")

            ENGINE_STATE["status"] = "RUNNING"
            ENGINE_STATE["campaign_id"] = campaign_id
            ENGINE_STATE["last_action"] = "START"

            ENGINE_STOP_EVENT.clear()
            ENGINE_THREAD = threading.Thread(target=engine_loop, daemon=True)
            ENGINE_THREAD.start()

            return EngineResponse(
                status="RUNNING",
                detail="Engine iniciada e campanha ativada",
                campaign_id=campaign_id,
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/engine/pause", response_model=EngineResponse)
def engine_pause():
    with ENGINE_LOCK:
        if ENGINE_STATE["status"] != "RUNNING":
            return EngineResponse(
                status=ENGINE_STATE["status"],
                detail="Engine não está em execução",
                campaign_id=ENGINE_STATE["campaign_id"],
            )

        ENGINE_STATE["status"] = "PAUSED"
        ENGINE_STATE["last_action"] = "PAUSE"

        return EngineResponse(
            status="PAUSED",
            detail="Engine pausada (lógica interna)",
            campaign_id=ENGINE_STATE["campaign_id"],
        )


@app.post("/engine/kill", response_model=EngineResponse)
def engine_kill():
    with ENGINE_LOCK:
        ENGINE_STATE["status"] = "KILLED"
        ENGINE_STATE["last_action"] = "KILL"
        ENGINE_STOP_EVENT.set()

        return EngineResponse(
            status="KILLED",
            detail="Engine encerrada definitivamente",
            campaign_id=ENGINE_STATE["campaign_id"],
        )


@app.get("/engine/status")
def engine_status():
    return ENGINE_STATE

# ======================================================
# WEBHOOK HOTMART (RECEPÇÃO REAL)
# ======================================================

@app.post("/webhook/hotmart")
def hotmart_webhook(payload: dict):
    # Validação do secret poderá ser adicionada na próxima iteração
    # Neste ponto, o objetivo é materializar o endpoint real
    print("[HOTMART EVENT RECEIVED]", payload)
    return {"ok": True}

# ======================================================
# HEALTHCHECK BÁSICO
# ======================================================

@app.get("/")
def root():
    return {
        "service": "Robo Global AI",
        "engine_status": ENGINE_STATE["status"],
    }

# ======================================================
# ENTRYPOINT
# ======================================================
# Render / uvicorn:
# uvicorn main:app --host 0.0.0.0 --port 8000
