from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase_client import get_supabase

app = FastAPI(
    title="Robô Global de Afiliados",
    description="API para ranking e pontuação de produtos usando Supabase.",
    version="1.0.0"
)

class AtualizarPayload(BaseModel):
    id_produto: str
    metrica: str
    valor: float

@app.get("/status")
def status():
    return {"status": "ok"}

@app.get("/produtos")
def listar_produtos():
    supabase = get_supabase()
    res = supabase.table("produtos").select("*").execute()
    return res.data

@app.post("/atualizar")
def atualizar(payload: AtualizarPayload):
    supabase = get_supabase()

    res = supabase.table("plataforma_metrica").insert({
        "id_produto": payload.id_produto,
        "metrica": payload.metrica,
        "valor": payload.valor
    }).execute()

    return {"status": "sucesso", "data": res.data}
