from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from unibot.public_safety import scan_text
from unibot.python_exam_drill_loop_control_panel import build_python_exam_drill_loop_control_panel
from unibot.python_exam_drill_loop_progress_journal import (
    build_python_exam_drill_loop_progress_journal,
    summarize_python_exam_drill_loop_progress_journal,
)
from unibot.server import route_request

from tests.test_unibot_python_exam_drill_session_runner import ready_pack_and_carryover


def ready_control_panel(temp_dir: str) -> dict:
    pack, carryover = ready_pack_and_carryover(temp_dir)
    return build_python_exam_drill_loop_control_panel(
        python_exam_tutor_drill_pack=pack,
        skill_to_workspace_session_carryover=carryover,
        selected_skill_tag="python_lists",
        cell_source="private_progress_attempt = []\n# local only\n",
        student_reflection="Ich habe erst vorhergesagt und dann lokal geprueft.",
    )


class UniBotPythonExamDrillLoopProgressJournalTests(unittest.TestCase):
    def test_progress_journal_previews_resume_record_without_write_or_raw_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            panel = ready_control_panel(temp_dir)
            journal_path = Path(temp_dir) / "progress.jsonl"
            report = build_python_exam_drill_loop_progress_journal(
                python_exam_drill_loop_control_panel=panel,
                progress_journal_path=journal_path,
                operator_confirmed_progress_journal_append=False,
            )
            payload = json.dumps(report, ensure_ascii=False)
            entry = report["journal_entry_preview"]
            resume = report["resume_state"]

            self.assertEqual(report["artifact_type"], "python_exam_drill_loop_progress_journal")
            self.assertEqual(report["status"], "write_preview_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertFalse(report["journal_written"])
            self.assertFalse(journal_path.exists())
            self.assertEqual(entry["skill_tag"], "python_lists")
            self.assertEqual(entry["microtask_hash"], panel["control_panel_summary"]["current_task_hash"])
            self.assertEqual(entry["checkpoint_hash"], panel["control_panel_summary"]["checkpoint_hash"])
            self.assertEqual(entry["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
            self.assertEqual(entry["help_level"], "A2")
            self.assertTrue(entry["help_ledger_event_hash"])
            self.assertTrue(entry["carryover_session_receipt_id"])
            self.assertTrue(entry["review_loop_receipt_id"])
            self.assertEqual(entry["next_step_action"], "run_next_microtask")
            self.assertEqual(entry["reflection_status"], "ok_study_session_receipt")
            self.assertTrue(entry["not_cleared_receipt"])
            self.assertEqual(resume["status"], "resume_ready")
            self.assertEqual(resume["last_safe_microtask_hash"], entry["microtask_hash"])
            self.assertEqual(resume["next_microtask_hash"], entry["next_task_hash"])
            self.assertEqual(resume["resume_action"], "run_next_microtask")
            self.assertEqual(resume["accepted_record_count"], 1)
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
            self.assertEqual(scan_text(payload, "python-exam-drill-loop-progress-journal")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_confirmed_progress_journal_append_writes_jsonl_without_returning_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            panel = ready_control_panel(temp_dir)
            journal_path = Path(temp_dir) / "progress.jsonl"
            report = build_python_exam_drill_loop_progress_journal(
                python_exam_drill_loop_control_panel=panel,
                progress_journal_path=journal_path,
                operator_confirmed_progress_journal_append=True,
            )
            payload = json.dumps(report, ensure_ascii=False)
            records = [json.loads(line) for line in journal_path.read_text(encoding="utf-8").splitlines()]
            summary = summarize_python_exam_drill_loop_progress_journal(journal_path)

            self.assertEqual(report["status"], "stored")
            self.assertTrue(report["journal_written"])
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["status"], "accepted")
            self.assertEqual(records[0]["entry"]["skill_tag"], "python_lists")
            self.assertEqual(summary["resume_state"]["accepted_record_count"], 1)
            self.assertEqual(summary["resume_state"]["resume_action"], "run_next_microtask")
            self.assertNotIn(str(journal_path), payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertEqual(summary["public_safety_status"], "pass")

    def test_progress_journal_api_route_blocks_unready_control_panel_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            status, report = route_request(
                "/api/unibot/course/python-exam-drill-loop-progress-journal",
                {
                    "python_exam_drill_loop_control_panel": {
                        "artifact_type": "python_exam_drill_loop_control_panel",
                        "status": "python_exam_drill_loop_control_panel_attention",
                        "exam_deployment_status": "not_cleared",
                        "public_safety_status": "pass",
                    },
                    "progress_journal_path": str(Path(temp_dir) / "progress.jsonl"),
                    "operator_confirmed_progress_journal_append": True,
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "blocked_record_not_accepted")
            self.assertFalse(report["journal_written"])
            self.assertIn("control_panel_must_be_ready", report["journal_entry_preview"]["issues"])


if __name__ == "__main__":
    unittest.main()
