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

# --- ESTADO ECONÔMICO (MVP) ---
from datetime import datetime

ESTADO = {
    "capital": 0.0,
    "eventos": 0,
    "ultima_decisao": None,
}

@app.get("/estado")
def estado():
    return ESTADO

@app.post("/ciclo")
def ciclo():
    ESTADO["eventos"] += 1
    ESTADO["ultima_decisao"] = {
        "acao": "OBSERVAR",
        "timestamp": datetime.utcnow().isoformat()
    }
    print("CICLO_EXECUTADO", ESTADO["eventos"], ESTADO["ultima_decisao"])
    return {"status": "ciclo_ok", "eventos": ESTADO["eventos"]}
