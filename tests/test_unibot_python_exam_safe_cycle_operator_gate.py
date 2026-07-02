from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate
from unibot.server import route_request

from tests.test_unibot_python_exam_safe_cycle_console import ready_safe_cycle_inputs
from unibot.python_exam_safe_cycle_console import build_python_exam_safe_cycle_console


def ready_gate_input(temp_dir: str) -> dict:
    active, guided, bridge, control, progress = ready_safe_cycle_inputs(temp_dir)
    return build_python_exam_safe_cycle_console(
        python_exam_active_study_loop_dashboard=active,
        python_exam_active_study_guided_runner=guided,
        python_exam_guided_action_execution_bridge=bridge,
        python_exam_drill_loop_control_panel=control,
        python_exam_drill_loop_progress_journal=progress,
        selected_skill_tag="python_lists",
    )


class UniBotPythonExamSafeCycleOperatorGateTests(unittest.TestCase):
    def test_operator_gate_builds_separate_false_confirmation_cards_without_raw_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console = ready_gate_input(temp_dir)
            report = build_python_exam_safe_cycle_operator_gate(
                python_exam_safe_cycle_console=console,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(report, ensure_ascii=False)
            summary = report["operator_gate_summary"]
            cards = report["confirmation_cards"]
            matrix = report["operator_confirmation_matrix"]

            self.assertEqual(report["artifact_type"], "python_exam_safe_cycle_operator_gate")
            self.assertEqual(report["status"], "python_exam_safe_cycle_operator_gate_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(summary["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["gate_status"], "operator_gate_ready_for_human_review")
            self.assertEqual(summary["next_safe_action"], "run_next_microtask")
            self.assertEqual(summary["confirmation_card_count"], 5)
            self.assertEqual(summary["confirmed_count"], 0)
            self.assertFalse(summary["local_writes_started"])
            self.assertTrue(summary["a0_a2_only"])
            self.assertEqual(
                [card["step_id"] for card in cards],
                [
                    "open_control_panel",
                    "prepare_notebook_checkpoint",
                    "use_a0_a2_help",
                    "review_help_ledger_preview",
                    "prepare_progress_journal_append",
                ],
            )
            for card in cards:
                self.assertEqual(card["status"], "operator_confirmation_required_dry_run")
                self.assertFalse(card["operator_confirmed"])
                self.assertFalse(card["write_started"])
                self.assertTrue(card["local_write_preview_only"])
                self.assertEqual(card["help_level"], "A2")
                self.assertEqual(card["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
                self.assertTrue(card["card_hash"])
            self.assertEqual(matrix["status"], "all_steps_waiting_for_operator_confirmation")
            self.assertEqual(matrix["confirmed_count"], 0)
            self.assertFalse(matrix["local_writes_requested"])
            self.assertFalse(report["local_writes_requested"])
            self.assertTrue(report["dry_run_default"])
            self.assertTrue(report["operator_gate_receipt"]["not_cleared_receipt"])
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
                self.assertFalse(report[flag], flag)
            self.assertNotIn("private_active_study_attempt", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-safe-cycle-operator-gate")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_operator_gate_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console = ready_gate_input(temp_dir)
            status, report = route_request(
                "/api/unibot/course/python-exam-safe-cycle-operator-gate",
                {
                    "python_exam_safe_cycle_console": console,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "python_exam_safe_cycle_operator_gate_ready")
            self.assertEqual(report["operator_gate_summary"]["confirmation_card_count"], 5)
            self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
