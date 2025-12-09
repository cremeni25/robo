from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from supabase_client import get_supabase

app = FastAPI(
    title="Robô Global de Afiliados",
    description="API para ranking, pontuação e monetização global.",
    version="4.1.0"
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


# -----------------------------------
# Registrar comissão recebida
# -----------------------------------
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


# -----------------------------------
# Consultar saldo interno
# -----------------------------------
@app.get("/capital")
def capital():
    try:
        result = supabase.table("capital_interno").select("*").order("id", desc=True).limit(1).execute()

        if not result.data:
            return {"saldo_atual": 0, "saldo_previsto": 0}

        return result.data[0]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------
# Produtos elegíveis (pagamento rápido)
# -----------------------------------
@app.get("/produtos_elegiveis")
def produtos_elegiveis():
    try:
        result = supabase.table("produtos_elegiveis").select("*").eq("status", "aprovado").execute()
        return result.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------
# Decisão automática do robô
# -----------------------------------
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

        produto = produtos_list[0]

        acao = f"Escalar produto {produto['nome']}"
        motivo = "Pagamento rápido + Produto elegível"
        recomendacao = "Aumentar presença deste produto nas estratégias internas de venda."

        # Registrar decisão (ajuste o nome da tabela se seu SQL criou outro)
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


# -----------------------------------
# Plano diário automático
# -----------------------------------
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

        acao = f"Priorizar divulgação do produto {produto['nome']}"
        prioridade = "alta" if saldo > 0 else "baixa"
        observacao = "Utilizar saldo interno disponível" if saldo > 0 else "Aguardando primeira comissão para aumentar ritmo"

        # Registrar plano diário
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------
# Análise estratégica interna
# -----------------------------------
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
        decisao_reg = supabase.table("decisoes_robo").select("*").order("id", desc=True).limit(1).execute()
        decisao_texto = decisao_reg.data[0]["acao"] if decisao_reg.data else "Sem decisão registrada"

        # Risco simples baseado no capital
        risco = "baixo" if saldo > 0 else "alto"
        recomendacao = "Acelerar divulgação" if saldo > 0 else "Aguardar primeira comissão"

        # Registrar indicadores internos
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


@app.get("/escala")
def escala():
    try:
        # Consultar capital interno
        capital = supabase.table("capital_interno").select("*").order("id", desc=True).limit(1).execute()
        saldo = capital.data[0]["saldo_atual"] if capital.data else 0

        # Consultar produto elegível
        produtos = supabase.table("produtos_elegiveis").select("*").eq("status", "aprovado").execute()
        produto = produtos.data[0] if produtos.data else None

        if not produto:
            return {"erro": "Nenhum produto elegível disponível para escalar."}

        # Calcular risco
        risco = "baixo" if saldo > 0 else "alto"

        # ROI previsto simples (primeira versão — será evoluído depois)
        roi_previsto = 0
        if produto["pagamento"] == "imediato":
            roi_previsto = 1.4   # 40% potencial de retorno rápido
        else:
            roi_previsto = 1.1   # retorno mais lento

        # Capital projetado
        capital_projetado = saldo * roi_previsto

        # Definir decisão
        if risco == "baixo":
            decisao = f"Escalar imediatamente o produto {produto['nome']}"
            observacao = "Saldo positivo permite aceleração controlada."
        else:
            decisao = f"Não escalar ainda o produto {produto['nome']}"
            observacao = "É necessário aguardar primeira comissão."

        # Registrar decisão financeira
        supabase.table("escala_financeira").insert({
            "produto_id": produto["id_produto"],
            "produto_nome": produto["nome"],
            "capital_projetado": capital_projetado,
            "risco": risco,
            "roi_previsto": roi_previsto,
            "decisao": decisao,
            "observacao": observacao
        }).execute()

        return {
            "produto": produto,
            "capital_atual": saldo,
            "capital_projetado": capital_projetado,
            "roi_previsto": roi_previsto,
            "risco": risco,
            "decisao": decisao,
            "observacao": observacao
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ciclo")
def ciclo():
    try:
        # 1 — Executar DECISÃO
        decisao_resp = decisao()
        decisao_texto = decisao_resp["acao"]
        produto_nome = decisao_resp["produto"]["nome"]

        # 2 — Executar PLANO DIÁRIO
        plano_resp = plano_diario()
        plano_texto = plano_resp["acao"]

        # 3 — Executar ANÁLISE
        analise_resp = analise()
        capital = analise_resp["capital"]
        risco = analise_resp["risco"]

        # 4 — Executar ESCALA
        escala_resp = escala()
        escala_texto = escala_resp["decisao"]

        # 5 — Registrar ciclo completo
        supabase.table("ciclos_robo").insert({
            "produto_nome": produto_nome,
            "decisao": decisao_texto,
            "plano": plano_texto,
            "capital": capital,
            "risco": risco,
            "escala": escala_texto
        }).execute()

        # 6 — Retorno consolidado
        return {
            "produto": produto_nome,
            "decisao": decisao_texto,
            "plano": plano_texto,
            "capital": capital,
            "risco": risco,
            "escala": escala_texto,
            "status": "Ciclo executado com sucesso"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/resultado")
def resultado():
    try:
        # Último produto analisado
        produto = supabase.table("produtos_elegiveis").select("*").order("id_produto", desc=True).limit(1).execute()
        produto_dados = produto.data[0] if produto.data else None

        # Última decisão
        decisao = supabase.table("decisoes_robo").select("*").order("id", desc=True).limit(1).execute()
        decisao_dados = decisao.data[0] if decisao.data else None

        # Último plano diário
        plano = supabase.table("plano_diario").select("*").order("id", desc=True).limit(1).execute()
        plano_dados = plano.data[0] if plano.data else None

        # Últimos indicadores internos
        indicadores = supabase.table("indicadores_internos").select("*").order("id", desc=True).limit(1).execute()
        indicadores_dados = indicadores.data[0] if indicadores.data else None

        # Último ciclo completo
        ciclo = supabase.table("ciclos_robo").select("*").order("id", desc=True).limit(1).execute()
        ciclo_dados = ciclo.data[0] if ciclo.data else None

        return {
            "produto": produto_dados,
            "decisao": decisao_dados,
            "plano": plano_dados,
            "indicadores": indicadores_dados,
            "ciclo": ciclo_dados
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

