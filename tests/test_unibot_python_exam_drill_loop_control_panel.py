from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_drill_loop_control_panel import build_python_exam_drill_loop_control_panel
from unibot.server import route_request

from tests.test_unibot_python_exam_drill_session_runner import ready_pack_and_carryover


class UniBotPythonExamDrillLoopControlPanelTests(unittest.TestCase):
    def test_control_panel_runs_pack_session_review_cycle_without_raw_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pack, carryover = ready_pack_and_carryover(temp_dir)
            report = build_python_exam_drill_loop_control_panel(
                python_exam_tutor_drill_pack=pack,
                skill_to_workspace_session_carryover=carryover,
                selected_skill_tag="python_lists",
                cell_source="private_control_panel_attempt = []\n",
                student_reflection="Ich habe den Schritt lokal reflektiert.",
            )
            payload = json.dumps(report, ensure_ascii=False)
            summary = report["control_panel_summary"]
            artifacts = report["control_panel_artifacts"]
            current = report["current_microtask"]
            evidence = report["session_evidence_summary"]
            next_step = report["next_step_recommendation"]

            self.assertEqual(report["artifact_type"], "python_exam_drill_loop_control_panel")
            self.assertEqual(report["status"], "python_exam_drill_loop_control_panel_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(summary["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["pack_status"], "python_exam_source_grounded_tutor_drill_pack_ready")
            self.assertEqual(summary["session_status"], "python_exam_drill_session_runner_ready")
            self.assertEqual(summary["review_loop_status"], "python_exam_drill_session_review_loop_ready")
            self.assertEqual(summary["next_step_action"], "run_next_microtask")
            self.assertEqual(summary["next_step_status"], "next_microtask_ready")
            self.assertEqual(summary["help_status"], "a0_a2_only")
            self.assertTrue(summary["current_task_hash"])
            self.assertTrue(summary["checkpoint_hash"])
            self.assertEqual(len(report["cycle_cards"]), 3)
            self.assertTrue(all(item["ready"] for item in report["cycle_cards"]))
            self.assertEqual(current["task_hash"], summary["current_task_hash"])
            self.assertEqual(current["next_action"], "run_next_microtask")
            self.assertEqual(evidence["checkpoint_hash"], summary["checkpoint_hash"])
            self.assertEqual(evidence["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
            self.assertEqual(evidence["help_level"], "A2")
            self.assertEqual(evidence["carryover_session_receipt_id"], carryover["carryover_summary"]["session_receipt_id"])
            self.assertEqual(next_step["action"], "run_next_microtask")
            self.assertEqual(next_step["help_level"], "A2")
            self.assertTrue(next_step["next_task_hash"])
            self.assertTrue(report["control_panel_receipt"]["not_cleared_receipt"])
            self.assertEqual(artifacts["drill_session_runner"]["status"], "python_exam_drill_session_runner_ready")
            self.assertEqual(artifacts["drill_session_review_loop"]["status"], "python_exam_drill_session_review_loop_ready")
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
            self.assertNotIn("private_control_panel_attempt", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-drill-loop-control-panel")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_api_route_builds_control_panel(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pack, carryover = ready_pack_and_carryover(temp_dir)
            status, report = route_request(
                "/api/unibot/course/python-exam-drill-loop-control-panel",
                {
                    "python_exam_tutor_drill_pack": pack,
                    "skill_to_workspace_session_carryover": carryover,
                    "selected_skill_tag": "python_lists",
                    "cell_source": "local_control_panel_attempt = []",
                    "student_reflection": "Lokal geprueft.",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "python_exam_drill_loop_control_panel_ready")
            self.assertEqual(report["control_panel_summary"]["next_step_action"], "run_next_microtask")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_control_panel_attention_without_local_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pack, carryover = ready_pack_and_carryover(temp_dir)
            report = build_python_exam_drill_loop_control_panel(
                python_exam_tutor_drill_pack=pack,
                skill_to_workspace_session_carryover=carryover,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(report["status"], "python_exam_drill_loop_control_panel_attention")
            self.assertEqual(report["control_panel_summary"]["session_status"], "python_exam_drill_session_runner_attention")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")


if __name__ == "__main__":
    unittest.main()
