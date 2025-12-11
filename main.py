from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from supabase_client import get_supabase
from datetime import datetime, timedelta
import os
import json

# =========================================================
#  CONFIGURAÇÃO PRINCIPAL DA API
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
ROI_MINIMO = 1.2
CAPITAL_MINIMO_PARA_ESCALA = 10.0
COOLDOWN_HORAS = 1

# Webhook secret (env)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

# =========================================================
#  MODELOS
# =========================================================
class AtualizarPayload(BaseModel):
    id_produto: str
    metrica: str
    valor: float

# =========================================================
#  UTILITÁRIOS (DE MAPEAMENTO E PADRONIZAÇÃO)
# =========================================================
def identificar_plataforma(payload: Dict[str, Any], headers: Dict[str, Any]) -> str:
    """
    Identifica a plataforma a partir do payload ou headers.
    Ordem: evidência explícita -> padrões conhecidos.
    """
    # Headers-based hints
    if headers.get("X-KIWIFY-SIGN") or ("event" in payload and "data" in payload):
        return "kiwify"
    if headers.get("X-HOTMART-SIGN") or "hotmart" in json.dumps(payload).lower():
        return "hotmart"
    if headers.get("X-EDUZZ-SIGN") or "eduzz" in json.dumps(payload).lower():
        return "eduzz"
    if "monetizze" in json.dumps(payload).lower() or "prod" in payload:
        return "monetizze"
    if "clickbank" in json.dumps(payload).lower() or "transactionType" in payload:
        return "clickbank"
    if "digistore" in json.dumps(payload).lower() or "eventType" in payload:
        return "digistore"
    # fallback
    return "unknown"


def mapear_evento_plataforma(plataforma: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte payloads específicos para o formato interno padronizado.
    Retorna dicionário com keys: tipo_evento, produto_id, valor, ticket, comissao, velocidade_pagamento, risco, raw
    """
    out = {
        "tipo_evento": None,
        "produto_id": None,
        "valor": None,
        "ticket": None,
        "comissao": None,
        "velocidade_pagamento": None,
        "risco": None,
        "raw": payload
    }

    try:
        if plataforma == "kiwify":
            evt = payload.get("event")
            data = payload.get("data", {})
            out["produto_id"] = data.get("product_id") or data.get("productId")
            out["valor"] = data.get("total_price") or data.get("price")
            out["ticket"] = data.get("total_price") or data.get("price")
            out["comissao"] = data.get("commission") or data.get("commission_percent")
            out["velocidade_pagamento"] = "imediato" if data.get("paid_at") else "normal"
            if evt == "sale.approved":
                out["tipo_evento"] = "venda_aprovada"
            elif evt == "sale.refunded":
                out["tipo_evento"] = "venda_reembolsada"
            else:
                out["tipo_evento"] = "outro"
            return out

        if plataforma == "hotmart":
            # exemplo genérico
            evt = payload.get("event") or payload.get("notification_type") or payload.get("type")
            data = payload.get("product") or payload
            out["produto_id"] = data.get("product_id") or data.get("productId") or data.get("id")
            out["valor"] = data.get("sale_value") or data.get("price")
            out["ticket"] = out["valor"]
            out["comissao"] = data.get("affiliate_commission") or data.get("commission")
            out["velocidade_pagamento"] = "imediato" if data.get("pay_time") == "instant" else "normal"
            if "approved" in str(evt).lower():
                out["tipo_evento"] = "venda_aprovada"
            elif "refun" in str(evt).lower():
                out["tipo_evento"] = "venda_reembolsada"
            else:
                out["tipo_evento"] = "outro"
            return out

        if plataforma == "eduzz":
            evt = payload.get("trans_status") or payload.get("event")
            out["produto_id"] = payload.get("prod") or payload.get("product_id")
            out["valor"] = payload.get("price") or payload.get("valor")
            out["ticket"] = out["valor"]
            out["comissao"] = payload.get("affiliate_fee") or payload.get("commission")
            out["velocidade_pagamento"] = "imediato" if payload.get("paid") else "normal"
            if evt in ["approved", "pago", "aprovado"]:
                out["tipo_evento"] = "venda_aprovada"
            elif evt in ["refunded", "estornado"]:
                out["tipo_evento"] = "venda_reembolsada"
            else:
                out["tipo_evento"] = "outro"
            return out

        if plataforma == "monetizze":
            out["produto_id"] = payload.get("prod") or payload.get("product_id")
            out["valor"] = payload.get("value") or payload.get("price")
            out["ticket"] = out["valor"]
            out["comissao"] = payload.get("commission")
            status = payload.get("status") or payload.get("transactionStatus")
            if status in ["paid", "approved", "pago", "aprovado"]:
                out["tipo_evento"] = "venda_aprovada"
            elif status in ["refunded", "chargeback", "estornado"]:
                out["tipo_evento"] = "venda_reembolsada"
            else:
                out["tipo_evento"] = "outro"
            return out

        if plataforma == "clickbank":
            out["produto_id"] = payload.get("item_number") or payload.get("vendorProductId")
            out["valor"] = payload.get("amount")
            out["ticket"] = out["valor"]
            ev = payload.get("transactionType")
            if ev in ["SALE", "SALE-RECURRING"]:
                out["tipo_evento"] = "venda_aprovada"
            elif ev == "REFUND":
                out["tipo_evento"] = "venda_reembolsada"
            else:
                out["tipo_evento"] = "outro"
            return out

        if plataforma == "digistore":
            out["produto_id"] = payload.get("productId") or payload.get("product_id")
            out["valor"] = payload.get("orderAmount") or payload.get("amount")
            ev = payload.get("eventType") or payload.get("type")
            if ev in ["ORDER_PAID", "SALE"]:
                out["tipo_evento"] = "venda_aprovada"
            elif ev in ["ORDER_REFUND", "REFUND"]:
                out["tipo_evento"] = "venda_reembolsada"
            else:
                out["tipo_evento"] = "outro"
            return out

        # fallback generic
        if "status" in payload and payload.get("status") in ["paid", "approved", "pago", "aprovado"]:
            out["tipo_evento"] = "venda_aprovada"
            out["valor"] = payload.get("price") or payload.get("amount")
            out["produto_id"] = payload.get("product_id") or payload.get("prod")
            out["ticket"] = out["valor"]
            return out

    except Exception:
        out["tipo_evento"] = "outro"

    return out


def persistir_evento_padronizado(plataforma: str, evento: Dict[str, Any]):
    """
    Persiste vendas/metricas padronizadas no Supabase.
    """
    tipo = evento.get("tipo_evento")
    pid = evento.get("produto_id")
    valor = evento.get("valor")
    ticket = evento.get("ticket")
    comissao = evento.get("comissao")
    pagamento = evento.get("velocidade_pagamento")

    # registrar venda quando aplicável
    if tipo == "venda_aprovada" and pid:
        try:
            supabase.table("vendas").insert({
                "produto_id": pid,
                "valor": valor or 0,
                "plataforma": plataforma,
                "data": datetime.utcnow().isoformat(),
                "raw": evento.get("raw")
            }).execute()
        except Exception:
            pass

    # atualizar métricas padronizadas
    try:
        if tipo == "venda_aprovada":
            supabase.table("metricas_plataforma").insert({
                "plataforma": plataforma,
                "nome_metrica": "taxa_aprovacao_pagamento",
                "valor": 1,
                "atualizado_em": datetime.utcnow().isoformat()
            }).execute()

        if tipo == "venda_reembolsada":
            supabase.table("metricas_plataforma").insert({
                "plataforma": plataforma,
                "nome_metrica": "taxa_reembolso",
                "valor": 1,
                "atualizado_em": datetime.utcnow().isoformat()
            }).execute()

        # ticket médio e comissão se vierem
        if ticket:
            supabase.table("metricas_plataforma").insert({
                "plataforma": plataforma,
                "nome_metrica": "ticket_medio",
                "valor": ticket,
                "atualizado_em": datetime.utcnow().isoformat()
            }).execute()

        if comissao:
            supabase.table("metricas_plataforma").insert({
                "plataforma": plataforma,
                "nome_metrica": "comissao_media",
                "valor": comissao,
                "atualizado_em": datetime.utcnow().isoformat()
            }).execute()
    except Exception:
        pass

# =========================================================
#  ENDPOINTS BÁSICOS (mantidos)
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
#  WIDGET (mantido)
# =========================================================
@app.get("/widget-ranking", response_class=HTMLResponse)
def widget_ranking():
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Ranking – Widget</title>
    ...
    </html>
    """
    return HTMLResponse(content=html)


# =========================================================
#  WEBHOOK UNIVERSAL (SUBSTITUI TODOS OS WEBHOOKS INDIVIDUAIS)
# =========================================================
@app.post("/webhook/universal")
async def webhook_universal(request: Request):
    """
    Webhook Universal:
    - exige header X-ROBO-SECRET == WEBHOOK_SECRET
    - autodetecta a plataforma
    - mapeia e padroniza
    - persiste vendas e métricas padronizadas
    - retorna 200/401 conforme validação
    """
    # autenticação simples por segredo universal
    header_secret = request.headers.get("X-ROBO-SECRET", "")
    if not WEBHOOK_SECRET or header_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        body = await request.body()
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            # tentar como form-data ou texto
            payload = {}

        headers = dict(request.headers)
        plataforma = identificar_plataforma(payload, headers)

        mapped = mapear_evento_plataforma(plataforma, payload)
        persistir_evento_padronizado(plataforma, mapped)

        # opcional: atualizar ROI do produto se product_id vier
        pid = mapped.get("produto_id")
        if pid:
            try:
                calcular_roi(pid)
            except Exception:
                pass

        return {"status": "ok", "plataforma": plataforma, "evento": mapped.get("tipo_evento")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# =========================================================
#  CAPITAL / PRODUTOS / DECISÕES / ESCALA ETC. (mantidos)
# =========================================================
@app.post("/registrar_comissao")
def registrar_comissao(valor: float, origem: str = "desconhecida"):
    try:
        supabase.table("capital_interno").insert({
            "saldo_atual": valor,
            "saldo_previsto": 0,
            "origem": origem,
            "observacao": "comissão registrada",
            "created_at": datetime.utcnow().isoformat()
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
            "created_at": datetime.utcnow().isoformat()
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
#  ROI (mantido)
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
#  ESCALA AUTOMÁTICA (mantido)
# =========================================================
@app.post("/escala-automatica")
def escala_automatica():
    try:
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
                pass

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

        produtos = (
            supabase.table("produtos_elegiveis")
            .select("*")
            .eq("status", "aprovado")
            .execute()
        )
        produtos_list = produtos.data
        if not produtos_list:
            return {"status": "erro", "mensagem": "Nenhum produto elegível."}

        melhor = None
        melhor_roi = -999
        for p in produtos_list:
            idp = p.get("id_produto")
            try:
                roi_resp = calcular_roi(idp)
                roi_val = roi_resp.get("roi_previsto", 0)
            except Exception:
                roi_val = 0

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

        if roi_val >= ROI_MINIMO:
            acao = "escalar"
            motivo = f"ROI {roi_val:.4f} >= {ROI_MINIMO}"
            supabase.table("decisoes_robo").insert({
                "produto_id": produto.get("id_produto"),
                "produto_nome": produto.get("nome"),
                "acao": acao,
                "motivo": motivo,
                "capital_disponivel": saldo,
                "recomendacao": "Iniciar escalada controlada",
                "created_at": datetime.utcnow().isoformat()
            }).execute()

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
#  CICLO / RESULTADO / LOOP (mantidos)
# =========================================================
@app.get("/ciclo")
def ciclo():
    try:
        decisao_resp = decisao()
        decisao_texto = decisao_resp["acao"]
        produto_nome = decisao_resp["produto"]["nome"]

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
