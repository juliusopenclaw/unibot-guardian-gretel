from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_active_study_guided_runner import build_python_exam_active_study_guided_runner
from unibot.python_exam_active_study_loop_dashboard import build_python_exam_active_study_loop_dashboard
from unibot.server import route_request

from tests.test_unibot_python_exam_active_study_loop_dashboard import ready_active_inputs


def ready_guided_inputs(temp_dir: str) -> tuple[dict, dict, dict]:
    dashboard, pack, control, journal, launcher = ready_active_inputs(temp_dir)
    active = build_python_exam_active_study_loop_dashboard(
        course_exam_coverage_dashboard=dashboard,
        python_exam_tutor_drill_pack=pack,
        python_exam_drill_loop_control_panel=control,
        python_exam_drill_loop_progress_journal=journal,
        python_exam_resume_launcher=launcher,
        selected_skill_tag="python_lists",
    )
    return active, launcher, control


class UniBotPythonExamActiveStudyGuidedRunnerTests(unittest.TestCase):
    def test_guided_runner_builds_next_action_card_without_raw_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            active, launcher, control = ready_guided_inputs(temp_dir)
            report = build_python_exam_active_study_guided_runner(
                python_exam_active_study_loop_dashboard=active,
                python_exam_resume_launcher=launcher,
                python_exam_drill_loop_control_panel=control,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(report, ensure_ascii=False)
            summary = report["guided_runner_summary"]
            card = report["guided_action_card"]
            prefill = report["control_panel_prefill"]

            self.assertEqual(report["artifact_type"], "python_exam_active_study_guided_runner")
            self.assertEqual(report["status"], "python_exam_active_study_guided_runner_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(summary["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["action"], "run_next_microtask")
            self.assertEqual(summary["route"], "control_panel")
            self.assertEqual(summary["endpoint"], "/api/unibot/course/python-exam-drill-loop-control-panel")
            self.assertTrue(summary["ready"])
            self.assertTrue(summary["a0_a2_only"])
            self.assertEqual(card["selected_task_hash"], launcher["resume_decision"]["selected_task_hash"])
            self.assertEqual(card["checkpoint_hash"], control["control_panel_summary"]["checkpoint_hash"])
            self.assertEqual(card["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
            self.assertEqual(card["help_level"], "A2")
            self.assertEqual(card["operator_confirmations_default"], "all_false_dry_run")
            self.assertIn("checkpoint_store", card["operator_confirmations_required"])
            self.assertEqual(prefill["selected_task_hash"], card["selected_task_hash"])
            self.assertEqual(prefill["requested_help_level"], "A2")
            self.assertTrue(prefill["prefill_hash"])
            self.assertFalse(report["local_writes_requested"])
            self.assertTrue(report["dry_run_default"])
            self.assertTrue(report["guided_runner_receipt"]["not_cleared_receipt"])
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
            self.assertEqual(scan_text(payload, "python-exam-active-study-guided-runner")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_guided_runner_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            active, launcher, control = ready_guided_inputs(temp_dir)
            status, report = route_request(
                "/api/unibot/course/python-exam-active-study-guided-runner",
                {
                    "python_exam_active_study_loop_dashboard": active,
                    "python_exam_resume_launcher": launcher,
                    "python_exam_drill_loop_control_panel": control,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "python_exam_active_study_guided_runner_ready")
            self.assertEqual(report["guided_runner_summary"]["action"], "run_next_microtask")
            self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
