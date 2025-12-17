from fastapi import FastAPI
from datetime import datetime
from supabase import create_client
import os

app = FastAPI()

def sb():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")  # ← AJUSTE REAL

    if not url or not key:
        raise Exception("SUPABASE NÃO CONFIGURADO NO AMBIENTE")

    return create_client(url, key)

def estado_atual():
    r = sb().table("estado_atual").select("*").eq("id", 1).execute()
    return r.data[0] if r.data else None

def bootstrap():
    estado = estado_atual()
    if estado:
        return estado

    ciclo = sb().table("ciclos").insert({
        "decisao": "BOOTSTRAP",
        "resultado": "INIT",
        "capital_antes": 0,
        "capital_depois": 0,
        "status": "SUCESSO",
        "payload": {}
    }).execute()

    sb().table("estado_atual").insert({
        "id": 1,
        "fase": "OPERANDO",
        "capital": 0,
        "ultima_decisao": "BOOTSTRAP",
        "ultimo_ciclo_id": ciclo.data[0]["id"],
        "atualizado_em": datetime.utcnow().isoformat()
    }).execute()

    return estado_atual()

@app.post("/ping")
def ping():
    return {"ok": True}

@app.post("/ciclo")
def ciclo(payload: dict = {}):
    try:
        estado = bootstrap()
        capital_antes = estado["capital"]

        decisao = "OBSERVAR"
        capital_depois = capital_antes

        ciclo = sb().table("ciclos").insert({
            "decisao": decisao,
            "resultado": "EXECUTADO",
            "capital_antes": capital_antes,
            "capital_depois": capital_depois,
            "status": "SUCESSO",
            "payload": payload
        }).execute()

        ciclo_id = ciclo.data[0]["id"]

        sb().table("estado_atual").update({
            "capital": capital_depois,
            "ultima_decisao": decisao,
            "ultimo_ciclo_id": ciclo_id,
            "atualizado_em": datetime.utcnow().isoformat()
        }).eq("id", 1).execute()

        return {"ok": True, "ciclo_id": ciclo_id}

    except Exception as e:
        return {
            "ok": False,
            "erro": str(e)
        }

@app.get("/estado")
def estado():
    sbc = sb()
    res = sbc.table("estado_atual").select("*").eq("id", 1).execute()
    return res.data[0] if res.data else {}
