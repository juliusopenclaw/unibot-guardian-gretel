from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402
from unibot.submission import (  # noqa: E402
    build_stakeholder_submission_bundle,
    build_stakeholder_submission_markdown,
    build_stakeholder_submission_release_claim_alignment,
    stakeholder_submission_evidence_summary_hash,
    stakeholder_submission_lanes_hash,
    synthetic_submission_workspace_card,
)


def write_submission_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Videos").mkdir(parents=True)
    (root / "Week 1" / "lecture.pdf").write_bytes(b"%PDF-1.4\nfixture")
    (root / "Week 1" / "pandas_intro.md").write_text("pandas DataFrame boxplot", encoding="utf-8")
    (root / "Videos" / "lecture.mov").write_bytes(b"video")


class UniBotStakeholderSubmissionTests(unittest.TestCase):
    def test_submission_bundle_covers_remaining_decision_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_submission_fixture(fixture_root)

            bundle = build_stakeholder_submission_bundle(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
            )
            payload = json.dumps(bundle, ensure_ascii=False)
            lane_ids = {lane["lane_id"] for lane in bundle["decision_lanes"]}

            self.assertEqual(bundle["schema_version"], "unibot-stakeholder-submission-v1")
            self.assertEqual(bundle["artifact_type"], "unibot_stakeholder_submission_bundle")
            self.assertEqual(bundle["status"], "ready_for_human_submission_not_sent")
            self.assertEqual(bundle["exam_deployment_status"], "not_cleared")
            self.assertEqual(bundle["public_safety_status"], "pass")
            self.assertEqual(bundle["release_claim_alignment"]["status"], "ready")
            self.assertEqual(bundle["release_claim_alignment"]["public_safety_status"], "pass")
            self.assertEqual(lane_ids, {"rights_privacy_local_extraction", "exam_gateway_authority_clearance"})
            self.assertIn("does not send messages", bundle["submission_boundary"])
            self.assertIn("rights/privacy decision before local OCR/transcription", bundle["open_external_gates"])
            self.assertNotIn(str(fixture_root), payload)
            self.assertEqual(scan_text(payload, "submission-bundle-test")["status"], "pass")

    def test_submission_release_claim_alignment_links_review_and_human_gates(self) -> None:
        bundle = build_stakeholder_submission_bundle()
        alignment = bundle["release_claim_alignment"]

        self.assertEqual(
            alignment["schema_version"],
            "unibot-stakeholder-submission-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("stakeholder_submission_bundle", alignment["required_readiness_check_ids"])
        self.assertIn("review_board_packet", alignment["required_readiness_check_ids"])
        self.assertIn("authority_handoff", alignment["required_readiness_check_ids"])
        self.assertIn("data_protection_screening", alignment["required_readiness_check_ids"])
        self.assertIn("compliance_matrix", alignment["required_readiness_check_ids"])
        self.assertIn("source_card_drift_guard", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("public_safety_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertIn("automatic submission", alignment["blocked_claims"])
        self.assertIn("exam clearance", alignment["blocked_claims"])
        self.assertIn("public raw course text release", alignment["blocked_claims"])
        self.assertTrue(alignment["contracts"]["workspace_card_submission_lane_gate_linked"])
        self.assertEqual(alignment["workspace_card_status"], "python_exam_local_cycle_operator_workspace_card_ready")
        self.assertEqual(alignment["workspace_card_selected_skill_tag"], "pandas")
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertTrue(alignment["workspace_card_submission_lane_gate_linked"])

    def test_submission_hash_helpers_link_lanes_and_evidence_summary(self) -> None:
        bundle = build_stakeholder_submission_bundle()

        self.assertTrue(stakeholder_submission_lanes_hash(bundle))
        self.assertTrue(stakeholder_submission_evidence_summary_hash(bundle))
        self.assertNotEqual(stakeholder_submission_lanes_hash(bundle), stakeholder_submission_evidence_summary_hash(bundle))

    def test_submission_release_claim_alignment_rejects_unlinked_workspace_card_hashes(self) -> None:
        bundle = build_stakeholder_submission_bundle()
        card = synthetic_submission_workspace_card()
        card["workspace_card_summary"]["checkpoint_hash"] = "wrong-lane-hash"
        card["workspace_card_summary"]["task_hash"] = "wrong-evidence-hash"

        alignment = build_stakeholder_submission_release_claim_alignment(bundle, card)

        self.assertEqual(alignment["status"], "needs_review")
        self.assertFalse(alignment["workspace_card_submission_lane_gate_linked"])
        self.assertIn("workspace_card_submission_lane_gate_linked", alignment["failed_contract_ids"])

    def test_submission_release_claim_alignment_blocks_send_or_clearance_claims(self) -> None:
        bundle = build_stakeholder_submission_bundle()
        bundle["status"] = "sent"
        bundle["exam_deployment_status"] = "cleared"
        bundle["submission_boundary"] = "Submission was sent and approved."
        bundle["open_external_gates"] = []

        alignment = build_stakeholder_submission_release_claim_alignment(bundle)

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("bundle_prepares_human_submission_not_sent", alignment["failed_contract_ids"])
        self.assertIn("exam_deployment_not_cleared", alignment["failed_contract_ids"])
        self.assertIn("submission_boundary_blocks_send_approval_legal_exam", alignment["failed_contract_ids"])
        self.assertIn("open_external_gates_explicit", alignment["failed_contract_ids"])

    def test_submission_lanes_have_validators_and_templates(self) -> None:
        bundle = build_stakeholder_submission_bundle()
        lanes = {lane["lane_id"]: lane for lane in bundle["decision_lanes"]}
        extraction = lanes["rights_privacy_local_extraction"]
        exam = lanes["exam_gateway_authority_clearance"]

        self.assertEqual(extraction["validator_endpoint"], "/api/unibot/course/extraction-decision/validate")
        self.assertEqual(extraction["follow_up_endpoint_if_valid"], "/api/unibot/course/extraction-operator-packet")
        self.assertIn("Datenschutz", extraction["reviewer_roles"])
        self.assertFalse(extraction["minimum_record_template"]["cloud_processing_allowed"])
        self.assertFalse(extraction["minimum_record_template"]["raw_text_public_release_allowed"])
        self.assertIn("exam deployment is authorized", extraction["must_not_claim"])

        self.assertEqual(exam["validator_endpoint"], "/api/unibot/institutional-clearance/validate")
        self.assertEqual(exam["exam_deployment_status"], "not_cleared")
        self.assertIn("Pruefungsamt", exam["reviewer_roles"])
        self.assertEqual(exam["minimum_record_template"]["help_levels_allowed"], ["A0", "A1", "A2"])
        self.assertIn("exam use is already cleared", exam["must_not_claim"])

    def test_submission_markdown_and_api_routes(self) -> None:
        markdown = build_stakeholder_submission_markdown()
        self.assertIn("# UniBot Stakeholder Submission Bundle", markdown)
        self.assertIn("Exam deployment: not_cleared", markdown)
        self.assertIn("## Release Claim Alignment", markdown)
        self.assertIn("Status: ready", markdown)
        self.assertIn("Local OCR/transcription", markdown)
        self.assertIn("Controlled A0-A2 exam gateway", markdown)

        status, bundle = route_request("/api/unibot/stakeholder/submission-bundle", {})
        self.assertEqual(status, 200)
        self.assertEqual(bundle["artifact_type"], "unibot_stakeholder_submission_bundle")
        self.assertEqual(bundle["release_claim_alignment"]["status"], "ready")

        status, response = route_request("/api/unibot/stakeholder/submission-bundle-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("Open External Gates", response["markdown"])


if __name__ == "__main__":
    unittest.main()
