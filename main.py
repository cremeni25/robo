# main.py — Robo Global AI (estado persistente real)

from fastapi import FastAPI, Request
from datetime import datetime
from supabase import create_client
import os

app = FastAPI()

# Supabase (SERVICE ROLE)
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"]
)

# ---------- UTIL ----------

def get_estado():
    res = supabase.table("estado_atual").select("*").eq("id", 1).execute()
    return res.data[0] if res.data else None


def bootstrap():
    estado = get_estado()
    if estado:
        return estado

    ciclo = supabase.table("ciclos").insert({
        "decisao": "BOOTSTRAP",
        "resultado": "INICIALIZACAO",
        "capital_antes": 0.0,
        "capital_depois": 0.0,
        "status": "SUCESSO",
        "payload": {}
    }).execute()

    ciclo_id = ciclo.data[0]["id"]

    supabase.table("estado_atual").insert({
        "id": 1,
        "fase": "INICIAL",
        "capital": 0.0,
        "ultima_decisao": "BOOTSTRAP",
        "ultimo_ciclo_id": ciclo_id,
        "atualizado_em": datetime.utcnow().isoformat()
    }).execute()

    return get_estado()


# ---------- ENDPOINTS ----------

@app.post("/ping")
def ping():
    return {"ok": True, "ts": datetime.utcnow().isoformat()}


@app.post("/ciclo")
def ciclo(payload: dict = {}):
    estado = bootstrap()

    capital_antes = estado["capital"]

    # LÓGICA ATUAL DO ROBÔ (MVP REAL)
    decisao = "OBSERVAR"
    capital_depois = capital_antes

    ciclo = supabase.table("ciclos").insert({
        "decisao": decisao,
        "resultado": "EXECUTADO",
        "capital_antes": capital_antes,
        "capital_depois": capital_depois,
        "status": "SUCESSO",
        "payload": payload
    }).execute()

    ciclo_id = ciclo.data[0]["id"]

    supabase.table("estado_atual").update({
        "fase": "OPERANDO",
        "capital": capital_depois,
        "ultima_decisao": decisao,
        "ultimo_ciclo_id": ciclo_id,
        "atualizado_em": datetime.utcnow().isoformat()
    }).eq("id", 1).execute()

    return {"status": "ok", "ciclo_id": ciclo_id}


@app.get("/estado")
def estado():
    return get_estado()
