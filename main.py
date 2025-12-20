# main.py — ROBO GLOBAL AI
# ETAPA 1: ESQUELETO DO BACKEND

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(
    title="Robo Global AI",
    version="1.0.0",
    description="Backend central do Robo Global AI — Afiliados"
)

# ======================================================
# CORS (liberado para dashboard humano no futuro)
# ======================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# HEALTH CHECK
# ======================================================
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Robo Global AI",
        "timestamp": datetime.utcnow().isoformat()
    }

# ======================================================
# ROOT
# ======================================================
@app.get("/")
def root():
    return {
        "message": "Robo Global AI ativo",
        "stage": "ETAPA 1 — Esqueleto do backend"
    }
