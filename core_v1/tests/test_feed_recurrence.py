import pytest
from core_v1.app import awin_routes as routes


def test_recurring_import_normalizes_and_deduplicates_sources(monkeypatch):
    raw = 'https://productdata.awin.com/datafeed/key/example/adultcontent/0/columns/product name'
    monkeypatch.setenv('AWIN_FEED_URL', raw)
    monkeypatch.setenv('AWIN_FEED_URLS', __import__('json').dumps([raw, raw]))
    monkeypatch.setenv('DATABASE_URL', 'unused-test-database')
    requested = []

    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def geturl(self): return requested[-1]
        def read(self, size): return b'feed'

    def open_feed(request, timeout):
        requested.append(request.full_url)
        return Response()

    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): pass

    class Summary:
        discovered = candidates = imported = 2
        eligible = skipped = 0

    monkeypatch.setattr(routes, 'urlopen', open_feed)
    monkeypatch.setattr(routes, 'parse_feed', lambda *args, **kwargs: [object(), object()])
    monkeypatch.setattr(routes, 'connect', lambda *args: Connection())

    def import_candidates(conn, offers, membership, reviewed_terms, dry_run):
        assert membership == {} and reviewed_terms == set() and dry_run is False
        return Summary()

    monkeypatch.setattr(routes, 'import_offers', import_candidates)
    result = routes.import_multiple_feeds(routes.ImportRequest(dry_run=False))
    assert requested == ['https://productdata.awin.com/datafeed/key/example/columns/product%20name']
    assert result['successful_sources'] == 1 and result['imported'] == 2
    assert result['publication_enabled'] is False


@pytest.mark.parametrize('url', ['http://productdata.awin.com/feed', 'https://evil.example/feed',
                                 'https://user:pass@productdata.awin.com/feed'])
def test_feed_host_validation(url):
    with pytest.raises(ValueError):
        routes._normalized_feed_url(url)


def test_feed_normalization_preserves_existing_escapes_and_query():
    url = 'https://productdata.awin.com/feed/a%20b?format=csv&key=example'
    assert routes._normalized_feed_url(url) == url
