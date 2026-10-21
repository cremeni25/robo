import pytest

from core_v1.app.awin_import import sync_candidate_memberships


@pytest.mark.parametrize("payload", [None, {}, {"data": []}, [{}], [{"id": None}], [{"id": "invalid"}]])
def test_invalid_official_response_cannot_touch_database(payload):
    # No connection is provided: validation must reject the response before any
    # cursor, update, or commit can be attempted.
    with pytest.raises(ValueError, match="invalid joined-programmes"):
        sync_candidate_memberships(None, payload)
