from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_manual_export_review_queue import build_python_exam_manual_export_review_queue
from unibot.python_exam_manual_review_export_authorization_gate import (
    build_python_exam_manual_review_export_authorization_gate,
)
from unibot.server import route_request

from tests.test_unibot_python_exam_manual_review_export_authorization_gate import authorization_gate_inputs


def export_review_queue_inputs(
    temp_dir: str,
    *,
    confirmed: bool,
    mode: str = "missing",
) -> tuple[dict, dict, dict, dict]:
    preview, packet, timeline, ledger = authorization_gate_inputs(temp_dir, confirmed=confirmed, mode=mode)
    gate = build_python_exam_manual_review_export_authorization_gate(
        python_exam_manual_review_export_preview=preview,
        python_exam_manual_cycle_review_packet=packet,
        python_exam_manual_cycle_review_timeline=timeline,
        python_exam_manual_cycle_closure_ledger=ledger,
        selected_skill_tag="python_lists",
    )
    return gate, preview, packet, timeline


class UniBotPythonExamManualExportReviewQueueTests(unittest.TestCase):
    def test_queue_keeps_blocked_gate_open_without_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            gate, preview, packet, timeline = export_review_queue_inputs(temp_dir, confirmed=False)
            queue = build_python_exam_manual_export_review_queue(
                python_exam_manual_review_export_authorization_gate=gate,
                python_exam_manual_review_export_preview=preview,
                python_exam_manual_cycle_review_packet=packet,
                python_exam_manual_cycle_review_timeline=timeline,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(queue, ensure_ascii=False)
            summary = queue["queue_summary"]
            candidate = queue["queue_candidates"][0]

            self.assertEqual(queue["artifact_type"], "python_exam_manual_export_review_queue")
            self.assertEqual(queue["status"], "python_exam_manual_export_review_queue_ready")
            self.assertEqual(queue["exam_deployment_status"], "not_cleared")
            self.assertEqual(queue["queue_recommendation"], "keep_queue_open")
            self.assertEqual(summary["queue_recommendation"], "keep_queue_open")
            self.assertEqual(candidate["queue_entry_recommendation"], "keep_queue_open")
            self.assertEqual(candidate["authorization_gate_decision"], "keep_export_blocked")
            self.assertTrue(candidate["export_manifest_hash"])
            self.assertTrue(candidate["authorization_gate_hash"])
            self.assertFalse(queue["export_created"])
            self.assertFalse(queue["export_authorized"])
            self.assertTrue(queue["manual_export_review_queue_receipt"]["not_cleared_receipt"])
            self.assertTrue(queue["dry_run_default"])
            self.assertFalse(queue["local_writes_requested"])
            self.assertFalse(queue["local_execution_started"])
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
                self.assertFalse(queue[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-manual-export-review-queue")["status"], "pass")
            self.assertEqual(queue["public_safety_status"], "pass")

    def test_queue_requests_hash_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            gate, preview, packet, timeline = export_review_queue_inputs(temp_dir, confirmed=True)
            queue = build_python_exam_manual_export_review_queue(
                python_exam_manual_review_export_authorization_gate=gate,
                python_exam_manual_review_export_preview=preview,
                python_exam_manual_cycle_review_packet=packet,
                python_exam_manual_cycle_review_timeline=timeline,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(queue["queue_recommendation"], "request_hash_completion")
            self.assertEqual(queue["queue_candidates"][0]["queue_entry_recommendation"], "request_hash_completion")
            self.assertIn("notebook_checkpoint_hash", queue["queue_candidates"][0]["missing_required_hashes"])
            self.assertFalse(queue["export_created"])
            self.assertFalse(queue["export_authorized"])
            self.assertEqual(queue["public_safety_status"], "pass")

    def test_queue_ready_for_manual_export_review_queue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            gate, preview, packet, timeline = export_review_queue_inputs(temp_dir, confirmed=True, mode="complete")
            queue = build_python_exam_manual_export_review_queue(
                python_exam_manual_review_export_authorization_gate=gate,
                python_exam_manual_review_export_preview=preview,
                python_exam_manual_cycle_review_packet=packet,
                python_exam_manual_cycle_review_timeline=timeline,
                selected_skill_tag="python_lists",
            )
            candidate = queue["queue_candidates"][0]

            self.assertEqual(queue["queue_recommendation"], "ready_for_manual_export_review_queue")
            self.assertEqual(candidate["queue_entry_recommendation"], "ready_for_manual_export_review_queue")
            self.assertEqual(candidate["authorization_gate_decision"], "ready_for_manual_export_authorization_review")
            self.assertTrue(candidate["accepted_post_cycle_hashes"]["notebook_checkpoint_hash"])
            self.assertTrue(candidate["preview_receipt_hash"])
            self.assertTrue(candidate["authorization_gate_receipt_hash"])
            self.assertTrue(queue["queue_summary"]["queue_hash"])
            self.assertFalse(queue["export_created"])
            self.assertFalse(queue["export_authorized"])
            self.assertEqual(queue["public_safety_status"], "pass")

    def test_queue_rejects_rejected_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            gate, preview, packet, timeline = export_review_queue_inputs(temp_dir, confirmed=True, mode="reject")
            queue = build_python_exam_manual_export_review_queue(
                python_exam_manual_review_export_authorization_gate=gate,
                python_exam_manual_review_export_preview=preview,
                python_exam_manual_cycle_review_packet=packet,
                python_exam_manual_cycle_review_timeline=timeline,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(queue["queue_recommendation"], "reject_queue_entry")
            self.assertEqual(queue["queue_candidates"][0]["authorization_gate_decision"], "reject_export_authorization")
            self.assertFalse(queue["notebook_code_returned"])
            self.assertFalse(queue["export_created"])
            self.assertFalse(queue["export_authorized"])
            self.assertEqual(queue["public_safety_status"], "pass")

    def test_queue_accepts_additional_hash_only_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            gate, preview, packet, timeline = export_review_queue_inputs(temp_dir, confirmed=False)
            queue = build_python_exam_manual_export_review_queue(
                python_exam_manual_review_export_authorization_gate=gate,
                python_exam_manual_review_export_preview=preview,
                python_exam_manual_cycle_review_packet=packet,
                python_exam_manual_cycle_review_timeline=timeline,
                queue_candidates=[
                    {
                        "candidate_id": "second-candidate",
                        "authorization_gate_decision": "keep_export_blocked",
                        "export_manifest_hash": "hash_export_manifest_2",
                        "authorization_gate_hash": "hash_gate_2",
                        "receipt_hashes": {"preview_receipt_hash": "hash_preview_2"},
                        "selected_skill_tag": "python_lists",
                        "help_level": "A2",
                    }
                ],
                selected_skill_tag="python_lists",
            )

            self.assertEqual(queue["queue_summary"]["candidate_count"], 2)
            self.assertEqual(queue["queue_recommendation"], "keep_queue_open")
            self.assertEqual(queue["queue_candidates"][1]["candidate_id"], "second-candidate")
            self.assertFalse(queue["export_created"])
            self.assertEqual(queue["public_safety_status"], "pass")

    def test_queue_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            gate, preview, packet, timeline = export_review_queue_inputs(temp_dir, confirmed=True, mode="complete")
            status, queue = route_request(
                "/api/unibot/course/python-exam-manual-export-review-queue",
                {
                    "python_exam_manual_review_export_authorization_gate": gate,
                    "python_exam_manual_review_export_preview": preview,
                    "python_exam_manual_cycle_review_packet": packet,
                    "python_exam_manual_cycle_review_timeline": timeline,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(queue["status"], "python_exam_manual_export_review_queue_ready")
            self.assertEqual(queue["queue_recommendation"], "ready_for_manual_export_review_queue")
            self.assertFalse(queue["export_created"])
            self.assertFalse(queue["export_authorized"])
            self.assertEqual(queue["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
