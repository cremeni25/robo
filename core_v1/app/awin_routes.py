"""Awin integration endpoints: credential-free status, authenticated dry-run/import.

The feed URL is configured server-side. Never accept arbitrary external URLs from
request parameters; feed links may contain API keys.
"""
from __future__ import annotations

import os
from urllib.request import Request, urlopen
import logging
from threading import Thread
from urllib.parse import urlparse

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
        req = Request(url, headers={"User-Agent": "RoboGlobalCore/1.0"})
        with urlopen(req, timeout=45) as response:
            if urlparse(response.geturl()).hostname not in {"productdata.awin.com", "ui.awin.com"}:
                raise ValueError("unapproved redirect")
            content = response.read(15_000_001)
        if len(content) > 15_000_000:
            raise ValueError("feed too large")
        offers = parse_feed(content, compressed=content.startswith(bytes([0x1f, 0x8b])), max_rows=10000)
        logging.getLogger("robo-global-core").info("AWIN_PROBE success candidates=%s publication_enabled=false database_writes=0", len(offers))
    except Exception as exc:
        logging.getLogger("robo-global-core").error("AWIN_PROBE failed category=%s", type(exc).__name__)


@router.on_event("startup")
def awin_startup_probe():
    Thread(target=_startup_feed_probe, daemon=True).start()
