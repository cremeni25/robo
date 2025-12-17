from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.post("/ping")
def ping():
    print("PING_REAL", datetime.utcnow().isoformat())
    return {"ok": True}
