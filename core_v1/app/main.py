from __future__ import annotations

import hashlib
import html
import json
import logging
import secrets
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from psycopg import connect
from psycopg.rows import dict_row

from core_v1.app.hotmart import normalize_webhook, validate_hottok

logger = logging.getLogger("robo-global-core")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    core_ingest_key: str
    hotmart_hottok: str | None = None
    environment: str = "development"
    core_schema: Literal["robo_global_core"] = "robo_global_core"


settings = Settings()
app = FastAPI(title="Robo Global Core API", version="1.0.0-alpha.4")


def db_connection():
    return connect(settings.database_url, row_factory=dict_row)


def require_ingest_key(x_core_ingest_key: str = Header(default="")) -> None:
    if not secrets.compare_digest(x_core_ingest_key, settings.core_ingest_key):
        raise HTTPException(status_code=401, detail="invalid ingest key")


def classify_db_error(exc: Exception) -> str:
    message = str(exc).lower()
    if "password authentication failed" in message or "authentication failed" in message:
        return "authentication_failed"
    if "could not translate host" in message or "name or service not known" in message:
        return "dns_failed"
    if "connection refused" in message or "timeout" in message:
        return "connection_failed"
    if "invalid uri" in message or "invalid dsn" in message or "missing '='" in message:
        return "database_url_invalid"
    if "percent" in message or "escape" in message:
        return "database_url_encoding_error"
    return exc.__class__.__name__


def opportunity_score(a: Decimal, b: Decimal, c: Decimal, d: Decimal) -> Decimal:
    result = Decimal("1")
    for value in (a, b, c, d):
        result *= max(Decimal("0"), min(Decimal("1"), value))
    return result


def tracked_url(affiliate_url: str, strategy: str, template: str | None, attribution_key: str) -> str:
    if strategy == "none":
        return affiliate_url
    if strategy == "url_template":
        if not template or "{attribution_key}" not in template:
            raise HTTPException(status_code=500, detail="invalid offer tracking template")
        return template.replace("{attribution_key}", attribution_key)
    if strategy == "query_param":
        if not template:
            raise HTTPException(status_code=500, detail="missing tracking query parameter")
        parts = urlsplit(affiliate_url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query[template] = attribution_key
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    if strategy == "platform_adapter":
        raise HTTPException(status_code=503, detail="platform tracking adapter not configured")
    raise HTTPException(status_code=500, detail="unknown tracking strategy")


def insert_raw_event(cur, platform: str, external_event_id: str | None, event_type: str | None, payload: dict[str, Any]):
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    cur.execute(
        f"""insert into {settings.core_schema}.affiliate_events_raw
        (platform, external_event_id, event_type, payload, payload_hash)
        values (%s,%s,%s,%s::jsonb,%s) on conflict do nothing returning id""",
        (platform, external_event_id, event_type, canonical, payload_hash),
    )
    row = cur.fetchone()
    if row:
        return row["id"], True
    if external_event_id:
        cur.execute(
            f"select id from {settings.core_schema}.affiliate_events_raw where platform=%s and external_event_id=%s",
            (platform, external_event_id),
        )
    else:
        cur.execute(f"select id from {settings.core_schema}.affiliate_events_raw where payload_hash=%s", (payload_hash,))
    existing = cur.fetchone()
    return (existing["id"] if existing else None), False


def economic_effect(status: str, commission_value: Decimal) -> tuple[str, Decimal] | None:
    amount = abs(commission_value)
    if amount == 0:
        return None
    if status == "approved":
        return "commission_accrued", amount
    if status == "refunded":
        return "refund", -amount
    if status == "chargeback":
        return "chargeback", -amount
    return None


def esc(value: Any) -> str:
    if value is None:
        return "—"
    return html.escape(str(value))


def money(value: Any, currency: str = "BRL") -> str:
    try:
        number = Decimal(str(value or 0))
    except Exception:
        number = Decimal("0")
    formatted = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    symbol = "R$" if currency == "BRL" else currency
    return f"{symbol} {formatted}"


def masked_transaction(value: Any) -> str:
    text = str(value or "")
    if len(text) <= 8:
        return esc(text or "—")
    return esc(f"{text[:4]}…{text[-4:]}")


@app.on_event("startup")
def startup_database_probe() -> None:
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select count(*) as tables from information_schema.tables where table_schema=%s", (settings.core_schema,))
                row = cur.fetchone()
        logger.info("CORE_DB_READY schema=%s tables=%s", settings.core_schema, row["tables"])
    except Exception as exc:
        logger.error("CORE_DB_NOT_READY category=%s", classify_db_error(exc))


class DemandCreate(BaseModel):
    market: str = Field(min_length=2, max_length=80)
    language: str = Field(min_length=2, max_length=20)
    category: str | None = Field(default=None, max_length=120)
    problem: str = Field(min_length=3, max_length=1200)
    desire: str | None = Field(default=None, max_length=1200)
    source: str = Field(min_length=2, max_length=120)
    signal_strength: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    economic_intent_score: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    evidence: dict[str, Any] = Field(default_factory=dict)


class OfferCreate(BaseModel):
    platform: str = Field(min_length=2, max_length=80)
    external_product_id: str | None = Field(default=None, max_length=200)
    name: str = Field(min_length=2, max_length=300)
    affiliate_url: HttpUrl
    market: str | None = Field(default=None, max_length=80)
    language: str | None = Field(default=None, max_length=20)
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    price: Decimal | None = Field(default=None, ge=0)
    commission_type: Literal["fixed", "percent", "unknown"] = "unknown"
    commission_value: Decimal | None = Field(default=None, ge=0)
    commission_rate: Decimal | None = Field(default=None, ge=0, le=1)
    refund_rate: Decimal | None = Field(default=None, ge=0, le=1)
    tracking_strategy: Literal["none", "query_param", "url_template", "platform_adapter"] = "none"
    tracking_template: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class OpportunityCreate(BaseModel):
    demand_id: UUID
    offer_id: UUID
    market: str
    language: str
    audience: str | None = None
    angle: str
    economic_potential: Decimal = Field(ge=0, le=1)
    signal_quality: Decimal = Field(ge=0, le=1)
    offer_fit: Decimal = Field(ge=0, le=1)
    data_confidence: Decimal = Field(ge=0, le=1)


class AffiliateEventIn(BaseModel):
    platform: str
    external_event_id: str | None = None
    event_type: str | None = None
    payload: dict[str, Any]


class ConversionUpsert(BaseModel):
    platform: str
    external_sale_id: str
    offer_id: UUID | None = None
    opportunity_id: UUID | None = None
    attribution_key: str | None = None
    gross_value: Decimal = Field(default=Decimal("0"), ge=0)
    commission_value: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = "BRL"
    status: Literal["pending", "approved", "refunded", "chargeback", "cancelled"]
    occurred_at: str
    raw_event_id: UUID | None = None


@app.get("/health")
def health():
    return {"status": "ok", "service": "robo-global-core", "environment": settings.environment}


@app.get("/health/db")
def health_db():
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) as tables from information_schema.tables where table_schema=%s", (settings.core_schema,))
            row = cur.fetchone()
    return {"status": "ok", "schema": settings.core_schema, "tables": row["tables"]}


@app.get("/control", response_class=HTMLResponse)
def control_panel():
    test_sql = """(
        coalesce(r.payload->'data'->'product'->>'id','') = '0'
        or lower(coalesce(r.payload->'data'->'product'->>'name','')) like '%test%'
        or lower(coalesce(r.payload->'data'->'buyer'->>'email','')) like '%@example.com'
    )"""
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) as n from information_schema.tables where table_schema=%s", (settings.core_schema,))
            table_count = cur.fetchone()["n"]
            cur.execute(f"select count(*) n, count(*) filter (where status='active') active from {settings.core_schema}.offers")
            offers = cur.fetchone()
            cur.execute(f"select count(*) n, count(*) filter (where status in ('testing','winner')) active from {settings.core_schema}.opportunities")
            opportunities = cur.fetchone()
            cur.execute(f"select count(*) n from {settings.core_schema}.interactions where event_type='redirect'")
            redirects = cur.fetchone()["n"]
            cur.execute(f"""select
                count(*) filter (where not {test_sql}) as commercial,
                count(*) filter (where {test_sql}) as tests
                from {settings.core_schema}.conversions c
                left join {settings.core_schema}.affiliate_events_raw r on r.id=c.raw_event_id""")
            conversions = cur.fetchone()
            cur.execute(f"""select coalesce(sum(e.amount) filter (where not {test_sql}),0) as net
                from {settings.core_schema}.economic_outcomes e
                left join {settings.core_schema}.affiliate_events_raw r on r.id=e.raw_event_id""")
            net_commission = cur.fetchone()["net"]
            cur.execute(f"""select o.name,o.platform,o.status,o.market,o.language,o.currency,o.price,o.commission_value,o.tracking_strategy
                from {settings.core_schema}.offers o order by o.updated_at desc limit 8""")
            offer_rows = cur.fetchall()
            cur.execute(f"""select op.angle,op.market,op.language,op.score,op.status,ofr.name offer_name
                from {settings.core_schema}.opportunities op
                join {settings.core_schema}.offers ofr on ofr.id=op.offer_id
                order by op.updated_at desc limit 8""")
            opportunity_rows = cur.fetchall()
            cur.execute(f"""select r.event_type,r.processing_status,r.received_at,
                r.payload->'data'->'product'->>'name' product_name,
                r.payload->'data'->'purchase'->>'transaction' transaction,
                case when {test_sql} then true else false end as is_test
                from {settings.core_schema}.affiliate_events_raw r
                where r.platform='HOTMART' order by r.received_at desc limit 10""")
            event_rows = cur.fetchall()
            cur.execute(f"""select c.external_sale_id,c.status,c.gross_value,c.commission_value,c.currency,c.occurred_at,
                case when {test_sql} then true else false end as is_test
                from {settings.core_schema}.conversions c
                left join {settings.core_schema}.affiliate_events_raw r on r.id=c.raw_event_id
                order by c.updated_at desc limit 10""")
            conversion_rows = cur.fetchall()

    offer_html = "".join(
        f"<tr><td>{esc(r['name'])}</td><td>{esc(r['platform'])}</td><td><span class='pill'>{esc(r['status'])}</span></td><td>{esc(r['market'])}</td><td>{money(r['price'], r['currency'])}</td><td>{money(r['commission_value'], r['currency']) if r['commission_value'] is not None else '—'}</td></tr>"
        for r in offer_rows
    ) or "<tr><td colspan='6' class='empty'>Nenhuma oferta real cadastrada no Core.</td></tr>"
    opp_html = "".join(
        f"<tr><td>{esc(r['offer_name'])}</td><td>{esc(r['angle'])}</td><td>{esc(r['market'])}</td><td>{float(r['score'] or 0):.4f}</td><td><span class='pill'>{esc(r['status'])}</span></td></tr>"
        for r in opportunity_rows
    ) or "<tr><td colspan='5' class='empty'>Nenhuma oportunidade criada.</td></tr>"
    event_html = "".join(
        f"<tr><td>{esc(r['received_at'].strftime('%d/%m %H:%M:%S'))}</td><td>{esc(r['event_type'])}</td><td>{esc(r['product_name'])}</td><td>{masked_transaction(r['transaction'])}</td><td><span class='tag {'test' if r['is_test'] else 'commercial'}'>{'TESTE HOTMART' if r['is_test'] else 'COMERCIAL'}</span></td><td>{esc(r['processing_status'])}</td></tr>"
        for r in event_rows
    ) or "<tr><td colspan='6' class='empty'>Nenhum evento Hotmart recebido.</td></tr>"
    conversion_html = "".join(
        f"<tr><td>{masked_transaction(r['external_sale_id'])}</td><td><span class='pill'>{esc(r['status'])}</span></td><td>{money(r['gross_value'], r['currency'])}</td><td>{money(r['commission_value'], r['currency'])}</td><td>{'TESTE HOTMART' if r['is_test'] else 'COMERCIAL'}</td><td>{esc(r['occurred_at'].strftime('%d/%m/%Y %H:%M'))}</td></tr>"
        for r in conversion_rows
    ) or "<tr><td colspan='6' class='empty'>Nenhuma conversão registrada.</td></tr>"

    hottok_status = "CONFIGURADO" if bool(settings.hotmart_hottok) else "NÃO CONFIGURADO"
    db_status = "OPERACIONAL" if table_count == 10 else f"ATENÇÃO ({table_count}/10 tabelas)"
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")
    page = f"""<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Robo Global — Controle</title><meta http-equiv='refresh' content='30'>
<style>
:root{{--bg:#071019;--panel:#0d1823;--panel2:#111f2c;--line:#203244;--text:#edf4fa;--muted:#8fa4b7;--ok:#57d49b;--warn:#f1bf5b;--blue:#79aefc}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:Inter,Segoe UI,Arial,sans-serif}}main{{max-width:1280px;margin:auto;padding:34px 22px 60px}}
header{{display:flex;justify-content:space-between;gap:20px;align-items:flex-end;margin-bottom:26px}}h1{{margin:0;font-size:28px;letter-spacing:.2px}}h2{{font-size:17px;margin:0 0 14px}}.sub{{color:var(--muted);font-size:13px;margin-top:7px}}.stamp{{color:var(--muted);font-size:12px;text-align:right}}
.grid{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px;margin-bottom:22px}}.card{{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:14px;padding:16px;min-height:112px}}.label{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.8px}}.value{{font-size:25px;font-weight:700;margin-top:12px}}.small{{font-size:12px;color:var(--muted);margin-top:6px}}.ok{{color:var(--ok)}}.warn{{color:var(--warn)}}
section{{background:var(--panel);border:1px solid var(--line);border-radius:14px;margin-top:14px;padding:18px;overflow:auto}}table{{width:100%;border-collapse:collapse;min-width:760px}}th,td{{padding:11px 9px;border-bottom:1px solid var(--line);text-align:left;font-size:12px}}th{{color:var(--muted);font-weight:600}}.pill,.tag{{display:inline-block;border:1px solid #35506a;border-radius:999px;padding:3px 8px;font-size:10px;text-transform:uppercase}}.tag.test{{border-color:#8a6b2a;color:#f4cd74}}.tag.commercial{{border-color:#277956;color:#67dda9}}.empty{{color:var(--muted);padding:20px 9px}}.notice{{margin-top:18px;color:var(--muted);font-size:12px;line-height:1.5}}@media(max-width:900px){{.grid{{grid-template-columns:repeat(2,1fr)}}header{{display:block}}.stamp{{text-align:left;margin-top:10px}}}}@media(max-width:520px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<header><div><h1>Robô Global — Controle Operacional</h1><div class='sub'>Evidência direta do Core. Somente leitura, sem dados pessoais e sem métricas simuladas.</div></div><div class='stamp'>Atualizado em {now}<br>Atualização automática a cada 30 s</div></header>
<div class='grid'>
<div class='card'><div class='label'>API Core</div><div class='value ok'>ONLINE</div><div class='small'>{esc(settings.environment)}</div></div>
<div class='card'><div class='label'>Banco</div><div class='value {'ok' if table_count == 10 else 'warn'}'>{db_status}</div><div class='small'>{table_count} tabelas canônicas</div></div>
<div class='card'><div class='label'>Hotmart</div><div class='value {'ok' if settings.hotmart_hottok else 'warn'}'>{hottok_status}</div><div class='small'>Webhook V2 autenticado</div></div>
<div class='card'><div class='label'>Ofertas</div><div class='value'>{offers['n']}</div><div class='small'>{offers['active']} ativas</div></div>
<div class='card'><div class='label'>Oportunidades</div><div class='value'>{opportunities['n']}</div><div class='small'>{opportunities['active']} em teste/vencedoras · {redirects} redirects</div></div>
<div class='card'><div class='label'>Comissão líquida comercial</div><div class='value'>{money(net_commission)}</div><div class='small'>{conversions['commercial']} conversões comerciais · {conversions['tests']} de teste</div></div>
</div>
<section><h2>Ofertas no Core</h2><table><thead><tr><th>Oferta</th><th>Plataforma</th><th>Status</th><th>Mercado</th><th>Preço</th><th>Comissão estimada</th></tr></thead><tbody>{offer_html}</tbody></table></section>
<section><h2>Oportunidades econômicas</h2><table><thead><tr><th>Oferta</th><th>Ângulo</th><th>Mercado</th><th>Score</th><th>Status</th></tr></thead><tbody>{opp_html}</tbody></table></section>
<section><h2>Últimas conversões</h2><table><thead><tr><th>Transação</th><th>Status</th><th>Valor bruto</th><th>Comissão</th><th>Origem</th><th>Ocorrência</th></tr></thead><tbody>{conversion_html}</tbody></table></section>
<section><h2>Últimos eventos Hotmart</h2><table><thead><tr><th>Recebido</th><th>Evento</th><th>Produto</th><th>Transação</th><th>Origem</th><th>Processamento</th></tr></thead><tbody>{event_html}</tbody></table></section>
<div class='notice'>Critério de separação: eventos oficiais de teste da Hotmart são identificados pelos marcadores do payload de teste (produto id 0, produto identificado como teste ou e-mail @example.com). Eles permanecem auditáveis, mas não entram na comissão comercial. Este painel não exibe e-mail, IP, token, URL de afiliado ou payload bruto.</div>
</main></body></html>"""
    return HTMLResponse(page)


@app.post("/v1/demands", status_code=201)
def create_demand(payload: DemandCreate):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""insert into {settings.core_schema}.demands
            (market,language,category,problem,desire,source,signal_strength,economic_intent_score,evidence)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb) returning *""",
            (payload.market,payload.language,payload.category,payload.problem,payload.desire,payload.source,payload.signal_strength,payload.economic_intent_score,json.dumps(payload.evidence)))
            row=cur.fetchone()
        conn.commit()
    return row


@app.post("/v1/offers", status_code=201)
def create_offer(payload: OfferCreate):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""insert into {settings.core_schema}.offers
            (platform,external_product_id,name,affiliate_url,market,language,currency,price,commission_type,commission_value,commission_rate,refund_rate,tracking_strategy,tracking_template,evidence)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
            on conflict (affiliate_url) do update set name=excluded.name,evidence=excluded.evidence,updated_at=now() returning *""",
            (payload.platform.upper(),payload.external_product_id,payload.name,str(payload.affiliate_url),payload.market,payload.language,payload.currency.upper(),payload.price,payload.commission_type,payload.commission_value,payload.commission_rate,payload.refund_rate,payload.tracking_strategy,payload.tracking_template,json.dumps(payload.evidence)))
            row=cur.fetchone()
        conn.commit()
    return row


@app.post("/v1/opportunities", status_code=201)
def create_opportunity(payload: OpportunityCreate):
    score=opportunity_score(payload.economic_potential,payload.signal_quality,payload.offer_fit,payload.data_confidence)
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""insert into {settings.core_schema}.opportunities
            (demand_id,offer_id,market,language,audience,angle,economic_potential,signal_quality,offer_fit,data_confidence,score)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            on conflict (demand_id,offer_id,market,language,angle) do update set audience=excluded.audience,economic_potential=excluded.economic_potential,signal_quality=excluded.signal_quality,offer_fit=excluded.offer_fit,data_confidence=excluded.data_confidence,score=excluded.score,score_version={settings.core_schema}.opportunities.score_version+1,updated_at=now() returning *""",
            (payload.demand_id,payload.offer_id,payload.market,payload.language,payload.audience,payload.angle,payload.economic_potential,payload.signal_quality,payload.offer_fit,payload.data_confidence,score))
            row=cur.fetchone()
        conn.commit()
    return row


@app.get("/r/{opportunity_id}")
def redirect_opportunity(opportunity_id: UUID, request: Request):
    attribution_key=secrets.token_urlsafe(18)
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""select o.id opportunity_id,o.offer_id,f.affiliate_url,f.tracking_strategy,f.tracking_template
            from {settings.core_schema}.opportunities o join {settings.core_schema}.offers f on f.id=o.offer_id
            where o.id=%s and o.status in ('testing','winner') and f.status='active'""",(opportunity_id,))
            row=cur.fetchone()
            if not row: raise HTTPException(status_code=404,detail="opportunity not commercially active")
            destination=tracked_url(row["affiliate_url"],row["tracking_strategy"],row["tracking_template"],attribution_key)
            ua=request.headers.get("user-agent") or ""; forwarded=request.headers.get("x-forwarded-for") or ""
            cur.execute(f"""insert into {settings.core_schema}.interactions
            (opportunity_id,offer_id,event_type,attribution_key,source,referrer,user_agent_hash,ip_hash,metadata)
            values (%s,%s,'redirect',%s,%s,%s,%s,%s,%s::jsonb)""",
            (row["opportunity_id"],row["offer_id"],attribution_key,request.query_params.get("src"),request.headers.get("referer"),hashlib.sha256(ua.encode()).hexdigest() if ua else None,hashlib.sha256(forwarded.encode()).hexdigest() if forwarded else None,json.dumps({"path":str(request.url.path)})))
        conn.commit()
    return RedirectResponse(destination,status_code=302)


@app.post("/v1/internal/affiliate-events", dependencies=[Depends(require_ingest_key)])
def ingest_affiliate_event(payload: AffiliateEventIn):
    with db_connection() as conn:
        with conn.cursor() as cur:
            event_id,created=insert_raw_event(cur,payload.platform.upper(),payload.external_event_id,payload.event_type,payload.payload)
        conn.commit()
    return {"status":"accepted" if created else "duplicate","event_id":str(event_id) if event_id else None}


@app.post("/v1/internal/conversions", dependencies=[Depends(require_ingest_key)])
def upsert_conversion(payload: ConversionUpsert):
    with db_connection() as conn:
        with conn.cursor() as cur:
            interaction_id=None; opportunity_id=payload.opportunity_id
            if payload.attribution_key:
                cur.execute(f"select id,opportunity_id from {settings.core_schema}.interactions where attribution_key=%s",(payload.attribution_key,)); hit=cur.fetchone()
                if hit: interaction_id=hit["id"]; opportunity_id=opportunity_id or hit["opportunity_id"]
            cur.execute(f"""insert into {settings.core_schema}.conversions
            (platform,external_sale_id,offer_id,opportunity_id,attribution_key,gross_value,commission_value,currency,status,occurred_at,raw_event_id,interaction_id)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::timestamptz,%s,%s)
            on conflict (platform,external_sale_id) do update set offer_id=coalesce(excluded.offer_id,{settings.core_schema}.conversions.offer_id),opportunity_id=coalesce(excluded.opportunity_id,{settings.core_schema}.conversions.opportunity_id),attribution_key=coalesce(excluded.attribution_key,{settings.core_schema}.conversions.attribution_key),gross_value=excluded.gross_value,commission_value=excluded.commission_value,currency=excluded.currency,status=excluded.status,occurred_at=excluded.occurred_at,raw_event_id=coalesce(excluded.raw_event_id,{settings.core_schema}.conversions.raw_event_id),interaction_id=coalesce(excluded.interaction_id,{settings.core_schema}.conversions.interaction_id),updated_at=now() returning *""",
            (payload.platform.upper(),payload.external_sale_id,payload.offer_id,opportunity_id,payload.attribution_key,payload.gross_value,payload.commission_value,payload.currency.upper(),payload.status,payload.occurred_at,payload.raw_event_id,interaction_id)); row=cur.fetchone()
        conn.commit()
    return row


@app.post("/v1/webhooks/hotmart")
async def hotmart_webhook(request: Request, x_hotmart_hottok: str | None = Header(default=None)):
    if not validate_hottok(x_hotmart_hottok, settings.hotmart_hottok):
        raise HTTPException(status_code=401, detail="invalid Hotmart token")
    payload = await request.json()
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid payload")
    normalized = normalize_webhook(payload)
    with db_connection() as conn:
        with conn.cursor() as cur:
            raw_id, created = insert_raw_event(cur, "HOTMART", normalized.external_event_id, normalized.event_type, payload)
            if not created:
                conn.commit()
                return {"status":"duplicate","event_id":str(raw_id) if raw_id else None}
            if not normalized.status or not normalized.external_sale_id:
                cur.execute(f"update {settings.core_schema}.affiliate_events_raw set processing_status='ignored',processed_at=now() where id=%s",(raw_id,))
                conn.commit()
                return {"status":"ignored","event_id":str(raw_id)}
            offer_id=None
            if normalized.external_product_id:
                cur.execute(f"select id from {settings.core_schema}.offers where platform='HOTMART' and external_product_id=%s limit 1",(normalized.external_product_id,)); offer=cur.fetchone(); offer_id=offer["id"] if offer else None
            interaction_id=None; opportunity_id=None
            if normalized.attribution_key:
                cur.execute(f"select id,opportunity_id from {settings.core_schema}.interactions where attribution_key=%s",(normalized.attribution_key,)); hit=cur.fetchone()
                if hit: interaction_id=hit["id"]; opportunity_id=hit["opportunity_id"]
            occurred=datetime.fromtimestamp(normalized.occurred_at_ms/1000,tz=timezone.utc) if normalized.occurred_at_ms else datetime.now(timezone.utc)
            cur.execute(f"""insert into {settings.core_schema}.conversions
            (platform,external_sale_id,offer_id,opportunity_id,interaction_id,attribution_key,gross_value,commission_value,currency,status,occurred_at,raw_event_id)
            values ('HOTMART',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            on conflict (platform,external_sale_id) do update set offer_id=coalesce(excluded.offer_id,{settings.core_schema}.conversions.offer_id),opportunity_id=coalesce(excluded.opportunity_id,{settings.core_schema}.conversions.opportunity_id),interaction_id=coalesce(excluded.interaction_id,{settings.core_schema}.conversions.interaction_id),attribution_key=coalesce(excluded.attribution_key,{settings.core_schema}.conversions.attribution_key),gross_value=excluded.gross_value,commission_value=excluded.commission_value,currency=excluded.currency,status=excluded.status,occurred_at=excluded.occurred_at,raw_event_id=excluded.raw_event_id,updated_at=now() returning id""",
            (normalized.external_sale_id,offer_id,opportunity_id,interaction_id,normalized.attribution_key,normalized.gross_value,normalized.commission_value,normalized.currency,normalized.status,occurred,raw_id)); conversion=cur.fetchone()
            effect=economic_effect(normalized.status,normalized.commission_value)
            if effect:
                event_type,amount=effect
                cur.execute(f"""insert into {settings.core_schema}.economic_outcomes
                (conversion_id,opportunity_id,raw_event_id,event_type,amount,currency,occurred_at)
                values (%s,%s,%s,%s,%s,%s,%s)
                on conflict (raw_event_id) do nothing""",
                (conversion["id"],opportunity_id,raw_id,event_type,amount,normalized.currency,occurred))
            cur.execute(f"update {settings.core_schema}.affiliate_events_raw set processing_status='processed',processed_at=now() where id=%s",(raw_id,))
        conn.commit()
    return {"status":"processed","event_id":str(raw_id),"conversion_id":str(conversion["id"])}
