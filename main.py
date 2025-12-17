from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os, hmac, hashlib, json, time, uuid
from datetime import datetime
from supabase import create_client

SUPABASE_URL=os.getenv("SUPABASE_URL")
SUPABASE_KEY=os.getenv("SUPABASE_SERVICE_ROLE_KEY")
HOTMART_SECRET=os.getenv("HOTMART_SECRET","")
EDUZZ_SECRET=os.getenv("EDUZZ_SECRET","")

supabase=create_client(SUPABASE_URL,SUPABASE_KEY)

app=FastAPI()
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])

def now():
    return datetime.utcnow().isoformat()

def log(origem,nivel,mensagem):
    supabase.table("logs").insert({
        "id":str(uuid.uuid4()),
        "origem":origem,
        "nivel":nivel,
        "mensagem":mensagem,
        "ts":now()
    }).execute()

def validar_hmac(payload,assinatura,secret):
    if not secret:
        return True
    mac=hmac.new(secret.encode(),payload,hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac,assinatura or "")

def registrar_operacao(dados):
    supabase.table("operacoes").insert(dados).execute()

def registrar_financeiro(valor,origem,produto):
    supabase.table("financeiro").insert({
        "id":str(uuid.uuid4()),
        "valor":valor,
        "origem":origem,
        "produto":produto,
        "ts":now()
    }).execute()

def calcular_comissao(evento):
    return float(evento.get("valor",0))

def calcular_rentabilidade(produto):
    res=supabase.table("financeiro").select("valor").eq("produto",produto).execute()
    total=sum([r["valor"] for r in res.data]) if res.data else 0
    return total

def analisar_produto(produto):
    rent=calcular_rentabilidade(produto)
    return {"produto":produto,"rentabilidade":rent}

def escolher_melhor_oferta():
    res=supabase.table("financeiro").select("produto","valor").execute()
    ranking={}
    for r in res.data or []:
        ranking[r["produto"]]=ranking.get(r["produto"],0)+r["valor"]
    if not ranking:
        return None
    return max(ranking,key=ranking.get)

def normalizar_evento(origem,body):
    if origem=="hotmart":
        return {
            "origem":"hotmart",
            "produto":body.get("product",""),
            "valor":float(body.get("value",0)),
            "evento":body.get("event","")
        }
    if origem=="eduzz":
        return {
            "origem":"eduzz",
            "produto":body.get("product_name",""),
            "valor":float(body.get("commission",0)),
            "evento":body.get("event","")
        }
    return body

def processar_evento(evento):
    valor=calcular_comissao(evento)
    registrar_financeiro(valor,evento["origem"],evento["produto"])
    registrar_operacao({
        "id":str(uuid.uuid4()),
        "origem":evento["origem"],
        "produto":evento["produto"],
        "valor":valor,
        "ts":now()
    })
    log("ROBO","INFO","evento_processado")

def pipeline_operacional():
    melhor=escolher_melhor_oferta()
    if melhor:
        log("ROBO","INFO",f"escalar_{melhor}")

def executar_ciclo():
    pipeline_operacional()
    log("ROBO","INFO","ciclo_executado")

def gerenciar_escalada():
    executar_ciclo()

@app.post("/webhook/hotmart")
async def webhook_hotmart(request:Request):
    payload=await request.body()
    assinatura=request.headers.get("X-Hotmart-Hmac-SHA256")
    if not validar_hmac(payload,assinatura,HOTMART_SECRET):
        raise HTTPException(401)
    body=json.loads(payload.decode())
    evento=normalizar_evento("hotmart",body)
    processar_evento(evento)
    return {"status":"ok"}

@app.post("/webhook/eduzz")
async def webhook_eduzz(request:Request):
    payload=await request.body()
    assinatura=request.headers.get("X-Eduzz-Signature")
    if not validar_hmac(payload,assinatura,EDUZZ_SECRET):
        raise HTTPException(401)
    body=json.loads(payload.decode())
    evento=normalizar_evento("eduzz",body)
    processar_evento(evento)
    return {"status":"ok"}

@app.get("/status")
def status():
    return {"status":"operacional","ts":now()}

@app.get("/capital")
def capital():
    res=supabase.table("financeiro").select("valor").execute()
    total=sum([r["valor"] for r in res.data]) if res.data else 0
    return {"capital":total}

@app.get("/decisao")
def decisao():
    return {"melhor_oferta":escolher_melhor_oferta()}

@app.post("/ciclo")
def ciclo():
    executar_ciclo()
    return {"status":"executado"}

@app.get("/resultado")
def resultado():
    return {"top":escolher_melhor_oferta()}
