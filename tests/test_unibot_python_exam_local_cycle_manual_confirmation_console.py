from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_local_cycle_chain_snapshot import build_python_exam_local_cycle_chain_snapshot
from unibot.python_exam_local_cycle_manual_confirmation_console import (
    build_python_exam_local_cycle_manual_confirmation_console,
)
from unibot.python_exam_local_cycle_operator_workspace_card import build_python_exam_local_cycle_operator_workspace_card
from unibot.python_exam_local_cycle_readiness_handoff import build_python_exam_local_cycle_readiness_handoff
from unibot.python_exam_local_cycle_readiness_review import build_python_exam_local_cycle_readiness_review
from unibot.python_exam_local_cycle_start_packet import build_python_exam_local_cycle_start_packet
from unibot.python_exam_operator_gate_decision_receipt import build_python_exam_operator_gate_decision_receipt
from unibot.python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate
from unibot.server import route_request

from tests.test_unibot_python_exam_local_cycle_start_packet import ready_start_packet_inputs


def manual_confirmation_inputs(temp_dir: str, *, confirmed: bool) -> tuple[dict, dict, dict, dict]:
    console, gate, decision = ready_start_packet_inputs(temp_dir)
    if confirmed:
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
    handoff = build_python_exam_local_cycle_readiness_handoff(
        python_exam_local_cycle_readiness_review=review,
        python_exam_local_cycle_start_packet=start_packet,
        selected_skill_tag="python_lists",
    )
    workspace_card = build_python_exam_local_cycle_operator_workspace_card(
        python_exam_local_cycle_readiness_review=review,
        python_exam_local_cycle_readiness_handoff=handoff,
        python_exam_local_cycle_start_packet=start_packet,
        selected_skill_tag="python_lists",
    )
    chain_snapshot = build_python_exam_local_cycle_chain_snapshot(
        python_exam_local_cycle_readiness_review=review,
        python_exam_local_cycle_readiness_handoff=handoff,
        python_exam_local_cycle_operator_workspace_card=workspace_card,
        selected_skill_tag="python_lists",
    )
    return review, handoff, workspace_card, chain_snapshot


class UniBotPythonExamLocalCycleManualConfirmationConsoleTests(unittest.TestCase):
    def test_console_reviews_open_confirmations_side_by_side_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            review, handoff, workspace_card, chain_snapshot = manual_confirmation_inputs(temp_dir, confirmed=False)
            console = build_python_exam_local_cycle_manual_confirmation_console(
                python_exam_local_cycle_readiness_review=review,
                python_exam_local_cycle_readiness_handoff=handoff,
                python_exam_local_cycle_operator_workspace_card=workspace_card,
                python_exam_local_cycle_chain_snapshot=chain_snapshot,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(console, ensure_ascii=False)
            summary = console["console_summary"]

            self.assertEqual(console["artifact_type"], "python_exam_local_cycle_manual_confirmation_console")
            self.assertEqual(console["status"], "python_exam_local_cycle_manual_confirmation_console_ready")
            self.assertEqual(console["exam_deployment_status"], "not_cleared")
            self.assertEqual(console["next_manual_confirmation_action"], "review_missing_confirmation")
            self.assertEqual(summary["next_manual_confirmation_reason"], "open_operator_confirmations_present")
            self.assertEqual(console["confirmation_matrix"]["open_count"], 5)
            self.assertEqual(console["confirmation_matrix"]["confirmed_count"], 0)
            self.assertEqual(len(console["open_confirmation_cards"]), 5)
            self.assertEqual(console["confirmed_hash_metadata_cards"], [])
            self.assertEqual(console["source_checkpoint_metadata"]["help_level"], "A2")
            self.assertTrue(console["manual_confirmation_console_receipt"]["not_cleared_receipt"])
            self.assertFalse(console["local_writes_requested"])
            self.assertFalse(console["local_execution_started"])
            self.assertTrue(console["dry_run_default"])
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
                self.assertFalse(console[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-local-cycle-manual-confirmation-console")["status"], "pass")
            self.assertEqual(console["public_safety_status"], "pass")

    def test_console_can_continue_after_confirmed_hash_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            review, handoff, workspace_card, chain_snapshot = manual_confirmation_inputs(temp_dir, confirmed=True)
            console = build_python_exam_local_cycle_manual_confirmation_console(
                python_exam_local_cycle_readiness_review=review,
                python_exam_local_cycle_readiness_handoff=handoff,
                python_exam_local_cycle_operator_workspace_card=workspace_card,
                python_exam_local_cycle_chain_snapshot=chain_snapshot,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(console["next_manual_confirmation_action"], "continue_to_manual_local_cycle")
            self.assertEqual(console["confirmation_matrix"]["open_count"], 0)
            self.assertEqual(console["confirmation_matrix"]["confirmed_count"], 5)
            self.assertEqual(len(console["confirmed_hash_metadata_cards"]), 5)
            self.assertEqual(console["public_safety_status"], "pass")

    def test_console_refreshes_start_packet_review_without_chain_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            review, handoff, workspace_card, _chain_snapshot = manual_confirmation_inputs(temp_dir, confirmed=False)
            console = build_python_exam_local_cycle_manual_confirmation_console(
                python_exam_local_cycle_readiness_review=review,
                python_exam_local_cycle_readiness_handoff=handoff,
                python_exam_local_cycle_operator_workspace_card=workspace_card,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(console["status"], "python_exam_local_cycle_manual_confirmation_console_attention")
            self.assertEqual(console["next_manual_confirmation_action"], "refresh_start_packet_review")
            self.assertEqual(console["public_safety_status"], "pass")

    def test_console_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            review, handoff, workspace_card, chain_snapshot = manual_confirmation_inputs(temp_dir, confirmed=False)
            status, console = route_request(
                "/api/unibot/course/python-exam-local-cycle-manual-confirmation-console",
                {
                    "python_exam_local_cycle_readiness_review": review,
                    "python_exam_local_cycle_readiness_handoff": handoff,
                    "python_exam_local_cycle_operator_workspace_card": workspace_card,
                    "python_exam_local_cycle_chain_snapshot": chain_snapshot,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(console["status"], "python_exam_local_cycle_manual_confirmation_console_ready")
            self.assertEqual(console["next_manual_confirmation_action"], "review_missing_confirmation")
            self.assertEqual(console["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
