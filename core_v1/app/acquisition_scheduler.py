"""Best-effort in-service acquisition scheduler for the existing Core V1 Render service.

Uses the service's own configured environment. No additional paid service or
GitHub secrets are needed. Free services may sleep: this is not a guaranteed cron.
"""
from __future__ import annotations

import logging
import os
import threading
import time

logger = logging.getLogger("robo-global-core")
_started = False
_lock = threading.Lock()



def _run_monetizze_cycle() -> None:
    key = os.getenv("MONETIZZE_CONSUMER_KEY", "").strip()
    if not key:
        logger.warning("MONETIZZE_CATALOG_SKIPPED reason=consumer_key_not_configured publication_changed=false")
        return
    try:
        from psycopg import connect
        from core_v1.app.monetizze_catalog import MonetizzeCatalogClient, record_catalog
        records = MonetizzeCatalogClient(key).products()
        with connect(os.environ["DATABASE_URL"]) as conn:
            inserted = record_catalog(conn, records)
        logger.warning("MONETIZZE_CATALOG completed products=%s new_snapshots=%s publication_changed=false",
                       len(records), inserted)
    except Exception as exc:
        logger.warning("MONETIZZE_CATALOG_FAILED category=%s publication_changed=false",
                       type(exc).__name__)


def _run_cycle() -> None:
    _run_monetizze_cycle()
    from core_v1.app.awin import AwinClient
    from core_v1.app.awin_routes import ImportRequest, import_multiple_feeds

    joined = None
    if os.getenv("AWIN_PUBLISHER_ID") and os.getenv("AWIN_API_TOKEN"):
        try:
            client = AwinClient(int(os.environ["AWIN_PUBLISHER_ID"]), os.environ["AWIN_API_TOKEN"])
            programs = client.programs()
            joined = client.programs("joined")
            logger.warning("ACQUISITION_DISCOVERY programmes=%s joined=%s",
                           len(programs) if isinstance(programs, list) else -1,
                           len(joined) if isinstance(joined, list) else -1)
        except Exception as exc:
            logger.warning("ACQUISITION_DISCOVERY_FAILED category=%s", type(exc).__name__)
    else:
        logger.warning("ACQUISITION_DISCOVERY_SKIPPED credentials_not_configured")

    if os.getenv("AWIN_PUBLISHER_ID") and os.getenv("AWIN_API_TOKEN"):
        try:
            from core_v1.app.approved_service import publish_approved_service
            result = publish_approved_service()
            logger.warning("ACQUISITION_APPROVED_SERVICE status=%s reason=%s",
                           result.get("status"), result.get("reason", "none"))
        except Exception as exc:
            logger.warning("ACQUISITION_APPROVED_SERVICE_FAILED category=%s", type(exc).__name__)

    if os.getenv("AWIN_FEED_URL") or os.getenv("AWIN_FEED_URLS"):
        try:
            result = import_multiple_feeds(ImportRequest(dry_run=False, max_rows=10000))
            logger.warning("ACQUISITION_IMPORT sources=%s successful=%s imported=%s skipped=%s",
                           result.get("sources"), result.get("successful_sources"),
                           result.get("imported"), result.get("skipped"))
        except Exception as exc:
            logger.warning("ACQUISITION_IMPORT_FAILED category=%s", type(exc).__name__)
    else:
        logger.warning("ACQUISITION_IMPORT_SKIPPED no_feed_configured")

    # Use the official response already fetched in this cycle. Run after import
    # so freshly imported candidates also retain independently checked evidence.
    if joined is not None:
        try:
            from psycopg import connect
            from core_v1.app.awin_import import sync_candidate_memberships
            with connect(os.environ["DATABASE_URL"]) as conn:
                checked = sync_candidate_memberships(conn, joined)
            logger.warning("ACQUISITION_MEMBERSHIP_SYNC checked=%s publication_changed=false", checked)
        except Exception as exc:
            logger.warning("ACQUISITION_MEMBERSHIP_SYNC_FAILED category=%s", type(exc).__name__)


def start_scheduler() -> None:
    """Start one daemon per Python process, immediately then every six hours."""
    global _started
    with _lock:
        if _started:
            return
        _started = True

    def loop() -> None:
        while True:
            try:
                _run_cycle()
            except Exception as exc:
                logger.error("ACQUISITION_CYCLE_FAILED category=%s", type(exc).__name__)
            time.sleep(6 * 60 * 60)

    threading.Thread(target=loop, name="robo-acquisition", daemon=True).start()
