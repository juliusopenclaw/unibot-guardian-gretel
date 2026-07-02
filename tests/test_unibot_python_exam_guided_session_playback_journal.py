from __future__ import annotations

import copy
import json
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_guided_loop_control_surface import build_python_exam_guided_loop_control_surface
from unibot.python_exam_guided_session_playback_journal import build_python_exam_guided_session_playback_journal
from unibot.server import route_request

from tests.test_unibot_python_exam_guided_loop_control_surface import guided_loop_for


def control_surface_for(action_key: str = "") -> dict:
    coach, loop = guided_loop_for(action_key)
    return build_python_exam_guided_loop_control_surface(
        python_exam_gap_coach_guided_rehearsal_loop=loop,
        python_exam_rehearsal_playback_gap_coach=coach,
        selected_skill_tag="python_lists",
    )


class UniBotPythonExamGuidedSessionPlaybackJournalTests(unittest.TestCase):
    def test_journal_records_surface_hashes_and_resume_confirmation_review(self) -> None:
        surface = control_surface_for()
        report = build_python_exam_guided_session_playback_journal(
            python_exam_guided_loop_control_surface=surface,
            selected_skill_tag="python_lists",
        )
        payload = json.dumps(report, ensure_ascii=False)

        self.assertEqual(report["artifact_type"], "python_exam_guided_session_playback_journal")
        self.assertEqual(report["status"], "python_exam_guided_session_playback_journal_ready")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertEqual(report["journal_summary"]["entry_count"], 1)
        self.assertEqual(report["resume_decision"]["decision"], "review_open_confirmation")
        self.assertEqual(report["latest_entry"]["action_key"], "review_operator_confirmation")
        self.assertTrue(report["latest_entry"]["prefill_hash"])
        self.assertTrue(report["latest_entry"]["surface_receipt_hash"])
        self.assertGreaterEqual(report["latest_entry"]["source_anchor_count"], 1)
        self.assertGreaterEqual(report["latest_entry"]["checkpoint_hash_count"], 1)
        self.assertTrue(report["journal_receipt"]["not_cleared_receipt"])
        self.assertFalse(report["local_writes_requested"])
        self.assertFalse(report["local_execution_started"])
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
        self.assertEqual(scan_text(payload, "python-exam-guided-session-playback-journal")["status"], "pass")
        self.assertEqual(report["public_safety_status"], "pass")

    def test_journal_resume_decisions_cover_safe_routes(self) -> None:
        cases = {
            "resolve_source_gap": "refresh_source_checkpoint",
            "continue_a0_a2_drill": "continue_a0_a2_drill",
            "ready_to_rehearse_again": "repeat_dry_run_rehearsal",
            "ready_for_human_review_packet": "handoff_to_human_review",
        }
        for action_key, decision in cases.items():
            surface = control_surface_for(action_key)
            if action_key == "continue_a0_a2_drill":
                surface = copy.deepcopy(surface)
                surface["operator_confirmation_status"]["open_operator_confirmation_count"] = 0
                surface["control_summary"]["open_operator_confirmation_count"] = 0
            report = build_python_exam_guided_session_playback_journal(
                python_exam_guided_loop_control_surface=surface,
                selected_skill_tag="python_lists",
            )
            self.assertEqual(report["resume_decision"]["decision"], decision)
            self.assertEqual(report["public_safety_status"], "pass")

    def test_journal_can_include_previous_surfaces(self) -> None:
        first = control_surface_for()
        second = control_surface_for("ready_to_rehearse_again")
        report = build_python_exam_guided_session_playback_journal(
            previous_control_surfaces=[first],
            python_exam_guided_loop_control_surface=second,
            selected_skill_tag="python_lists",
        )

        self.assertEqual(report["journal_summary"]["entry_count"], 2)
        self.assertEqual(len(report["journal_entries"]), 2)
        self.assertEqual(report["latest_entry"]["action_key"], "ready_to_rehearse_again")

    def test_journal_api_route(self) -> None:
        status, report = route_request(
            "/api/unibot/course/python-exam-guided-session-playback-journal",
            payload={
                "python_exam_guided_loop_control_surface": control_surface_for(),
                "selected_skill_tag": "python_lists",
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "python_exam_guided_session_playback_journal_ready")
        self.assertEqual(report["resume_decision"]["decision"], "review_open_confirmation")
        self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
