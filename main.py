from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.post("/ping")
def ping():
    print("PING_REAL", datetime.utcnow().isoformat())
    return {"ok": True}

from datetime import datetime

@app.post("/ciclo")
def ciclo():
    print("CICLO_EXECUTADO", datetime.utcnow().isoformat())
    return {"status": "ciclo_ok"}
