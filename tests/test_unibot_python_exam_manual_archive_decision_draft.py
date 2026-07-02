from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_manual_archive_decision_draft import build_python_exam_manual_archive_decision_draft
from unibot.python_exam_manual_export_reviewer_packet import build_python_exam_manual_export_reviewer_packet
from unibot.server import route_request

from tests.test_unibot_python_exam_manual_export_reviewer_packet import reviewer_packet_inputs


def archive_decision_draft_inputs(
    temp_dir: str,
    *,
    confirmed: bool,
    mode: str = "missing",
) -> tuple[dict, dict, dict, dict]:
    queue, gate, preview, packet, timeline = reviewer_packet_inputs(temp_dir, confirmed=confirmed, mode=mode)
    reviewer = build_python_exam_manual_export_reviewer_packet(
        python_exam_manual_export_review_queue=queue,
        python_exam_manual_review_export_authorization_gate=gate,
        python_exam_manual_review_export_preview=preview,
        python_exam_manual_cycle_review_packet=packet,
        python_exam_manual_cycle_review_timeline=timeline,
        selected_skill_tag="python_lists",
    )
    return reviewer, queue, gate, preview


class UniBotPythonExamManualArchiveDecisionDraftTests(unittest.TestCase):
    def test_archive_decision_draft_keeps_open_without_archive_or_submission(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reviewer, queue, gate, preview = archive_decision_draft_inputs(temp_dir, confirmed=False)
            draft = build_python_exam_manual_archive_decision_draft(
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                python_exam_manual_review_export_authorization_gate=gate,
                python_exam_manual_review_export_preview=preview,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(draft, ensure_ascii=False)
            summary = draft["archive_decision_draft_summary"]
            body = draft["archive_decision_draft_body"]

            self.assertEqual(draft["artifact_type"], "python_exam_manual_archive_decision_draft")
            self.assertEqual(draft["status"], "python_exam_manual_archive_decision_draft_ready")
            self.assertEqual(draft["exam_deployment_status"], "not_cleared")
            self.assertEqual(draft["archive_decision_draft_recommendation"], "keep_archive_decision_draft_open")
            self.assertEqual(summary["reviewer_packet_recommendation"], "keep_reviewer_packet_open")
            self.assertEqual(summary["queue_recommendation"], "keep_queue_open")
            self.assertTrue(summary["reviewer_packet_hash"])
            self.assertTrue(summary["queue_hash"])
            self.assertTrue(summary["export_manifest_hash"])
            self.assertTrue(summary["authorization_gate_hash"])
            self.assertTrue(body["archive_decision_draft_hash"])
            self.assertFalse(draft["export_created"])
            self.assertFalse(draft["export_authorized"])
            self.assertFalse(draft["archive_created"])
            self.assertFalse(draft["submission_started"])
            self.assertTrue(draft["manual_archive_decision_draft_receipt"]["not_cleared_receipt"])
            self.assertTrue(draft["dry_run_default"])
            self.assertFalse(draft["local_writes_requested"])
            self.assertFalse(draft["local_execution_started"])
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
                self.assertFalse(draft[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-manual-archive-decision-draft")["status"], "pass")
            self.assertEqual(draft["public_safety_status"], "pass")

    def test_archive_decision_draft_requests_hash_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reviewer, queue, gate, preview = archive_decision_draft_inputs(temp_dir, confirmed=True)
            draft = build_python_exam_manual_archive_decision_draft(
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                python_exam_manual_review_export_authorization_gate=gate,
                python_exam_manual_review_export_preview=preview,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(draft["archive_decision_draft_recommendation"], "request_hash_completion")
            self.assertIn("notebook_checkpoint_hash", draft["archive_decision_draft_summary"]["missing_required_hashes"])
            self.assertFalse(draft["archive_created"])
            self.assertFalse(draft["submission_started"])
            self.assertEqual(draft["public_safety_status"], "pass")

    def test_archive_decision_draft_ready_for_manual_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reviewer, queue, gate, preview = archive_decision_draft_inputs(temp_dir, confirmed=True, mode="complete")
            draft = build_python_exam_manual_archive_decision_draft(
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                python_exam_manual_review_export_authorization_gate=gate,
                python_exam_manual_review_export_preview=preview,
                selected_skill_tag="python_lists",
            )
            summary = draft["archive_decision_draft_summary"]

            self.assertEqual(draft["archive_decision_draft_recommendation"], "ready_for_manual_archive_decision_review")
            self.assertEqual(summary["reviewer_packet_recommendation"], "ready_for_human_reviewer_packet")
            self.assertTrue(summary["accepted_post_cycle_hashes"]["notebook_checkpoint_hash"])
            self.assertTrue(summary["receipt_hashes"]["reviewer_packet_receipt_hash"])
            self.assertTrue(summary["archive_decision_draft_hash"])
            self.assertFalse(draft["archive_created"])
            self.assertFalse(draft["submission_started"])
            self.assertEqual(draft["public_safety_status"], "pass")

    def test_archive_decision_draft_rejects_rejected_reviewer_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reviewer, queue, gate, preview = archive_decision_draft_inputs(temp_dir, confirmed=True, mode="reject")
            draft = build_python_exam_manual_archive_decision_draft(
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                python_exam_manual_review_export_authorization_gate=gate,
                python_exam_manual_review_export_preview=preview,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(draft["archive_decision_draft_recommendation"], "reject_archive_decision_draft")
            self.assertEqual(draft["archive_decision_draft_summary"]["reviewer_packet_recommendation"], "reject_reviewer_packet")
            self.assertFalse(draft["notebook_code_returned"])
            self.assertFalse(draft["archive_created"])
            self.assertFalse(draft["submission_started"])
            self.assertEqual(draft["public_safety_status"], "pass")

    def test_archive_decision_draft_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reviewer, queue, gate, preview = archive_decision_draft_inputs(temp_dir, confirmed=True, mode="complete")
            status, draft = route_request(
                "/api/unibot/course/python-exam-manual-archive-decision-draft",
                {
                    "python_exam_manual_export_reviewer_packet": reviewer,
                    "python_exam_manual_export_review_queue": queue,
                    "python_exam_manual_review_export_authorization_gate": gate,
                    "python_exam_manual_review_export_preview": preview,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(draft["status"], "python_exam_manual_archive_decision_draft_ready")
            self.assertEqual(draft["archive_decision_draft_recommendation"], "ready_for_manual_archive_decision_review")
            self.assertFalse(draft["archive_created"])
            self.assertFalse(draft["submission_started"])
            self.assertEqual(draft["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
