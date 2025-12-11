from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from supabase_client import get_supabase
from datetime import datetime, timedelta
import os

# =========================================================
#  CONFIGURAÇÃO PRINCIPAL DA API (ÚNICO app = FastAPI)
# =========================================================
app = FastAPI(
    title="Robô Global de Afiliados",
    description="API para ranking, pontuação e monetização global usando Supabase.",
    version="4.1.0",
)

# --- CORS LIBERADO PARA O DASHBOARD EM GITHUB PAGES ---
origins = [
    "https://cremeni25.github.io",
    "https://cremeni25.github.io/robo-global-dashboard",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexão única com o Supabase
supabase = get_supabase()

# =========================================================
#  CONFIGURAÇÕES OPERACIONAIS (AJUSTÁVEIS)
# =========================================================
ROI_MINIMO = 1.2              # definido por você
CAPITAL_MINIMO_PARA_ESCALA = 10.0  # valor mínimo de saldo para permitir escala (ajustável)
COOLDOWN_HORAS = 1           # mínimo entre execuções de escala para evitar loops agressivos

# =========================================================
#  MODELOS
# =========================================================
class AtualizarPayload(BaseModel):
    id_produto: str
    metrica: str
    valor: float

# =========================================================
#  ENDPOINTS BÁSICOS
# =========================================================
@app.get("/status")
def status():
    return {"status": "OK", "supabase": "conectado"}


@app.get("/produtos")
def produtos():
    try:
        result = supabase.table("produtos").select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/atualizar")
def atualizar(payload: AtualizarPayload):
    try:
        data = {
            "id_produto": payload.id_produto,
            "metrica": payload.metrica,
            "valor": payload.valor,
        }
        result = supabase.table("metrica_historico").insert(data).execute()
        return {"status": "OK", "inserido": result.data}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/pontuacao")
def pontuacao(id_produto: Optional[str] = None):
    try:
        if not id_produto:
            raise HTTPException(400, "id_produto é obrigatório")

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
        raise HTTPException(500, str(e))


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
        raise HTTPException(500, str(e))


# =========================================================
#  WIDGET OFICIAL /widget-ranking
# =========================================================
@app.get("/widget-ranking", response_class=HTMLResponse)
def widget_ranking():
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Ranking – Widget</title>
        <style>
            body { font-family: Arial, sans-serif; margin:0; padding:0; background:#ffffff; }
            .box { padding:15px; }
            h2 { text-align:center; color:#222; margin-bottom:10px; }
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


# =========================================================
#  CAPITAL E COMISSÕES
# =========================================================
@app.post("/registrar_comissao")
def registrar_comissao(valor: float, origem: str = "desconhecida"):
    try:
        supabase.table("capital_interno").insert({
            "saldo_atual": valor,
            "saldo_previsto": 0,
            "origem": origem,
            "observacao": "comissão registrada",
        }).execute()

        return {"status": "OK", "valor_registrado": valor}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/capital")
def capital():
    try:
        result = (
            supabase.table("capital_interno")
            .select("*")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )

        if not result.data:
            return {"saldo_atual": 0, "saldo_previsto": 0}

        return result.data[0]
    except Exception as e:
        raise HTTPException(500, str(e))


# =========================================================
#  PRODUTOS ELEGÍVEIS
# =========================================================
@app.get("/produtos_elegiveis")
def produtos_elegiveis():
    try:
        result = (
            supabase.table("produtos_elegiveis")
            .select("*")
            .eq("status", "aprovado")
            .execute()
        )
        return result.data
    except Exception as e:
        raise HTTPException(500, str(e))


# =========================================================
#  DECISÃO DO ROBÔ
# =========================================================
@app.get("/decisao")
def decisao():
    try:
        capital = (
            supabase.table("capital_interno")
            .select("*")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        saldo = capital.data[0]["saldo_atual"] if capital.data else 0

        produtos = (
            supabase.table("produtos_elegiveis")
            .select("*")
            .eq("status", "aprovado")
            .execute()
        )
        produtos_list = produtos.data

        if not produtos_list:
            return {"erro": "Nenhum produto elegível encontrado."}

        produto = produtos_list[0]

        acao = f"Escalar produto {produto['nome']}"
        motivo = "Pagamento rápido + Produto elegível"
        recomendacao = "Aumentar presença deste produto nas estratégias internas de venda."

        supabase.table("decisoes_robo").insert({
            "produto_id": produto["id_produto"],
            "produto_nome": produto["nome"],
            "acao": acao,
            "motivo": motivo,
            "capital_disponivel": saldo,
            "recomendacao": recomendacao,
        }).execute()

        return {
            "produto": produto,
            "acao": acao,
            "motivo": motivo,
            "capital_disponivel": saldo,
            "recomendacao": recomendacao,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# =========================================================
#  WEBHOOK OFICIAL KIWIFY
# =========================================================
@app.post("/webhook/kiwify")
async def webhook_kiwify(request: Request):
    try:
        payload = await request.json()
        evento = payload.get("event")
        dados = payload.get("data", {})

        metricas = []

        if evento == "sale.approved":
            metricas.append(("taxa_aprovacao_pagamento", 1))
            metricas.append(("velocidade_media_pagamento_horas", 1))
            metricas.append(("media_conversao_checkout", 1))

            produto_id = dados.get("product_id")

            if produto_id:
                supabase.table("vendas").insert({
                    "produto_id": produto_id,
                    "valor": dados.get("total_price", 0),
                    "data": datetime.utcnow().isoformat()
                }).execute()

        if evento == "sale.refunded":
            metricas.append(("taxa_reembolso", 1))

        for nome, valor in metricas:
            supabase.table("metricas_plataforma").insert({
                "plataforma": "kiwify",
                "nome_metrica": nome,
                "valor": valor,
                "atualizado_em": datetime.utcnow().isoformat()
            }).execute()

        return {"status": "ok"}

    except Exception as e:
        raise HTTPException(500, str(e))


# =========================================================
#  PLANO DIÁRIO
# =========================================================
@app.get("/plano-diario")
def plano_diario():
    try:
        capital = (
            supabase.table("capital_interno")
            .select("*")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        saldo = capital.data[0]["saldo_atual"] if capital.data else 0

        produtos = (
            supabase.table("produtos_elegiveis")
            .select("*")
            .eq("status", "aprovado")
            .execute()
        )
        produtos_list = produtos.data

        if not produtos_list:
            return {"erro": "Nenhum produto elegível disponível."}

        produto = produtos_list[0]

        acao = f"Priorizar divulgação do produto {produto['nome']}"
        prioridade = "alta" if saldo > 0 else "baixa"
        observacao = (
            "Utilizar saldo interno disponível"
            if saldo > 0
            else "Aguardando primeira comissão para aumentar ritmo"
        )

        supabase.table("plano_diario").insert({
            "produto_id": produto["id_produto"],
            "produto_nome": produto["nome"],
            "capital_disponivel": saldo,
            "acao": acao,
            "prioridade": prioridade,
            "observacao": observacao,
        }).execute()

        return {
            "produto": produto,
            "capital_disponivel": saldo,
            "acao": acao,
            "prioridade": prioridade,
            "observacao": observacao,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# =========================================================
#  ANÁLISE E INDICADORES INTERNOS
# =========================================================
@app.get("/analise")
def analise():
    try:
        capital = (
            supabase.table("capital_interno")
            .select("*")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        saldo = capital.data[0]["saldo_atual"] if capital.data else 0

        produtos = (
            supabase.table("produtos_elegiveis")
            .select("*")
            .eq("status", "aprovado")
            .execute()
        )
        produto = produtos.data[0] if produtos.data else None

        plano = (
            supabase.table("plano_diario")
            .select("*")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        plano_texto = plano.data[0]["acao"] if plano.data else "Sem plano registrado"

        decisao_reg = (
            supabase.table("decisoes_robo")
            .select("*")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        decisao_texto = (
            decisao_reg.data[0]["acao"] if decisao_reg.data else "Sem decisão registrada"
        )

        risco = "baixo" if saldo > 0 else "alto"
        recomendacao = (
            "Acelerar divulgação" if saldo > 0 else "Aguardar primeira comissão"
        )

        supabase.table("indicadores_internos").insert({
            "produto_id": produto["id_produto"] if produto else None,
            "produto_nome": produto["nome"] if produto else None,
            "capital": saldo,
            "decisao": decisao_texto,
            "plano": plano_texto,
            "risco": risco,
            "recomendacao": recomendacao,
        }).execute()

        return {
            "produto": produto,
            "capital": saldo,
            "decisao": decisao_texto,
            "plano": plano_texto,
            "risco": risco,
            "recomendacao": recomendacao,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# =========================================================
#  ESCALA FINANCEIRA
# =========================================================
@app.get("/escala")
def escala():
    try:
        capital = (
            supabase.table("capital_interno")
            .select("*")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        saldo = capital.data[0]["saldo_atual"] if capital.data else 0

        produtos = (
            supabase.table("produtos_elegiveis")
            .select("*")
            .eq("status", "aprovado")
            .execute()
        )
        produto = produtos.data[0] if produtos.data else None

        if not produto:
            return {"erro": "Nenhum produto elegível disponível para escalar."}

        risco = "baixo" if saldo > 0 else "alto"

        if produto.get("pagamento") == "imediato":
            roi_previsto = 1.4
        else:
            roi_previsto = 1.1

        capital_projetado = saldo * roi_previsto

        if risco == "baixo":
            decisao = f"Escalar imediatamente o produto {produto['nome']}"
            observacao = "Saldo positivo permite aceleração controlada."
        else:
            decisao = f"Não escalar ainda o produto {produto['nome']}"
            observacao = "É necessário aguardar primeira comissão."

        supabase.table("escala_financeira").insert({
            "produto_id": produto["id_produto"],
            "produto_nome": produto["nome"],
            "capital_projetado": capital_projetado,
            "risco": risco,
            "roi_previsto": roi_previsto,
            "decisao": decisao,
            "observacao": observacao,
        }).execute()

        return {
            "produto": produto,
            "capital_atual": saldo,
            "capital_projetado": capital_projetado,
            "roi_previsto": roi_previsto,
            "risco": risco,
            "decisao": decisao,
            "observacao": observacao,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# =========================================================
#  ROI AUTOMÁTICO  (POSIÇÃO CONFIRMADA)
# =========================================================
@app.get("/roi/{id_produto}")
def calcular_roi(id_produto: str):
    try:
        produto = (
            supabase.table("monetizacao_produtos")
            .select("*")
            .eq("id_produto", id_produto)
            .execute()
        )

        if not produto.data:
            raise HTTPException(404, "Produto não encontrado")

        prod = produto.data[0]

        preco = prod.get("preco", 0)
        ticket = prod.get("ticket_medio", 0)
        comissao = prod.get("comissao_media", 0)
        risco = prod.get("risco", "médio")
        pagamento = prod.get("velocidade_pagamento", "normal")

        roi = (ticket * comissao) / preco if preco > 0 else 0

        if pagamento == "imediato":
            roi *= 1.05

        if risco == "alto":
            roi *= 0.97

        reemb = (
            supabase.table("metricas_plataforma")
            .select("valor")
            .eq("plataforma", "kiwify")
            .eq("nome_metrica", "taxa_reembolso")
            .order("atualizado_em", desc=True)
            .limit(1)
            .execute()
        )

        if reemb.data:
            taxa = float(reemb.data[0]["valor"])
            roi *= (1 - (taxa * 1.5))

        supabase.table("monetizacao_produtos").update({
            "roi_previsto": roi
        }).eq("id_produto", id_produto).execute()

        return {
            "id_produto": id_produto,
            "roi_previsto": roi,
            "status": "ROI calculado e atualizado"
        }

    except Exception as e:
        raise HTTPException(500, str(e))


# =========================================================
#  ESCALA AUTOMÁTICA (NOVO MOTOR) - AÇÃO 4
# =========================================================
@app.post("/escala-automatica")
def escala_automatica():
    """
    Motor automático de escalada:
    - seleciona produto elegível
    - calcula ROI (usa /roi logic)
    - compara com ROI_MINIMO
    - checa capital e cooldown
    - registra decisão e retorna ação recomendada
    """
    try:
        # 1) verificar último horário de escala para cooldown
        last = (
            supabase.table("decisoes_robo")
            .select("*")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if last.data and "created_at" in last.data[0]:
            ultima = last.data[0]["created_at"]
            try:
                ultima_dt = datetime.fromisoformat(ultima)
                if datetime.utcnow() - ultima_dt < timedelta(hours=COOLDOWN_HORAS):
                    return {"status": "cooldown", "mensagem": "Cooldown ativo. Aguardar."}
            except Exception:
                # se created_at não for ISO, ignorar e prosseguir
                pass

        # 2) capital disponível
        cap = (
            supabase.table("capital_interno")
            .select("*")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        saldo = cap.data[0]["saldo_atual"] if cap.data else 0.0
        if saldo < CAPITAL_MINIMO_PARA_ESCALA:
            return {"status": "fora_capital", "mensagem": "Saldo insuficiente para escalar."}

        # 3) escolher melhor produto elegível (critério: ticket_medio * comissao_media / preco ou existente)
        produtos = (
            supabase.table("produtos_elegiveis")
            .select("*")
            .eq("status", "aprovado")
            .execute()
        )
        produtos_list = produtos.data
        if not produtos_list:
            return {"status": "erro", "mensagem": "Nenhum produto elegível."}

        # buscar melhores candidatos e calcular ROI via lógica já existente
        melhor = None
        melhor_roi = -999
        for p in produtos_list:
            idp = p.get("id_produto")
            # chamar função interna calcular_roi (não via HTTP)
            try:
                roi_resp = calcular_roi(idp)
                roi_val = roi_resp.get("roi_previsto", 0)
            except Exception:
                roi_val = 0

            # priorizar pagamento imediato e maior roi
            prioridade = 1
            if p.get("pagamento") == "imediato":
                prioridade += 0.1

            score = roi_val * prioridade

            if score > melhor_roi:
                melhor_roi = score
                melhor = {"produto": p, "roi": roi_val}

        if not melhor:
            return {"status": "erro", "mensagem": "Não foi possível determinar produto para escalar."}

        produto = melhor["produto"]
        roi_val = melhor["roi"]

        # 4) decisão baseada no ROI_MINIMO
        if roi_val >= ROI_MINIMO:
            acao = "escalar"
            motivo = f"ROI {roi_val:.4f} >= {ROI_MINIMO}"
            # registrar decisão de escala
            supabase.table("decisoes_robo").insert({
                "produto_id": produto.get("id_produto"),
                "produto_nome": produto.get("nome"),
                "acao": acao,
                "motivo": motivo,
                "capital_disponivel": saldo,
                "recomendacao": "Iniciar escalada controlada",
                "created_at": datetime.utcnow().isoformat()
            }).execute()

            # opcional: marcar produto como em_escala (coluna hipotética)
            try:
                supabase.table("produtos_elegiveis").update({
                    "em_escala": True
                }).eq("id_produto", produto.get("id_produto")).execute()
            except Exception:
                pass

            return {
                "status": "ok",
                "acao": acao,
                "produto": produto,
                "roi": roi_val,
                "mensagem": "Escalada autorizada e registrada."
            }
        else:
            acao = "nao_escalar"
            motivo = f"ROI {roi_val:.4f} < {ROI_MINIMO}"
            supabase.table("decisoes_robo").insert({
                "produto_id": produto.get("id_produto"),
                "produto_nome": produto.get("nome"),
                "acao": acao,
                "motivo": motivo,
                "capital_disponivel": saldo,
                "recomendacao": "Aguardar melhorias",
                "created_at": datetime.utcnow().isoformat()
            }).execute()

            return {
                "status": "ok",
                "acao": acao,
                "produto": produto,
                "roi": roi_val,
                "mensagem": "Escalada não autorizada — ROI abaixo do mínimo."
            }

    except Exception as e:
        raise HTTPException(500, str(e))


# =========================================================
#  CICLO (ATUALIZADO PARA USAR O MOTOR AUTOMÁTICO)
# =========================================================
@app.get("/ciclo")
def ciclo():
    try:
        decisao_resp = decisao()
        decisao_texto = decisao_resp["acao"]
        produto_nome = decisao_resp["produto"]["nome"]

        # prioriza o motor automático de escala
        escala_resp = escala_automatica()

        plano_resp = plano_diario()
        plano_texto = plano_resp["acao"]

        analise_resp = analise()
        capital_valor = analise_resp["capital"]
        risco_valor = analise_resp["risco"]

        supabase.table("ciclos_robo").insert({
            "produto_nome": produto_nome,
            "decisao": decisao_texto,
            "plano": plano_texto,
            "capital": capital_valor,
            "risco": risco_valor,
            "escala": escala_resp.get("acao") if isinstance(escala_resp, dict) else None,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        return {
            "produto": produto_nome,
            "decisao": decisao_texto,
            "plano": plano_texto,
            "capital": capital_valor,
            "risco": risco_valor,
            "escala": escala_resp,
            "status": "Ciclo executado com sucesso",
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# =========================================================
#  RESULTADO CONSOLIDADO
# =========================================================
@app.get("/resultado")
def resultado():
    try:
        produto = (
            supabase.table("produtos_elegiveis")
            .select("*")
            .order("id_produto", desc=True)
            .limit(1)
            .execute()
        )
        produto_dados = produto.data[0] if produto.data else None

        decisao_reg = (
            supabase.table("decisoes_robo")
            .select("*")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        decisao_dados = decisao_reg.data[0] if decisao_reg.data else None

        plano = (
            supabase.table("plano_diario")
            .select("*")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        plano_dados = plano.data[0] if plano.data else None

        indicadores = (
            supabase.table("indicadores_internos")
            .select("*")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        indicadores_dados = indicadores.data[0] if indicadores.data else None

        ciclo_reg = (
            supabase.table("ciclos_robo")
            .select("*")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        ciclo_dados = ciclo_reg.data[0] if ciclo_reg.data else None

        return {
            "produto": produto_dados,
            "decisao": decisao_dados,
            "plano": plano_dados,
            "indicadores": indicadores_dados,
            "ciclo": ciclo_dados,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# =========================================================
#  LOOP DIÁRIO
# =========================================================
@app.get("/loop-diario")
def loop_diario(qtd: int = 1):
    try:
        if qtd < 1:
            qtd = 1

        resultados = []
        for _ in range(qtd):
            res = ciclo()
            resultados.append(res)

        return {
            "execucoes": len(resultados),
            "resultados": resultados,
            "status": "Loop diário executado com sucesso",
        }
    except Exception as e:
        raise HTTPException(500, str(e))
