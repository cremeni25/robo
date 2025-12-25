# main.py — ROBO GLOBAL AI (API SOBERANA)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import os

app = FastAPI(title="Robo Global AI")

class ExecuteRequest(BaseModel):
    mode: str
    max_spend: float

@app.get("/status")
def status():
    return {
        "service": "Robo Global AI",
        "engine_status": "READY"
    }

@app.post("/engine/execute")
def execute_engine(payload: ExecuteRequest):
    if payload.mode != "acquisition_meta_ads":
        raise HTTPException(status_code=400, detail="Modo inválido")

    if payload.max_spend <= 0:
        raise HTTPException(status_code=400, detail="Max spend inválido")

    try:
        result = subprocess.Popen(
            ["python", "acquisition_meta_ads.py"],
            env={**os.environ, "MAX_TEST_SPEND": str(payload.max_spend)}
        )
        return {
            "status": "EXECUTING",
            "mode": payload.mode,
            "pid": result.pid
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
