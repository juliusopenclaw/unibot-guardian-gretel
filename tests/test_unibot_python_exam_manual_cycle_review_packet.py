from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_manual_cycle_review_packet import build_python_exam_manual_cycle_review_packet
from unibot.python_exam_manual_cycle_review_timeline import build_python_exam_manual_cycle_review_timeline
from unibot.server import route_request

from tests.test_unibot_python_exam_manual_cycle_review_timeline import review_timeline_inputs


def review_packet_inputs(temp_dir: str, *, confirmed: bool, mode: str = "missing") -> tuple[dict, dict, dict, dict, dict, dict]:
    ledger, intake, binder, launch_receipt, console = review_timeline_inputs(temp_dir, confirmed=confirmed, mode=mode)
    timeline = build_python_exam_manual_cycle_review_timeline(
        python_exam_manual_cycle_closure_ledger=ledger,
        python_exam_manual_post_cycle_receipt_intake=intake,
        python_exam_manual_cycle_evidence_binder=binder,
        python_exam_manual_cycle_launch_receipt=launch_receipt,
        python_exam_manual_confirmation_console=console,
        selected_skill_tag="python_lists",
    )
    return timeline, ledger, intake, binder, launch_receipt, console


class UniBotPythonExamManualCycleReviewPacketTests(unittest.TestCase):
    def test_review_packet_keeps_open_cycle_packet_open(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            timeline, ledger, intake, binder, launch_receipt, console = review_packet_inputs(temp_dir, confirmed=False)
            packet = build_python_exam_manual_cycle_review_packet(
                python_exam_manual_cycle_review_timeline=timeline,
                python_exam_manual_cycle_closure_ledger=ledger,
                python_exam_manual_post_cycle_receipt_intake=intake,
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(packet, ensure_ascii=False)
            summary = packet["review_packet_summary"]

            self.assertEqual(packet["artifact_type"], "python_exam_manual_cycle_review_packet")
            self.assertEqual(packet["status"], "python_exam_manual_cycle_review_packet_ready")
            self.assertEqual(packet["exam_deployment_status"], "not_cleared")
            self.assertEqual(packet["packet_recommendation"], "keep_review_packet_open")
            self.assertEqual(summary["timeline_recommendation"], "continue_cycle_review")
            self.assertEqual(summary["timeline_event_count"], 5)
            self.assertEqual(summary["help_level"], "A2")
            self.assertTrue(packet["manual_cycle_review_packet_receipt"]["not_cleared_receipt"])
            self.assertFalse(packet["local_writes_requested"])
            self.assertFalse(packet["local_execution_started"])
            self.assertTrue(packet["dry_run_default"])
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
                self.assertFalse(packet[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-manual-cycle-review-packet")["status"], "pass")
            self.assertEqual(packet["public_safety_status"], "pass")

    def test_review_packet_requests_hash_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            timeline, ledger, intake, binder, launch_receipt, console = review_packet_inputs(temp_dir, confirmed=True)
            packet = build_python_exam_manual_cycle_review_packet(
                python_exam_manual_cycle_review_timeline=timeline,
                python_exam_manual_cycle_closure_ledger=ledger,
                python_exam_manual_post_cycle_receipt_intake=intake,
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(packet["packet_recommendation"], "request_hash_completion")
            self.assertEqual(packet["review_packet_summary"]["timeline_recommendation"], "collect_missing_hashes")
            self.assertIn("notebook_checkpoint_hash", packet["review_packet_summary"]["missing_required_hashes"])
            self.assertEqual(packet["public_safety_status"], "pass")

    def test_review_packet_ready_for_human_packet_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            timeline, ledger, intake, binder, launch_receipt, console = review_packet_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            packet = build_python_exam_manual_cycle_review_packet(
                python_exam_manual_cycle_review_timeline=timeline,
                python_exam_manual_cycle_closure_ledger=ledger,
                python_exam_manual_post_cycle_receipt_intake=intake,
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                selected_skill_tag="python_lists",
            )
            accepted = packet["review_packet_summary"]["accepted_post_cycle_hashes"]

            self.assertEqual(packet["packet_recommendation"], "ready_for_human_packet_review")
            self.assertEqual(packet["review_packet_summary"]["timeline_recommendation"], "ready_for_human_timeline_review")
            self.assertTrue(accepted["notebook_checkpoint_hash"])
            self.assertTrue(packet["review_packet_summary"]["operator_reflection_hash"])
            self.assertTrue(packet["review_packet_summary"]["receipt_hashes"]["timeline_receipt_hash"])
            self.assertEqual(packet["public_safety_status"], "pass")

    def test_review_packet_rejects_rejected_timeline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            timeline, ledger, intake, binder, launch_receipt, console = review_packet_inputs(
                temp_dir,
                confirmed=True,
                mode="reject",
            )
            packet = build_python_exam_manual_cycle_review_packet(
                python_exam_manual_cycle_review_timeline=timeline,
                python_exam_manual_cycle_closure_ledger=ledger,
                python_exam_manual_post_cycle_receipt_intake=intake,
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(packet["packet_recommendation"], "reject_review_packet")
            self.assertEqual(packet["review_packet_summary"]["timeline_recommendation"], "reject_timeline_review")
            self.assertFalse(packet["notebook_code_returned"])
            self.assertEqual(packet["public_safety_status"], "pass")

    def test_review_packet_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            timeline, ledger, intake, binder, launch_receipt, console = review_packet_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            status, packet = route_request(
                "/api/unibot/course/python-exam-manual-cycle-review-packet",
                {
                    "python_exam_manual_cycle_review_timeline": timeline,
                    "python_exam_manual_cycle_closure_ledger": ledger,
                    "python_exam_manual_post_cycle_receipt_intake": intake,
                    "python_exam_manual_cycle_evidence_binder": binder,
                    "python_exam_manual_cycle_launch_receipt": launch_receipt,
                    "python_exam_manual_confirmation_console": console,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(packet["status"], "python_exam_manual_cycle_review_packet_ready")
            self.assertEqual(packet["packet_recommendation"], "ready_for_human_packet_review")
            self.assertEqual(packet["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
