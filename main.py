from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from supabase_client import get_supabase

app = FastAPI(
    title="Robô Global de Afiliados",
    description="API para ranking, pontuação e monetização global.",
    version="4.0.0"
)

supabase = get_supabase()


# -----------------------------------
# MODELO /atualizar
# -----------------------------------
class AtualizarPayload(BaseModel):
    id_produto: str
    metrica: str
    valor: float


# -----------------------------------
# /status
# -----------------------------------
@app.get("/status")
def status():
    return {"status": "OK", "supabase": "conectado"}


# -----------------------------------
# /produtos
# -----------------------------------
@app.get("/produtos")
def produtos():
    try:
        result = supabase.table("produtos").select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------
# /atualizar
# -----------------------------------
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


# -----------------------------------
# /pontuacao
# -----------------------------------
@app.get("/pontuacao")
def pontuacao(id_produto: Optional[str] = None):
    try:
        if not id_produto:
            raise HTTPException(status_code=400, detail="id_produto é obrigatório")

        query = f"""
            SELECT
                p.id_produto,
                p.nome,
                COALESCE(SUM(m.valor), 0) AS pontuacao_total
            FROM produtos p
            LEFT JOIN metrica_historico m
                ON m.id_produto = p.id_produto
            WHERE p.id_produto = '{id_produto}'
            GROUP BY p.id_produto, p.nome;
        """

        result = supabase.rpc("executar_query", {"query": query}).execute()
        return result.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------
# /ranking
# -----------------------------------
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


# -----------------------------------
# WIDGET OFICIAL /widget-ranking
# -----------------------------------
@app.get("/widget-ranking", response_class=HTMLResponse)
def widget_ranking():
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Ranking – Widget</title>
        <style>
            body { font-family: Arial; margin:0; padding:0; background:#fff; }
            .box { padding:15px; }
            h2 { text-align:center; color:#222; }
            table { width:100%; border-collapse:collapse; margin-top:15px; }
            th { background:#0057ff; color:white; padding:10px; }
            td { padding:8px; border-bottom:1px solid #eee; text-align:center; }
            tr:nth-child(even) { background:#f6f6f6; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>🏆 Ranking de Produtos</h2>
            <table id="rankingTable">
                <tr>
                    <th>Pos.</th>
                    <th>Produto</th>
                    <th>Pontos</th>
                </tr>
            </table>
        </div>

        <script>
            async function load() {
                const resp = await fetch("/ranking");
                const data = await resp.json();
                const table = document.getElementById("rankingTable");

                table.innerHTML = `
                <tr>
                    <th>Pos.</th>
                    <th>Produto</th>
                    <th>Pontos</th>
                </tr>
                `;

                data.forEach((item, i) => {
                    table.innerHTML += `
                    <tr>
                        <td>${i+1}º</td>
                        <td>${item.nome}</td>
                        <td>${item.pontuacao_total}</td>
                    </tr>`;
                });
            }

            load();
            setInterval(load, 5000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# ---------------------------
# Registrar comissão recebida
# ---------------------------
@app.post("/registrar_comissao")
def registrar_comissao(valor: float, origem: str = "desconhecida"):
    try:
        supabase.table("capital_interno").insert({
            "saldo_atual": valor,
            "saldo_previsto": 0,
            "origem": origem,
            "observacao": "comissão registrada"
        }).execute()

        return {"status": "OK", "valor_registrado": valor}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# Consultar saldo interno
# ---------------------------
@app.get("/capital")
def capital():
    try:
        result = supabase.table("capital_interno").select("*").order("id", desc=True).limit(1).execute()

        if not result.data:
            return {"saldo_atual": 0, "saldo_previsto": 0}

        return result.data[0]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# Produtos elegíveis (pagamento rápido)
# ---------------------------
@app.get("/produtos_elegiveis")
def produtos_elegiveis():
    try:
        result = supabase.table("produtos_elegiveis").select("*").eq("status", "aprovado").execute()
        return result.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/decisao")
def decisao():
    try:
        # Consultar saldo
        capital = supabase.table("capital_interno").select("*").order("id", desc=True).limit(1).execute()
        saldo = capital.data[0]["saldo_atual"] if capital.data else 0

        # Consultar produtos elegíveis
        produtos = supabase.table("produtos_elegiveis").select("*").eq("status", "aprovado").execute()
        produtos_list = produtos.data

        if not produtos_list:
            return {"erro": "Nenhum produto elegível encontrado."}

        # Selecionar produto com regra simples inicial (placeholder inteligente)
        produto = produtos_list[0]

        acao = f"Escalar produto {produto['nome']}"
        motivo = "Pagamento rápido + Produto elegível"
        recomendacao = "Aumentar presença deste produto nas estratégias internas de venda."

        # Registrar a decisão
        supabase.table("decisoes_robo").insert({
            "produto_id": produto["id_produto"],
            "produto_nome": produto["nome"],
            "acao": acao,
            "motivo": motivo,
            "capital_disponivel": saldo,
            "recomendacao": recomendacao
        }).execute()

        return {
            "produto": produto,
            "acao": acao,
            "motivo": motivo,
            "capital_disponivel": saldo,
            "recomendacao": recomendacao
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/plano-diario")
def plano_diario():
    try:
        # Saldo atual
        capital = supabase.table("capital_interno").select("*").order("id", desc=True).limit(1).execute()
        saldo = capital.data[0]["saldo_atual"] if capital.data else 0

        # Produtos elegíveis
        produtos = supabase.table("produtos_elegiveis").select("*").eq("status", "aprovado").execute()
        produtos_list = produtos.data

        if not produtos_list:
            return {"erro": "Nenhum produto elegível disponível."}

        produto = produtos_list[0]

        # Geração do plano diário
        acao = f"Priorizar divulgação do produto {produto['nome']}"
        prioridade = "alta" if saldo > 0 else "baixa"
        observacao = "Utilizar saldo interno disponível" if saldo > 0 else "Aguardando primeira comissão para aumentar ritmo"

        # Registrar no banco
        supabase.table("plano_diario").insert({
            "produto_id": produto["id_produto"],
            "produto_nome": produto["nome"],
            "capital_disponivel": saldo,
            "acao": acao,
            "prioridade": prioridade,
            "observacao": observacao
        }).execute()

        return {
            "produto": produto,
            "capital_disponivel": saldo,
            "acao": acao,
            "prioridade": prioridade,
            "observacao": observacao
        }


    @app.get("/analise")
def analise():
    try:
        # Capital interno
        capital = supabase.table("capital_interno").select("*").order("id", desc=True).limit(1).execute()
        saldo = capital.data[0]["saldo_atual"] if capital.data else 0

        # Produto elegível
        produtos = supabase.table("produtos_elegiveis").select("*").eq("status", "aprovado").execute()
        produto = produtos.data[0] if produtos.data else None

        # Plano diário
        plano = supabase.table("plano_diario").select("*").order("id", desc=True).limit(1).execute()
        plano_texto = plano.data[0]["acao"] if plano.data else "Sem plano registrado"

        # Decisão do robô
        decisao = supabase.table("decisoes_robo").select("*").order("id", desc=True).limit(1).execute()
        decisao_texto = decisao.data[0]["acao"] if decisao.data else "Sem decisão registrada"

        # Risco simples baseado no capital
        risco = "baixo" if saldo > 0 else "alto"

        recomendacao = "Acelerar divulgação" if saldo > 0 else "Aguardar primeira comissão"

        # Registrar indicadores
        supabase.table("indicadores_internos").insert({
            "produto_id": produto["id_produto"] if produto else None,
            "produto_nome": produto["nome"] if produto else None,
            "capital": saldo,
            "decisao": decisao_texto,
            "plano": plano_texto,
            "risco": risco,
            "recomendacao": recomendacao
        }).execute()

        return {
            "produto": produto,
            "capital": saldo,
            "decisao": decisao_texto,
            "plano": plano_texto,
            "risco": risco,
            "recomendacao": recomendacao
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

