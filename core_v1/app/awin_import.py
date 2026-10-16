"""Fail-closed Awin offer importer for the isolated Core.

Only verified merchant terms plus program membership/verified soft membership
can move offers to validated. No automated publishing or paid traffic.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable

from core_v1.app.awin import AwinOffer, eligibility_for_program


@dataclass(frozen=True)
class ImportSummary:
    discovered: int
    eligible: int
    candidates: int
    imported: int
    skipped: int


def import_offers(conn: Any, offers: Iterable[AwinOffer], programs: dict[str, dict[str, Any]],
                  *, reviewed_terms: set[str], verified_soft_memberships: set[str] | None = None,
                  dry_run: bool = True, schema: str = "robo_global_core") -> ImportSummary:
    if schema != "robo_global_core":
        raise ValueError("schema not allowed")
    soft = verified_soft_memberships or set()
    discovered = eligible = candidates = imported = skipped = 0
    seen: set[str] = set()
    with conn.cursor() as cur:
        for offer in offers:
            discovered += 1
            external_id = f"{offer.merchant_id}:{offer.product_id}"
            if external_id in seen:
                skipped += 1
                continue
            seen.add(external_id)
            program = programs.get(offer.merchant_id, {})
            eligibility = eligibility_for_program(
                program, has_feed=True,
                soft_membership_verified=offer.merchant_id in soft,
                terms_reviewed=offer.merchant_id in reviewed_terms,
            )
            status = "validated" if eligibility == "verified" else "candidate"
            if status == "validated":
                eligible += 1
            else:
                candidates += 1
            if dry_run:
                continue
            evidence = {
                "source": "awin_product_feed",
                "merchant_id": offer.merchant_id,
                "eligibility": eligibility,
                "membership_status": str(program.get("membershipStatus") or program.get("membership_status") or ""),
                "terms_reviewed": offer.merchant_id in reviewed_terms,
                "soft_membership_verified": offer.merchant_id in soft,
                "product_feed_record": offer.raw,
            }
            cur.execute(
                f"""insert into {schema}.offers
                (platform,external_product_id,name,affiliate_url,market,language,currency,price,
                 commission_type,evidence,status,tracking_strategy)
                values ('AWIN',%s,%s,%s,'BR','pt-BR',%s,%s,'unknown',%s::jsonb,%s,'none')
                on conflict (platform,external_product_id) where external_product_id is not null
                do update set name=excluded.name,affiliate_url=excluded.affiliate_url,
                currency=excluded.currency,price=excluded.price,evidence=excluded.evidence,
                status=case when {schema}.offers.status in ('active','paused') then {schema}.offers.status
                            else excluded.status end,
                updated_at=now()
                returning id""",
                (external_id, offer.name, offer.affiliate_url, offer.currency,
                 offer.price, json.dumps(evidence), status),
            )
            if cur.fetchone():
                imported += 1
    if not dry_run:
        conn.commit()
    return ImportSummary(discovered, eligible, candidates, imported, skipped)
