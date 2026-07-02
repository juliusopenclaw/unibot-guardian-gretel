from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_local_cycle_readiness_handoff import build_python_exam_local_cycle_readiness_handoff
from unibot.python_exam_local_cycle_readiness_review import build_python_exam_local_cycle_readiness_review
from unibot.python_exam_local_cycle_start_packet import build_python_exam_local_cycle_start_packet
from unibot.server import route_request

from tests.test_unibot_python_exam_local_cycle_start_packet import ready_start_packet_inputs


class UniBotPythonExamLocalCycleReadinessHandoffTests(unittest.TestCase):
    def test_handoff_prefills_operator_run_for_blocked_start_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, gate, decision = ready_start_packet_inputs(temp_dir)
            start_packet = build_python_exam_local_cycle_start_packet(
                python_exam_safe_cycle_console=console,
                python_exam_safe_cycle_operator_gate=gate,
                python_exam_operator_gate_decision_receipt=decision,
                selected_skill_tag="python_lists",
            )
            review = build_python_exam_local_cycle_readiness_review(
                python_exam_local_cycle_start_packet=start_packet,
                selected_skill_tag="python_lists",
            )
            report = build_python_exam_local_cycle_readiness_handoff(
                python_exam_local_cycle_readiness_review=review,
                python_exam_local_cycle_start_packet=start_packet,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(report, ensure_ascii=False)
            summary = report["handoff_summary"]
            prefill = report["operator_run_prefill"]
            manual = report["manual_local_cycle_handoff"]

            self.assertEqual(report["artifact_type"], "python_exam_local_cycle_readiness_handoff")
            self.assertEqual(report["status"], "python_exam_local_cycle_readiness_handoff_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertTrue(summary["ready_for_operator_prefill"])
            self.assertEqual(summary["recommendation"], "request_missing_confirmation_review")
            self.assertEqual(prefill["status"], "prefill_ready")
            self.assertEqual(prefill["endpoint"], "/api/unibot/exam-workspace/operator-run")
            self.assertEqual(prefill["selected_skill_tag"], "python_lists")
            self.assertEqual(prefill["requested_help_level"], "A2")
            self.assertEqual(manual["status"], "manual_local_cycle_handoff_ready")
            self.assertEqual(manual["next_operator_action"], "open_operator_run_prefill")
            self.assertTrue(report["handoff_receipt"]["not_cleared_receipt"])
            self.assertFalse(report["local_writes_requested"])
            self.assertFalse(report["local_execution_started"])
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
            self.assertNotIn("private_active_study_attempt", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-local-cycle-readiness-handoff")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_handoff_can_remain_attention_without_start_packet(self) -> None:
        report = build_python_exam_local_cycle_readiness_handoff(selected_skill_tag="python_lists")

        self.assertEqual(report["status"], "python_exam_local_cycle_readiness_handoff_attention")
        self.assertFalse(report["handoff_summary"]["ready_for_operator_prefill"])
        self.assertEqual(report["operator_run_prefill"]["status"], "prefill_attention")
        self.assertEqual(report["manual_local_cycle_handoff"]["status"], "manual_local_cycle_handoff_attention")

    def test_handoff_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, gate, decision = ready_start_packet_inputs(temp_dir)
            start_packet = build_python_exam_local_cycle_start_packet(
                python_exam_safe_cycle_console=console,
                python_exam_safe_cycle_operator_gate=gate,
                python_exam_operator_gate_decision_receipt=decision,
                selected_skill_tag="python_lists",
            )
            review = build_python_exam_local_cycle_readiness_review(
                python_exam_local_cycle_start_packet=start_packet,
                selected_skill_tag="python_lists",
            )
            status, report = route_request(
                "/api/unibot/course/python-exam-local-cycle-readiness-handoff",
                {
                    "python_exam_local_cycle_readiness_review": review,
                    "python_exam_local_cycle_start_packet": start_packet,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "python_exam_local_cycle_readiness_handoff_ready")
            self.assertEqual(report["operator_run_prefill"]["status"], "prefill_ready")
            self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
