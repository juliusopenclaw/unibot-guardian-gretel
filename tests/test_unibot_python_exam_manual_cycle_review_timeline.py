from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_manual_cycle_closure_ledger import build_python_exam_manual_cycle_closure_ledger
from unibot.python_exam_manual_cycle_review_timeline import build_python_exam_manual_cycle_review_timeline
from unibot.server import route_request

from tests.test_unibot_python_exam_manual_cycle_closure_ledger import closure_ledger_inputs


def review_timeline_inputs(temp_dir: str, *, confirmed: bool, mode: str = "missing") -> tuple[dict, dict, dict, dict, dict]:
    intake, binder, launch_receipt, console = closure_ledger_inputs(temp_dir, confirmed=confirmed, mode=mode)
    ledger = build_python_exam_manual_cycle_closure_ledger(
        python_exam_manual_post_cycle_receipt_intake=intake,
        python_exam_manual_cycle_evidence_binder=binder,
        python_exam_manual_cycle_launch_receipt=launch_receipt,
        python_exam_manual_confirmation_console=console,
        selected_skill_tag="python_lists",
    )
    return ledger, intake, binder, launch_receipt, console


class UniBotPythonExamManualCycleReviewTimelineTests(unittest.TestCase):
    def test_review_timeline_continues_open_cycle_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger, intake, binder, launch_receipt, console = review_timeline_inputs(temp_dir, confirmed=False)
            timeline = build_python_exam_manual_cycle_review_timeline(
                python_exam_manual_cycle_closure_ledger=ledger,
                python_exam_manual_post_cycle_receipt_intake=intake,
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(timeline, ensure_ascii=False)
            summary = timeline["timeline_summary"]

            self.assertEqual(timeline["artifact_type"], "python_exam_manual_cycle_review_timeline")
            self.assertEqual(timeline["status"], "python_exam_manual_cycle_review_timeline_ready")
            self.assertEqual(timeline["exam_deployment_status"], "not_cleared")
            self.assertEqual(timeline["timeline_review_recommendation"], "continue_cycle_review")
            self.assertEqual(summary["closure_ledger_decision"], "keep_cycle_open")
            self.assertEqual(summary["timeline_event_count"], 5)
            self.assertEqual(len(timeline["timeline_events"]), 5)
            self.assertTrue(timeline["manual_cycle_review_timeline_receipt"]["not_cleared_receipt"])
            self.assertFalse(timeline["local_writes_requested"])
            self.assertFalse(timeline["local_execution_started"])
            self.assertTrue(timeline["dry_run_default"])
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
                self.assertFalse(timeline[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-manual-cycle-review-timeline")["status"], "pass")
            self.assertEqual(timeline["public_safety_status"], "pass")

    def test_review_timeline_collects_missing_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger, intake, binder, launch_receipt, console = review_timeline_inputs(temp_dir, confirmed=True)
            timeline = build_python_exam_manual_cycle_review_timeline(
                python_exam_manual_cycle_closure_ledger=ledger,
                python_exam_manual_post_cycle_receipt_intake=intake,
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(timeline["timeline_review_recommendation"], "collect_missing_hashes")
            self.assertEqual(timeline["timeline_summary"]["closure_ledger_decision"], "request_post_cycle_hash_review")
            self.assertIn("notebook_checkpoint_hash", timeline["timeline_summary"]["missing_required_hashes"])
            self.assertEqual(timeline["public_safety_status"], "pass")

    def test_review_timeline_ready_for_human_review_after_closed_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger, intake, binder, launch_receipt, console = review_timeline_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            timeline = build_python_exam_manual_cycle_review_timeline(
                python_exam_manual_cycle_closure_ledger=ledger,
                python_exam_manual_post_cycle_receipt_intake=intake,
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(timeline["timeline_review_recommendation"], "ready_for_human_timeline_review")
            self.assertEqual(timeline["timeline_summary"]["closure_ledger_decision"], "close_cycle_for_human_review")
            self.assertTrue(timeline["timeline_summary"]["accepted_post_cycle_hashes"]["notebook_checkpoint_hash"])
            self.assertTrue(timeline["timeline_summary"]["operator_reflection_hash"])
            self.assertEqual(timeline["public_safety_status"], "pass")

    def test_review_timeline_rejects_rejected_closure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger, intake, binder, launch_receipt, console = review_timeline_inputs(
                temp_dir,
                confirmed=True,
                mode="reject",
            )
            timeline = build_python_exam_manual_cycle_review_timeline(
                python_exam_manual_cycle_closure_ledger=ledger,
                python_exam_manual_post_cycle_receipt_intake=intake,
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(timeline["timeline_review_recommendation"], "reject_timeline_review")
            self.assertEqual(timeline["timeline_summary"]["closure_ledger_decision"], "reject_cycle_closure")
            self.assertFalse(timeline["notebook_code_returned"])
            self.assertEqual(timeline["public_safety_status"], "pass")

    def test_review_timeline_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger, intake, binder, launch_receipt, console = review_timeline_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            status, timeline = route_request(
                "/api/unibot/course/python-exam-manual-cycle-review-timeline",
                {
                    "python_exam_manual_cycle_closure_ledger": ledger,
                    "python_exam_manual_post_cycle_receipt_intake": intake,
                    "python_exam_manual_cycle_evidence_binder": binder,
                    "python_exam_manual_cycle_launch_receipt": launch_receipt,
                    "python_exam_manual_confirmation_console": console,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(timeline["status"], "python_exam_manual_cycle_review_timeline_ready")
            self.assertEqual(timeline["timeline_review_recommendation"], "ready_for_human_timeline_review")
            self.assertEqual(timeline["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
