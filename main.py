from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from supabase import create_client
import os

app = FastAPI(
    title="Robô Global de Afiliados",
    description="API para ranking e pontuação de produtos usando Supabase.",
    version="3.0.0"
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.get("/status")
def status():
    if supabase:
        return {"status": "OK", "supabase": "conectado"}
    return {"status": "ERRO", "supabase": "nao_conectado"}


@app.get("/produtos")
def listar_produtos():
    if not supabase:
        raise HTTPException(500, "Falha na conexão com Supabase")

    data = supabase.table("produtos").select("*").execute()
    return data.data


class AtualizarPayload(BaseModel):
    id_produto: str
    metrica: str
    valor: float


@app.post("/atualizar")
def atualizar_metrica(payload: AtualizarPayload):
    if not supabase:
        raise HTTPException(500, "Supabase desconectado")

    existente = supabase.table("plataforma_metrica") \
        .select("*") \
        .eq("id_produto", payload.id_produto) \
        .eq("metrica", payload.metrica) \
        .execute()

    if existente.data:
        supabase.table("plataforma_metrica") \
            .update({"valor": payload.valor}) \
            .eq("id_produto", payload.id_produto) \
            .eq("metrica", payload.metrica) \
            .execute()
    else:
        supabase.table("plataforma_metrica") \
            .insert({
                "id_produto": payload.id_produto,
                "metrica": payload.metrica,
                "valor": payload.valor
            }).execute()

    return {"status": "OK"}


@app.get("/ranking")
def ranking():
    if not supabase:
        raise HTTPException(500, "Supabase desconectado")

    query = """
    SELECT p.id_produto, p.nome, COALESCE(SUM(m.valor),0) AS score
    FROM produtos p
    LEFT JOIN plataforma_metrica m ON m.id_produto = p.id_produto
    GROUP BY p.id_produto, p.nome
    ORDER BY score DESC;
    """

    data = supabase.rpc("executar_query", {"query": query}).execute()
    return data.data


@app.get("/pontuacao")
def pontuacao():
    if not supabase:
        raise HTTPException(500, "Supabase desconectado")

    data = supabase.table("plataforma_metrica").select("*").execute()
    return data.data
