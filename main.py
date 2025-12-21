# main.py — versão completa e final
# ROBO GLOBAL AI — Backend Operacional
# Ajuste de schema: leitura de valor → valor_unitário
# Nenhuma outra alteração estrutural

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from supabase import create_client

# =====================================================
# APP
# =====================================================

app = FastAPI(title="ROBO GLOBAL AI", version="2.1")

# =====================================================
# CORS
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

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def sb():
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# =====================================================
# LOG HUMANO
# =====================================================

def log_humano(origem, nivel, mensagem):
    print(f"[{origem}] [{nivel}] {mensagem}")

# =====================================================
# FUNÇÕES NÚCLEO (MANTIDAS)
# =====================================================

def normalizar_evento(payload: dict):
    return payload

def processar_evento(evento: dict):
    return evento

def calcular_comissao(valor_unitario):
    return round(valor_unitario * 0.5, 4)

def calcular_rentabilidade(valor_unitario):
    return round(valor_unitario * 0.3, 4)

def analisar_produto(produto):
    return {"produto": produto, "score": 1}

def escolher_melhor_oferta(ofertas):
    return ofertas[0] if ofertas else None

def pipeline_operacional(evento):
    return evento

def registrar_operacao(evento):
    supabase = sb()
    supabase.table("eventos_financeiros").insert(evento).execute()

def executar_ciclo():
    return {"ciclo": "executado"}

def gerenciar_escalada():
    return {"escala": "avaliada"}

# =====================================================
# WEBHOOKS
# =====================================================

@app.post("/webhook/universal")
async def webhook_universal(request: Request):
    payload = await request.json()
    evento = normalizar_evento(payload)
    registrar_operacao(evento)
    log_humano("WEBHOOK", "INFO", "Evento universal registrado")
    return {"status": "ok"}

@app.post("/webhook/hotmart")
async def webhook_hotmart(request: Request):
    payload = await request.json()
    evento = normalizar_evento(payload)
    registrar_operacao(evento)
    log_humano("HOTMART", "INFO", "Evento Hotmart registrado")
    return {"status": "ok"}

@app.post("/webhook/eduzz")
async def webhook_eduzz(request: Request):
    payload = await request.json()
    evento = normalizar_evento(payload)
    registrar_operacao(evento)
    log_humano("EDUZZ", "INFO", "Evento Eduzz registrado")
    return {"status": "ok"}

# =====================================================
# ENDPOINTS OPERACIONAIS
# =====================================================

@app.get("/status")
def status():
    return {"status": "ativo", "timestamp": datetime.utcnow().isoformat()}

@app.get("/capital")
def capital():
    supabase = sb()
    res = supabase.table("eventos_financeiros").select("valor_unitário").execute()
    total = sum([(r.get("valor_unitário") or 0) for r in (res.data or [])])
    return {"capital": round(total, 4)}

@app.get("/decisao")
def decisao():
    return {"decisao": "monitorar"}

@app.get("/ciclo")
def ciclo():
    return executar_ciclo()

@app.get("/resultado")
def resultado():
    supabase = sb()
    res = supabase.table("eventos_financeiros").select("valor_unitário").execute()
    total = sum([(r.get("valor_unitário") or 0) for r in (res.data or [])])
    return {"resultado_total": round(total, 4)}

# =====================================================
# PAINEL OPERACIONAL (ALINHADO AO SCHEMA)
# =====================================================

@app.get("/painel/operacional")
def painel_operacional():
    try:
        supabase = sb()

        response = (
            supabase.table("eventos_financeiros")
            .select("valor_unitário, created_at")
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )

        eventos = response.data or []
        total_eventos = len(eventos)
        total_valor = sum([(e.get("valor_unitário") or 0) for e in eventos])

        ultimo_evento = eventos[0]["created_at"] if total_eventos > 0 else None

        return {
            "status": "ativo",
            "eventos_recebidos": total_eventos,
            "ultimo_evento": ultimo_evento,
            "resultado_total": round(total_valor, 4),
            "mensagem": (
                "Sistema ativo e monitorando eventos reais"
                if total_eventos > 0
                else "Sistema ativo, aguardando eventos reais"
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        log_humano("PAINEL", "ERRO", str(e))
        return {
            "status": "erro_controlado",
            "eventos_recebidos": 0,
            "ultimo_evento": None,
            "resultado_total": 0,
            "mensagem": "Falha ao carregar painel operacional",
            "detalhe": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }

# =====================================================
# WIDGET RANKING
# =====================================================

@app.get("/widget-ranking")
def widget_ranking():
    supabase = sb()
    res = supabase.table("eventos_financeiros").select("valor_unitário").execute()
    valores = [r.get("valor_unitário") for r in (res.data or [])]
    return {"ranking": sorted(valores, reverse=True)}

# =====================================================
# ROOT
# =====================================================

@app.get("/")
def root():
    return {"robo": "ROBO GLOBAL AI", "status": "online"}
