from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.decision_request import (  # noqa: E402
    build_stakeholder_decision_request,
    build_stakeholder_decision_request_markdown,
    validate_decision_request_receipt,
)
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_request_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Videos").mkdir(parents=True)
    (root / "Week 1" / "lecture.pdf").write_bytes(b"%PDF-1.4\nfixture")
    (root / "Videos" / "lecture.mov").write_bytes(b"video")


class UniBotDecisionRequestTests(unittest.TestCase):
    def test_rights_privacy_request_is_public_safe_and_not_sent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_request_fixture(fixture_root)

            packet = build_stakeholder_decision_request(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
            )
            payload = json.dumps(packet, ensure_ascii=False)

            self.assertEqual(packet["schema_version"], "unibot-stakeholder-decision-request-v1")
            self.assertEqual(packet["artifact_type"], "unibot_stakeholder_decision_request")
            self.assertEqual(packet["status"], "ready_for_manual_review_not_sent")
            self.assertEqual(packet["lane_id"], "rights_privacy_local_extraction")
            self.assertEqual(packet["exam_deployment_status"], "not_cleared")
            self.assertEqual(packet["public_safety_status"], "pass")
            self.assertTrue(packet["request_id"])
            self.assertFalse(packet["receipt_template"]["tool_sent_message"])
            self.assertEqual(packet["receipt_template"]["manual_submission_status"], "draft_not_sent")
            self.assertIn("cloud processing", json.dumps(packet["human_review_checklist"], ensure_ascii=False))
            self.assertNotIn(str(fixture_root), payload)
            self.assertEqual(scan_text(payload, "decision-request-test")["status"], "pass")

    def test_exam_request_keeps_exam_not_cleared(self) -> None:
        packet = build_stakeholder_decision_request(lane_id="exam_gateway_authority_clearance")

        self.assertEqual(packet["status"], "ready_for_manual_review_not_sent")
        self.assertEqual(packet["lane_id"], "exam_gateway_authority_clearance")
        self.assertEqual(packet["exam_deployment_status"], "not_cleared")
        checklist = " ".join(packet["human_review_checklist"])
        self.assertIn("exam_deployment_status remains not_cleared", checklist)
        self.assertIn("real-world reminder, not a technical blocker", checklist)
        self.assertIn("exam use is already cleared", packet["must_not_claim"])

    def test_unsupported_lane_is_blocked(self) -> None:
        packet = build_stakeholder_decision_request(lane_id="unknown_lane")

        self.assertEqual(packet["status"], "blocked_unsupported_decision_lane")
        self.assertEqual(packet["public_safety_status"], "pass")
        self.assertIn("rights_privacy_local_extraction", packet["available_lane_ids"])

    def test_decision_request_markdown_is_review_ready_and_public_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_request_fixture(fixture_root)

            markdown = build_stakeholder_decision_request_markdown(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
            )

            self.assertIn("# UniBot Stakeholder Decision Request", markdown)
            self.assertIn("Exam deployment: `not_cleared`", markdown)
            self.assertIn("## Human Review Checklist", markdown)
            self.assertIn("## Manual Receipt Template", markdown)
            self.assertIn("tool_sent_message", markdown)
            self.assertIn("does not claim approval", markdown)
            self.assertNotIn(str(fixture_root), markdown)
            self.assertEqual(scan_text(markdown, "decision-request-markdown-test")["status"], "pass")

    def test_receipt_validation_hashes_reference_and_blocks_tool_sent_message(self) -> None:
        packet = build_stakeholder_decision_request()
        receipt = dict(packet["receipt_template"])
        receipt.update(
            {
                "manual_submission_status": "sent_for_human_review",
                "channel": "manual university mail portal",
                "submission_reference": "synthetic manually sent request reference",
            }
        )

        validation = validate_decision_request_receipt(receipt)
        payload = json.dumps(validation, ensure_ascii=False)

        self.assertEqual(validation["status"], "ok_manual_request_receipt")
        self.assertEqual(validation["receipt_effect"], "manual_request_sent_for_rights_privacy_local_extraction_no_decision_record_yet")
        self.assertTrue(validation["submission_reference_hash"])
        self.assertFalse(validation["raw_submission_reference_stored"])
        self.assertNotIn("synthetic manually sent request reference", payload)
        self.assertEqual(validation["public_safety_status"], "pass")

        invalid = dict(receipt)
        invalid["tool_sent_message"] = True
        blocked = validate_decision_request_receipt(invalid)
        self.assertEqual(blocked["status"], "blocked")
        self.assertIn("tool_must_not_send_stakeholder_request", blocked["issues"])

    def test_decision_request_api_routes(self) -> None:
        status, packet = route_request(
            "/api/unibot/stakeholder/decision-request",
            {"lane_id": "rights_privacy_local_extraction"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(packet["artifact_type"], "unibot_stakeholder_decision_request")

        status, response = route_request(
            "/api/unibot/stakeholder/decision-request-markdown",
            {"lane_id": "rights_privacy_local_extraction"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("# UniBot Stakeholder Decision Request", response["markdown"])

        receipt = dict(packet["receipt_template"])
        receipt.update(
            {
                "manual_submission_status": "sent_for_human_review",
                "channel": "manual review channel",
                "submission_reference": "synthetic manual receipt",
            }
        )
        status, validation = route_request(
            "/api/unibot/stakeholder/decision-request/validate-receipt",
            {"receipt": receipt},
        )
        self.assertEqual(status, 200)
        self.assertEqual(validation["status"], "ok_manual_request_receipt")


if __name__ == "__main__":
    unittest.main()
