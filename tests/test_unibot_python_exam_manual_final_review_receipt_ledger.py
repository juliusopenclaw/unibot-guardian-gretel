from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_manual_final_review_handoff import build_python_exam_manual_final_review_handoff
from unibot.python_exam_manual_final_review_receipt_ledger import (
    build_python_exam_manual_final_review_receipt_ledger,
)
from unibot.server import route_request

from tests.test_unibot_python_exam_manual_final_review_handoff import final_review_handoff_inputs


def final_review_receipt_ledger_inputs(
    temp_dir: str,
    *,
    confirmed: bool,
    mode: str = "missing",
) -> tuple[dict, dict, dict, dict]:
    draft, reviewer, queue, gate = final_review_handoff_inputs(temp_dir, confirmed=confirmed, mode=mode)
    handoff = build_python_exam_manual_final_review_handoff(
        python_exam_manual_archive_decision_draft=draft,
        python_exam_manual_export_reviewer_packet=reviewer,
        python_exam_manual_export_review_queue=queue,
        python_exam_manual_review_export_authorization_gate=gate,
        selected_skill_tag="python_lists",
    )
    return handoff, draft, reviewer, queue


class UniBotPythonExamManualFinalReviewReceiptLedgerTests(unittest.TestCase):
    def test_final_review_receipt_ledger_keeps_open_without_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            handoff, draft, reviewer, queue = final_review_receipt_ledger_inputs(temp_dir, confirmed=False)
            ledger = build_python_exam_manual_final_review_receipt_ledger(
                python_exam_manual_final_review_handoff=handoff,
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(ledger, ensure_ascii=False)
            summary = ledger["final_review_receipt_ledger_summary"]
            body = ledger["final_review_receipt_ledger_body"]

            self.assertEqual(ledger["artifact_type"], "python_exam_manual_final_review_receipt_ledger")
            self.assertEqual(ledger["status"], "python_exam_manual_final_review_receipt_ledger_ready")
            self.assertEqual(ledger["exam_deployment_status"], "not_cleared")
            self.assertEqual(ledger["final_review_receipt_ledger_recommendation"], "keep_final_ledger_open")
            self.assertEqual(summary["final_review_handoff_recommendation"], "keep_final_handoff_open")
            self.assertEqual(summary["archive_decision_draft_recommendation"], "keep_archive_decision_draft_open")
            self.assertEqual(summary["reviewer_packet_recommendation"], "keep_reviewer_packet_open")
            self.assertEqual(summary["queue_recommendation"], "keep_queue_open")
            self.assertTrue(summary["final_review_handoff_hash"])
            self.assertTrue(summary["archive_decision_draft_hash"])
            self.assertTrue(summary["reviewer_packet_hash"])
            self.assertTrue(summary["queue_hash"])
            self.assertTrue(summary["export_manifest_hash"])
            self.assertTrue(summary["authorization_gate_hash"])
            self.assertTrue(body["final_review_receipt_ledger_hash"])
            self.assertEqual(summary["ledger_event_count"], 5)
            self.assertEqual(len(summary["ledger_event_hashes"]), 5)
            self.assertFalse(ledger["export_created"])
            self.assertFalse(ledger["export_authorized"])
            self.assertFalse(ledger["archive_created"])
            self.assertFalse(ledger["submission_started"])
            self.assertTrue(ledger["manual_final_review_receipt_ledger_receipt"]["not_cleared_receipt"])
            self.assertTrue(ledger["dry_run_default"])
            self.assertFalse(ledger["local_writes_requested"])
            self.assertFalse(ledger["local_execution_started"])
            for flag in [
                "raw_query_returned",
                "raw_text_returned",
                "raw_cell_returned",
                "raw_notebook_returned",
                "notebook_code_returned",
                "local_paths_returned",
                "values_returned",
                "solutions_returned",
                "final_interpretations_returned",
                "score_returned",
                "percentage_returned",
                "ranking_returned",
                "grade_returned",
                "automatic_grading_started",
                "proctoring_started",
                "ai_detection_started",
                "exam_clearance_claimed",
            ]:
                self.assertFalse(ledger[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-manual-final-review-receipt-ledger")["status"], "pass")
            self.assertEqual(ledger["public_safety_status"], "pass")

    def test_final_review_receipt_ledger_requests_hash_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            handoff, draft, reviewer, queue = final_review_receipt_ledger_inputs(temp_dir, confirmed=True)
            ledger = build_python_exam_manual_final_review_receipt_ledger(
                python_exam_manual_final_review_handoff=handoff,
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(ledger["final_review_receipt_ledger_recommendation"], "request_hash_completion")
            self.assertIn("notebook_checkpoint_hash", ledger["final_review_receipt_ledger_summary"]["missing_required_hashes"])
            self.assertFalse(ledger["archive_created"])
            self.assertFalse(ledger["submission_started"])
            self.assertEqual(ledger["public_safety_status"], "pass")

    def test_final_review_receipt_ledger_ready_for_manual_final_ledger_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            handoff, draft, reviewer, queue = final_review_receipt_ledger_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            ledger = build_python_exam_manual_final_review_receipt_ledger(
                python_exam_manual_final_review_handoff=handoff,
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                selected_skill_tag="python_lists",
            )
            summary = ledger["final_review_receipt_ledger_summary"]

            self.assertEqual(
                ledger["final_review_receipt_ledger_recommendation"],
                "ready_for_manual_final_ledger_review",
            )
            self.assertEqual(summary["final_review_handoff_recommendation"], "ready_for_manual_final_review")
            self.assertEqual(summary["gate_decisions"], ["ready_for_manual_export_authorization_review"])
            self.assertTrue(summary["accepted_post_cycle_hashes"]["notebook_checkpoint_hash"])
            self.assertTrue(summary["receipt_hashes"]["final_review_handoff_receipt_hash"])
            self.assertTrue(summary["ledger_event_hashes"][0])
            self.assertFalse(ledger["archive_created"])
            self.assertFalse(ledger["submission_started"])
            self.assertEqual(ledger["public_safety_status"], "pass")

    def test_final_review_receipt_ledger_rejects_rejected_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            handoff, draft, reviewer, queue = final_review_receipt_ledger_inputs(
                temp_dir,
                confirmed=True,
                mode="reject",
            )
            ledger = build_python_exam_manual_final_review_receipt_ledger(
                python_exam_manual_final_review_handoff=handoff,
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(ledger["final_review_receipt_ledger_recommendation"], "reject_final_ledger")
            self.assertEqual(
                ledger["final_review_receipt_ledger_summary"]["final_review_handoff_recommendation"],
                "reject_final_handoff",
            )
            self.assertFalse(ledger["notebook_code_returned"])
            self.assertFalse(ledger["archive_created"])
            self.assertFalse(ledger["submission_started"])
            self.assertEqual(ledger["public_safety_status"], "pass")

    def test_final_review_receipt_ledger_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            handoff, draft, reviewer, queue = final_review_receipt_ledger_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            status, ledger = route_request(
                "/api/unibot/course/python-exam-manual-final-review-receipt-ledger",
                {
                    "python_exam_manual_final_review_handoff": handoff,
                    "python_exam_manual_archive_decision_draft": draft,
                    "python_exam_manual_export_reviewer_packet": reviewer,
                    "python_exam_manual_export_review_queue": queue,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(ledger["status"], "python_exam_manual_final_review_receipt_ledger_ready")
            self.assertEqual(
                ledger["final_review_receipt_ledger_recommendation"],
                "ready_for_manual_final_ledger_review",
            )
            self.assertFalse(ledger["archive_created"])
            self.assertFalse(ledger["submission_started"])
            self.assertEqual(ledger["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
