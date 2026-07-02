from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_manual_cycle_closure_ledger import build_python_exam_manual_cycle_closure_ledger
from unibot.python_exam_manual_post_cycle_receipt_intake import (
    build_python_exam_manual_post_cycle_receipt_intake,
)
from unibot.server import route_request

from tests.test_unibot_python_exam_manual_post_cycle_receipt_intake import (
    complete_hash_metadata,
    intake_inputs,
)


def closure_ledger_inputs(temp_dir: str, *, confirmed: bool, mode: str = "missing") -> tuple[dict, dict, dict, dict]:
    binder, launch_receipt, console = intake_inputs(temp_dir, confirmed=confirmed)
    metadata = None
    if mode == "complete":
        metadata = complete_hash_metadata(binder)
    elif mode == "reject":
        metadata = complete_hash_metadata(binder)
        metadata["notebook_code"] = "print('raw solution code')"
    intake = build_python_exam_manual_post_cycle_receipt_intake(
        python_exam_manual_cycle_evidence_binder=binder,
        python_exam_manual_cycle_launch_receipt=launch_receipt,
        python_exam_manual_confirmation_console=console,
        post_cycle_hash_metadata=metadata,
        selected_skill_tag="python_lists",
    )
    return intake, binder, launch_receipt, console


class UniBotPythonExamManualCycleClosureLedgerTests(unittest.TestCase):
    def test_closure_ledger_keeps_cycle_open_for_open_post_cycle_intake(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            intake, binder, launch_receipt, console = closure_ledger_inputs(temp_dir, confirmed=False)
            ledger = build_python_exam_manual_cycle_closure_ledger(
                python_exam_manual_post_cycle_receipt_intake=intake,
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(ledger, ensure_ascii=False)
            summary = ledger["closure_summary"]

            self.assertEqual(ledger["artifact_type"], "python_exam_manual_cycle_closure_ledger")
            self.assertEqual(ledger["status"], "python_exam_manual_cycle_closure_ledger_ready")
            self.assertEqual(ledger["exam_deployment_status"], "not_cleared")
            self.assertEqual(ledger["closure_ledger_decision"], "keep_cycle_open")
            self.assertEqual(summary["post_cycle_review_recommendation"], "keep_post_cycle_review_open")
            self.assertEqual(summary["next_safe_review_action"], "continue_manual_cycle_review")
            self.assertEqual(summary["help_level"], "A2")
            self.assertTrue(ledger["manual_cycle_closure_ledger_receipt"]["not_cleared_receipt"])
            self.assertEqual(len(ledger["closure_ledger_entries"]), 4)
            self.assertFalse(ledger["local_writes_requested"])
            self.assertFalse(ledger["local_execution_started"])
            self.assertTrue(ledger["dry_run_default"])
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
            self.assertEqual(scan_text(payload, "python-exam-manual-cycle-closure-ledger")["status"], "pass")
            self.assertEqual(ledger["public_safety_status"], "pass")

    def test_closure_ledger_requests_post_cycle_hash_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            intake, binder, launch_receipt, console = closure_ledger_inputs(temp_dir, confirmed=True)
            ledger = build_python_exam_manual_cycle_closure_ledger(
                python_exam_manual_post_cycle_receipt_intake=intake,
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(ledger["closure_ledger_decision"], "request_post_cycle_hash_review")
            self.assertIn("notebook_checkpoint_hash", ledger["closure_summary"]["missing_required_hashes"])
            self.assertEqual(ledger["closure_summary"]["next_safe_review_action"], "collect_missing_post_cycle_hash_metadata")
            self.assertEqual(ledger["public_safety_status"], "pass")

    def test_closure_ledger_closes_hash_only_cycle_for_human_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            intake, binder, launch_receipt, console = closure_ledger_inputs(temp_dir, confirmed=True, mode="complete")
            ledger = build_python_exam_manual_cycle_closure_ledger(
                python_exam_manual_post_cycle_receipt_intake=intake,
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                selected_skill_tag="python_lists",
            )
            accepted = ledger["closure_summary"]["accepted_post_cycle_hashes"]

            self.assertEqual(ledger["closure_ledger_decision"], "close_cycle_for_human_review")
            self.assertEqual(
                ledger["closure_summary"]["post_cycle_review_recommendation"],
                "accept_hash_only_post_cycle_receipt_for_human_review",
            )
            self.assertTrue(accepted["notebook_checkpoint_hash"])
            self.assertTrue(accepted["help_ledger_entry_hash"])
            self.assertTrue(accepted["operator_reflection_hash"])
            self.assertEqual(ledger["closure_summary"]["next_safe_review_action"], "review_closed_cycle_evidence_with_human")
            self.assertEqual(ledger["public_safety_status"], "pass")

    def test_closure_ledger_rejects_cycle_closure_for_rejected_intake(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            intake, binder, launch_receipt, console = closure_ledger_inputs(temp_dir, confirmed=True, mode="reject")
            ledger = build_python_exam_manual_cycle_closure_ledger(
                python_exam_manual_post_cycle_receipt_intake=intake,
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(ledger["closure_ledger_decision"], "reject_cycle_closure")
            self.assertIn("notebook_code", ledger["closure_summary"]["forbidden_metadata_keys"])
            self.assertFalse(ledger["notebook_code_returned"])
            self.assertEqual(ledger["public_safety_status"], "pass")

    def test_closure_ledger_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            intake, binder, launch_receipt, console = closure_ledger_inputs(temp_dir, confirmed=True, mode="complete")
            status, ledger = route_request(
                "/api/unibot/course/python-exam-manual-cycle-closure-ledger",
                {
                    "python_exam_manual_post_cycle_receipt_intake": intake,
                    "python_exam_manual_cycle_evidence_binder": binder,
                    "python_exam_manual_cycle_launch_receipt": launch_receipt,
                    "python_exam_manual_confirmation_console": console,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(ledger["status"], "python_exam_manual_cycle_closure_ledger_ready")
            self.assertEqual(ledger["closure_ledger_decision"], "close_cycle_for_human_review")
            self.assertEqual(ledger["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
