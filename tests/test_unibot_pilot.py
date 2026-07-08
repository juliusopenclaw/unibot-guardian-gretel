from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.pilot import (  # noqa: E402
    build_controlled_pilot_launch_gate,
    build_pilot_evidence_alignment,
    build_pilot_protocol,
    build_pilot_protocol_markdown,
)
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def complete_clearance_receipt() -> dict[str, bool]:
    return {
        "voluntary_participation_confirmed": True,
        "transparent_information_sheet_confirmed": True,
        "no_grade_or_exam_effect_confirmed": True,
        "synthetic_tasks_only_confirmed": True,
        "datenschutz_review_documented": True,
        "ethics_or_supervisor_review_documented": True,
        "withdrawal_redaction_process_tested": True,
        "authority_boundary_review_documented": True,
        "public_safety_review_passed": True,
    }


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
        self.assertEqual(protocol["controlled_pilot_launch_gate"]["status"], "blocked_pending_human_clearance")
        self.assertEqual(protocol["controlled_pilot_launch_gate"]["public_safety_status"], "pass")
        self.assertEqual(protocol["controlled_pilot_launch_gate"]["clearance_receipt_public_safety_status"], "pass")
        self.assertGreaterEqual(protocol["controlled_pilot_launch_gate"]["missing_clearance_count"], 9)
        self.assertFalse(protocol["controlled_pilot_launch_gate"]["real_pilot_started"])
        self.assertFalse(protocol["controlled_pilot_launch_gate"]["real_pilot_allowed_by_ai"])
        self.assertFalse(protocol["controlled_pilot_launch_gate"]["raw_receipt_returned"])
        self.assertIn(
            "datenschutz_review_required_before_real_pilot",
            protocol["controlled_pilot_launch_gate"]["required_human_gates"],
        )

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

    def test_controlled_pilot_launch_gate_accepts_complete_clearance_for_manual_review_only(self) -> None:
        protocol = build_pilot_protocol()
        gate = build_controlled_pilot_launch_gate(protocol, complete_clearance_receipt())

        self.assertEqual(gate["schema_version"], "unibot-controlled-pilot-launch-gate-v1")
        self.assertEqual(gate["status"], "ready_for_manual_pilot_go_review_not_started")
        self.assertEqual(gate["pilot_mode"], "voluntary_transparent_formative_synthetic_only")
        self.assertEqual(gate["missing_clearance_item_ids"], [])
        self.assertEqual(gate["missing_clearance_count"], 0)
        self.assertEqual(gate["failed_contract_ids"], [])
        self.assertTrue(all(gate["protection_contracts"].values()))
        self.assertTrue(gate["receipt_hash_present"])
        self.assertTrue(gate["receipt_hash"])
        self.assertFalse(gate["real_pilot_started"])
        self.assertFalse(gate["real_pilot_allowed_by_ai"])
        self.assertFalse(gate["raw_receipt_returned"])
        self.assertIn("manual review of a clearance receipt", gate["ready_for"])
        self.assertIn("real pilot start by AI", gate["not_ready_for"])

    def test_controlled_pilot_launch_gate_blocks_high_stakes_receipt_claims(self) -> None:
        protocol = build_pilot_protocol()
        receipt = complete_clearance_receipt()
        receipt["requested_mode"] = "official grading and exam clearance"
        gate = build_controlled_pilot_launch_gate(protocol, receipt)

        self.assertEqual(gate["status"], "blocked_claim_boundary")
        self.assertIn("exam clearance", gate["high_stakes_terms_found"])
        self.assertIn("official grading", gate["high_stakes_terms_found"])
        self.assertIn("high_stakes_modes_not_claimed", gate["failed_contract_ids"])
        self.assertFalse(gate["protection_contracts"]["high_stakes_modes_not_claimed"])
        self.assertFalse(gate["real_pilot_allowed_by_ai"])

    def test_controlled_pilot_launch_gate_blocks_unsafe_receipt_without_returning_raw_text(self) -> None:
        protocol = build_pilot_protocol()
        receipt = complete_clearance_receipt()
        unsafe_contact = "student" + "@example.com"
        receipt["private_contact"] = unsafe_contact
        gate = build_controlled_pilot_launch_gate(protocol, receipt)

        self.assertEqual(gate["status"], "blocked_receipt_public_safety")
        self.assertEqual(gate["clearance_receipt_public_safety_status"], "blocked")
        self.assertIn("receipt_public_safe", gate["failed_contract_ids"])
        self.assertFalse(gate["protection_contracts"]["receipt_public_safe"])
        self.assertFalse(gate["raw_receipt_returned"])
        self.assertNotIn(unsafe_contact, json.dumps(gate, ensure_ascii=False))

    def test_pilot_markdown_and_api_routes(self) -> None:
        markdown = build_pilot_protocol_markdown()

        self.assertIn("# UniBot Pilot Protocol", markdown)
        self.assertIn("Consent Checklist", markdown)
        self.assertIn("Ethics Review Triggers", markdown)
        self.assertIn("Evidence Alignment", markdown)
        self.assertIn("Controlled Pilot Launch Gate", markdown)
        self.assertIn("Real pilot allowed by AI: False", markdown)
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
