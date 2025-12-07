from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from supabase_client import get_supabase

app = FastAPI(
    title="Robô Global de Afiliados",
    description="API para ranking e pontuação de produtos usando Supabase.",
    version="3.0.0"
)

supabase = get_supabase()


# ---------------------------
# MODELO /atualizar
# ---------------------------
class AtualizarPayload(BaseModel):
    id_produto: str
    metrica: str
    valor: float


# ---------------------------
# /status
# ---------------------------
@app.get("/status")
def status():
    return {"status": "OK", "supabase": "conectado"}


# ---------------------------
# /produtos
# ---------------------------
@app.get("/produtos")
def produtos():
    try:
        result = supabase.table("produtos").select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# /atualizar
# ---------------------------
@app.post("/atualizar")
def atualizar(payload: AtualizarPayload):
    try:
        data = {
            "id_produto": payload.id_produto,
            "metrica": payload.metrica,
            "valor": payload.valor
        }

        result = supabase.table("metrica_historico").insert(data).execute()
        return {"status": "OK", "inserido": result.data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# /pontuacao
# ---------------------------
@app.get("/pontuacao")
def pontuacao(id_produto: Optional[str] = None):
    try:
        if not id_produto:
            raise HTTPException(status_code=400, detail="id_produto é obrigatório")

        query = """
            SELECT
                p.id_produto,
                p.nome,
                COALESCE(SUM(m.valor), 0) AS pontuacao_total
            FROM produtos p
            LEFT JOIN metrica_historico m
                ON m.id_produto = p.id_produto
            WHERE p.id_produto = '{}'
            GROUP BY p.id_produto, p.nome;
        """.format(id_produto)

        result = supabase.rpc("executar_query", {"query": query}).execute()
        return result.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# /ranking  (CORRIGIDO)
# ---------------------------
@app.get("/ranking")
def ranking():
    try:
        query = """
            SELECT
                p.id_produto,
                p.nome,
                COALESCE(SUM(m.valor), 0) AS pontuacao_total
            FROM produtos p
            LEFT JOIN metrica_historico m
                ON m.id_produto = p.id_produto
            GROUP BY p.id_produto, p.nome
            ORDER BY pontuacao_total DESC;
        """

        result = supabase.rpc("executar_query", {"query": query}).execute()
        dados = result.data

        if isinstance(dados, list):
            return dados

        if isinstance(dados, dict):
            return [dados]

        return []

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
