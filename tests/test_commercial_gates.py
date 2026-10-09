"""Static safety regression tests; no production database or secrets required."""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def route_function(route):
    for node in TREE.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for deco in node.decorator_list:
                if isinstance(deco, ast.Call) and deco.args and isinstance(deco.args[0], ast.Constant):
                    if deco.args[0].value == route:
                        return node
    return None


class CommercialGateTests(unittest.TestCase):
    def test_canonical_redirect_exists(self):
        self.assertIsNotNone(route_function("/go/offer/{offer_id}"))

    def test_canonical_redirect_requires_published_offer(self):
        node = route_function("/go/offer/{offer_id}")
        self.assertIsNotNone(node)
        body = ast.get_source_segment(SOURCE, node)
        self.assertIn('.eq("status", "published")', body)
        self.assertIn('evidence.get("terms_reviewed") is not True', body)
        self.assertIn('evidence.get("membership_status") != "approved"', body)
        self.assertIn('parsed.scheme != "https"', body)

    def test_public_offers_require_published_opportunity(self):
        node = route_function("/public/dores/{dor_id}/ofertas")
        self.assertIsNotNone(node)
        body = ast.get_source_segment(SOURCE, node)
        self.assertIn('.eq("status", "published")', body)
        self.assertIn('"b1_pain:" + str(dor_id)', body)
        self.assertNotIn('affiliate_url', body)

    def test_master_catalog_requires_auth(self):
        node = route_function("/master/catalogo/awin/resumo")
        self.assertIsNotNone(node)
        self.assertIn('validar_master(request)', ast.get_source_segment(SOURCE, node))

    def test_legacy_public_solution_route_does_not_publish_links(self):
        node = route_function("/public/dores/{dor_id}/solucoes")
        self.assertIsNotNone(node)
        body = ast.get_source_segment(SOURCE, node)
        self.assertNotIn('link_afiliado', body)
        self.assertIn('"data": []', body)


if __name__ == "__main__":
    unittest.main()
