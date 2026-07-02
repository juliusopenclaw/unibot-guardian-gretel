from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_local_cycle_operator_workspace_card import build_python_exam_local_cycle_operator_workspace_card
from unibot.python_exam_local_cycle_readiness_handoff import build_python_exam_local_cycle_readiness_handoff
from unibot.python_exam_local_cycle_readiness_review import build_python_exam_local_cycle_readiness_review
from unibot.python_exam_local_cycle_start_packet import build_python_exam_local_cycle_start_packet
from unibot.python_exam_operator_gate_decision_receipt import build_python_exam_operator_gate_decision_receipt
from unibot.python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate
from unibot.server import route_request

from tests.test_unibot_python_exam_local_cycle_start_packet import ready_start_packet_inputs


class UniBotPythonExamLocalCycleOperatorWorkspaceCardTests(unittest.TestCase):
    def test_operator_workspace_card_combines_review_handoff_and_help_ledger_preview(self) -> None:
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
            start_packet = build_python_exam_local_cycle_start_packet(
                python_exam_safe_cycle_console=console,
                python_exam_safe_cycle_operator_gate=confirmed_gate,
                python_exam_operator_gate_decision_receipt=decision,
                selected_skill_tag="python_lists",
            )
            review = build_python_exam_local_cycle_readiness_review(
                python_exam_local_cycle_start_packet=start_packet,
                selected_skill_tag="python_lists",
            )
            handoff = build_python_exam_local_cycle_readiness_handoff(
                python_exam_local_cycle_readiness_review=review,
                python_exam_local_cycle_start_packet=start_packet,
                selected_skill_tag="python_lists",
            )
            card = build_python_exam_local_cycle_operator_workspace_card(
                python_exam_local_cycle_readiness_review=review,
                python_exam_local_cycle_readiness_handoff=handoff,
                python_exam_local_cycle_start_packet=start_packet,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(card, ensure_ascii=False)

            self.assertEqual(card["artifact_type"], "python_exam_local_cycle_operator_workspace_card")
            self.assertEqual(card["status"], "python_exam_local_cycle_operator_workspace_card_ready")
            self.assertEqual(card["exam_deployment_status"], "not_cleared")
            self.assertEqual(card["selected_skill_tag"], "python_lists")
            self.assertEqual(card["workspace_card_summary"]["help_ledger_preview_status"], "help_ledger_preview_ready")
            self.assertEqual(card["help_ledger_preview"]["status"], "help_ledger_preview_ready")
            self.assertEqual(card["help_ledger_preview"]["help_level"], "A2")
            self.assertEqual(card["workspace_card_summary"]["next_safe_action"], review["readiness_review_summary"]["next_safe_action"])
            self.assertTrue(card["workspace_card_summary"]["ready_for_operator_prefill"])
            self.assertTrue(card["dry_run_default"])
            self.assertFalse(card["local_writes_requested"])
            self.assertFalse(card["local_execution_started"])
            self.assertTrue(card["not_cleared_receipt"])
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
                self.assertFalse(card[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-local-cycle-operator-workspace-card")["status"], "pass")
            self.assertEqual(card["public_safety_status"], "pass")

    def test_operator_workspace_card_api_route(self) -> None:
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
            start_packet = build_python_exam_local_cycle_start_packet(
                python_exam_safe_cycle_console=console,
                python_exam_safe_cycle_operator_gate=confirmed_gate,
                python_exam_operator_gate_decision_receipt=decision,
                selected_skill_tag="python_lists",
            )
            review = build_python_exam_local_cycle_readiness_review(
                python_exam_local_cycle_start_packet=start_packet,
                selected_skill_tag="python_lists",
            )
            handoff = build_python_exam_local_cycle_readiness_handoff(
                python_exam_local_cycle_readiness_review=review,
                python_exam_local_cycle_start_packet=start_packet,
                selected_skill_tag="python_lists",
            )
            status, card = route_request(
                "/api/unibot/course/python-exam-local-cycle-operator-workspace-card",
                {
                    "python_exam_local_cycle_readiness_review": review,
                    "python_exam_local_cycle_readiness_handoff": handoff,
                    "python_exam_local_cycle_start_packet": start_packet,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(card["status"], "python_exam_local_cycle_operator_workspace_card_ready")
            self.assertEqual(card["help_ledger_preview"]["status"], "help_ledger_preview_ready")
            self.assertEqual(card["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
