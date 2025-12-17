# main.py — ROBO GLOBAL AI
# MVP SÓLIDO • RENTÁVEL • 24/7 • DASHBOARD ATIVO
# ATIVAÇÃO REAL COM CONFIRMAÇÃO HUMANA

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from supabase import create_client
import os

# =====================================================
# APP
# =====================================================

app = FastAPI()

# =====================================================
# CORS (DASHBOARD GITHUB PAGES)
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# SUPABASE
# =====================================================

def sb():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise Exception("SUPABASE NÃO CONFIGURADO")

    return create_client(url, key)

# =====================================================
# LIMITES / SEGURANÇA
# =====================================================

def limite_ok(valor: float) -> bool:
    return isinstance(valor, (int, float)) and 0 < valor <= 5000

# =====================================================
# ESTADO
# =====================================================

def estado_atual():
    res = sb().table("estado_atual").select("*").eq("id", 1).execute()
    return res.data[0] if res.data else None


def bootstrap():
    estado = estado_atual()
    if estado:
        return estado

    ciclo = sb().table("ciclos").insert({
        "decisao": "BOOTSTRAP",
        "resultado": "INICIALIZACAO",
        "capital_antes": 0.0,
        "capital_depois": 0.0,
        "status": "SUCESSO",
        "payload": {}
    }).execute()

    sb().table("estado_atual").insert({
        "id": 1,
        "fase": "OPERANDO",
        "capital": 0.0,
        "ultima_decisao": "BOOTSTRAP",
        "ultimo_ciclo_id": ciclo.data[0]["id"],
        "atualizado_em": datetime.utcnow().isoformat()
    }).execute()

    return estado_atual()

# =====================================================
# AÇÃO PENDENTE (GOVERNANÇA HUMANA)
# =====================================================

acao_pendente = {
    "tipo": None,
    "payload": None,
    "criada_em": None
}

# =====================================================
# ENDPOINTS BÁSICOS
# =====================================================

@app.post("/ping")
def ping():
    return {"ok": True}


@app.get("/estado")
def estado():
    res = sb().table("estado_atual").select("*").eq("id", 1).execute()
    return res.data[0] if res.data else {}


# ALIAS PARA DASHBOARD
@app.get("/status")
def status():
    return estado()

# =====================================================
# CICLO AUTOMÁTICO (WORKER 24/7)
# ROBÔ DECIDE → CRIA AÇÃO PENDENTE
# =====================================================

@app.post("/ciclo")
def ciclo(payload: dict = {}):
    bootstrap()

    decisao = {
        "tipo": "PUBLICAR_CONTEUDO_E_ATIVAR_TRÁFEGO",
        "descricao": "Publicar conteúdo automaticamente e ativar tráfego pago mínimo"
    }

    global acao_pendente
    acao_pendente = {
        "tipo": decisao["tipo"],
        "payload": decisao,
        "criada_em": datetime.utcnow().isoformat()
    }

    return {
        "status": "acao_pendente",
        "acao": acao_pendente
    }

# =====================================================
# CONFIRMAÇÃO HUMANA → EXECUÇÃO REAL
# =====================================================

@app.post("/confirmar-acao")
def confirmar_acao():
    global acao_pendente

    if not acao_pendente["tipo"]:
        return {"status": "nenhuma_acao_pendente"}

    # =================================================
    # AÇÃO REAL A — PUBLICAÇÃO DE CONTEÚDO
    # (ligar API real aqui quando desejar)
    # =================================================
    print("AÇÃO REAL: PUBLICANDO CONTEÚDO")

    # =================================================
    # AÇÃO REAL B — ATIVAÇÃO DE TRÁFEGO PAGO MÍNIMO
    # (ligar API real aqui quando desejar)
    # =================================================
    print("AÇÃO REAL: ATIVANDO TRÁFEGO PAGO")

    estado = estado_atual()
    capital_antes = estado["capital"]

    ciclo = sb().table("ciclos").insert({
        "decisao": acao_pendente["tipo"],
        "resultado": "EXECUTADO_COM_CONFIRMACAO",
        "capital_antes": capital_antes,
        "capital_depois": capital_antes,
        "status": "SUCESSO",
        "payload": acao_pendente
    }).execute()

    sb().table("estado_atual").update({
        "ultima_decisao": acao_pendente["tipo"],
        "ultimo_ciclo_id": ciclo.data[0]["id"],
        "atualizado_em": datetime.utcnow().isoformat()
    }).eq("id", 1).execute()

    acao_pendente = {
        "tipo": None,
        "payload": None,
        "criada_em": None
    }

    return {"status": "acao_real_executada"}

# =====================================================
# WEBHOOK — HOTMART
# =====================================================

@app.post("/webhook/hotmart")
def webhook_hotmart(payload: dict):
    valor = float(payload.get("purchase", {}).get("price", 0))

    if not limite_ok(valor):
        return {"ok": False}

    estado = estado_atual()
    capital_antes = estado["capital"]
    capital_depois = capital_antes + valor

    ciclo = sb().table("ciclos").insert({
        "decisao": "VENDA_HOTMART",
        "resultado": "VENDA_CONFIRMADA",
        "capital_antes": capital_antes,
        "capital_depois": capital_depois,
        "status": "SUCESSO",
        "payload": payload
    }).execute()

    sb().table("estado_atual").update({
        "capital": capital_depois,
        "ultima_decisao": "VENDA_HOTMART",
        "ultimo_ciclo_id": ciclo.data[0]["id"],
        "atualizado_em": datetime.utcnow().isoformat()
    }).eq("id", 1).execute()

    return {"ok": True}

# =====================================================
# WEBHOOK — EDUZZ
# =====================================================

@app.post("/webhook/eduzz")
def webhook_eduzz(payload: dict):
    valor = float(payload.get("transaction", {}).get("price", 0))

    if not limite_ok(valor):
        return {"ok": False}

    estado = estado_atual()
    capital_antes = estado["capital"]
    capital_depois = capital_antes + valor

    ciclo = sb().table("ciclos").insert({
        "decisao": "VENDA_EDUZZ",
        "resultado": "VENDA_CONFIRMADA",
        "capital_antes": capital_antes,
        "capital_depois": capital_depois,
        "status": "SUCESSO",
        "payload": payload
    }).execute()

    sb().table("estado_atual").update({
        "capital": capital_depois,
        "ultima_decisao": "VENDA_EDUZZ",
        "ultimo_ciclo_id": ciclo.data[0]["id"],
        "atualizado_em": datetime.utcnow().isoformat()
    }).eq("id", 1).execute()

    return {"ok": True}
