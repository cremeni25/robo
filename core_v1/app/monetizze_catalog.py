"""Read-only Monetizze 2.1 catalog adapter; no enrollment, sales or publication.

Contract: https://api.monetizze.com.br/2.1/apidoc/api_data.json
/myproducts is not paginated. Its default scope includes active affiliations
and some producer products, so catalog presence alone is not affiliate proof.
"""
from __future__ import annotations
import hashlib
import json
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError


class CatalogError(Exception):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CatalogError("unexpected_redirect")


class MonetizzeCatalogClient:
    BASE = "https://api.monetizze.com.br/2.1"

    def __init__(self, consumer_key: str):
        if not consumer_key or not consumer_key.strip():
            raise CatalogError("credentials_not_configured")
        self._key = consumer_key
        self._opener = build_opener(_NoRedirect())

    def _get(self, path: str, headers: dict) -> object:
        if path not in {"/token", "/myproducts?retorno_produtor=0&retornar_produtos_aprovacao=0"}:
            raise CatalogError("unsupported_endpoint")
        request = Request(self.BASE + path, headers={"Accept": "application/json", **headers})
        try:
            with self._opener.open(request, timeout=30) as response:
                raw = response.read(20_000_001)
            if len(raw) > 20_000_000:
                raise CatalogError("response_too_large")
            return json.loads(raw)
        except HTTPError as exc:
            raise CatalogError("http_" + str(exc.code)) from None
        except CatalogError:
            raise
        except Exception:
            raise CatalogError("catalog_request_failed") from None

    def products(self) -> list[dict]:
        auth = self._get("/token", {"X_CONSUMER_KEY": self._key})
        if not isinstance(auth, dict) or not isinstance(auth.get("TOKEN"), str) or not auth["TOKEN"]:
            raise CatalogError("invalid_auth_response")
        payload = self._get("/myproducts?retorno_produtor=0&retornar_produtos_aprovacao=0",
                            {"TOKEN": auth["TOKEN"]})
        return normalize_products(payload)


def normalize_products(payload: object) -> list[dict]:
    if not isinstance(payload, dict) or payload.get("status") != 200 or not isinstance(payload.get("dados"), list):
        raise CatalogError("invalid_catalog_response")
    records = []
    seen = set()
    for item in payload["dados"]:
        if not isinstance(item, dict) or not str(item.get("codigo", "")).isdigit() or not isinstance(item.get("nome"), str) or not item["nome"].strip():
            raise CatalogError("invalid_product")
        code = str(item["codigo"])
        if code in seen:
            raise CatalogError("duplicate_product")
        seen.add(code)
        plans = item.get("planos")
        if not isinstance(plans, list):
            raise CatalogError("invalid_plans")
        active_plans = []
        for plan in plans:
            if not isinstance(plan, dict) or not str(plan.get("codigo", "")).isdigit():
                raise CatalogError("invalid_plan")
            if str(plan.get("status")) == "1":
                active_plans.append({"codigo": str(plan["codigo"]), "nome": plan.get("nome"),
                                     "valor": plan.get("valor"), "status": "1"})
        records.append({"codigo": code, "nome": item["nome"].strip(),
                        "status": str(item.get("status", "")), "planos_ativos": active_plans,
                        "source": "monetizze_myproducts", "affiliate_link_verified": False,
                        "membership_verified": False, "publication_authorized": False})
    if payload.get("totalRegistros") != len(records):
        raise CatalogError("incomplete_catalog_response")
    return records


def record_catalog(conn, records: list[dict]) -> int:
    """Use the Core's existing raw-event intake; never synthesize an offer URL."""
    inserted = 0
    with conn.cursor() as cur:
        for record in records:
            canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            digest = hashlib.sha256(canonical.encode()).hexdigest()
            external_id = "catalog:" + record["codigo"] + ":" + digest
            cur.execute("""insert into robo_global_core.affiliate_events_raw
                (platform, external_event_id, event_type, payload, payload_hash)
                values ('MONETIZZE', %s, 'catalog_product', %s::jsonb, %s)
                on conflict do nothing returning id""", (external_id, canonical, digest))
            inserted += int(cur.fetchone() is not None)
    conn.commit()
    return inserted
