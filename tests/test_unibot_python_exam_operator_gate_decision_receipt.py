from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_operator_gate_decision_receipt import build_python_exam_operator_gate_decision_receipt
from unibot.server import route_request

from tests.test_unibot_python_exam_safe_cycle_operator_gate import ready_gate_input
from unibot.python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate


def ready_decision_input(temp_dir: str) -> dict:
    console = ready_gate_input(temp_dir)
    return build_python_exam_safe_cycle_operator_gate(
        python_exam_safe_cycle_console=console,
        selected_skill_tag="python_lists",
    )


class UniBotPythonExamOperatorGateDecisionReceiptTests(unittest.TestCase):
    def test_decision_receipt_records_unconfirmed_gate_without_raw_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            gate = ready_decision_input(temp_dir)
            report = build_python_exam_operator_gate_decision_receipt(
                python_exam_safe_cycle_operator_gate=gate,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(report, ensure_ascii=False)
            summary = report["decision_receipt_summary"]
            next_action = report["next_allowed_local_action"]

            self.assertEqual(report["artifact_type"], "python_exam_operator_gate_decision_receipt")
            self.assertEqual(report["status"], "python_exam_operator_gate_decision_receipt_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(summary["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["decision_status"], "decision_receipt_ready_for_human_review")
            self.assertEqual(summary["card_count"], 5)
            self.assertEqual(summary["confirmed_count"], 0)
            self.assertEqual(summary["unconfirmed_count"], 5)
            self.assertEqual(summary["next_confirmable_step_id"], "open_control_panel")
            self.assertEqual(next_action["step_id"], "open_control_panel")
            self.assertEqual(next_action["status"], "awaiting_operator_confirmation")
            self.assertFalse(next_action["execution_started"])
            self.assertFalse(report["local_writes_requested"])
            self.assertFalse(report["local_writes_started"])
            self.assertEqual(len(report["unconfirmed_steps"]), 5)
            self.assertEqual(report["confirmed_step_hash_metadata"], [])
            self.assertTrue(report["operator_decision_receipt"]["not_cleared_receipt"])
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
            self.assertEqual(scan_text(payload, "python-exam-operator-gate-decision-receipt")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_decision_receipt_mirrors_confirmed_hash_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            gate = ready_decision_input(temp_dir)
            report = build_python_exam_operator_gate_decision_receipt(
                python_exam_safe_cycle_operator_gate=gate,
                confirmed_step_ids=["open_control_panel"],
                selected_skill_tag="python_lists",
            )

            self.assertEqual(report["decision_receipt_summary"]["confirmed_count"], 1)
            self.assertEqual(report["decision_receipt_summary"]["unconfirmed_count"], 4)
            self.assertEqual(report["decision_receipt_summary"]["next_confirmable_step_id"], "prepare_notebook_checkpoint")
            self.assertEqual(len(report["confirmed_step_hash_metadata"]), 1)
            self.assertEqual(report["confirmed_step_hash_metadata"][0]["step_id"], "open_control_panel")
            self.assertTrue(report["confirmed_step_hash_metadata"][0]["card_hash"])
            self.assertFalse(report["local_writes_started"])
            self.assertEqual(report["public_safety_status"], "pass")

    def test_decision_receipt_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            gate = ready_decision_input(temp_dir)
            status, report = route_request(
                "/api/unibot/course/python-exam-operator-gate-decision-receipt",
                {
                    "python_exam_safe_cycle_operator_gate": gate,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "python_exam_operator_gate_decision_receipt_ready")
            self.assertEqual(report["decision_receipt_summary"]["unconfirmed_count"], 5)
            self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
