from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_drill_loop_progress_journal import build_python_exam_drill_loop_progress_journal
from unibot.python_exam_resume_launcher import build_python_exam_resume_launcher
from unibot.server import route_request

from tests.test_unibot_python_exam_drill_loop_progress_journal import ready_control_panel


class UniBotPythonExamResumeLauncherTests(unittest.TestCase):
    def test_resume_launcher_prefills_next_microtask_from_progress_journal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            panel = ready_control_panel(temp_dir)
            progress = build_python_exam_drill_loop_progress_journal(
                python_exam_drill_loop_control_panel=panel,
                operator_confirmed_progress_journal_append=False,
            )
            report = build_python_exam_resume_launcher(
                python_exam_drill_loop_progress_journal=progress,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(report, ensure_ascii=False)
            decision = report["resume_decision"]
            prefill = report["control_panel_prefill"]

            self.assertEqual(report["artifact_type"], "python_exam_resume_launcher")
            self.assertEqual(report["status"], "python_exam_resume_launcher_next_microtask_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(decision["action"], "run_next_microtask")
            self.assertEqual(decision["route"], "control_panel")
            self.assertEqual(decision["selected_skill_tag"], "python_lists")
            self.assertEqual(
                decision["selected_task_hash"],
                progress["journal_entry_preview"]["next_task_hash"],
            )
            self.assertEqual(prefill["endpoint"], "/api/unibot/course/python-exam-drill-loop-control-panel")
            self.assertEqual(prefill["selected_task_hash"], decision["selected_task_hash"])
            self.assertEqual(prefill["requested_help_level"], "A2")
            self.assertEqual(prefill["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
            self.assertTrue(prefill["prefill_hash"])
            self.assertFalse(report["local_writes_requested"])
            self.assertTrue(report["dry_run_default"])
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
            self.assertNotIn("private_progress_attempt", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-resume-launcher")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_resume_launcher_prefills_repeat_current_microtask_from_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            panel = ready_control_panel(temp_dir)
            progress = build_python_exam_drill_loop_progress_journal(
                python_exam_drill_loop_control_panel=panel,
                operator_confirmed_progress_journal_append=False,
            )
            record = dict(progress["preview_record"])
            record["entry"] = dict(record["entry"])
            record["entry"]["next_step_action"] = "repeat_current_microtask"
            record["entry"]["next_task_hash"] = ""
            report = build_python_exam_resume_launcher(previous_records=[record])

            self.assertEqual(report["status"], "python_exam_resume_launcher_repeat_microtask_ready")
            self.assertEqual(report["resume_decision"]["action"], "repeat_current_microtask")
            self.assertEqual(report["resume_decision"]["selected_task_hash"], record["entry"]["microtask_hash"])
            self.assertEqual(
                report["control_panel_prefill"]["selected_task_hash"],
                record["entry"]["microtask_hash"],
            )
            self.assertEqual(report["public_safety_status"], "pass")

    def test_resume_launcher_starts_first_microtask_when_journal_is_empty(self) -> None:
        report = build_python_exam_resume_launcher(selected_skill_tag="python_lists")

        self.assertEqual(report["status"], "python_exam_resume_launcher_first_microtask_ready")
        self.assertEqual(report["resume_decision"]["action"], "start_first_microtask")
        self.assertEqual(report["control_panel_prefill"]["endpoint"], "/api/unibot/course/python-exam-drill-loop-control-panel")
        self.assertEqual(report["control_panel_prefill"]["selected_skill_tag"], "python_lists")
        self.assertEqual(report["control_panel_prefill"]["selected_task_hash"], "")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertEqual(report["public_safety_status"], "pass")

    def test_resume_launcher_api_route_accepts_progress_journal_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            panel = ready_control_panel(temp_dir)
            progress = build_python_exam_drill_loop_progress_journal(
                python_exam_drill_loop_control_panel=panel,
                operator_confirmed_progress_journal_append=False,
            )
            status, report = route_request(
                "/api/unibot/course/python-exam-resume-launcher",
                {
                    "python_exam_drill_loop_progress_journal": progress,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "python_exam_resume_launcher_next_microtask_ready")
            self.assertEqual(report["resume_decision"]["action"], "run_next_microtask")
            self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
