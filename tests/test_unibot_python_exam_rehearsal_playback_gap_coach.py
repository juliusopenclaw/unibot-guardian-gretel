from __future__ import annotations

import copy
import json
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_full_local_rehearsal_pack import build_python_exam_full_local_rehearsal_pack
from unibot.python_exam_rehearsal_playback_gap_coach import build_python_exam_rehearsal_playback_gap_coach
from unibot.server import route_request

from tests.test_unibot_python_exam_full_local_rehearsal_pack import full_rehearsal_inputs


def ready_full_rehearsal_pack() -> dict:
    inputs = full_rehearsal_inputs()
    return build_python_exam_full_local_rehearsal_pack(
        exam_skill_drilldown=inputs["drilldown"],
        python_exam_local_cycle_readiness_review=inputs["local_review"],
        python_exam_local_cycle_readiness_handoff=inputs["local_handoff"],
        python_exam_local_cycle_operator_workspace_card=inputs["workspace_card"],
        exam_workspace_operator_run=inputs["operator"],
        exam_workspace_session_console=inputs["session"],
        exam_workspace_run_history_export_review=inputs["run_history"],
        exam_run_packet=inputs["exam_run_packet"],
        exam_packet_timeline=inputs["exam_packet_timeline"],
        timeline_export_review_packet=inputs["review"],
        timeline_export_receipt_journal_summary=inputs["journal"],
        review_chain_integrity_check=inputs["chain"],
        python_exam_readiness_console=inputs["readiness"],
        selected_skill_tag="python_lists",
    )


class UniBotPythonExamRehearsalPlaybackGapCoachTests(unittest.TestCase):
    def test_gap_coach_routes_open_confirmations_before_human_review_packet(self) -> None:
        pack = ready_full_rehearsal_pack()
        report = build_python_exam_rehearsal_playback_gap_coach(
            python_exam_full_local_rehearsal_pack=pack,
            selected_skill_tag="python_lists",
        )
        payload = json.dumps(report, ensure_ascii=False)

        self.assertEqual(report["artifact_type"], "python_exam_rehearsal_playback_gap_coach")
        self.assertEqual(report["status"], "python_exam_rehearsal_playback_gap_coach_ready")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertEqual(report["next_safe_action_key"], "review_operator_confirmation")
        self.assertTrue(report["gap_profile"]["operator_confirmation_gap"])
        self.assertEqual(report["source_anchor_metadata"]["source_anchor_count"], 2)
        self.assertEqual(report["a0_a2_help_status"]["status"], "a0_a2_only")
        self.assertGreaterEqual(report["notebook_checkpoint_metadata"]["checkpoint_hash_count"], 1)
        self.assertEqual(report["evidence_playback"]["evidence_preview_status"], "python_exam_evidence_export_preview_ready")
        self.assertEqual(report["evidence_playback"]["human_handoff_status"], "python_exam_human_handoff_packet_ready")
        self.assertTrue(report["dry_run_default"])
        self.assertFalse(report["local_writes_executed_by_gap_coach"])
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
        self.assertEqual(scan_text(payload, "python-exam-rehearsal-playback-gap-coach")["status"], "pass")
        self.assertEqual(report["public_safety_status"], "pass")

    def test_gap_coach_marks_fully_confirmed_pack_for_human_review_packet(self) -> None:
        pack = ready_full_rehearsal_pack()
        pack["operator_confirmation_status"]["open_operator_confirmation_count"] = 0
        pack["operator_confirmation_status"]["confirmed_count"] = pack["operator_confirmation_status"]["write_step_count"]
        pack["rehearsal_summary"]["open_operator_confirmation_count"] = 0

        report = build_python_exam_rehearsal_playback_gap_coach(
            python_exam_full_local_rehearsal_pack=pack,
            selected_skill_tag="python_lists",
        )

        self.assertEqual(report["next_safe_action_key"], "ready_for_human_review_packet")
        self.assertTrue(report["gap_profile"]["ready_for_human_review_packet"])

    def test_gap_coach_routes_missing_artifact_before_other_actions(self) -> None:
        pack = ready_full_rehearsal_pack()
        pack["rehearsal_steps"] = copy.deepcopy(pack["rehearsal_steps"])
        pack["rehearsal_steps"][0]["step_status"] = "missing"
        pack["rehearsal_summary"]["missing_step_count"] = 1

        report = build_python_exam_rehearsal_playback_gap_coach(
            python_exam_full_local_rehearsal_pack=pack,
            selected_skill_tag="python_lists",
        )

        self.assertEqual(report["next_safe_action_key"], "resolve_missing_artifact")
        self.assertIn("skill_selection", report["gap_profile"]["missing_artifact_step_ids"])

    def test_gap_coach_routes_source_gap(self) -> None:
        pack = ready_full_rehearsal_pack()
        pack["source_anchor_metadata"] = {
            "source_card_ids": [],
            "source_anchor_count": 0,
            "source_anchored": False,
        }

        report = build_python_exam_rehearsal_playback_gap_coach(
            python_exam_full_local_rehearsal_pack=pack,
            selected_skill_tag="python_lists",
        )

        self.assertEqual(report["next_safe_action_key"], "resolve_source_gap")
        self.assertTrue(report["gap_profile"]["source_gap"])

    def test_gap_coach_routes_operator_confirmation_gap(self) -> None:
        pack = ready_full_rehearsal_pack()
        pack["operator_confirmation_status"]["open_operator_confirmation_count"] = 2

        report = build_python_exam_rehearsal_playback_gap_coach(
            python_exam_full_local_rehearsal_pack=pack,
            selected_skill_tag="python_lists",
        )

        self.assertEqual(report["next_safe_action_key"], "review_operator_confirmation")
        self.assertTrue(report["gap_profile"]["operator_confirmation_gap"])

    def test_gap_coach_routes_a0_a2_gap(self) -> None:
        pack = ready_full_rehearsal_pack()
        pack["operator_confirmation_status"]["open_operator_confirmation_count"] = 0
        pack["operator_confirmation_status"]["confirmed_count"] = pack["operator_confirmation_status"]["write_step_count"]
        pack["a0_a2_help_status"] = {
            "status": "nonstandard_help_attention",
            "profile": {"A2": 1, "A3": 1},
            "nonstandard_help_event_count": 1,
        }

        report = build_python_exam_rehearsal_playback_gap_coach(
            python_exam_full_local_rehearsal_pack=pack,
            selected_skill_tag="python_lists",
        )

        self.assertEqual(report["next_safe_action_key"], "continue_a0_a2_drill")
        self.assertTrue(report["gap_profile"]["a0_a2_profile_gap"])

    def test_gap_coach_api_route(self) -> None:
        status, report = route_request(
            "/api/unibot/course/python-exam-rehearsal-playback-gap-coach",
            payload={
                "python_exam_full_local_rehearsal_pack": ready_full_rehearsal_pack(),
                "selected_skill_tag": "python_lists",
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(report["next_safe_action_key"], "review_operator_confirmation")
        self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
