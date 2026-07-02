from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_local_cycle_start_packet import build_python_exam_local_cycle_start_packet
from unibot.python_exam_operator_gate_decision_receipt import build_python_exam_operator_gate_decision_receipt
from unibot.python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate
from unibot.server import route_request

from tests.test_unibot_python_exam_safe_cycle_operator_gate import ready_gate_input


def ready_start_packet_inputs(temp_dir: str) -> tuple[dict, dict, dict]:
    console = ready_gate_input(temp_dir)
    gate = build_python_exam_safe_cycle_operator_gate(
        python_exam_safe_cycle_console=console,
        selected_skill_tag="python_lists",
    )
    decision = build_python_exam_operator_gate_decision_receipt(
        python_exam_safe_cycle_operator_gate=gate,
        selected_skill_tag="python_lists",
    )
    return console, gate, decision


class UniBotPythonExamLocalCycleStartPacketTests(unittest.TestCase):
    def test_start_packet_is_blocked_for_open_confirmations_without_raw_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, gate, decision = ready_start_packet_inputs(temp_dir)
            report = build_python_exam_local_cycle_start_packet(
                python_exam_safe_cycle_console=console,
                python_exam_safe_cycle_operator_gate=gate,
                python_exam_operator_gate_decision_receipt=decision,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(report, ensure_ascii=False)
            summary = report["local_cycle_start_summary"]
            packet = report["start_packet"]

            self.assertEqual(report["artifact_type"], "python_exam_local_cycle_start_packet")
            self.assertEqual(report["status"], "python_exam_local_cycle_start_packet_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(summary["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["start_status"], "blocked_for_confirmation")
            self.assertEqual(summary["blocked_reason"], "operator_confirmations_open")
            self.assertEqual(summary["next_safe_action"], "run_next_microtask")
            self.assertEqual(summary["next_safe_user_action"], "review_next_operator_confirmation")
            self.assertEqual(summary["open_confirmation_count"], 5)
            self.assertEqual(summary["confirmed_count"], 0)
            self.assertEqual(packet["task_hash"], console["safe_cycle_summary"]["selected_task_hash"])
            self.assertEqual(packet["checkpoint_hash"], console["safe_cycle_summary"]["checkpoint_hash"])
            self.assertEqual(packet["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
            self.assertEqual(packet["help_level"], "A2")
            self.assertEqual(packet["gate_receipt_id"], gate["operator_gate_receipt"]["receipt_id"])
            self.assertEqual(packet["decision_receipt_id"], decision["operator_decision_receipt"]["receipt_id"])
            self.assertEqual(len(packet["open_confirmations"]), 5)
            self.assertEqual(packet["confirmed_hash_metadata"], [])
            self.assertFalse(report["local_writes_requested"])
            self.assertFalse(report["local_execution_started"])
            self.assertTrue(report["dry_run_default"])
            self.assertTrue(report["local_cycle_start_receipt"]["not_cleared_receipt"])
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
            self.assertEqual(scan_text(payload, "python-exam-local-cycle-start-packet")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_start_packet_can_show_ready_after_all_human_confirmations_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console = ready_gate_input(temp_dir)
            gate = build_python_exam_safe_cycle_operator_gate(
                python_exam_safe_cycle_console=console,
                selected_skill_tag="python_lists",
            )
            confirmed_ids = [card["step_id"] for card in gate["confirmation_cards"]]
            decision = build_python_exam_operator_gate_decision_receipt(
                python_exam_safe_cycle_operator_gate=gate,
                confirmed_step_ids=confirmed_ids,
                selected_skill_tag="python_lists",
            )
            report = build_python_exam_local_cycle_start_packet(
                python_exam_safe_cycle_console=console,
                python_exam_safe_cycle_operator_gate=gate,
                python_exam_operator_gate_decision_receipt=decision,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(report["local_cycle_start_summary"]["start_status"], "ready_after_human_confirmation")
            self.assertEqual(report["local_cycle_start_summary"]["open_confirmation_count"], 0)
            self.assertEqual(report["local_cycle_start_summary"]["confirmed_count"], 5)
            self.assertEqual(len(report["start_packet"]["confirmed_hash_metadata"]), 5)
            self.assertFalse(report["local_execution_started"])
            self.assertFalse(report["local_writes_requested"])
            self.assertEqual(report["public_safety_status"], "pass")

    def test_start_packet_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, gate, decision = ready_start_packet_inputs(temp_dir)
            status, report = route_request(
                "/api/unibot/course/python-exam-local-cycle-start-packet",
                {
                    "python_exam_safe_cycle_console": console,
                    "python_exam_safe_cycle_operator_gate": gate,
                    "python_exam_operator_gate_decision_receipt": decision,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "python_exam_local_cycle_start_packet_ready")
            self.assertEqual(report["local_cycle_start_summary"]["start_status"], "blocked_for_confirmation")
            self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
