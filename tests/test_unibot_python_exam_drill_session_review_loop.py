from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_drill_session_review_loop import build_python_exam_drill_session_review_loop
from unibot.python_exam_drill_session_runner import build_python_exam_drill_session_runner
from unibot.server import route_request

from tests.test_unibot_python_exam_drill_session_runner import ready_pack_and_carryover


def ready_session(temp_dir: str) -> tuple[dict, dict]:
    pack, carryover = ready_pack_and_carryover(temp_dir)
    first_task = pack["skill_drills"][0]["microtasks"][0]
    session = build_python_exam_drill_session_runner(
        python_exam_tutor_drill_pack=pack,
        skill_to_workspace_session_carryover=carryover,
        selected_skill_tag="python_lists",
        selected_task_hash=first_task["task_hash"],
        cell_source="private_review_loop_attempt = []\n",
        student_reflection="Ich habe den Check lokal reflektiert.",
    )
    return pack, session


class UniBotPythonExamDrillSessionReviewLoopTests(unittest.TestCase):
    def test_review_loop_suggests_next_microtask_without_score_or_solution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pack, session = ready_session(temp_dir)
            report = build_python_exam_drill_session_review_loop(
                python_exam_drill_session_runner=session,
                python_exam_tutor_drill_pack=pack,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(report, ensure_ascii=False)
            next_step = report["next_step_recommendation"]
            summary = report["review_loop_summary"]

            self.assertEqual(report["artifact_type"], "python_exam_drill_session_review_loop")
            self.assertEqual(report["status"], "python_exam_drill_session_review_loop_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["session_status"], "python_exam_drill_session_runner_ready")
            self.assertEqual(summary["pack_status"], "python_exam_source_grounded_tutor_drill_pack_ready")
            self.assertEqual(summary["next_step_status"], "next_microtask_ready")
            self.assertEqual(summary["next_step_action"], "run_next_microtask")
            self.assertTrue(summary["no_score_or_grade"])
            self.assertEqual(report["session_evidence_summary"]["microtask_hash"], session["selected_microtask"]["task_hash"])
            self.assertEqual(report["session_evidence_summary"]["checkpoint_hash"], session["notebook_checkpoint_adapter_summary"]["notebook_work_sha256"])
            self.assertEqual(report["source_anchor_metadata"]["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
            self.assertEqual(report["help_ledger_preview"]["status"], "preview_ready")
            self.assertEqual(report["carryover_reference"]["session_receipt_id"], session["carryover_reference"]["session_receipt_id"])
            self.assertEqual(report["reflection_status"]["status"], "reflection_metadata_present")
            self.assertEqual(next_step["action"], "run_next_microtask")
            self.assertEqual(next_step["help_level"], "A2")
            self.assertNotEqual(next_step["next_task_hash"], session["selected_microtask"]["task_hash"])
            self.assertTrue(report["review_loop_receipt"]["not_cleared_receipt"])
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
            self.assertNotIn("private_review_loop_attempt", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-drill-session-review-loop")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_api_route_builds_review_loop(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pack, session = ready_session(temp_dir)
            status, report = route_request(
                "/api/unibot/course/python-exam-drill-session-review-loop",
                {
                    "python_exam_drill_session_runner": session,
                    "python_exam_tutor_drill_pack": pack,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "python_exam_drill_session_review_loop_ready")
            self.assertEqual(report["next_step_recommendation"]["status"], "next_microtask_ready")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_review_loop_requires_repeat_when_session_evidence_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pack, carryover = ready_pack_and_carryover(temp_dir)
            incomplete = build_python_exam_drill_session_runner(
                python_exam_tutor_drill_pack=pack,
                skill_to_workspace_session_carryover=carryover,
                selected_skill_tag="python_lists",
            )
            report = build_python_exam_drill_session_review_loop(
                python_exam_drill_session_runner=incomplete,
                python_exam_tutor_drill_pack=pack,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(report["status"], "python_exam_drill_session_review_loop_attention")
            self.assertEqual(report["next_step_recommendation"]["action"], "repeat_current_microtask")
            self.assertEqual(report["next_step_recommendation"]["status"], "repeat_current_microtask_required")
            self.assertFalse(report["score_returned"])
            self.assertEqual(report["exam_deployment_status"], "not_cleared")


if __name__ == "__main__":
    unittest.main()
