from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.pilot import build_pilot_protocol, build_pilot_protocol_markdown  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotPilotProtocolTests(unittest.TestCase):
    def test_pilot_protocol_contains_consent_data_and_ethics_sections(self) -> None:
        protocol = build_pilot_protocol()

        self.assertEqual(protocol["schema_version"], "unibot-pilot-protocol-v1")
        self.assertEqual(protocol["status"], "draft_not_ethics_or_authority_cleared")
        self.assertEqual(protocol["exam_deployment_status"], "not_cleared")
        self.assertGreaterEqual(len(protocol["consent_items"]), 7)
        self.assertGreaterEqual(len(protocol["ethics_review_triggers"]), 6)
        self.assertIn("data_management_plan", protocol)
        self.assertIn("session_flow", protocol)
        self.assertEqual(protocol["readiness_gates"]["redteam_status"], "pass")
        self.assertEqual(protocol["readiness_gates"]["compliance_status"], "draft_ready_for_authority_review")

    def test_pilot_protocol_boundaries_exclude_high_stakes_and_private_data(self) -> None:
        protocol = build_pilot_protocol()
        payload = json.dumps(protocol, ensure_ascii=False)
        excluded = protocol["participant_scope"]["excluded"]

        self.assertIn("real exams", excluded)
        self.assertIn("graded assignments", excluded)
        self.assertIn("private course files", excluded)
        self.assertIn("medical or accommodation personal data", protocol["data_management_plan"]["excluded_data"])
        self.assertIn("grades", protocol["data_management_plan"]["excluded_data"])
        self.assertNotIn("official_grade", payload)
        self.assertNotIn("solution_key", payload)
        self.assertNotIn("raw_external_ai_output", payload)

    def test_pilot_protocol_public_safe(self) -> None:
        payload = json.dumps(build_pilot_protocol(), ensure_ascii=False)
        lowered = payload.lower()

        self.assertEqual(scan_text(payload, "pilot-protocol")["status"], "pass")
        self.assertIn("not ethics clearance", lowered)
        self.assertIn("not exam clearance", lowered)
        self.assertNotIn("student@example", lowered)
        self.assertNotIn("sk-test", lowered)

    def test_pilot_markdown_and_api_routes(self) -> None:
        markdown = build_pilot_protocol_markdown()

        self.assertIn("# UniBot Pilot Protocol", markdown)
        self.assertIn("Consent Checklist", markdown)
        self.assertIn("Ethics Review Triggers", markdown)
        self.assertIn("Exam deployment: not_cleared", markdown)

        status, protocol = route_request("/api/unibot/pilot-protocol", {})
        self.assertEqual(status, 200)
        self.assertEqual(protocol["schema_version"], "unibot-pilot-protocol-v1")

        status, response = route_request("/api/unibot/pilot-protocol-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("Data Management", response["markdown"])


if __name__ == "__main__":
    unittest.main()
