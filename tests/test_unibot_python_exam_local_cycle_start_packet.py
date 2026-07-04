from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_local_cycle_start_packet import (
    build_python_exam_local_cycle_start_packet,
    build_python_exam_local_cycle_start_packet_release_claim_alignment,
)
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

    def test_start_packet_release_claim_alignment_links_review_board_claims(self) -> None:
        alignment = build_python_exam_local_cycle_start_packet_release_claim_alignment()
        payload = json.dumps(alignment, ensure_ascii=False)

        self.assertEqual(
            alignment["schema_version"],
            "unibot-python-exam-local-cycle-start-packet-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["open_packet_status"], "python_exam_local_cycle_start_packet_ready")
        self.assertEqual(alignment["open_packet_public_safety_status"], "pass")
        self.assertEqual(alignment["confirmed_packet_status"], "python_exam_local_cycle_start_packet_ready")
        self.assertEqual(alignment["confirmed_packet_public_safety_status"], "pass")
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertEqual(alignment["selected_skill_tag"], "python_lists")
        self.assertEqual(alignment["open_start_status"], "blocked_for_confirmation")
        self.assertEqual(alignment["open_blocked_reason"], "operator_confirmations_open")
        self.assertEqual(alignment["open_confirmation_count"], 5)
        self.assertEqual(alignment["confirmed_start_status"], "ready_after_human_confirmation")
        self.assertEqual(alignment["confirmed_count"], 5)
        self.assertTrue(alignment["task_hash_present"])
        self.assertTrue(alignment["checkpoint_hash_present"])
        self.assertEqual(alignment["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
        self.assertEqual(alignment["source_anchor_count"], 2)
        self.assertEqual(alignment["help_level"], "A2")
        self.assertTrue(alignment["gate_receipt_id_present"])
        self.assertTrue(alignment["decision_receipt_id_present"])
        self.assertEqual(alignment["start_receipt_status"], "local_cycle_start_packet_receipt_ready_not_exam_clearance")
        self.assertTrue(alignment["start_receipt_hash_present"])
        self.assertTrue(alignment["not_cleared_receipt"])
        self.assertEqual(alignment["safe_cycle_console_status"], "python_exam_safe_cycle_console_ready")
        self.assertEqual(alignment["operator_gate_status"], "python_exam_safe_cycle_operator_gate_ready")
        self.assertEqual(alignment["decision_receipt_status"], "python_exam_operator_gate_decision_receipt_ready")
        self.assertTrue(alignment["dry_run_default"])
        self.assertFalse(alignment["local_writes_requested"])
        self.assertFalse(alignment["local_execution_started"])
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("python_exam_local_cycle_start_packet", alignment["required_readiness_check_ids"])
        self.assertIn("exam_workspace_session_console", alignment["required_readiness_check_ids"])
        self.assertIn("exam_workspace_operator_run", alignment["required_readiness_check_ids"])
        self.assertIn("study_session", alignment["required_readiness_check_ids"])
        self.assertIn("external_decision_state", alignment["required_readiness_check_ids"])
        self.assertIn("evaluation_packet", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertTrue(alignment["contracts"]["open_packet_public_safe"])
        self.assertTrue(alignment["contracts"]["confirmed_packet_public_safe"])
        self.assertTrue(alignment["contracts"]["start_packet_metadata_only_ready"])
        self.assertTrue(alignment["contracts"]["open_confirmations_block_local_cycle"])
        self.assertTrue(alignment["contracts"]["confirmed_packet_still_no_execution"])
        self.assertTrue(alignment["contracts"]["source_gate_decision_receipts_linked"])
        self.assertTrue(alignment["contracts"]["public_outputs_hide_private_start_packet_data"])
        self.assertTrue(alignment["contracts"]["high_stakes_actions_not_started"])
        self.assertTrue(alignment["contracts"]["not_cleared_receipt_present"])
        self.assertIn("local execution started", alignment["blocked_claims"])
        self.assertIn("raw notebook code returned", alignment["blocked_claims"])
        self.assertIn("automatic grading", alignment["blocked_claims"])
        self.assertIn("proctoring", alignment["blocked_claims"])
        self.assertIn("KI-detection evidence", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])
        self.assertNotIn("private_active_study_attempt", payload)
        self.assertEqual(scan_text(payload, "start-packet-alignment")["status"], "pass")

    def test_start_packet_release_claim_alignment_flags_overstated_claims(self) -> None:
        unsafe_open = {
            "status": "python_exam_local_cycle_start_packet_ready",
            "public_safety_status": "pass",
            "exam_deployment_status": "cleared",
            "execution_boundary": "executes local writes and returns notebook code",
            "dry_run_default": False,
            "local_writes_requested": True,
            "local_execution_started": True,
            "operator_confirmation_required_for_local_write": False,
            "local_cycle_start_summary": {
                "start_status": "ready_after_human_confirmation",
                "blocked_reason": "",
                "open_confirmation_count": 0,
                "confirmed_count": 0,
            },
            "start_packet": {
                "selected_skill_tag": "python_lists",
                "source_card_ids": [],
                "task_hash": "",
                "checkpoint_hash": "",
                "gate_receipt_hash": "",
                "decision_receipt_hash": "",
                "open_confirmations": [],
                "confirmed_hash_metadata": [],
                "local_writes_requested": True,
                "local_execution_started": True,
                "not_cleared_receipt": False,
                "exam_deployment_status": "cleared",
            },
            "local_cycle_start_receipt": {
                "status": "local_cycle_start_packet_receipt_ready_not_exam_clearance",
                "receipt_hash": "",
                "not_cleared_receipt": False,
                "exam_deployment_status": "cleared",
            },
            "source_reports": {
                "safe_cycle_console_status": "missing",
                "operator_gate_status": "missing",
                "decision_receipt_status": "missing",
            },
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
        unsafe_confirmed = {
            "status": "python_exam_local_cycle_start_packet_ready",
            "public_safety_status": "pass",
            "exam_deployment_status": "cleared",
            "local_writes_requested": True,
            "local_execution_started": True,
            "local_cycle_start_summary": {
                "start_status": "ready_after_human_confirmation",
                "open_confirmation_count": 0,
                "confirmed_count": 5,
            },
            "start_packet": {
                "confirmed_hash_metadata": [],
                "local_execution_started": True,
                "not_cleared_receipt": False,
            },
            "local_cycle_start_receipt": {"not_cleared_receipt": False},
        }

        alignment = build_python_exam_local_cycle_start_packet_release_claim_alignment(
            open_report=unsafe_open,
            confirmed_report=unsafe_confirmed,
        )

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("start_packet_metadata_only_ready", alignment["failed_contract_ids"])
        self.assertIn("open_confirmations_block_local_cycle", alignment["failed_contract_ids"])
        self.assertIn("confirmed_packet_still_no_execution", alignment["failed_contract_ids"])
        self.assertIn("source_gate_decision_receipts_linked", alignment["failed_contract_ids"])
        self.assertIn("public_outputs_hide_private_start_packet_data", alignment["failed_contract_ids"])
        self.assertIn("high_stakes_actions_not_started", alignment["failed_contract_ids"])
        self.assertIn("not_cleared_receipt_present", alignment["failed_contract_ids"])


if __name__ == "__main__":
    unittest.main()
