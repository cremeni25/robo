"""Deterministic triage of Awin invitation signals, without automatic consent.

An invitation is an opportunity to apply, never proof of a joined programme.
No email credentials, personal information, or commission promises are stored.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class InvitationSignal:
    advertiser: str
    source: str = "awin"
    invited: bool = True
    commission_base_percent: str | None = None
    commission_bonus_percent: str | None = None
    terms_available: bool = False


def triage_invitation(signal: InvitationSignal, *, joined: bool = False,
                      terms_verified: bool = False,
                      channel_permitted: bool = False,
                      tracking_verified: bool = False) -> dict:
    if not signal.advertiser.strip():
        raise ValueError("advertiser required")
    if signal.source.lower() != "awin":
        raise ValueError("unsupported invitation source")

    def percentage(raw: str | None) -> str | None:
        if raw is None:
            return None
        try:
            value = Decimal(raw)
        except (InvalidOperation, ValueError):
            raise ValueError("invalid commission percentage") from None
        if not value.is_finite() or value < 0 or value > 100:
            raise ValueError("commission percentage out of range")
        return str(value)

    base = percentage(signal.commission_base_percent)
    bonus = percentage(signal.commission_bonus_percent)
    publication_ready = bool(joined and terms_verified and channel_permitted and tracking_verified)
    return {
        "advertiser": signal.advertiser.strip(),
        "source": "awin",
        "invitation_received": signal.invited,
        "membership": "joined" if joined else "unverified",
        "commission_base_percent_claimed": base,
        "commission_bonus_percent_claimed": bonus,
        "terms_available": signal.terms_available,
        "terms_verified": terms_verified,
        "channel_permitted": channel_permitted,
        "tracking_verified": tracking_verified,
        "publication_ready": publication_ready,
        "requires_external_consent": not joined,
        "next_action": (
            "eligible_for_separate_offer_validation" if publication_ready else
            "verify_terms_channels_and_tracking" if joined else
            "verify_invitation_and_programme_membership"
        ),
    }
