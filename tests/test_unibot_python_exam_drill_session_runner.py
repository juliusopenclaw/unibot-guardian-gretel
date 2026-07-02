from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from unibot.public_safety import scan_text
from unibot.python_exam_drill_session_runner import build_python_exam_drill_session_runner
from unibot.python_exam_source_grounded_tutor_drill_pack import (
    build_python_exam_source_grounded_tutor_drill_pack,
)
from unibot.server import route_request

from tests.test_unibot_python_exam_source_grounded_tutor_drill_pack import ready_inputs


def ready_pack_and_carryover(temp_dir: str) -> tuple[dict, dict]:
    dashboard, drilldown, carryover = ready_inputs(temp_dir)
    pack = build_python_exam_source_grounded_tutor_drill_pack(
        course_exam_coverage_dashboard=dashboard,
        exam_skill_drilldown=drilldown,
        skill_to_workspace_session_carryover=carryover,
        selected_skill_tag="python_lists",
        max_drills=1,
    )
    return pack, carryover


class UniBotPythonExamDrillSessionRunnerTests(unittest.TestCase):
    def test_runs_selected_microtask_as_hash_only_a0_a2_drill_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pack, carryover = ready_pack_and_carryover(temp_dir)
            journal_path = Path(temp_dir) / "checkpoint_journal.jsonl"
            microtask = pack["skill_drills"][0]["microtasks"][0]
            report = build_python_exam_drill_session_runner(
                python_exam_tutor_drill_pack=pack,
                skill_to_workspace_session_carryover=carryover,
                selected_skill_tag="python_lists",
                selected_task_hash=microtask["task_hash"],
                cell_source="private_work = []\n# local notebook only\n",
                student_reflection="Ich habe erst vorhergesagt und dann lokal geprueft.",
                checkpoint_journal_path=journal_path,
                operator_confirmed_checkpoint_store=False,
            )
            payload = json.dumps(report, ensure_ascii=False)
            summary = report["drill_session_summary"]
            checkpoint = report["notebook_checkpoint_adapter_summary"]
            ledger = report["help_ledger_preview"]

            self.assertEqual(report["artifact_type"], "python_exam_drill_session_runner")
            self.assertEqual(report["status"], "python_exam_drill_session_runner_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["selected_skill_tag"], "python_lists")
            self.assertEqual(report["selected_microtask"]["task_hash"], microtask["task_hash"])
            self.assertEqual(report["selected_microtask"]["help_level"], "A2")
            self.assertFalse(report["selected_microtask"]["complete_code_returned"])
            self.assertFalse(report["selected_microtask"]["solution_returned"])
            self.assertEqual(summary["pack_status"], "python_exam_source_grounded_tutor_drill_pack_ready")
            self.assertEqual(summary["drill_status"], "drill_ready")
            self.assertEqual(summary["checkpoint_status"], "notebook_checkpoint_ready")
            self.assertEqual(summary["study_receipt_status"], "ok_study_session_receipt")
            self.assertEqual(summary["help_status"], "a0_a2_only")
            self.assertEqual(summary["carryover_status"], "skill_to_workspace_session_carryover_ready")
            self.assertEqual(checkpoint["status"], "notebook_checkpoint_ready")
            self.assertEqual(checkpoint["study_receipt_status"], "ok_study_session_receipt")
            self.assertTrue(checkpoint["notebook_work_sha256"])
            self.assertFalse(checkpoint["checkpoint_journal_written"])
            self.assertFalse(checkpoint["raw_cell_returned"])
            self.assertFalse(checkpoint["notebook_code_returned"])
            self.assertFalse(checkpoint["local_paths_returned"])
            self.assertEqual(ledger["status"], "preview_ready")
            self.assertTrue(ledger["event_hash"])
            self.assertFalse(ledger["ledger_written"])
            self.assertEqual(report["carryover_reference"]["session_receipt_id"], carryover["carryover_summary"]["session_receipt_id"])
            self.assertTrue(report["drill_session_receipt"]["not_cleared_receipt"])
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
                "ranking_returned",
                "automatic_grading_started",
                "proctoring_started",
                "ai_detection_started",
                "exam_clearance_claimed",
            ]:
                self.assertFalse(report[flag], flag)
            self.assertFalse(journal_path.exists())
            self.assertNotIn("private_work", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-drill-session-runner")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_api_route_runs_drill_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pack, carryover = ready_pack_and_carryover(temp_dir)
            status, report = route_request(
                "/api/unibot/course/python-exam-drill-session-runner",
                {
                    "python_exam_tutor_drill_pack": pack,
                    "skill_to_workspace_session_carryover": carryover,
                    "selected_skill_tag": "python_lists",
                    "cell_source": "local_attempt = []",
                    "student_reflection": "Eigene Vorhersage geprueft.",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "python_exam_drill_session_runner_ready")
            self.assertEqual(report["selected_skill_tag"], "python_lists")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_attention_without_local_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pack, carryover = ready_pack_and_carryover(temp_dir)
            report = build_python_exam_drill_session_runner(
                python_exam_tutor_drill_pack=pack,
                skill_to_workspace_session_carryover=carryover,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(report["status"], "python_exam_drill_session_runner_attention")
            self.assertEqual(report["drill_session_summary"]["checkpoint_status"], "notebook_checkpoint_waiting_for_local_cell")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")


if __name__ == "__main__":
    unittest.main()
