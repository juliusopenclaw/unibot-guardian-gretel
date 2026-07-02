from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_manual_export_reviewer_packet import build_python_exam_manual_export_reviewer_packet
from unibot.python_exam_manual_export_review_queue import build_python_exam_manual_export_review_queue
from unibot.server import route_request

from tests.test_unibot_python_exam_manual_export_review_queue import export_review_queue_inputs


def reviewer_packet_inputs(
    temp_dir: str,
    *,
    confirmed: bool,
    mode: str = "missing",
) -> tuple[dict, dict, dict, dict, dict]:
    gate, preview, packet, timeline = export_review_queue_inputs(temp_dir, confirmed=confirmed, mode=mode)
    queue = build_python_exam_manual_export_review_queue(
        python_exam_manual_review_export_authorization_gate=gate,
        python_exam_manual_review_export_preview=preview,
        python_exam_manual_cycle_review_packet=packet,
        python_exam_manual_cycle_review_timeline=timeline,
        selected_skill_tag="python_lists",
    )
    return queue, gate, preview, packet, timeline


class UniBotPythonExamManualExportReviewerPacketTests(unittest.TestCase):
    def test_reviewer_packet_keeps_open_queue_open_without_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            queue, gate, preview, packet, timeline = reviewer_packet_inputs(temp_dir, confirmed=False)
            reviewer = build_python_exam_manual_export_reviewer_packet(
                python_exam_manual_export_review_queue=queue,
                python_exam_manual_review_export_authorization_gate=gate,
                python_exam_manual_review_export_preview=preview,
                python_exam_manual_cycle_review_packet=packet,
                python_exam_manual_cycle_review_timeline=timeline,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(reviewer, ensure_ascii=False)
            summary = reviewer["reviewer_packet_summary"]
            body = reviewer["reviewer_packet_body"]

            self.assertEqual(reviewer["artifact_type"], "python_exam_manual_export_reviewer_packet")
            self.assertEqual(reviewer["status"], "python_exam_manual_export_reviewer_packet_ready")
            self.assertEqual(reviewer["exam_deployment_status"], "not_cleared")
            self.assertEqual(reviewer["reviewer_packet_recommendation"], "keep_reviewer_packet_open")
            self.assertEqual(summary["queue_recommendation"], "keep_queue_open")
            self.assertTrue(summary["queue_hash"])
            self.assertTrue(summary["candidate_hashes"])
            self.assertTrue(summary["export_manifest_hash"])
            self.assertTrue(summary["authorization_gate_hash"])
            self.assertTrue(body["reviewer_packet_hash"])
            self.assertFalse(reviewer["export_created"])
            self.assertFalse(reviewer["export_authorized"])
            self.assertTrue(reviewer["manual_export_reviewer_packet_receipt"]["not_cleared_receipt"])
            self.assertTrue(reviewer["dry_run_default"])
            self.assertFalse(reviewer["local_writes_requested"])
            self.assertFalse(reviewer["local_execution_started"])
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
                self.assertFalse(reviewer[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-manual-export-reviewer-packet")["status"], "pass")
            self.assertEqual(reviewer["public_safety_status"], "pass")

    def test_reviewer_packet_requests_hash_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            queue, gate, preview, packet, timeline = reviewer_packet_inputs(temp_dir, confirmed=True)
            reviewer = build_python_exam_manual_export_reviewer_packet(
                python_exam_manual_export_review_queue=queue,
                python_exam_manual_review_export_authorization_gate=gate,
                python_exam_manual_review_export_preview=preview,
                python_exam_manual_cycle_review_packet=packet,
                python_exam_manual_cycle_review_timeline=timeline,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(reviewer["reviewer_packet_recommendation"], "request_hash_completion")
            self.assertIn("notebook_checkpoint_hash", reviewer["reviewer_packet_summary"]["missing_required_hashes"])
            self.assertFalse(reviewer["export_created"])
            self.assertFalse(reviewer["export_authorized"])
            self.assertEqual(reviewer["public_safety_status"], "pass")

    def test_reviewer_packet_ready_for_human_reviewer_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            queue, gate, preview, packet, timeline = reviewer_packet_inputs(temp_dir, confirmed=True, mode="complete")
            reviewer = build_python_exam_manual_export_reviewer_packet(
                python_exam_manual_export_review_queue=queue,
                python_exam_manual_review_export_authorization_gate=gate,
                python_exam_manual_review_export_preview=preview,
                python_exam_manual_cycle_review_packet=packet,
                python_exam_manual_cycle_review_timeline=timeline,
                selected_skill_tag="python_lists",
            )
            summary = reviewer["reviewer_packet_summary"]

            self.assertEqual(reviewer["reviewer_packet_recommendation"], "ready_for_human_reviewer_packet")
            self.assertEqual(summary["queue_recommendation"], "ready_for_manual_export_review_queue")
            self.assertEqual(summary["gate_decisions"], ["ready_for_manual_export_authorization_review"])
            self.assertTrue(summary["accepted_post_cycle_hashes"]["notebook_checkpoint_hash"])
            self.assertTrue(summary["preview_receipt_hash"])
            self.assertTrue(summary["authorization_gate_receipt_hash"])
            self.assertTrue(summary["queue_receipt_hash"])
            self.assertFalse(reviewer["export_created"])
            self.assertFalse(reviewer["export_authorized"])
            self.assertEqual(reviewer["public_safety_status"], "pass")

    def test_reviewer_packet_rejects_rejected_queue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            queue, gate, preview, packet, timeline = reviewer_packet_inputs(temp_dir, confirmed=True, mode="reject")
            reviewer = build_python_exam_manual_export_reviewer_packet(
                python_exam_manual_export_review_queue=queue,
                python_exam_manual_review_export_authorization_gate=gate,
                python_exam_manual_review_export_preview=preview,
                python_exam_manual_cycle_review_packet=packet,
                python_exam_manual_cycle_review_timeline=timeline,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(reviewer["reviewer_packet_recommendation"], "reject_reviewer_packet")
            self.assertEqual(reviewer["reviewer_packet_summary"]["queue_recommendation"], "reject_queue_entry")
            self.assertFalse(reviewer["notebook_code_returned"])
            self.assertFalse(reviewer["export_created"])
            self.assertFalse(reviewer["export_authorized"])
            self.assertEqual(reviewer["public_safety_status"], "pass")

    def test_reviewer_packet_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            queue, gate, preview, packet, timeline = reviewer_packet_inputs(temp_dir, confirmed=True, mode="complete")
            status, reviewer = route_request(
                "/api/unibot/course/python-exam-manual-export-reviewer-packet",
                {
                    "python_exam_manual_export_review_queue": queue,
                    "python_exam_manual_review_export_authorization_gate": gate,
                    "python_exam_manual_review_export_preview": preview,
                    "python_exam_manual_cycle_review_packet": packet,
                    "python_exam_manual_cycle_review_timeline": timeline,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(reviewer["status"], "python_exam_manual_export_reviewer_packet_ready")
            self.assertEqual(reviewer["reviewer_packet_recommendation"], "ready_for_human_reviewer_packet")
            self.assertFalse(reviewer["export_created"])
            self.assertFalse(reviewer["export_authorized"])
            self.assertEqual(reviewer["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
