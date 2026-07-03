from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.pilot import build_pilot_evidence_alignment, build_pilot_protocol, build_pilot_protocol_markdown  # noqa: E402
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
        self.assertEqual(protocol["pilot_evidence_alignment"]["status"], "ready")
        self.assertEqual(protocol["pilot_evidence_alignment"]["public_safety_status"], "pass")
        self.assertEqual(protocol["pilot_evidence_alignment"]["missing_release_review_board_claim_check_ids"], [])
        self.assertEqual(protocol["pilot_evidence_alignment"]["missing_release_review_board_claim_human_gates"], [])

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

    def test_pilot_evidence_alignment_maps_protocol_to_review_gates(self) -> None:
        protocol = build_pilot_protocol()
        alignment = build_pilot_evidence_alignment(protocol)
        by_section = {section["section_id"]: section for section in alignment["sections"]}

        self.assertEqual(alignment["schema_version"], "unibot-pilot-evidence-alignment-v1")
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["missing_protocol_keys"], [])
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertIn("data_protection_screening", alignment["required_readiness_check_ids"])
        self.assertIn("release_runbook", alignment["required_readiness_check_ids"])
        self.assertIn("review_board_packet", alignment["required_readiness_check_ids"])
        self.assertIn("gretel_bachelor_thesis_package", alignment["required_readiness_check_ids"])
        self.assertIn("adaptive_task_plan", alignment["required_readiness_check_ids"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("ethics_or_supervisor_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        release_claim_contract = alignment["pilot_release_review_board_claim_contract"]
        self.assertEqual(
            release_claim_contract["expected_schema_version"],
            "unibot-pilot-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(
            release_claim_contract["required_release_runbook_schema_version"],
            "unibot-release-runbook-evidence-alignment-v1",
        )
        self.assertEqual(
            release_claim_contract["required_review_board_thesis_evaluation_schema_version"],
            "unibot-review-board-thesis-evaluation-claim-alignment-v1",
        )
        self.assertEqual(alignment["missing_release_review_board_claim_check_ids"], [])
        self.assertEqual(alignment["missing_release_review_board_claim_human_gates"], [])
        self.assertEqual(alignment["source_card_drift_contract"]["expected_check_id"], "source_card_drift_guard")
        self.assertEqual(alignment["data_protection_contract"]["expected_check_id"], "data_protection_screening")
        self.assertIn("gdpr-2016-679", by_section["data_management"]["source_card_ids"])
        self.assertIn("consent_items", by_section["consent_boundary"]["protocol_keys"])
        self.assertIn(
            "adaptive_task_plan",
            by_section["review_board_thesis_evaluation_pilot_boundary"]["readiness_check_ids"],
        )

    def test_pilot_markdown_and_api_routes(self) -> None:
        markdown = build_pilot_protocol_markdown()

        self.assertIn("# UniBot Pilot Protocol", markdown)
        self.assertIn("Consent Checklist", markdown)
        self.assertIn("Ethics Review Triggers", markdown)
        self.assertIn("Evidence Alignment", markdown)
        self.assertIn("Release review-board claim alignment: unibot-pilot-release-review-board-claim-alignment-v1", markdown)
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
