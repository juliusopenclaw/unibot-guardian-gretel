from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_manual_archive_decision_draft import build_python_exam_manual_archive_decision_draft
from unibot.python_exam_manual_final_review_handoff import build_python_exam_manual_final_review_handoff
from unibot.server import route_request

from tests.test_unibot_python_exam_manual_archive_decision_draft import archive_decision_draft_inputs


def final_review_handoff_inputs(
    temp_dir: str,
    *,
    confirmed: bool,
    mode: str = "missing",
) -> tuple[dict, dict, dict, dict]:
    reviewer, queue, gate, preview = archive_decision_draft_inputs(temp_dir, confirmed=confirmed, mode=mode)
    draft = build_python_exam_manual_archive_decision_draft(
        python_exam_manual_export_reviewer_packet=reviewer,
        python_exam_manual_export_review_queue=queue,
        python_exam_manual_review_export_authorization_gate=gate,
        python_exam_manual_review_export_preview=preview,
        selected_skill_tag="python_lists",
    )
    return draft, reviewer, queue, gate


class UniBotPythonExamManualFinalReviewHandoffTests(unittest.TestCase):
    def test_final_handoff_keeps_open_without_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            draft, reviewer, queue, gate = final_review_handoff_inputs(temp_dir, confirmed=False)
            handoff = build_python_exam_manual_final_review_handoff(
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                python_exam_manual_review_export_authorization_gate=gate,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(handoff, ensure_ascii=False)
            summary = handoff["final_review_handoff_summary"]
            body = handoff["final_review_handoff_body"]

            self.assertEqual(handoff["artifact_type"], "python_exam_manual_final_review_handoff")
            self.assertEqual(handoff["status"], "python_exam_manual_final_review_handoff_ready")
            self.assertEqual(handoff["exam_deployment_status"], "not_cleared")
            self.assertEqual(handoff["final_review_handoff_recommendation"], "keep_final_handoff_open")
            self.assertEqual(summary["archive_decision_draft_recommendation"], "keep_archive_decision_draft_open")
            self.assertEqual(summary["reviewer_packet_recommendation"], "keep_reviewer_packet_open")
            self.assertEqual(summary["queue_recommendation"], "keep_queue_open")
            self.assertTrue(summary["archive_decision_draft_hash"])
            self.assertTrue(summary["reviewer_packet_hash"])
            self.assertTrue(summary["queue_hash"])
            self.assertTrue(summary["export_manifest_hash"])
            self.assertTrue(summary["authorization_gate_hash"])
            self.assertTrue(body["final_review_handoff_hash"])
            self.assertFalse(handoff["export_created"])
            self.assertFalse(handoff["export_authorized"])
            self.assertFalse(handoff["archive_created"])
            self.assertFalse(handoff["submission_started"])
            self.assertTrue(handoff["manual_final_review_handoff_receipt"]["not_cleared_receipt"])
            self.assertTrue(handoff["dry_run_default"])
            self.assertFalse(handoff["local_writes_requested"])
            self.assertFalse(handoff["local_execution_started"])
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
                self.assertFalse(handoff[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-manual-final-review-handoff")["status"], "pass")
            self.assertEqual(handoff["public_safety_status"], "pass")

    def test_final_handoff_requests_hash_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            draft, reviewer, queue, gate = final_review_handoff_inputs(temp_dir, confirmed=True)
            handoff = build_python_exam_manual_final_review_handoff(
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                python_exam_manual_review_export_authorization_gate=gate,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(handoff["final_review_handoff_recommendation"], "request_hash_completion")
            self.assertIn("notebook_checkpoint_hash", handoff["final_review_handoff_summary"]["missing_required_hashes"])
            self.assertFalse(handoff["archive_created"])
            self.assertFalse(handoff["submission_started"])
            self.assertEqual(handoff["public_safety_status"], "pass")

    def test_final_handoff_ready_for_manual_final_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            draft, reviewer, queue, gate = final_review_handoff_inputs(temp_dir, confirmed=True, mode="complete")
            handoff = build_python_exam_manual_final_review_handoff(
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                python_exam_manual_review_export_authorization_gate=gate,
                selected_skill_tag="python_lists",
            )
            summary = handoff["final_review_handoff_summary"]

            self.assertEqual(handoff["final_review_handoff_recommendation"], "ready_for_manual_final_review")
            self.assertEqual(summary["archive_decision_draft_recommendation"], "ready_for_manual_archive_decision_review")
            self.assertEqual(summary["gate_decisions"], ["ready_for_manual_export_authorization_review"])
            self.assertTrue(summary["accepted_post_cycle_hashes"]["notebook_checkpoint_hash"])
            self.assertTrue(summary["receipt_hashes"]["archive_decision_draft_receipt_hash"])
            self.assertTrue(summary["final_review_handoff_hash"])
            self.assertFalse(handoff["archive_created"])
            self.assertFalse(handoff["submission_started"])
            self.assertEqual(handoff["public_safety_status"], "pass")

    def test_final_handoff_rejects_rejected_draft(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            draft, reviewer, queue, gate = final_review_handoff_inputs(temp_dir, confirmed=True, mode="reject")
            handoff = build_python_exam_manual_final_review_handoff(
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                python_exam_manual_review_export_authorization_gate=gate,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(handoff["final_review_handoff_recommendation"], "reject_final_handoff")
            self.assertEqual(
                handoff["final_review_handoff_summary"]["archive_decision_draft_recommendation"],
                "reject_archive_decision_draft",
            )
            self.assertFalse(handoff["notebook_code_returned"])
            self.assertFalse(handoff["archive_created"])
            self.assertFalse(handoff["submission_started"])
            self.assertEqual(handoff["public_safety_status"], "pass")

    def test_final_handoff_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            draft, reviewer, queue, gate = final_review_handoff_inputs(temp_dir, confirmed=True, mode="complete")
            status, handoff = route_request(
                "/api/unibot/course/python-exam-manual-final-review-handoff",
                {
                    "python_exam_manual_archive_decision_draft": draft,
                    "python_exam_manual_export_reviewer_packet": reviewer,
                    "python_exam_manual_export_review_queue": queue,
                    "python_exam_manual_review_export_authorization_gate": gate,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(handoff["status"], "python_exam_manual_final_review_handoff_ready")
            self.assertEqual(handoff["final_review_handoff_recommendation"], "ready_for_manual_final_review")
            self.assertFalse(handoff["archive_created"])
            self.assertFalse(handoff["submission_started"])
            self.assertEqual(handoff["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
