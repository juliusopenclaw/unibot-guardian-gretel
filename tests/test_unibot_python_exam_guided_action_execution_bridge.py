from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_active_study_guided_runner import build_python_exam_active_study_guided_runner
from unibot.python_exam_guided_action_execution_bridge import build_python_exam_guided_action_execution_bridge
from unibot.server import route_request

from tests.test_unibot_python_exam_active_study_guided_runner import ready_guided_inputs


def ready_bridge_inputs(temp_dir: str) -> tuple[dict, dict, dict]:
    active, launcher, control = ready_guided_inputs(temp_dir)
    guided = build_python_exam_active_study_guided_runner(
        python_exam_active_study_loop_dashboard=active,
        python_exam_resume_launcher=launcher,
        python_exam_drill_loop_control_panel=control,
        selected_skill_tag="python_lists",
    )
    progress = {
        "status": "write_preview_ready",
        "journal_written": False,
        "exam_deployment_status": "not_cleared",
    }
    return guided, control, progress


class UniBotPythonExamGuidedActionExecutionBridgeTests(unittest.TestCase):
    def test_execution_bridge_previews_control_panel_cycle_without_raw_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            guided, control, progress = ready_bridge_inputs(temp_dir)
            report = build_python_exam_guided_action_execution_bridge(
                python_exam_active_study_guided_runner=guided,
                python_exam_drill_loop_control_panel=control,
                python_exam_drill_loop_progress_journal=progress,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(report, ensure_ascii=False)
            summary = report["execution_bridge_summary"]
            preview = report["control_panel_cycle_preview"]
            matrix = report["operator_confirmation_matrix"]

            self.assertEqual(report["artifact_type"], "python_exam_guided_action_execution_bridge")
            self.assertEqual(report["status"], "python_exam_guided_action_execution_bridge_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(summary["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["action"], "run_next_microtask")
            self.assertEqual(summary["route"], "control_panel")
            self.assertEqual(summary["endpoint"], "/api/unibot/course/python-exam-drill-loop-control-panel")
            self.assertEqual(summary["preview_status"], "control_panel_execution_preview_ready")
            self.assertTrue(summary["ready"])
            self.assertTrue(summary["a0_a2_only"])
            self.assertEqual(preview["selected_task_hash"], guided["guided_action_card"]["selected_task_hash"])
            self.assertEqual(preview["checkpoint_hash"], guided["guided_action_card"]["checkpoint_hash"])
            self.assertEqual(preview["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
            self.assertEqual(preview["help_level"], "A2")
            self.assertEqual(preview["progress_journal_preview_status"], "write_preview_ready")
            self.assertFalse(preview["progress_journal_written"])
            self.assertTrue(preview["preview_hash"])
            self.assertEqual(matrix["status"], "all_steps_dry_run")
            self.assertEqual(matrix["confirmed_count"], 0)
            self.assertFalse(matrix["local_writes_requested"])
            self.assertFalse(report["local_writes_requested"])
            self.assertTrue(report["dry_run_default"])
            self.assertTrue(report["execution_bridge_receipt"]["not_cleared_receipt"])
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
            self.assertEqual(scan_text(payload, "python-exam-guided-action-execution-bridge")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_execution_bridge_previews_dashboard_return(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            active, launcher, control = ready_guided_inputs(temp_dir)
            guided = build_python_exam_active_study_guided_runner(
                python_exam_active_study_loop_dashboard=active,
                python_exam_resume_launcher=launcher,
                python_exam_drill_loop_control_panel=control,
                selected_skill_tag="python_lists",
                requested_action="return_to_skill_dashboard",
            )
            report = build_python_exam_guided_action_execution_bridge(
                python_exam_active_study_guided_runner=guided,
                python_exam_drill_loop_control_panel=control,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(report["status"], "python_exam_guided_action_execution_bridge_ready")
            self.assertEqual(report["execution_bridge_summary"]["route"], "skill_dashboard")
            self.assertEqual(report["dashboard_return_preview"]["status"], "dashboard_return_preview_ready")
            self.assertEqual(report["dashboard_return_preview"]["endpoint"], "/api/unibot/course/exam-coverage-dashboard")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_execution_bridge_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            guided, control, progress = ready_bridge_inputs(temp_dir)
            status, report = route_request(
                "/api/unibot/course/python-exam-guided-action-execution-bridge",
                {
                    "python_exam_active_study_guided_runner": guided,
                    "python_exam_drill_loop_control_panel": control,
                    "python_exam_drill_loop_progress_journal": progress,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "python_exam_guided_action_execution_bridge_ready")
            self.assertEqual(report["execution_bridge_summary"]["action"], "run_next_microtask")
            self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
