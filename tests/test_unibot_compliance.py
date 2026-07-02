from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.compliance import build_compliance_matrix, build_compliance_matrix_markdown  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.source_cards import get_source_card  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotComplianceTests(unittest.TestCase):
    def test_compliance_matrix_links_rules_controls_and_evidence(self) -> None:
        matrix = build_compliance_matrix()
        requirement_ids = {item["requirement_id"] for item in matrix["requirements"]}

        self.assertEqual(matrix["schema_version"], "unibot-compliance-matrix-v1")
        self.assertEqual(matrix["status"], "draft_ready_for_authority_review")
        self.assertEqual(matrix["exam_deployment_status"], "not_cleared")
        self.assertEqual(matrix["missing_source_card_ids"], [])
        self.assertGreaterEqual(matrix["requirement_count"], 9)
        self.assertIn("exam-clearance-boundary", requirement_ids)
        self.assertIn("accessibility-neutrality", requirement_ids)
        self.assertIn("data-minimisation-and-public-safety", requirement_ids)
        self.assertIn("browser-overlay-limit", requirement_ids)

        for requirement in matrix["requirements"]:
            self.assertTrue(requirement["implemented_controls"], requirement["requirement_id"])
            self.assertTrue(requirement["verification_evidence"], requirement["requirement_id"])
            self.assertTrue(requirement["blocked_use"], requirement["requirement_id"])

    def test_all_referenced_source_cards_exist(self) -> None:
        matrix = build_compliance_matrix()

        for requirement in matrix["requirements"]:
            for source_id in requirement["source_card_ids"]:
                self.assertIsNotNone(get_source_card(source_id), source_id)

    def test_compliance_matrix_public_safe_and_boundary_language(self) -> None:
        payload = json.dumps(build_compliance_matrix(), ensure_ascii=False)
        lowered = payload.lower()

        self.assertEqual(scan_text(payload, "compliance-matrix")["status"], "pass")
        self.assertIn("not legal advice", lowered)
        self.assertIn("not exam clearance", lowered)
        self.assertIn("not_cleared", payload)
        self.assertNotIn("raw_external_ai_output", payload)
        self.assertNotIn("solution_key", payload)
        self.assertNotIn("official_grade", payload)

    def test_markdown_and_api_routes(self) -> None:
        markdown = build_compliance_matrix_markdown()

        self.assertIn("# UniBot Compliance Matrix", markdown)
        self.assertIn("exam-clearance-boundary", markdown)
        self.assertIn("accessibility-neutrality", markdown)
        self.assertIn("Missing source cards: none", markdown)

        status, matrix = route_request("/api/unibot/compliance-matrix", {})
        self.assertEqual(status, 200)
        self.assertEqual(matrix["schema_version"], "unibot-compliance-matrix-v1")

        status, response = route_request("/api/unibot/compliance-matrix-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("Boundary:", response["markdown"])


if __name__ == "__main__":
    unittest.main()
