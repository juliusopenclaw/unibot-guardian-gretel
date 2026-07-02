from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_local_cycle_chain_snapshot import build_python_exam_local_cycle_chain_snapshot
from unibot.python_exam_local_cycle_operator_workspace_card import build_python_exam_local_cycle_operator_workspace_card
from unibot.python_exam_local_cycle_readiness_handoff import build_python_exam_local_cycle_readiness_handoff
from unibot.python_exam_local_cycle_readiness_review import build_python_exam_local_cycle_readiness_review
from unibot.python_exam_local_cycle_start_packet import build_python_exam_local_cycle_start_packet
from unibot.python_exam_operator_gate_decision_receipt import build_python_exam_operator_gate_decision_receipt
from unibot.python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate
from unibot.server import route_request

from tests.test_unibot_python_exam_local_cycle_start_packet import ready_start_packet_inputs


class UniBotPythonExamLocalCycleChainSnapshotTests(unittest.TestCase):
    def test_chain_snapshot_compacts_review_handoff_and_workspace_card(self) -> None:
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
            workspace_card = build_python_exam_local_cycle_operator_workspace_card(
                python_exam_local_cycle_readiness_review=review,
                python_exam_local_cycle_readiness_handoff=handoff,
                python_exam_local_cycle_start_packet=start_packet,
                selected_skill_tag="python_lists",
            )
            snapshot = build_python_exam_local_cycle_chain_snapshot(
                python_exam_local_cycle_readiness_review=review,
                python_exam_local_cycle_readiness_handoff=handoff,
                python_exam_local_cycle_operator_workspace_card=workspace_card,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(snapshot, ensure_ascii=False)

            self.assertEqual(snapshot["artifact_type"], "python_exam_local_cycle_chain_snapshot")
            self.assertEqual(snapshot["status"], "python_exam_local_cycle_chain_snapshot_ready")
            self.assertEqual(snapshot["exam_deployment_status"], "not_cleared")
            self.assertEqual(snapshot["chain_snapshot_summary"]["chain_step_count"], 3)
            self.assertIn(
                snapshot["chain_snapshot_summary"]["review_recommendation"],
                {"request_missing_confirmation_review", "ready_for_manual_local_cycle_review"},
            )
            self.assertTrue(snapshot["chain_snapshot_summary"]["ready_for_operator_prefill"])
            self.assertEqual(len(snapshot["chain_steps"]), 3)
            self.assertTrue(snapshot["chain_snapshot_receipt"]["not_cleared_receipt"])
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-local-cycle-chain-snapshot")["status"], "pass")
            self.assertEqual(snapshot["public_safety_status"], "pass")

    def test_chain_snapshot_api_route(self) -> None:
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
            workspace_card = build_python_exam_local_cycle_operator_workspace_card(
                python_exam_local_cycle_readiness_review=review,
                python_exam_local_cycle_readiness_handoff=handoff,
                python_exam_local_cycle_start_packet=start_packet,
                selected_skill_tag="python_lists",
            )
            status, snapshot = route_request(
                "/api/unibot/course/python-exam-local-cycle-chain-snapshot",
                {
                    "python_exam_local_cycle_readiness_review": review,
                    "python_exam_local_cycle_readiness_handoff": handoff,
                    "python_exam_local_cycle_operator_workspace_card": workspace_card,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(snapshot["status"], "python_exam_local_cycle_chain_snapshot_ready")
            self.assertEqual(snapshot["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
