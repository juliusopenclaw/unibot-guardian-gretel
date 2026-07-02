from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.privacy import build_data_protection_screening, build_data_protection_screening_markdown  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotDataProtectionTests(unittest.TestCase):
    def test_screening_contains_processing_risks_and_open_decisions(self) -> None:
        screening = build_data_protection_screening()
        activity_ids = {item["activity_id"] for item in screening["processing_activities"]}
        risk_ids = {item["risk_id"] for item in screening["risk_register"]}

        self.assertEqual(screening["schema_version"], "unibot-data-protection-screening-v1")
        self.assertEqual(screening["status"], "draft_for_datenschutz_review")
        self.assertEqual(screening["exam_deployment_status"], "not_cleared")
        self.assertIn("prompt_card_generation", activity_ids)
        self.assertIn("external_ai_postfilter", activity_ids)
        self.assertIn("help_ledger", activity_ids)
        self.assertIn("synthetic_pilot_records", activity_ids)
        self.assertIn("exam_controlled_mode", activity_ids)
        self.assertIn("private_data_entry", risk_ids)
        self.assertIn("external_tool_transfer", risk_ids)
        self.assertGreaterEqual(len(screening["open_decisions_for_datenschutz"]), 6)

    def test_screening_requires_review_before_real_pilot(self) -> None:
        screening = build_data_protection_screening()
        gates = screening["review_gates"]

        self.assertTrue(gates["datenschutz_review_required_before_real_pilot"])
        self.assertTrue(gates["ethics_or_supervisor_review_required_before_real_pilot"])
        self.assertTrue(gates["authority_review_required_before_exam_context"])
        self.assertEqual(gates["exam_deployment_status"], "not_cleared")
        self.assertEqual(screening["pilot_alignment"]["compliance_status"], "draft_ready_for_authority_review")

    def test_screening_public_safe_and_no_approval_language(self) -> None:
        payload = json.dumps(build_data_protection_screening(), ensure_ascii=False)
        lowered = payload.lower()

        self.assertEqual(scan_text(payload, "data-protection-screening")["status"], "pass")
        self.assertIn("not legal advice", lowered)
        self.assertIn("not datenschutz approval", lowered)
        self.assertNotIn("raw_external_ai_output", payload)
        self.assertNotIn("solution_key", payload)
        self.assertNotIn("official_grade", payload)
        self.assertNotIn("approved for exam", lowered)

    def test_markdown_and_api_routes(self) -> None:
        markdown = build_data_protection_screening_markdown()

        self.assertIn("# UniBot Data Protection Screening", markdown)
        self.assertIn("Processing Activities", markdown)
        self.assertIn("Risk Register", markdown)
        self.assertIn("Open Decisions For Datenschutz", markdown)

        status, screening = route_request("/api/unibot/data-protection-screening", {})
        self.assertEqual(status, 200)
        self.assertEqual(screening["schema_version"], "unibot-data-protection-screening-v1")

        status, response = route_request("/api/unibot/data-protection-screening-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("Boundary:", response["markdown"])


if __name__ == "__main__":
    unittest.main()
