from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client
import os

# --- Inicialização ---
app = FastAPI()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- STATUS ---
@app.get("/status")
def status():
    try:
        supabase.table("produtos").select("*").limit(1).execute()
        return {"status": "OK", "supabase": "conectado"}
    except:
        return {"status": "OK", "supabase": "erro_na_consulta"}


# --- LISTAR PRODUTOS ---
@app.get("/produtos")
def produtos():
    try:
        data = supabase.table("produtos").select("*").execute()
        return data.data
    except Exception as e:
        raise HTTPException(500, f"Erro ao consultar produtos: {e}")


# --- PONTUAÇÃO ---
@app.get("/pontuacao")
def pontuacao():
    try:
        data = supabase.table("plataforma_metrica").select("*").execute()
        return data.data
    except Exception as e:
        raise HTTPException(500, f"Erro ao consultar pontuação: {e}")


# --- STRUCT BODY ---
class AtualizarPayload(BaseModel):
    id_produto: str
    metrica: str
    valor: float


# --- ATUALIZAR MÉTRICA ---
@app.post("/atualizar")
def atualizar(payload: AtualizarPayload):
    try:
        ex = supabase.table("plataforma_metrica").select("*") \
            .eq("id_produto", payload.id_produto) \
            .eq("metrica", payload.metrica) \
            .execute()

        if ex.data:
            supabase.table("plataforma_metrica").update({
                "valor": payload.valor
            }).eq("id_produto", payload.id_produto) \
             .eq("metrica", payload.metrica).execute()
        else:
            supabase.table("plataforma_metrica").insert({
                "id_produto": payload.id_produto,
                "metrica": payload.metrica,
                "valor": payload.valor
            }).execute()

        return {"status": "OK"}

    except Exception as e:
        raise HTTPException(500, f"Erro ao atualizar métrica: {e}")


# --- RANKING ---
@app.get("/ranking")
def ranking():
    try:
        query = """
        SELECT
            p.id_produto,
            p.nome,
            COALESCE(SUM(m.valor), 0) AS score
        FROM produtos p
        LEFT JOIN plataforma_metrica m
            ON m.id_produto = p.id_produto
        GROUP BY p.id_produto, p.nome
        ORDER BY score DESC;
        """
        data = supabase.rpc("executar_query", {"query": query}).execute()
        return data.data
    except Exception as e:
        raise HTTPException(500, f"Erro ao consultar ranking: {e}")

