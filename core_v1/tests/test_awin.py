import gzip
import unittest
from decimal import Decimal

from core_v1.app.awin import AwinError, eligibility_for_program, parse_feed
from core_v1.app.awin_import import import_offers


class FakeCursor:
    def __init__(self):
        self.statements = []
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute(self, sql, args): self.statements.append((sql, args))
    def fetchone(self): return {"id": "test-id"}


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.commits = 0
    def cursor(self): return self.cursor_instance
    def commit(self): self.commits += 1


class AwinTests(unittest.TestCase):
    def setUp(self):
        self.csv = b"merchant_id,aw_product_id,product_name,aw_deep_link,search_price,currency\n106763,123,Vacuum,https://www.awin1.com/cread.php?x=1,99.90,BRL\n"

    def test_gzip_csv_and_default_unverified(self):
        offers = parse_feed(gzip.compress(self.csv))
        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0].price, Decimal("99.90"))
        self.assertFalse(offers[0].publishable)

    def test_eligibility_requires_channel_and_terms(self):
        program = {"membershipStatus": "joined"}
        self.assertEqual(eligibility_for_program(program, terms_reviewed=True), "channel_unverified")
        program["channel_permitted"] = True
        self.assertEqual(eligibility_for_program(program, terms_reviewed=True), "verified")

    def test_soft_membership_must_be_explicit(self):
        program = {"membershipStatus": "notjoined", "channel_permitted": True}
        self.assertEqual(eligibility_for_program(program, has_feed=True, soft_membership_verified=True, terms_reviewed=True), "not_authorized")
        program["soft_membership_allowed"] = True
        self.assertEqual(eligibility_for_program(program, has_feed=True, soft_membership_verified=True, terms_reviewed=True), "verified")

    def test_import_dry_run_has_no_writes(self):
        conn = FakeConnection()
        summary = import_offers(conn, parse_feed(gzip.compress(self.csv)), {}, reviewed_terms=set())
        self.assertEqual((summary.discovered, summary.candidates, summary.imported), (1, 1, 0))
        self.assertEqual(conn.cursor_instance.statements, [])
        self.assertEqual(conn.commits, 0)

    def test_import_candidate_writes_without_activation(self):
        conn = FakeConnection()
        summary = import_offers(conn, parse_feed(gzip.compress(self.csv)), {}, reviewed_terms=set(), dry_run=False)
        self.assertEqual(summary.imported, 1)
        self.assertEqual(conn.commits, 1)
        self.assertEqual(conn.cursor_instance.statements[0][1][-1], "candidate")


if __name__ == "__main__":
    unittest.main()
