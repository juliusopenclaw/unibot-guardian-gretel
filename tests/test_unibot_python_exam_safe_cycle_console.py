from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_active_study_guided_runner import build_python_exam_active_study_guided_runner
from unibot.python_exam_active_study_loop_dashboard import build_python_exam_active_study_loop_dashboard
from unibot.python_exam_guided_action_execution_bridge import build_python_exam_guided_action_execution_bridge
from unibot.python_exam_safe_cycle_console import build_python_exam_safe_cycle_console
from unibot.server import route_request

from tests.test_unibot_python_exam_active_study_loop_dashboard import ready_active_inputs


def ready_safe_cycle_inputs(temp_dir: str) -> tuple[dict, dict, dict, dict, dict]:
    dashboard, pack, control, progress, launcher = ready_active_inputs(temp_dir)
    active = build_python_exam_active_study_loop_dashboard(
        course_exam_coverage_dashboard=dashboard,
        python_exam_tutor_drill_pack=pack,
        python_exam_drill_loop_control_panel=control,
        python_exam_drill_loop_progress_journal=progress,
        python_exam_resume_launcher=launcher,
        selected_skill_tag="python_lists",
    )
    guided = build_python_exam_active_study_guided_runner(
        python_exam_active_study_loop_dashboard=active,
        python_exam_resume_launcher=launcher,
        python_exam_drill_loop_control_panel=control,
        selected_skill_tag="python_lists",
    )
    bridge = build_python_exam_guided_action_execution_bridge(
        python_exam_active_study_guided_runner=guided,
        python_exam_drill_loop_control_panel=control,
        python_exam_drill_loop_progress_journal=progress,
        selected_skill_tag="python_lists",
    )
    return active, guided, bridge, control, progress


class UniBotPythonExamSafeCycleConsoleTests(unittest.TestCase):
    def test_safe_cycle_console_merges_current_cycle_without_raw_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            active, guided, bridge, control, progress = ready_safe_cycle_inputs(temp_dir)
            report = build_python_exam_safe_cycle_console(
                python_exam_active_study_loop_dashboard=active,
                python_exam_active_study_guided_runner=guided,
                python_exam_guided_action_execution_bridge=bridge,
                python_exam_drill_loop_control_panel=control,
                python_exam_drill_loop_progress_journal=progress,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(report, ensure_ascii=False)
            summary = report["safe_cycle_summary"]
            view = report["current_cycle_view"]
            preview = view["preview"]
            receipts = view["receipts"]
            matrix = view["operator_confirmation_matrix"]

            self.assertEqual(report["artifact_type"], "python_exam_safe_cycle_console")
            self.assertEqual(report["status"], "python_exam_safe_cycle_console_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(summary["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["cycle_status"], "safe_cycle_ready_for_operator_review")
            self.assertEqual(summary["next_safe_action"], "run_next_microtask")
            self.assertEqual(summary["route"], "control_panel")
            self.assertEqual(summary["preview_status"], "control_panel_execution_preview_ready")
            self.assertTrue(summary["ready"])
            self.assertTrue(summary["a0_a2_only"])
            self.assertEqual(preview["selected_task_hash"], guided["guided_action_card"]["selected_task_hash"])
            self.assertEqual(preview["checkpoint_hash"], control["control_panel_summary"]["checkpoint_hash"])
            self.assertEqual(preview["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
            self.assertEqual(preview["help_level"], "A2")
            self.assertEqual(receipts["execution_bridge_receipt_id"], bridge["execution_bridge_receipt"]["receipt_id"])
            self.assertEqual(receipts["control_panel_receipt_id"], control["control_panel_receipt"]["receipt_id"])
            self.assertEqual(receipts["progress_entry_hash"], progress["journal_entry_preview"]["entry_hash"])
            self.assertTrue(receipts["help_ledger_event_hash"])
            self.assertTrue(receipts["review_loop_receipt_id"])
            self.assertFalse(receipts["progress_journal_written"])
            self.assertEqual(matrix["status"], "all_steps_dry_run")
            self.assertEqual(matrix["confirmed_count"], 0)
            self.assertFalse(matrix["local_writes_requested"])
            self.assertFalse(report["local_writes_requested"])
            self.assertTrue(report["dry_run_default"])
            self.assertTrue(report["safe_cycle_receipt"]["not_cleared_receipt"])
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
            self.assertEqual(scan_text(payload, "python-exam-safe-cycle-console")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_safe_cycle_console_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            active, guided, bridge, control, progress = ready_safe_cycle_inputs(temp_dir)
            status, report = route_request(
                "/api/unibot/course/python-exam-safe-cycle-console",
                {
                    "python_exam_active_study_loop_dashboard": active,
                    "python_exam_active_study_guided_runner": guided,
                    "python_exam_guided_action_execution_bridge": bridge,
                    "python_exam_drill_loop_control_panel": control,
                    "python_exam_drill_loop_progress_journal": progress,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "python_exam_safe_cycle_console_ready")
            self.assertEqual(report["safe_cycle_summary"]["next_safe_action"], "run_next_microtask")
            self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
