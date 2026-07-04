from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_local_cycle_operator_workspace_card import (
    build_python_exam_local_cycle_operator_workspace_card,
    build_python_exam_local_cycle_operator_workspace_card_release_claim_alignment,
)
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

    def test_operator_workspace_card_release_claim_alignment_links_review_board_claims(self) -> None:
        alignment = build_python_exam_local_cycle_operator_workspace_card_release_claim_alignment()
        payload = json.dumps(alignment, ensure_ascii=False)

        self.assertEqual(
            alignment["schema_version"],
            "unibot-python-exam-local-cycle-operator-workspace-card-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["ready_card_status"], "python_exam_local_cycle_operator_workspace_card_ready")
        self.assertEqual(alignment["ready_card_public_safety_status"], "pass")
        self.assertEqual(alignment["attention_card_status"], "python_exam_local_cycle_operator_workspace_card_attention")
        self.assertEqual(alignment["attention_card_public_safety_status"], "pass")
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertEqual(alignment["selected_skill_tag"], "python_lists")
        self.assertEqual(alignment["recommendation"], "ready_for_manual_local_cycle_review")
        self.assertEqual(alignment["recommendation_reason"], "full_human_confirmation_present")
        self.assertTrue(alignment["ready_for_operator_prefill"])
        self.assertEqual(alignment["help_ledger_preview_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["help_ledger_preview_hash_present"])
        self.assertEqual(alignment["operator_prefill_status"], "prefill_ready")
        self.assertTrue(alignment["operator_prefill_hash_present"])
        self.assertEqual(alignment["manual_handoff_status"], "manual_local_cycle_handoff_ready")
        self.assertEqual(alignment["manual_next_operator_action"], "open_operator_run_prefill")
        self.assertEqual(alignment["attention_help_ledger_preview_status"], "help_ledger_preview_attention")
        self.assertTrue(alignment["task_hash_present"])
        self.assertTrue(alignment["checkpoint_hash_present"])
        self.assertEqual(alignment["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
        self.assertEqual(alignment["source_anchor_count"], 2)
        self.assertEqual(alignment["help_level"], "A2")
        self.assertTrue(alignment["dry_run_default"])
        self.assertFalse(alignment["local_writes_requested"])
        self.assertFalse(alignment["local_execution_started"])
        self.assertTrue(alignment["not_cleared_receipt"])
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_readiness_handoff", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_readiness_review", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_start_packet", alignment["required_readiness_check_ids"])
        self.assertIn("exam_workspace_operator_run", alignment["required_readiness_check_ids"])
        self.assertIn("external_decision_state", alignment["required_readiness_check_ids"])
        self.assertIn("evaluation_packet", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertTrue(alignment["contracts"]["ready_card_public_safe"])
        self.assertTrue(alignment["contracts"]["attention_card_public_safe"])
        self.assertTrue(alignment["contracts"]["workspace_card_ready_metadata_only"])
        self.assertTrue(alignment["contracts"]["operator_prefill_and_manual_handoff_linked"])
        self.assertTrue(alignment["contracts"]["attention_card_stays_blocked"])
        self.assertTrue(alignment["contracts"]["hash_metadata_and_source_cards_preserved"])
        self.assertTrue(alignment["contracts"]["public_outputs_hide_private_workspace_card_data"])
        self.assertTrue(alignment["contracts"]["high_stakes_actions_not_started"])
        self.assertTrue(alignment["contracts"]["not_cleared_receipt_present"])
        self.assertTrue(alignment["contracts"]["no_local_execution_or_write"])
        self.assertIn("local write requested", alignment["blocked_claims"])
        self.assertIn("local execution started", alignment["blocked_claims"])
        self.assertIn("raw notebook code returned", alignment["blocked_claims"])
        self.assertIn("automatic grading", alignment["blocked_claims"])
        self.assertIn("proctoring", alignment["blocked_claims"])
        self.assertIn("KI-detection evidence", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])
        self.assertNotIn("private_active_study_attempt", payload)
        self.assertEqual(scan_text(payload, "workspace-card-alignment")["status"], "pass")

    def test_operator_workspace_card_release_claim_alignment_flags_overstated_claims(self) -> None:
        unsafe_ready = {
            "status": "python_exam_local_cycle_operator_workspace_card_ready",
            "public_safety_status": "pass",
            "exam_deployment_status": "cleared",
            "selected_skill_tag": "python_lists",
            "execution_boundary": "returns notebook code and starts local writes",
            "workspace_card_summary": {
                "recommendation": "ready_for_manual_local_cycle_review",
                "recommendation_reason": "invented",
                "ready_for_operator_prefill": True,
                "help_ledger_preview_status": "help_ledger_preview_ready",
                "source_card_ids": [],
                "help_ledger_preview_hash": "",
                "not_cleared_receipt": False,
            },
            "readiness_review": {"recommendation": "ready_for_manual_local_cycle_review"},
            "readiness_handoff": {"ready_for_operator_prefill": True},
            "help_ledger_preview": {
                "status": "help_ledger_preview_ready",
                "preview_hash": "",
                "raw_query_returned": True,
                "raw_text_returned": True,
                "local_paths_returned": True,
                "write_requested": True,
                "dry_run_default": False,
                "not_cleared_receipt": False,
            },
            "operator_run_prefill": {
                "status": "prefill_ready",
                "endpoint": "/api/unibot/exam-workspace/operator-run",
                "operator_confirmations_default": "all_true",
                "prefill_hash": "",
            },
            "manual_local_cycle_handoff": {
                "status": "manual_local_cycle_handoff_ready",
                "next_operator_action": "execute_local_write",
                "not_cleared_receipt": False,
            },
            "source_card_ids": [],
            "source_anchor_count": 0,
            "task_hash": "",
            "checkpoint_hash": "",
            "help_level": "A6",
            "dry_run_default": False,
            "local_writes_requested": True,
            "local_execution_started": True,
            "not_cleared_receipt": False,
            "raw_query_returned": True,
            "raw_text_returned": True,
            "raw_cell_returned": True,
            "raw_notebook_returned": True,
            "notebook_code_returned": True,
            "local_paths_returned": True,
            "values_returned": True,
            "solutions_returned": True,
            "final_interpretations_returned": True,
            "score_returned": True,
            "percentage_returned": True,
            "ranking_returned": True,
            "grade_returned": True,
            "automatic_grading_started": True,
            "proctoring_started": True,
            "ai_detection_started": True,
            "exam_clearance_claimed": True,
        }
        unsafe_attention = {
            "status": "python_exam_local_cycle_operator_workspace_card_ready",
            "public_safety_status": "pass",
            "workspace_card_summary": {
                "ready_for_operator_prefill": True,
                "help_ledger_preview_status": "help_ledger_preview_ready",
            },
            "help_ledger_preview": {"status": "help_ledger_preview_ready"},
        }

        alignment = build_python_exam_local_cycle_operator_workspace_card_release_claim_alignment(
            ready_card=unsafe_ready,
            attention_card=unsafe_attention,
        )

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("workspace_card_ready_metadata_only", alignment["failed_contract_ids"])
        self.assertIn("operator_prefill_and_manual_handoff_linked", alignment["failed_contract_ids"])
        self.assertIn("attention_card_stays_blocked", alignment["failed_contract_ids"])
        self.assertIn("hash_metadata_and_source_cards_preserved", alignment["failed_contract_ids"])
        self.assertIn("public_outputs_hide_private_workspace_card_data", alignment["failed_contract_ids"])
        self.assertIn("high_stakes_actions_not_started", alignment["failed_contract_ids"])
        self.assertIn("not_cleared_receipt_present", alignment["failed_contract_ids"])
        self.assertIn("no_local_execution_or_write", alignment["failed_contract_ids"])


if __name__ == "__main__":
    unittest.main()
