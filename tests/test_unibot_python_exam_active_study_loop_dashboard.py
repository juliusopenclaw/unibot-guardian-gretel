from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_active_study_loop_dashboard import build_python_exam_active_study_loop_dashboard
from unibot.python_exam_drill_loop_control_panel import build_python_exam_drill_loop_control_panel
from unibot.python_exam_drill_loop_progress_journal import build_python_exam_drill_loop_progress_journal
from unibot.python_exam_resume_launcher import build_python_exam_resume_launcher
from unibot.server import route_request

from tests.test_unibot_python_exam_source_grounded_tutor_drill_pack import ready_inputs
from unibot.python_exam_source_grounded_tutor_drill_pack import build_python_exam_source_grounded_tutor_drill_pack


def ready_active_inputs(temp_dir: str) -> tuple[dict, dict, dict, dict, dict]:
    dashboard, drilldown, carryover = ready_inputs(temp_dir)
    pack = build_python_exam_source_grounded_tutor_drill_pack(
        course_exam_coverage_dashboard=dashboard,
        exam_skill_drilldown=drilldown,
        skill_to_workspace_session_carryover=carryover,
        selected_skill_tag="python_lists",
        max_drills=1,
    )
    control = build_python_exam_drill_loop_control_panel(
        python_exam_tutor_drill_pack=pack,
        skill_to_workspace_session_carryover=carryover,
        selected_skill_tag="python_lists",
        cell_source="private_active_study_attempt = []\n",
        student_reflection="Ich habe erst vorhergesagt und dann lokal geprueft.",
    )
    journal = build_python_exam_drill_loop_progress_journal(
        python_exam_drill_loop_control_panel=control,
        operator_confirmed_progress_journal_append=False,
    )
    launcher = build_python_exam_resume_launcher(
        python_exam_drill_loop_progress_journal=journal,
        selected_skill_tag="python_lists",
    )
    return dashboard, pack, control, journal, launcher


class UniBotPythonExamActiveStudyLoopDashboardTests(unittest.TestCase):
    def test_active_study_loop_dashboard_merges_skill_loop_state_without_raw_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dashboard, pack, control, journal, launcher = ready_active_inputs(temp_dir)
            report = build_python_exam_active_study_loop_dashboard(
                course_exam_coverage_dashboard=dashboard,
                python_exam_tutor_drill_pack=pack,
                python_exam_drill_loop_control_panel=control,
                python_exam_drill_loop_progress_journal=journal,
                python_exam_resume_launcher=launcher,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(report, ensure_ascii=False)
            summary = report["active_study_summary"]
            row = report["skill_loop_dashboard"][0]

            self.assertEqual(report["artifact_type"], "python_exam_active_study_loop_dashboard")
            self.assertEqual(report["status"], "python_exam_active_study_loop_dashboard_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(summary["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["active_resume_action"], "run_next_microtask")
            self.assertEqual(summary["next_safe_action"], "run_next_microtask")
            self.assertEqual(summary["skill_count"], 1)
            self.assertEqual(summary["workspace_ready_skill_count"], 1)
            self.assertTrue(summary["a0_a2_only"])
            self.assertEqual(row["skill_tag"], "python_lists")
            self.assertEqual(row["workspace_readiness"], "ready_for_exam_workspace_dry_run")
            self.assertEqual(row["drill_status"], "drill_ready")
            self.assertEqual(row["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
            self.assertEqual(row["source_coverage_status"], "source_coverage_ready")
            self.assertEqual(row["last_safe_microtask_hash"], journal["journal_entry_preview"]["microtask_hash"])
            self.assertEqual(row["next_microtask_hash"], launcher["resume_decision"]["selected_task_hash"])
            self.assertEqual(row["next_safe_action"], "run_next_microtask")
            self.assertEqual(row["help_level"], "A2")
            self.assertTrue(row["checkpoint_hash"])
            self.assertTrue(row["help_ledger_event_hash"])
            self.assertTrue(row["carryover_session_receipt_id"])
            self.assertTrue(row["review_loop_receipt_id"])
            self.assertTrue(row["control_panel_receipt_id"])
            self.assertTrue(row["prefill_hash"])
            self.assertFalse(report["local_writes_requested"])
            self.assertTrue(report["dry_run_default"])
            self.assertTrue(report["active_study_loop_receipt"]["not_cleared_receipt"])
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
            self.assertEqual(scan_text(payload, "python-exam-active-study-loop-dashboard")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_active_study_loop_dashboard_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dashboard, pack, control, journal, launcher = ready_active_inputs(temp_dir)
            status, report = route_request(
                "/api/unibot/course/python-exam-active-study-loop-dashboard",
                {
                    "course_exam_coverage_dashboard": dashboard,
                    "python_exam_tutor_drill_pack": pack,
                    "python_exam_drill_loop_control_panel": control,
                    "python_exam_drill_loop_progress_journal": journal,
                    "python_exam_resume_launcher": launcher,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "python_exam_active_study_loop_dashboard_ready")
            self.assertEqual(report["active_study_summary"]["next_safe_action"], "run_next_microtask")
            self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
