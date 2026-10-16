from core_v1.app.awin_invitations import InvitationSignal, triage_invitation


def test_invitation_never_means_joined():
    signal = InvitationSignal(advertiser="World Businesses for Sale",
                              commission_base_percent="20",
                              commission_bonus_percent="10", terms_available=True)
    result = triage_invitation(signal)
    assert result["membership"] == "unverified"
    assert result["publication_ready"] is False
    assert result["requires_external_consent"] is True
    assert result["commission_base_percent_claimed"] == "20"
    assert result["commission_bonus_percent_claimed"] == "10"


def test_joined_alone_is_not_publication_approval():
    signal = InvitationSignal(advertiser="Example")
    assert not triage_invitation(signal, joined=True)["publication_ready"]
    assert triage_invitation(signal, joined=True, terms_verified=True,
                             channel_permitted=True, tracking_verified=True)["publication_ready"]


def test_rejects_invalid_commission():
    signal = InvitationSignal(advertiser="Example", commission_base_percent="101")
    try:
        triage_invitation(signal)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid commission must be rejected")
