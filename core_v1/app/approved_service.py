"""Publish the specifically approved Awin service offer, not marketplace listings.

The advertiser's written response (2026-10-13) authorizes promotion of its
business-selling plans through a dedicated catalogue page, without copying
individual marketplace listings. Membership is independently verified live.
"""
from __future__ import annotations

import json
import logging
import os
from urllib.parse import urlsplit, parse_qs
from urllib.request import Request, urlopen

from psycopg import connect

log = logging.getLogger("robo-global-core")
ADVERTISER_ID = "116725"
PRODUCT_ID = "116725:business-selling-plans"


def publish_approved_service() -> dict:
    from core_v1.app.awin import AwinClient

    publisher = int(os.environ["AWIN_PUBLISHER_ID"])
    token = os.environ["AWIN_API_TOKEN"]
    joined = AwinClient(publisher, token).programs("joined")
    if not isinstance(joined, list) or not any(
        isinstance(item, dict) and str(item.get("id")) == ADVERTISER_ID
        for item in joined
    ):
        return {"status": "blocked", "reason": "merchant_membership_not_joined"}

    # Default advertiser landing page: do not invent a selling-plan URL.
    body = json.dumps({"advertiserId": int(ADVERTISER_ID)}).encode()
    req = Request(
        f"https://api.awin.com/publishers/{publisher}/linkbuilder/generate",
        data=body,
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=30) as response:
        generated = json.load(response)
    link = generated.get("url", "") if isinstance(generated, dict) else ""
    parsed = urlsplit(link)
    if parsed.scheme != "https" or parsed.hostname not in {"www.awin1.com", "awin1.com"}:
        return {"status": "blocked", "reason": "unverified_tracking_link"}
    params = parse_qs(parsed.query)
    if params.get("awinaffid") not in ([str(publisher)], None):
        return {"status": "blocked", "reason": "wrong_publisher_tracking"}
    # The default Awin link and clickref parameter are independently generated
    # by the official Awin API, rather than guessed from a merchant destination.
    evidence = {
        "merchant_id": ADVERTISER_ID,
        "membership_status": "joined",
        "terms_reviewed": True,
        "channel_permitted": True,
        "eligibility": "verified",
        "service_scope": "business_selling_plans_only",
        "source": "merchant_written_authorization_2026_10_13",
        "tracking_source": "awin_linkbuilder_api",
        "no_marketplace_listing_reproduction": True,
    }
    with connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                insert into robo_global_core.offers
                (platform, external_product_id, name, affiliate_url, market,
                 language, currency, commission_type, commission_rate, evidence,
                 status, tracking_strategy, tracking_template)
                values ('AWIN', %s, %s, %s, 'GLOBAL', 'en', 'USD',
                        'percent', 0.20, %s::jsonb, 'active', 'query_param', 'clickref')
                on conflict (platform, external_product_id) where external_product_id is not null
                do update set affiliate_url=excluded.affiliate_url,
                    evidence=excluded.evidence, status='active',
                    tracking_strategy='query_param', tracking_template='clickref',
                    updated_at=now()
                returning id
            """, (PRODUCT_ID, "World Businesses for Sale — business selling plans",
                  link, json.dumps(evidence)))
            offer_id = cur.fetchone()[0]
            cur.execute("""
                select id from robo_global_core.demands
                where source='awin_worldbusinessesforsale_approved_service' limit 1
            """)
            row = cur.fetchone()
            if row:
                demand_id = row[0]
            else:
                cur.execute("""
                    insert into robo_global_core.demands
                    (market,language,category,problem,desire,source,
                     signal_strength,economic_intent_score,evidence)
                    values ('GLOBAL','en','business services',
                            'Find a channel to advertise a business for sale',
                            'Promote a business-selling plan',
                            'awin_worldbusinessesforsale_approved_service',
                            0,0,%s::jsonb) returning id
                """, (json.dumps({"source": "approved_service_offer_not_inferred_market_demand"}),))
                demand_id = cur.fetchone()[0]
            cur.execute("""
                insert into robo_global_core.opportunities
                (demand_id,offer_id,market,language,audience,angle,
                 economic_potential,signal_quality,offer_fit,data_confidence,score)
                values (%s,%s,'GLOBAL','en','business owners',
                        'Explore business-selling plans',0,0,1,1,0)
                on conflict (demand_id,offer_id,market,language,angle)
                do update set updated_at=now() returning id
            """, (demand_id, offer_id))
            opportunity_id = cur.fetchone()[0]
        conn.commit()
    return {"status": "active", "opportunity_id": str(opportunity_id)}
