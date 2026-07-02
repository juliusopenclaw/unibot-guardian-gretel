from __future__ import annotations

import json
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_gap_coach_guided_rehearsal_loop import build_python_exam_gap_coach_guided_rehearsal_loop
from unibot.python_exam_guided_loop_control_surface import build_python_exam_guided_loop_control_surface
from unibot.server import route_request

from tests.test_unibot_python_exam_gap_coach_guided_rehearsal_loop import gap_coach_for


def guided_loop_for(action_key: str = "") -> tuple[dict, dict]:
    coach = gap_coach_for(action_key)
    loop = build_python_exam_gap_coach_guided_rehearsal_loop(
        python_exam_rehearsal_playback_gap_coach=coach,
        selected_skill_tag="python_lists",
        requested_action_key=action_key,
    )
    return coach, loop


class UniBotPythonExamGuidedLoopControlSurfaceTests(unittest.TestCase):
    def test_control_surface_renders_operator_confirmation_next_click(self) -> None:
        coach, loop = guided_loop_for()
        report = build_python_exam_guided_loop_control_surface(
            python_exam_gap_coach_guided_rehearsal_loop=loop,
            python_exam_rehearsal_playback_gap_coach=coach,
            selected_skill_tag="python_lists",
        )
        payload = json.dumps(report, ensure_ascii=False)

        self.assertEqual(report["artifact_type"], "python_exam_guided_loop_control_surface")
        self.assertEqual(report["status"], "python_exam_guided_loop_control_surface_ready")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertEqual(report["control_summary"]["action_key"], "review_operator_confirmation")
        self.assertEqual(report["control_summary"]["next_safe_click"], "review_operator_confirmation_cards")
        self.assertEqual(report["current_guided_step_card"]["route"], "operator_confirmation_review")
        self.assertTrue(report["current_guided_step_card"]["prefill_hash"])
        self.assertGreaterEqual(report["operator_confirmation_status"]["open_operator_confirmation_count"], 1)
        self.assertGreaterEqual(report["source_anchor_status"]["source_anchor_count"], 1)
        self.assertGreaterEqual(report["notebook_checkpoint_status"]["checkpoint_hash_count"], 1)
        self.assertEqual(report["a0_a2_help_status"]["allowed_help_boundary"], "A0-A2")
        self.assertTrue(report["evidence_status"]["evidence_preview_receipt_id"])
        self.assertTrue(report["surface_receipt"]["not_cleared_receipt"])
        self.assertFalse(report["dry_run_request_executed_by_surface"])
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
        self.assertEqual(scan_text(payload, "python-exam-guided-loop-control-surface")["status"], "pass")
        self.assertEqual(report["public_safety_status"], "pass")

    def test_control_surface_can_mark_dry_run_request_confirmed_without_executing(self) -> None:
        coach, loop = guided_loop_for()
        report = build_python_exam_guided_loop_control_surface(
            python_exam_gap_coach_guided_rehearsal_loop=loop,
            python_exam_rehearsal_playback_gap_coach=coach,
            operator_confirmed_dry_run_request=True,
        )

        self.assertEqual(report["control_summary"]["dry_run_request_status"], "dry_run_request_confirmed_for_next_call")
        self.assertEqual(report["control_clicks"][1]["dry_run_request_status"], "confirmed_for_next_dry_run_request")
        self.assertFalse(report["dry_run_request_executed_by_surface"])
        self.assertFalse(report["local_writes_executed_by_surface"])

    def test_control_surface_routes_all_action_keys_to_clicks(self) -> None:
        expected_clicks = {
            "resolve_missing_artifact": "review_missing_artifact_card",
            "resolve_source_gap": "review_source_checkpoint_cards",
            "continue_a0_a2_drill": "prepare_a0_a2_drill_dry_run",
            "ready_to_rehearse_again": "prepare_full_rehearsal_dry_run",
            "ready_for_human_review_packet": "open_human_review_packet_metadata",
        }
        for action_key, click_id in expected_clicks.items():
            coach, loop = guided_loop_for(action_key)
            report = build_python_exam_guided_loop_control_surface(
                python_exam_gap_coach_guided_rehearsal_loop=loop,
                python_exam_rehearsal_playback_gap_coach=coach,
            )
            self.assertEqual(report["control_summary"]["action_key"], action_key)
            self.assertEqual(report["control_summary"]["next_safe_click"], click_id)
            self.assertEqual(report["public_safety_status"], "pass")

    def test_control_surface_api_route(self) -> None:
        coach, loop = guided_loop_for()
        status, report = route_request(
            "/api/unibot/course/python-exam-guided-loop-control-surface",
            payload={
                "python_exam_gap_coach_guided_rehearsal_loop": loop,
                "python_exam_rehearsal_playback_gap_coach": coach,
                "selected_skill_tag": "python_lists",
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "python_exam_guided_loop_control_surface_ready")
        self.assertEqual(report["control_summary"]["next_safe_click"], "review_operator_confirmation_cards")
        self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
