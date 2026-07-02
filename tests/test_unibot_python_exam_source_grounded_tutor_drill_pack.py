from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_source_grounded_tutor_drill_pack import (
    build_python_exam_source_grounded_tutor_drill_pack,
)
from unibot.server import route_request
from unibot.skill_to_workspace_session_carryover import build_skill_to_workspace_session_carryover

from tests.test_unibot_skill_to_workspace_session_carryover import ready_live_flow


def ready_inputs(temp_dir: str) -> tuple[dict, dict, dict]:
    live_flow = ready_live_flow(temp_dir)
    drilldown = live_flow["exam_skill_drilldown"]
    carryover = build_skill_to_workspace_session_carryover(skill_to_workspace_live_flow=live_flow)
    dashboard = {
        "artifact_type": "course_exam_coverage_dashboard",
        "status": "course_exam_coverage_dashboard_ready",
        "exam_deployment_status": "not_cleared",
        "skill_dashboard": [
            {
                "skill_tag": "python_lists",
                "title": "Python lists",
                "exam_task_type": "notebook_skill",
                "workspace_readiness": "ready_for_exam_workspace_dry_run",
                "source_anchor_count": 2,
                "reviewed_notebook_anchor_count": 1,
                "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
                "checkpoint_hash_count": 1,
                "help_level_profile": {"A2": 1},
                "open_operator_confirmation_count": 2,
                "allowed_exam_help": ["A0 accessibility", "A1 source and syntax", "A2 socratic check"],
            }
        ],
    }
    return dashboard, drilldown, carryover


class UniBotPythonExamSourceGroundedTutorDrillPackTests(unittest.TestCase):
    def test_builds_source_grounded_a0_a2_drill_pack_without_raw_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dashboard, drilldown, carryover = ready_inputs(temp_dir)
            report = build_python_exam_source_grounded_tutor_drill_pack(
                course_exam_coverage_dashboard=dashboard,
                exam_skill_drilldown=drilldown,
                skill_to_workspace_session_carryover=carryover,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(report, ensure_ascii=False)
            summary = report["drill_pack_summary"]
            drill = report["skill_drills"][0]
            checkpoint = drill["notebook_checkpoint_suggestions"]
            ledger = drill["help_ledger_preview"]

            self.assertEqual(report["artifact_type"], "python_exam_source_grounded_tutor_drill_pack")
            self.assertEqual(report["status"], "python_exam_source_grounded_tutor_drill_pack_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["skill_count"], 1)
            self.assertEqual(summary["ready_drill_count"], 1)
            self.assertGreaterEqual(summary["microtask_count"], 2)
            self.assertGreaterEqual(summary["retrieval_question_count"], 1)
            self.assertEqual(summary["checkpoint_template_count"], 1)
            self.assertEqual(summary["help_status"], "a0_a2_only")
            self.assertEqual(summary["carryover_status"], "skill_to_workspace_session_carryover_ready")
            self.assertEqual(drill["status"], "drill_ready")
            self.assertEqual(drill["skill_tag"], "python_lists")
            self.assertEqual(drill["allowed_help_levels"], ["A0", "A1", "A2"])
            self.assertEqual(drill["source_anchor_metadata"]["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
            self.assertGreaterEqual(drill["source_anchor_metadata"]["source_anchor_count"], 1)
            self.assertGreaterEqual(len(drill["microtasks"]), 2)
            self.assertTrue(drill["microtasks"][0]["task_hash"])
            self.assertFalse(drill["microtasks"][0]["complete_code_returned"])
            self.assertFalse(drill["microtasks"][0]["solution_returned"])
            self.assertFalse(drill["microtasks"][0]["values_returned"])
            self.assertFalse(drill["retrieval_questions"][0]["raw_query_returned"])
            self.assertFalse(drill["retrieval_questions"][0]["raw_source_text_returned"])
            self.assertEqual(checkpoint["status"], "checkpoint_template_ready")
            self.assertTrue(checkpoint["checkpoint_template_hash"])
            self.assertFalse(checkpoint["notebook_code_returned"])
            self.assertFalse(checkpoint["local_paths_returned"])
            self.assertEqual(ledger["help_level"], "A2")
            self.assertFalse(ledger["write_default"])
            self.assertEqual(report["pack_receipt"]["exam_deployment_status"], "not_cleared")
            self.assertTrue(report["pack_receipt"]["not_cleared_receipt"])
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
            self.assertNotIn("own_attempt", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-source-grounded-tutor-drill-pack")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_api_route_builds_pack(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dashboard, drilldown, carryover = ready_inputs(temp_dir)
            status, report = route_request(
                "/api/unibot/course/python-exam-source-grounded-tutor-drill-pack",
                {
                    "course_exam_coverage_dashboard": dashboard,
                    "exam_skill_drilldown": drilldown,
                    "skill_to_workspace_session_carryover": carryover,
                    "selected_skill_tag": "python_lists",
                    "max_drills": 1,
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "python_exam_source_grounded_tutor_drill_pack_ready")
            self.assertEqual(report["skill_drills"][0]["skill_tag"], "python_lists")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_marks_attention_when_source_anchors_are_missing(self) -> None:
        report = build_python_exam_source_grounded_tutor_drill_pack(
            course_exam_coverage_dashboard={
                "status": "course_exam_coverage_dashboard_ready",
                "skill_dashboard": [
                    {
                        "skill_tag": "python_lists",
                        "workspace_readiness": "needs_source_anchor_review",
                        "source_anchor_count": 0,
                        "source_card_ids": [],
                    }
                ],
            },
            selected_skill_tag="python_lists",
        )

        self.assertEqual(report["status"], "python_exam_source_grounded_tutor_drill_pack_attention")
        self.assertEqual(report["skill_drills"][0]["status"], "drill_attention_needs_source_anchor")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")


if __name__ == "__main__":
    unittest.main()
