from __future__ import annotations

import copy
import json
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_gap_coach_guided_rehearsal_loop import build_python_exam_gap_coach_guided_rehearsal_loop
from unibot.python_exam_rehearsal_playback_gap_coach import build_python_exam_rehearsal_playback_gap_coach
from unibot.server import route_request

from tests.test_unibot_python_exam_rehearsal_playback_gap_coach import ready_full_rehearsal_pack


def gap_coach_for(action_key: str = "") -> dict:
    pack = ready_full_rehearsal_pack()
    if action_key == "ready_for_human_review_packet":
        pack["operator_confirmation_status"]["open_operator_confirmation_count"] = 0
        pack["operator_confirmation_status"]["confirmed_count"] = pack["operator_confirmation_status"]["write_step_count"]
        pack["rehearsal_summary"]["open_operator_confirmation_count"] = 0
    if action_key == "resolve_missing_artifact":
        pack["rehearsal_steps"] = copy.deepcopy(pack["rehearsal_steps"])
        pack["rehearsal_steps"][0]["step_status"] = "missing"
    if action_key == "resolve_source_gap":
        pack["source_anchor_metadata"] = {"source_card_ids": [], "source_anchor_count": 0, "source_anchored": False}
    if action_key == "continue_a0_a2_drill":
        pack["operator_confirmation_status"]["open_operator_confirmation_count"] = 0
        pack["a0_a2_help_status"] = {
            "status": "nonstandard_help_attention",
            "profile": {"A2": 1, "A3": 1},
            "nonstandard_help_event_count": 1,
        }
    coach = build_python_exam_rehearsal_playback_gap_coach(
        python_exam_full_local_rehearsal_pack=pack,
        selected_skill_tag="python_lists",
    )
    if action_key == "ready_to_rehearse_again":
        coach["next_safe_action_key"] = "ready_to_rehearse_again"
    return coach


class UniBotPythonExamGapCoachGuidedRehearsalLoopTests(unittest.TestCase):
    def test_guided_loop_prepares_operator_confirmation_review(self) -> None:
        report = build_python_exam_gap_coach_guided_rehearsal_loop(
            python_exam_rehearsal_playback_gap_coach=gap_coach_for(),
            selected_skill_tag="python_lists",
        )
        payload = json.dumps(report, ensure_ascii=False)

        self.assertEqual(report["artifact_type"], "python_exam_gap_coach_guided_rehearsal_loop")
        self.assertEqual(report["status"], "python_exam_gap_coach_guided_rehearsal_loop_ready")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertEqual(report["requested_action_key"], "review_operator_confirmation")
        self.assertEqual(report["guided_step"]["route"], "operator_confirmation_review")
        self.assertGreaterEqual(len(report["operator_confirmation_review_cards"]), 1)
        self.assertTrue(report["guided_step"]["safe_prefill"]["prefill_hash"])
        self.assertTrue(report["guided_loop_receipt"]["not_cleared_receipt"])
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
        self.assertEqual(scan_text(payload, "python-exam-gap-coach-guided-rehearsal-loop")["status"], "pass")
        self.assertEqual(report["public_safety_status"], "pass")

    def test_guided_loop_routes_all_safe_action_keys(self) -> None:
        expected_routes = {
            "resolve_missing_artifact": "metadata_artifact_repair",
            "resolve_source_gap": "source_checkpoint_review",
            "continue_a0_a2_drill": "a0_a2_drill",
            "ready_to_rehearse_again": "full_rehearsal_dry_run",
            "ready_for_human_review_packet": "human_review_packet",
        }
        for action_key, route in expected_routes.items():
            report = build_python_exam_gap_coach_guided_rehearsal_loop(
                python_exam_rehearsal_playback_gap_coach=gap_coach_for(action_key),
                selected_skill_tag="python_lists",
                requested_action_key=action_key,
            )
            self.assertEqual(report["requested_action_key"], action_key)
            self.assertEqual(report["guided_step"]["route"], route)
            self.assertEqual(report["public_safety_status"], "pass")

    def test_guided_loop_api_route(self) -> None:
        status, report = route_request(
            "/api/unibot/course/python-exam-gap-coach-guided-rehearsal-loop",
            payload={
                "python_exam_rehearsal_playback_gap_coach": gap_coach_for(),
                "selected_skill_tag": "python_lists",
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(report["requested_action_key"], "review_operator_confirmation")
        self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
