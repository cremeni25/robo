# main.py — ROBO GLOBAL AI (API SOBERANA FINAL)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import acquisition_meta_ads

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
        # garante alinhamento do teto
        acquisition_meta_ads.MAX_TEST_SPEND = payload.max_spend

        result = acquisition_meta_ads.run_real_test()

        return {
            "status": "EXECUTED",
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
