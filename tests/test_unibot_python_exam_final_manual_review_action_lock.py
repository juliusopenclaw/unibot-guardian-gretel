from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_final_manual_review_action_lock import (
    build_python_exam_final_manual_review_action_lock,
)
from unibot.python_exam_final_manual_review_console import build_python_exam_final_manual_review_console
from unibot.server import route_request

from tests.test_unibot_python_exam_final_manual_review_console import final_manual_review_console_inputs


def final_manual_review_action_lock_inputs(
    temp_dir: str,
    *,
    confirmed: bool,
    mode: str = "missing",
) -> tuple[dict, dict, dict]:
    gate, ledger, handoff, draft, reviewer, queue = final_manual_review_console_inputs(
        temp_dir,
        confirmed=confirmed,
        mode=mode,
    )
    console = build_python_exam_final_manual_review_console(
        python_exam_final_review_ledger_integrity_gate=gate,
        python_exam_manual_final_review_receipt_ledger=ledger,
        python_exam_manual_final_review_handoff=handoff,
        python_exam_manual_archive_decision_draft=draft,
        python_exam_manual_export_reviewer_packet=reviewer,
        python_exam_manual_export_review_queue=queue,
        selected_skill_tag="python_lists",
    )
    return console, gate, ledger


class UniBotPythonExamFinalManualReviewActionLockTests(unittest.TestCase):
    def test_final_manual_review_action_lock_keeps_locked_without_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, gate, ledger = final_manual_review_action_lock_inputs(temp_dir, confirmed=False)
            lock = build_python_exam_final_manual_review_action_lock(
                python_exam_final_manual_review_console=console,
                python_exam_final_review_ledger_integrity_gate=gate,
                python_exam_manual_final_review_receipt_ledger=ledger,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(lock, ensure_ascii=False)
            summary = lock["final_manual_review_action_lock_summary"]

            self.assertEqual(lock["artifact_type"], "python_exam_final_manual_review_action_lock")
            self.assertEqual(lock["status"], "python_exam_final_manual_review_action_lock_ready")
            self.assertEqual(lock["exam_deployment_status"], "not_cleared")
            self.assertEqual(lock["final_manual_review_action_lock_recommendation"], "keep_action_locked")
            self.assertEqual(summary["final_manual_review_console_recommendation"], "keep_final_console_open")
            self.assertEqual(summary["final_review_ledger_integrity_gate_recommendation"], "keep_integrity_gate_open")
            self.assertEqual(summary["final_review_receipt_ledger_recommendation"], "keep_final_ledger_open")
            self.assertGreaterEqual(summary["integrity_issue_count"], 1)
            self.assertIn("notebook_checkpoint_hash", summary["missing_required_hashes"])
            self.assertFalse(summary["mismatched_hashes"])
            self.assertEqual(summary["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["help_level"], "A2")
            self.assertEqual(summary["ledger_event_count"], 5)
            self.assertTrue(summary["final_manual_review_action_lock_hash"])
            self.assertTrue(summary["final_manual_review_console_hash"])
            self.assertTrue(summary["final_review_ledger_integrity_gate_hash"])
            self.assertTrue(summary["final_review_receipt_ledger_hash"])
            self.assertTrue(lock["final_manual_review_action_lock_receipt"]["not_cleared_receipt"])
            self.assertFalse(lock["export_created"])
            self.assertFalse(lock["export_authorized"])
            self.assertFalse(lock["archive_created"])
            self.assertFalse(lock["submission_started"])
            self.assertTrue(lock["dry_run_default"])
            self.assertFalse(lock["local_writes_requested"])
            self.assertFalse(lock["local_execution_started"])
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
                self.assertFalse(lock[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-final-manual-review-action-lock")["status"], "pass")
            self.assertEqual(lock["public_safety_status"], "pass")

    def test_final_manual_review_action_lock_requests_manual_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, gate, ledger = final_manual_review_action_lock_inputs(temp_dir, confirmed=True)
            lock = build_python_exam_final_manual_review_action_lock(
                python_exam_final_manual_review_console=console,
                python_exam_final_review_ledger_integrity_gate=gate,
                python_exam_manual_final_review_receipt_ledger=ledger,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(
                lock["final_manual_review_action_lock_recommendation"],
                "request_manual_reconciliation",
            )
            self.assertEqual(
                lock["final_manual_review_action_lock_summary"]["final_manual_review_console_recommendation"],
                "request_integrity_reconciliation",
            )
            self.assertFalse(lock["archive_created"])
            self.assertFalse(lock["submission_started"])
            self.assertEqual(lock["public_safety_status"], "pass")

    def test_final_manual_review_action_lock_ready_for_manual_action_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, gate, ledger = final_manual_review_action_lock_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            lock = build_python_exam_final_manual_review_action_lock(
                python_exam_final_manual_review_console=console,
                python_exam_final_review_ledger_integrity_gate=gate,
                python_exam_manual_final_review_receipt_ledger=ledger,
                selected_skill_tag="python_lists",
            )
            summary = lock["final_manual_review_action_lock_summary"]

            self.assertEqual(lock["final_manual_review_action_lock_recommendation"], "ready_for_manual_action_review")
            self.assertEqual(summary["final_manual_review_console_recommendation"], "ready_for_manual_console_review")
            self.assertEqual(summary["final_review_ledger_integrity_gate_recommendation"], "ready_for_manual_integrity_review")
            self.assertEqual(summary["final_review_receipt_ledger_recommendation"], "ready_for_manual_final_ledger_review")
            self.assertEqual(summary["integrity_issue_count"], 0)
            self.assertFalse(summary["missing_required_hashes"])
            self.assertFalse(summary["mismatched_hashes"])
            self.assertEqual(summary["next_safe_human_review_action"], "present_locked_hash_only_action_review_to_human")
            self.assertFalse(lock["archive_created"])
            self.assertFalse(lock["submission_started"])
            self.assertEqual(lock["public_safety_status"], "pass")

    def test_final_manual_review_action_lock_rejects_rejected_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, gate, ledger = final_manual_review_action_lock_inputs(
                temp_dir,
                confirmed=True,
                mode="reject",
            )
            lock = build_python_exam_final_manual_review_action_lock(
                python_exam_final_manual_review_console=console,
                python_exam_final_review_ledger_integrity_gate=gate,
                python_exam_manual_final_review_receipt_ledger=ledger,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(lock["final_manual_review_action_lock_recommendation"], "reject_action_path")
            self.assertEqual(
                lock["final_manual_review_action_lock_summary"]["final_manual_review_console_recommendation"],
                "reject_final_console",
            )
            self.assertFalse(lock["notebook_code_returned"])
            self.assertFalse(lock["archive_created"])
            self.assertFalse(lock["submission_started"])
            self.assertEqual(lock["public_safety_status"], "pass")

    def test_final_manual_review_action_lock_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, gate, ledger = final_manual_review_action_lock_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            status, lock = route_request(
                "/api/unibot/course/python-exam-final-manual-review-action-lock",
                {
                    "python_exam_final_manual_review_console": console,
                    "python_exam_final_review_ledger_integrity_gate": gate,
                    "python_exam_manual_final_review_receipt_ledger": ledger,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(lock["status"], "python_exam_final_manual_review_action_lock_ready")
            self.assertEqual(lock["final_manual_review_action_lock_recommendation"], "ready_for_manual_action_review")
            self.assertFalse(lock["archive_created"])
            self.assertFalse(lock["submission_started"])
            self.assertEqual(lock["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
