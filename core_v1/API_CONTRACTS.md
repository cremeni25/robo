# Robo Global Core API — Contract v1

This contract is intentionally independent from the legacy application.

## Public health

### GET /health
Process health only. Does not prove database or commercial readiness.

### GET /health/db
Verifies connectivity with `robo_global_core` and reports the number of canonical tables.

## Economic intake

### POST /v1/demands
Registers an observed demand signal already normalized by a radar/collector.

Required economic dimensions:
- market
- language
- problem
- source
- signal_strength [0..1]
- economic_intent_score [0..1]

No synthetic demand may be promoted to production evidence.

### POST /v1/offers
Registers or updates a real affiliate offer by affiliate URL.

An offer is not eligible for commercial routing until its database status is `active`.
Tracking strategies:
- `none`: records redirect but does not claim closed-loop attribution.
- `query_param`: appends the attribution key using `tracking_template` as parameter name.
- `url_template`: `tracking_template` must contain `{attribution_key}`.
- `platform_adapter`: routing is blocked until a platform adapter is available.

### POST /v1/opportunities
Creates or re-evaluates the economic pairing demand + offer + market + language + angle.

v1 score is deliberately transparent:

`score = economic_potential × signal_quality × offer_fit × data_confidence`

All factors are constrained to [0..1]. Score version increments on re-evaluation.

## Monetization routing

### GET /r/{opportunity_id}
Commercial redirect endpoint.

It redirects only when:
- opportunity status is `testing` or `winner`;
- offer status is `active`;
- the configured tracking strategy can safely generate the destination URL.

Before redirect, a unique attribution key is generated and persisted in `interactions`.
Raw IP and user-agent are not stored; hashes are stored instead.

## Internal adapter boundary

These endpoints require `X-Core-Ingest-Key` and must not be called from public clients.

### POST /v1/internal/affiliate-events
Stores the original platform event as immutable raw evidence.

Idempotency is based on SHA-256 of canonical JSON payload. Duplicate payloads return `duplicate` instead of creating another event.

### POST /v1/internal/conversions
Canonical conversion upsert.

Uniqueness key: `(platform, external_sale_id)`.
Repeated affiliate webhooks update the same conversion instead of generating duplicate sales.
When an attribution key is supplied, the core resolves the original interaction/opportunity.

## Platform adapters

Hotmart, Eduzz, Monetizze and other platforms must live outside the economic core as adapters.
Their responsibilities are only:
1. validate the platform's authentic signature;
2. store the raw event through the internal event contract;
3. normalize the event;
4. call the canonical conversion contract;
5. never invent attribution or commission values.

## Commercial truth rule

A successful HTTP response, deployment or database write is not evidence of monetization.
The operational proof remains:

`real demand -> real asset/distribution -> tracked redirect -> platform conversion -> real commission -> correct attribution -> learning`
