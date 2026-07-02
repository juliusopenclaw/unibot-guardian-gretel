from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_manual_cycle_evidence_binder import build_python_exam_manual_cycle_evidence_binder
from unibot.server import route_request

from tests.test_unibot_python_exam_manual_cycle_launch_receipt import launch_receipt_inputs
from unibot.python_exam_manual_cycle_launch_receipt import build_python_exam_manual_cycle_launch_receipt


def evidence_binder_inputs(temp_dir: str, *, confirmed: bool) -> tuple[dict, dict, dict, dict, dict]:
    console, chain_snapshot, workspace_card, handoff = launch_receipt_inputs(temp_dir, confirmed=confirmed)
    launch_receipt = build_python_exam_manual_cycle_launch_receipt(
        python_exam_manual_confirmation_console=console,
        python_exam_local_cycle_chain_snapshot=chain_snapshot,
        python_exam_local_cycle_operator_workspace_card=workspace_card,
        python_exam_local_cycle_readiness_handoff=handoff,
        selected_skill_tag="python_lists",
    )
    return launch_receipt, console, chain_snapshot, workspace_card, handoff


class UniBotPythonExamManualCycleEvidenceBinderTests(unittest.TestCase):
    def test_evidence_binder_keeps_confirmation_review_for_open_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            launch_receipt, console, chain_snapshot, workspace_card, _handoff = evidence_binder_inputs(
                temp_dir,
                confirmed=False,
            )
            binder = build_python_exam_manual_cycle_evidence_binder(
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                python_exam_local_cycle_chain_snapshot=chain_snapshot,
                python_exam_local_cycle_operator_workspace_card=workspace_card,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(binder, ensure_ascii=False)
            summary = binder["binder_summary"]
            evidence = binder["manual_cycle_evidence"]

            self.assertEqual(binder["artifact_type"], "python_exam_manual_cycle_evidence_binder")
            self.assertEqual(binder["status"], "python_exam_manual_cycle_evidence_binder_ready")
            self.assertEqual(binder["exam_deployment_status"], "not_cleared")
            self.assertEqual(binder["next_safe_review_action"], "continue_confirmation_review")
            self.assertEqual(summary["launch_decision"], "stay_in_confirmation_review")
            self.assertEqual(summary["open_confirmation_count"], 5)
            self.assertEqual(summary["confirmed_count"], 0)
            self.assertEqual(summary["help_level"], "A2")
            self.assertTrue(evidence["launch_receipt_hash"])
            self.assertTrue(evidence["manual_confirmation_console_receipt_hash"])
            self.assertTrue(evidence["chain_snapshot_hash"])
            self.assertTrue(evidence["help_ledger_preview_hash"])
            self.assertTrue(binder["manual_cycle_evidence_binder_receipt"]["not_cleared_receipt"])
            self.assertFalse(binder["local_writes_requested"])
            self.assertFalse(binder["local_execution_started"])
            self.assertTrue(binder["dry_run_default"])
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
                self.assertFalse(binder[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-manual-cycle-evidence-binder")["status"], "pass")
            self.assertEqual(binder["public_safety_status"], "pass")

    def test_evidence_binder_ready_after_confirmed_launch_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            launch_receipt, console, chain_snapshot, workspace_card, _handoff = evidence_binder_inputs(
                temp_dir,
                confirmed=True,
            )
            binder = build_python_exam_manual_cycle_evidence_binder(
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                python_exam_local_cycle_chain_snapshot=chain_snapshot,
                python_exam_local_cycle_operator_workspace_card=workspace_card,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(binder["next_safe_review_action"], "ready_for_human_manual_cycle_review")
            self.assertTrue(binder["binder_summary"]["required_hashes_present"])
            self.assertEqual(binder["binder_summary"]["confirmed_count"], 5)
            self.assertEqual(binder["binder_summary"]["open_confirmation_count"], 0)
            self.assertFalse(binder["cycle_review_window"]["post_cycle_execution_claimed"])
            self.assertEqual(binder["public_safety_status"], "pass")

    def test_evidence_binder_refreshes_when_launch_receipt_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _launch_receipt, console, chain_snapshot, workspace_card, _handoff = evidence_binder_inputs(
                temp_dir,
                confirmed=False,
            )
            binder = build_python_exam_manual_cycle_evidence_binder(
                python_exam_manual_confirmation_console=console,
                python_exam_local_cycle_chain_snapshot=chain_snapshot,
                python_exam_local_cycle_operator_workspace_card=workspace_card,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(binder["next_safe_review_action"], "refresh_launch_receipt")
            self.assertEqual(binder["public_safety_status"], "pass")

    def test_evidence_binder_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            launch_receipt, console, chain_snapshot, workspace_card, _handoff = evidence_binder_inputs(
                temp_dir,
                confirmed=False,
            )
            status, binder = route_request(
                "/api/unibot/course/python-exam-manual-cycle-evidence-binder",
                {
                    "python_exam_manual_cycle_launch_receipt": launch_receipt,
                    "python_exam_manual_confirmation_console": console,
                    "python_exam_local_cycle_chain_snapshot": chain_snapshot,
                    "python_exam_local_cycle_operator_workspace_card": workspace_card,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(binder["status"], "python_exam_manual_cycle_evidence_binder_ready")
            self.assertEqual(binder["next_safe_review_action"], "continue_confirmation_review")
            self.assertEqual(binder["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
