"""Awin integration endpoints: credential-free status, authenticated dry-run/import.

The feed URL is configured server-side. Never accept arbitrary external URLs from
request parameters; feed links may contain API keys.
"""
from __future__ import annotations

import os
from urllib.request import Request, urlopen
import logging
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import urlparse, parse_qsl

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from psycopg import connect

from core_v1.app.awin import AwinClient, parse_feed
from core_v1.app.awin_import import import_offers

router = APIRouter(prefix="/v1/awin", tags=["awin"])


def _auth(x_core_ingest_key: str = __import__("fastapi").Header(default="")):
    import secrets
    expected = os.environ.get("CORE_INGEST_KEY", "")
    if not expected or not secrets.compare_digest(expected, x_core_ingest_key):
        raise HTTPException(401, "invalid ingest key")


class ImportRequest(BaseModel):
    dry_run: bool = True
    max_rows: int = Field(default=10000, ge=1, le=100000)


@router.get("/status", dependencies=[Depends(_auth)])
def status():
    return {
        "publisher_id_configured": bool(os.getenv("AWIN_PUBLISHER_ID")),
        "api_token_configured": bool(os.getenv("AWIN_API_TOKEN")),
        "feed_url_configured": bool(os.getenv("AWIN_FEED_URL")),
        "import_ready": bool(os.getenv("AWIN_FEED_URL") and os.getenv("DATABASE_URL")),
        "publication_enabled": False,
    }


@router.get("/programs", dependencies=[Depends(_auth)])
def programs():
    try:
        client = AwinClient(int(os.environ["AWIN_PUBLISHER_ID"]), os.environ["AWIN_API_TOKEN"])
        return {"programs": client.programs()}
    except KeyError:
        raise HTTPException(503, "Awin credentials not configured")
    except (ValueError, Exception) as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(502, "Awin program discovery unavailable")


@router.get("/discovery/summary", dependencies=[Depends(_auth)])
def discovery_summary():
    """Read-only advertiser discovery. Active does not imply publisher approval."""
    from collections import Counter
    try:
        client = AwinClient(int(os.environ["AWIN_PUBLISHER_ID"]), os.environ["AWIN_API_TOKEN"])
        programmes = client.programs()
        joined = client.programs("joined")
        if not isinstance(programmes, list) or not isinstance(joined, list):
            raise ValueError("unexpected programme response")
        joined_ids = {str(p.get("id")) for p in joined if isinstance(p, dict)}
        # Verify which programme metadata is present without inferring approval.
        catalogue_program = next((p for p in programmes if isinstance(p, dict) and str(p.get("id")) == "81383"), None)
        sectors = Counter(str(p.get("primarySector") or "unknown") for p in programmes if isinstance(p, dict))
        regions = Counter(str(p.get("primaryRegion") or "unknown") for p in programmes if isinstance(p, dict))
        return {
            "programmes_discovered": len(programmes),
            "joined_programmes": len(joined),
            "catalogue_merchant_id": "81383",
            "catalogue_merchant_joined": "81383" in joined_ids,
            "catalogue_merchant_discoverable": catalogue_program is not None,
            "catalogue_merchant_status": str(catalogue_program.get("status")) if catalogue_program else None,
            "sector_counts": dict(sectors.most_common()),
            "region_counts": dict(regions.most_common()),
            "offers_authorized_for_publication": 0,
            "requires_terms_and_channel_verification": True,
        }
    except Exception:
        raise HTTPException(502, "Awin advertiser discovery unavailable")


@router.get("/discovery/shortlist", dependencies=[Depends(_auth)])
def discovery_shortlist(region: str = "BR", limit: int = 30):
    """Read-only candidates for commercial review, never a claim of eligibility."""
    if len(region) != 2 or not region.isalpha():
        raise HTTPException(422, "region must be two letters")
    if limit < 1 or limit > 100:
        raise HTTPException(422, "limit must be between 1 and 100")
    try:
        client = AwinClient(int(os.environ["AWIN_PUBLISHER_ID"]), os.environ["AWIN_API_TOKEN"])
        programmes = client.programs()
        joined = client.programs("joined")
        if not isinstance(programmes, list) or not isinstance(joined, list):
            raise ValueError("unexpected response")
        joined_ids = {str(p.get("id")) for p in joined if isinstance(p, dict)}
        region = region.upper()
        matches = []
        for p in programmes:
            if not isinstance(p, dict):
                continue
            primary = p.get("primaryRegion")
            code = str(primary.get("countryCode") or primary.get("code") or primary.get("name") or "") if isinstance(primary, dict) else str(primary or "")
            aliases = {"BR": {"BR", "BRA", "BRAZIL", "BRASIL"}, "US": {"US", "USA", "UNITED STATES"}, "GB": {"GB", "UK", "UNITED KINGDOM"}}
            if code.strip().upper() not in aliases.get(region, {region}):
                continue
            matches.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "sector": p.get("primarySector"),
                "region": primary,
                "programme_active": str(p.get("status", "")).lower() == "active",
                "publisher_joined": str(p.get("id")) in joined_ids,
                "terms_reviewed": False,
                "publication_authorized": False,
            })
        matches.sort(key=lambda p: str(p.get("name") or "").casefold())
        return {"region": region, "matching_programmes": len(matches), "returned": min(len(matches), limit), "candidates": matches[:limit], "publication_enabled": False}
    except Exception:
        raise HTTPException(502, "Awin shortlist unavailable")


@router.post("/import", dependencies=[Depends(_auth)])
def import_feed(payload: ImportRequest):
    url = os.getenv("AWIN_FEED_URL", "")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"productdata.awin.com", "ui.awin.com"}:
        raise HTTPException(503, "approved Awin feed URL not configured")
    if not os.getenv("DATABASE_URL"):
        raise HTTPException(503, "database not configured")
    try:
        request = Request(url, headers={"User-Agent": "RoboGlobalCore/1.0"})
        with urlopen(request, timeout=45) as response:
            if urlparse(response.geturl()).hostname not in {"productdata.awin.com", "ui.awin.com"}:
                raise ValueError("unexpected redirect host")
            content = response.read(15_000_001)
        if len(content) > 15_000_000:
            raise ValueError("feed exceeds 15 MB limit")
        offers = parse_feed(content, compressed=content.startswith(bytes([0x1f, 0x8b])), max_rows=payload.max_rows)
        # No inferred approvals: until program/channel terms are separately verified,
        # all imported records remain candidates.
        with connect(os.environ["DATABASE_URL"]) as conn:
            summary = import_offers(conn, offers, {}, reviewed_terms=set(), dry_run=payload.dry_run)
        return {**summary.__dict__, "dry_run": payload.dry_run, "publication_enabled": False}
    except Exception:
        raise HTTPException(502, "Awin feed import failed; no credentials or URLs disclosed")


def _startup_feed_probe():
    """One-shot non-mutating feed verification; secrets never logged."""
    if not os.getenv("AWIN_FEED_URL"):
        logging.getLogger("robo-global-core").warning("AWIN_PROBE feed_not_configured")
        return
    try:
        url = os.environ["AWIN_FEED_URL"]
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in {"productdata.awin.com", "ui.awin.com"}:
            raise ValueError("unapproved feed host")
        logging.getLogger("robo-global-core").warning("AWIN_PROBE url_shape host=%s path_segments=%s query_keys=%s", parsed.hostname, len([segment for segment in parsed.path.split("/") if segment]), sorted({k for k, _ in parse_qsl(parsed.query, keep_blank_values=True)}))
        from urllib.parse import quote, urlsplit, urlunsplit
        # Awin's feed builder can emit unescaped reserved characters in path values.
        # Preserve structural separators, percent escapes and existing query values.
        parts = urlsplit(url)
        # Awin restricts adult-content filtering to UK/US/CA/IE; BR feeds must omit it.
        segments = parts.path.split("/")
        filtered = []
        removed_adult_filter = False
        i = 0
        while i < len(segments):
            if segments[i].lower() == "adultcontent" and i + 1 < len(segments):
                removed_adult_filter = True
                i += 2
                continue
            filtered.append(segments[i])
            i += 1
        if removed_adult_filter:
            logging.getLogger("robo-global-core").warning("AWIN_PROBE removed_unsupported_adultcontent_filter=true")
        safe_path = quote("/".join(filtered), safe="/%:@-._~")
        if safe_path != parts.path or removed_adult_filter:
            url = urlunsplit((parts.scheme, parts.netloc, safe_path, parts.query, parts.fragment))
            logging.getLogger("robo-global-core").warning("AWIN_PROBE encoded_reserved_path_characters=true")
        req = Request(url, headers={"User-Agent": "RoboGlobalCore/1.0"})
        with urlopen(req, timeout=45) as response:
            if urlparse(response.geturl()).hostname not in {"productdata.awin.com", "ui.awin.com"}:
                raise ValueError("unapproved redirect")
            content = response.read(15_000_001)
        if len(content) > 15_000_000:
            raise ValueError("feed too large")
        offers = parse_feed(content, compressed=content.startswith(bytes([0x1f, 0x8b])), max_rows=10000)
        logging.getLogger("robo-global-core").warning("AWIN_PROBE success candidates=%s publication_enabled=false database_writes=0", len(offers))
        if os.getenv("AWIN_CANDIDATE_IMPORT_ON_STARTUP") == "true" and offers:
            with connect(os.environ["DATABASE_URL"]) as conn:
                summary = import_offers(conn, offers, {}, reviewed_terms=set(), dry_run=False)
            logging.getLogger("robo-global-core").warning("AWIN_CANDIDATE_IMPORT completed discovered=%s candidates=%s imported=%s publication_enabled=false", summary.discovered, summary.candidates, summary.imported)
    except HTTPError as exc:
        category = "unclassified"
        try:
            import json
            body = json.loads(exc.read(4096).decode("utf-8", errors="replace"))
            message = str(body.get("message", "") if isinstance(body, dict) else "").lower()
            if any(term in message for term in ("column", "field", "format", "delimiter", "parameter", "invalid request")):
                category = "invalid_feed_parameters"
            elif any(term in message for term in ("feed", "advertiser", "not found", "no products")):
                category = "feed_unavailable"
            elif any(term in message for term in ("api key", "apikey", "authentication", "unauthorized", "access", "permission")):
                category = "feed_key_or_access"
            elif isinstance(body, dict):
                category = "json_error_keys_" + "_".join(sorted(k for k in body if k in {"message", "error", "errors", "status", "code"}))
        except Exception:
            pass
        logging.getLogger("robo-global-core").error("AWIN_PROBE failed category=HTTPError status=%s reason_category=%s", exc.code, category)
    except Exception as exc:
        logging.getLogger("robo-global-core").error("AWIN_PROBE failed category=%s sqlstate=%s", type(exc).__name__, getattr(exc, "sqlstate", "none"))


@router.on_event("startup")
def awin_startup_probe():
    Thread(target=_startup_feed_probe, daemon=True).start()


@router.get('/health/programs', dependencies=[Depends(_auth)])
def programs_health():
    response = programs()
    records = response.get('programs', [])
    return {'reachable': True, 'count': len(records)}


@router.on_event("startup")
def check_awin_oauth_at_startup():
    def check():
        logger = logging.getLogger("robo-global-core")
        try:
            data = AwinClient(int(os.environ["AWIN_PUBLISHER_ID"]), os.environ["AWIN_API_TOKEN"]).programs()
            if isinstance(data, list):
                count = len(data)
            elif isinstance(data, dict):
                count = len(data.get("programmes", data.get("data", [])))
            else:
                raise ValueError("unexpected response")
            logger.warning("AWIN_OAUTH_CHECK success programs=%s", count)
            try:
                joined = AwinClient(int(os.environ["AWIN_PUBLISHER_ID"]), os.environ["AWIN_API_TOKEN"]).programs("joined")
                logger.warning("AWIN_JOINED_DISCOVERY count=%s", len(joined) if isinstance(joined, list) else -1)
                logger.warning("AWIN_CATALOG_MERCHANT_MATCH merchant_id=81383 joined=%s", any(str(p.get("id")) == "81383" for p in joined if isinstance(p, dict)) if isinstance(joined, list) else False)
            except HTTPError as err:
                logger.warning("AWIN_JOINED_DISCOVERY http_status=%s", err.code)
            # Read-only membership breakdown; no offers are approved or published here.
            if isinstance(data, list):
                from collections import Counter
                statuses = Counter(str(p.get("relationship", p.get("membershipStatus", p.get("membership_status", p.get("status", "unknown"))))).lower() for p in data if isinstance(p, dict))
                logger.warning("AWIN_MEMBERSHIP_DISCOVERY total=%s statuses=%s keys=%s", count, dict(statuses.most_common(12)), sorted(data[0].keys()) if data and isinstance(data[0], dict) else [])
        except HTTPError as exc:
            logger.error("AWIN_OAUTH_CHECK http_status=%s", exc.code)
        except Exception as exc:
            logger.error("AWIN_OAUTH_CHECK error_type=%s configuration_flags=%s", type(exc).__name__, [bool(os.getenv("AWIN_PUBLISHER_ID")), bool(os.getenv("AWIN_API_TOKEN"))])
    Thread(target=check, daemon=True).start()
