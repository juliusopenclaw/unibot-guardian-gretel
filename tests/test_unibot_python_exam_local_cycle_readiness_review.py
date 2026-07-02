from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_local_cycle_readiness_review import build_python_exam_local_cycle_readiness_review
from unibot.python_exam_operator_gate_decision_receipt import build_python_exam_operator_gate_decision_receipt
from unibot.python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate
from unibot.server import route_request

from tests.test_unibot_python_exam_local_cycle_start_packet import ready_start_packet_inputs


class UniBotPythonExamLocalCycleReadinessReviewTests(unittest.TestCase):
    def test_readiness_review_keeps_blocked_without_start_packet(self) -> None:
        report = build_python_exam_local_cycle_readiness_review(selected_skill_tag="python_lists")

        self.assertEqual(report["artifact_type"], "python_exam_local_cycle_readiness_review")
        self.assertEqual(report["status"], "python_exam_local_cycle_readiness_review_attention")
        self.assertEqual(report["readiness_review_recommendation"], "keep_blocked")
        self.assertEqual(report["readiness_review_reason"], "missing_start_packet")
        self.assertFalse(report["readiness_review_summary"]["packet_present"])
        self.assertTrue(report["readiness_review_checks"]["keep_blocked"])
        self.assertEqual(report["public_safety_status"], "pass")

    def test_readiness_review_requests_missing_confirmation_review_for_blocked_start_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, gate, decision = ready_start_packet_inputs(temp_dir)
            start_packet = build_python_exam_local_cycle_start_packet_fixture(console, gate, decision)
            report = build_python_exam_local_cycle_readiness_review(
                python_exam_local_cycle_start_packet=start_packet,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(report, ensure_ascii=False)
            summary = report["readiness_review_summary"]
            packet = report["local_cycle_start_packet"]

            self.assertEqual(report["artifact_type"], "python_exam_local_cycle_readiness_review")
            self.assertEqual(report["status"], "python_exam_local_cycle_readiness_review_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(summary["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["start_status"], "blocked_for_confirmation")
            self.assertTrue(summary["blocked_for_confirmation"])
            self.assertEqual(summary["recommendation"], "request_missing_confirmation_review")
            self.assertEqual(summary["recommendation_reason"], "open_confirmations_present")
            self.assertEqual(summary["open_confirmation_count"], 5)
            self.assertEqual(summary["confirmed_count"], 0)
            self.assertEqual(summary["help_level"], "A2")
            self.assertEqual(summary["task_hash"], console["safe_cycle_summary"]["selected_task_hash"])
            self.assertEqual(summary["checkpoint_hash"], console["safe_cycle_summary"]["checkpoint_hash"])
            self.assertEqual(summary["gate_receipt_hash"], gate["operator_gate_receipt"]["receipt_hash"])
            self.assertEqual(summary["decision_receipt_hash"], decision["operator_decision_receipt"]["receipt_hash"])
            self.assertEqual(summary["start_receipt_hash"], packet["start_receipt_hash"])
            self.assertEqual(packet["open_confirmation_count"], 5)
            self.assertEqual(packet["confirmed_count"], 0)
            self.assertTrue(report["readiness_review_checks"]["request_missing_confirmation_review"])
            self.assertFalse(report["readiness_review_checks"]["ready_for_manual_local_cycle_review"])
            self.assertFalse(report["readiness_review_checks"]["keep_blocked"])
            self.assertFalse(report["local_writes_requested"])
            self.assertFalse(report["local_execution_started"])
            self.assertTrue(report["dry_run_default"])
            self.assertTrue(report["readiness_review_receipt"]["not_cleared_receipt"])
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
            self.assertEqual(scan_text(payload, "python-exam-local-cycle-readiness-review")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_readiness_review_can_mark_ready_after_full_human_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, gate, _decision = ready_start_packet_inputs(temp_dir)
            confirmed_gate = build_python_exam_safe_cycle_operator_gate(
                python_exam_safe_cycle_console=console,
                selected_skill_tag="python_lists",
            )
            confirmed_ids = [card["step_id"] for card in confirmed_gate["confirmation_cards"]]
            decision = build_python_exam_operator_gate_decision_receipt(
                python_exam_safe_cycle_operator_gate=confirmed_gate,
                confirmed_step_ids=confirmed_ids,
                selected_skill_tag="python_lists",
            )
            start_packet = build_python_exam_local_cycle_start_packet_fixture(console, confirmed_gate, decision)
            report = build_python_exam_local_cycle_readiness_review(
                python_exam_local_cycle_start_packet=start_packet,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(report["readiness_review_summary"]["recommendation"], "ready_for_manual_local_cycle_review")
            self.assertEqual(report["readiness_review_summary"]["ready_for_manual_local_cycle_review"], True)
            self.assertEqual(report["readiness_review_summary"]["open_confirmation_count"], 0)
            self.assertEqual(report["readiness_review_summary"]["confirmed_count"], 5)
            self.assertEqual(report["public_safety_status"], "pass")

    def test_readiness_review_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, gate, decision = ready_start_packet_inputs(temp_dir)
            start_packet = build_python_exam_local_cycle_start_packet_fixture(console, gate, decision)
            status, report = route_request(
                "/api/unibot/course/python-exam-local-cycle-readiness-review",
                {
                    "python_exam_local_cycle_start_packet": start_packet,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "python_exam_local_cycle_readiness_review_ready")
            self.assertEqual(report["readiness_review_summary"]["recommendation"], "request_missing_confirmation_review")
            self.assertEqual(report["public_safety_status"], "pass")


def build_python_exam_local_cycle_start_packet_fixture(console: dict, gate: dict, decision: dict) -> dict:
    from unibot.python_exam_local_cycle_start_packet import build_python_exam_local_cycle_start_packet

    return build_python_exam_local_cycle_start_packet(
        python_exam_safe_cycle_console=console,
        python_exam_safe_cycle_operator_gate=gate,
        python_exam_operator_gate_decision_receipt=decision,
        selected_skill_tag="python_lists",
    )


if __name__ == "__main__":
    unittest.main()
