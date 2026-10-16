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


def _run_cycle() -> None:
    from core_v1.app.awin import AwinClient
    from core_v1.app.awin_routes import ImportRequest, import_multiple_feeds

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
