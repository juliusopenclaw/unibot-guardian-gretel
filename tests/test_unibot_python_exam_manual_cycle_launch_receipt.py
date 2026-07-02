from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_local_cycle_manual_confirmation_console import (
    build_python_exam_local_cycle_manual_confirmation_console,
)
from unibot.python_exam_manual_cycle_launch_receipt import build_python_exam_manual_cycle_launch_receipt
from unibot.server import route_request

from tests.test_unibot_python_exam_local_cycle_manual_confirmation_console import manual_confirmation_inputs


def launch_receipt_inputs(temp_dir: str, *, confirmed: bool) -> tuple[dict, dict, dict, dict]:
    review, handoff, workspace_card, chain_snapshot = manual_confirmation_inputs(temp_dir, confirmed=confirmed)
    console = build_python_exam_local_cycle_manual_confirmation_console(
        python_exam_local_cycle_readiness_review=review,
        python_exam_local_cycle_readiness_handoff=handoff,
        python_exam_local_cycle_operator_workspace_card=workspace_card,
        python_exam_local_cycle_chain_snapshot=chain_snapshot,
        selected_skill_tag="python_lists",
    )
    return console, chain_snapshot, workspace_card, handoff


class UniBotPythonExamManualCycleLaunchReceiptTests(unittest.TestCase):
    def test_launch_receipt_stays_in_confirmation_review_for_open_confirmations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, chain_snapshot, workspace_card, handoff = launch_receipt_inputs(temp_dir, confirmed=False)
            receipt = build_python_exam_manual_cycle_launch_receipt(
                python_exam_manual_confirmation_console=console,
                python_exam_local_cycle_chain_snapshot=chain_snapshot,
                python_exam_local_cycle_operator_workspace_card=workspace_card,
                python_exam_local_cycle_readiness_handoff=handoff,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(receipt, ensure_ascii=False)
            summary = receipt["launch_receipt_summary"]

            self.assertEqual(receipt["artifact_type"], "python_exam_manual_cycle_launch_receipt")
            self.assertEqual(receipt["status"], "python_exam_manual_cycle_launch_receipt_ready")
            self.assertEqual(receipt["exam_deployment_status"], "not_cleared")
            self.assertEqual(receipt["launch_decision"], "stay_in_confirmation_review")
            self.assertEqual(summary["launch_decision_reason"], "manual_confirmation_review_not_finished")
            self.assertEqual(summary["open_confirmation_count"], 5)
            self.assertEqual(summary["confirmed_count"], 0)
            self.assertEqual(summary["help_level"], "A2")
            self.assertTrue(receipt["operator_run_prefill"]["prefill_hash"])
            self.assertTrue(receipt["manual_cycle_launch_receipt"]["not_cleared_receipt"])
            self.assertFalse(receipt["local_writes_requested"])
            self.assertFalse(receipt["local_execution_started"])
            self.assertTrue(receipt["dry_run_default"])
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
                self.assertFalse(receipt[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-manual-cycle-launch-receipt")["status"], "pass")
            self.assertEqual(receipt["public_safety_status"], "pass")

    def test_launch_receipt_ready_after_confirmed_hash_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, chain_snapshot, workspace_card, handoff = launch_receipt_inputs(temp_dir, confirmed=True)
            receipt = build_python_exam_manual_cycle_launch_receipt(
                python_exam_manual_confirmation_console=console,
                python_exam_local_cycle_chain_snapshot=chain_snapshot,
                python_exam_local_cycle_operator_workspace_card=workspace_card,
                python_exam_local_cycle_readiness_handoff=handoff,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(receipt["launch_decision"], "ready_for_manual_local_cycle")
            self.assertEqual(receipt["launch_receipt_summary"]["confirmed_count"], 5)
            self.assertEqual(receipt["launch_receipt_summary"]["open_confirmation_count"], 0)
            self.assertEqual(receipt["public_safety_status"], "pass")

    def test_launch_receipt_refreshes_when_manual_console_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _console, chain_snapshot, workspace_card, handoff = launch_receipt_inputs(temp_dir, confirmed=False)
            receipt = build_python_exam_manual_cycle_launch_receipt(
                python_exam_local_cycle_chain_snapshot=chain_snapshot,
                python_exam_local_cycle_operator_workspace_card=workspace_card,
                python_exam_local_cycle_readiness_handoff=handoff,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(receipt["launch_decision"], "refresh_manual_console")
            self.assertEqual(receipt["public_safety_status"], "pass")

    def test_launch_receipt_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, chain_snapshot, workspace_card, handoff = launch_receipt_inputs(temp_dir, confirmed=False)
            status, receipt = route_request(
                "/api/unibot/course/python-exam-manual-cycle-launch-receipt",
                {
                    "python_exam_manual_confirmation_console": console,
                    "python_exam_local_cycle_chain_snapshot": chain_snapshot,
                    "python_exam_local_cycle_operator_workspace_card": workspace_card,
                    "python_exam_local_cycle_readiness_handoff": handoff,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(receipt["status"], "python_exam_manual_cycle_launch_receipt_ready")
            self.assertEqual(receipt["launch_decision"], "stay_in_confirmation_review")
            self.assertEqual(receipt["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
