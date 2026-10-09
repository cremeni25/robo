# Robo Global Core v1

Isolated reconstruction of the Robo Global monetization engine.

## Isolation rules

- Legacy tables are not read or written by this application.
- Canonical database schema: `robo_global_core`.
- Current production service is not replaced by this branch.
- No paid traffic is permitted before organic sales validation.
- No simulated commercial data is accepted as production evidence.

## Runtime configuration

Required environment variables:

- `DATABASE_URL`: direct PostgreSQL connection string for the Supabase project.
- `CORE_INGEST_KEY`: high-entropy secret used only between trusted platform adapters and the core.
- `ENVIRONMENT`: optional, defaults to `development`.
- `CORE_SCHEMA`: optional, defaults to `robo_global_core`.

Do not expose `DATABASE_URL` or `CORE_INGEST_KEY` to browsers.

## Local start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Homologation gates

The branch may only replace the existing backend after all gates pass:

1. `/health` returns OK.
2. `/health/db` connects to `robo_global_core` and sees exactly the canonical schema expected by the build.
3. Demand, offer and opportunity contracts persist correctly.
4. A test opportunity cannot redirect while offer/opportunity are inactive.
5. An active homologation opportunity records one unique interaction per redirect.
6. Duplicate affiliate event payloads are rejected as duplicates.
7. Repeated webhook normalization for the same `(platform, external_sale_id)` updates one conversion row rather than duplicating a sale.
8. Platform-specific signature verification is proven with official sandbox/test events.
9. Refund/chargeback lifecycle is proven before financial reporting is considered authoritative.
10. Only after a real affiliate conversion is correctly attributed can the core be called commercially operational.

## Current scope

Core v1 contains contracts and economic primitives only. It intentionally does not contain legacy dashboards, CMS flows, partner payout logic, or historical presentation layers.
