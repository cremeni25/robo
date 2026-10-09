import importlib.util
import io
import json
import pathlib
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "awin_discover.py"
SPEC = importlib.util.spec_from_file_location("awin_discover", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, *args):
        return self.data.read(*args)

    def __init__(self, records):
        self.data = io.BytesIO(json.dumps(records).encode())


class DiscoveryTests(unittest.TestCase):
    def test_missing_credentials_is_safe(self):
        self.assertEqual(MODULE.discover(environment={})["status"], "configuration_required")

    def test_discovery_counts_membership_without_approving(self):
        def fake_fetch(request, timeout):
            self.assertIn("Bearer test-token", request.get_header("Authorization"))
            return FakeResponse([
                {"id": 81383, "relationship": "joined"},
                {"id": 17, "relationship": "pending"},
            ])

        result = MODULE.discover(fake_fetch, {
            "AWIN_API_TOKEN": "test-token", "AWIN_PUBLISHER_ID": "3117886"
        })
        self.assertEqual(result["advertiser_count"], 2)
        self.assertEqual(result["relationship_counts"], {"joined": 1, "pending": 1})
        self.assertEqual(result["offers_published"], 0)
        self.assertFalse(result["commercial_approval_automated"])


if __name__ == "__main__":
    unittest.main()
