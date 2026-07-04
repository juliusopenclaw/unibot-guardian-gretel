from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_local_cycle_readiness_review import (
    build_python_exam_local_cycle_readiness_review,
    build_python_exam_local_cycle_readiness_review_release_claim_alignment,
)
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

    def test_readiness_review_release_claim_alignment_links_review_board_claims(self) -> None:
        alignment = build_python_exam_local_cycle_readiness_review_release_claim_alignment()
        payload = json.dumps(alignment, ensure_ascii=False)

        self.assertEqual(
            alignment["schema_version"],
            "unibot-python-exam-local-cycle-readiness-review-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["open_review_status"], "python_exam_local_cycle_readiness_review_ready")
        self.assertEqual(alignment["open_review_public_safety_status"], "pass")
        self.assertEqual(alignment["confirmed_review_status"], "python_exam_local_cycle_readiness_review_ready")
        self.assertEqual(alignment["confirmed_review_public_safety_status"], "pass")
        self.assertEqual(alignment["missing_review_status"], "python_exam_local_cycle_readiness_review_attention")
        self.assertEqual(alignment["missing_review_public_safety_status"], "pass")
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertEqual(alignment["selected_skill_tag"], "python_lists")
        self.assertEqual(alignment["open_recommendation"], "request_missing_confirmation_review")
        self.assertEqual(alignment["open_recommendation_reason"], "open_confirmations_present")
        self.assertEqual(alignment["open_start_status"], "blocked_for_confirmation")
        self.assertEqual(alignment["open_confirmation_count"], 5)
        self.assertEqual(alignment["confirmed_recommendation"], "ready_for_manual_local_cycle_review")
        self.assertEqual(alignment["confirmed_count"], 5)
        self.assertEqual(alignment["missing_recommendation"], "keep_blocked")
        self.assertEqual(alignment["missing_recommendation_reason"], "missing_start_packet")
        self.assertTrue(alignment["packet_present"])
        self.assertTrue(alignment["hash_metadata_complete"])
        self.assertTrue(alignment["task_hash_present"])
        self.assertTrue(alignment["checkpoint_hash_present"])
        self.assertTrue(alignment["gate_receipt_hash_present"])
        self.assertTrue(alignment["decision_receipt_hash_present"])
        self.assertTrue(alignment["start_receipt_hash_present"])
        self.assertTrue(alignment["review_receipt_hash_present"])
        self.assertEqual(alignment["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
        self.assertEqual(alignment["source_anchor_count"], 2)
        self.assertEqual(alignment["help_level"], "A2")
        self.assertTrue(alignment["dry_run_default"])
        self.assertFalse(alignment["local_writes_requested"])
        self.assertFalse(alignment["local_execution_started"])
        self.assertTrue(alignment["not_cleared_receipt"])
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("python_exam_local_cycle_readiness_review", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_start_packet", alignment["required_readiness_check_ids"])
        self.assertIn("exam_workspace_session_console", alignment["required_readiness_check_ids"])
        self.assertIn("study_session", alignment["required_readiness_check_ids"])
        self.assertIn("external_decision_state", alignment["required_readiness_check_ids"])
        self.assertIn("evaluation_packet", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertTrue(alignment["contracts"]["open_review_public_safe"])
        self.assertTrue(alignment["contracts"]["confirmed_review_public_safe"])
        self.assertTrue(alignment["contracts"]["missing_review_public_safe"])
        self.assertTrue(alignment["contracts"]["open_confirmation_review_recommendation_ready"])
        self.assertTrue(alignment["contracts"]["confirmed_review_manual_only_ready"])
        self.assertTrue(alignment["contracts"]["missing_start_packet_keeps_blocked"])
        self.assertTrue(alignment["contracts"]["hash_metadata_and_source_cards_preserved"])
        self.assertTrue(alignment["contracts"]["public_outputs_hide_private_review_data"])
        self.assertTrue(alignment["contracts"]["high_stakes_actions_not_started"])
        self.assertTrue(alignment["contracts"]["not_cleared_receipt_present"])
        self.assertIn("local write requested", alignment["blocked_claims"])
        self.assertIn("local execution started", alignment["blocked_claims"])
        self.assertIn("raw notebook code returned", alignment["blocked_claims"])
        self.assertIn("automatic grading", alignment["blocked_claims"])
        self.assertIn("proctoring", alignment["blocked_claims"])
        self.assertIn("KI-detection evidence", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])
        self.assertNotIn("private_active_study_attempt", payload)
        self.assertEqual(scan_text(payload, "readiness-review-alignment")["status"], "pass")

    def test_readiness_review_release_claim_alignment_flags_overstated_claims(self) -> None:
        unsafe_open = {
            "status": "python_exam_local_cycle_readiness_review_ready",
            "public_safety_status": "pass",
            "exam_deployment_status": "cleared",
            "execution_boundary": "executes local writes and returns notebook code",
            "readiness_review_summary": {
                "recommendation": "ready_for_manual_local_cycle_review",
                "recommendation_reason": "full_human_confirmation_present",
                "start_status": "ready_after_human_confirmation",
                "open_confirmation_count": 0,
                "confirmed_count": 0,
                "hash_metadata_complete": False,
                "packet_present": True,
                "task_hash": "",
                "checkpoint_hash": "",
                "gate_receipt_hash": "",
                "decision_receipt_hash": "",
                "start_receipt_hash": "",
            },
            "local_cycle_start_packet": {
                "source_card_ids": [],
                "source_anchor_count": 0,
                "help_level": "A6",
                "exam_deployment_status": "cleared",
            },
            "readiness_review_checks": {
                "request_missing_confirmation_review": False,
                "keep_blocked": False,
            },
            "readiness_review_receipt": {
                "status": "local_cycle_readiness_review_receipt_ready_not_exam_clearance",
                "receipt_hash": "",
                "not_cleared_receipt": False,
                "exam_deployment_status": "cleared",
            },
            "dry_run_default": False,
            "local_writes_requested": True,
            "local_execution_started": True,
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
            "status": "python_exam_local_cycle_readiness_review_ready",
            "public_safety_status": "pass",
            "exam_deployment_status": "cleared",
            "local_writes_requested": True,
            "local_execution_started": True,
            "readiness_review_summary": {
                "recommendation": "ready_for_manual_local_cycle_review",
                "recommendation_reason": "full_human_confirmation_present",
                "open_confirmation_count": 0,
                "confirmed_count": 5,
            },
            "local_cycle_start_packet": {"ready_for_manual_local_cycle_review": True},
        }
        unsafe_missing = {
            "status": "python_exam_local_cycle_readiness_review_ready",
            "public_safety_status": "pass",
            "readiness_review_summary": {
                "recommendation": "ready_for_manual_local_cycle_review",
                "recommendation_reason": "invented",
                "packet_present": False,
            },
            "readiness_review_checks": {"keep_blocked": False},
        }

        alignment = build_python_exam_local_cycle_readiness_review_release_claim_alignment(
            open_review=unsafe_open,
            confirmed_review=unsafe_confirmed,
            missing_review=unsafe_missing,
        )

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("open_confirmation_review_recommendation_ready", alignment["failed_contract_ids"])
        self.assertIn("missing_start_packet_keeps_blocked", alignment["failed_contract_ids"])
        self.assertIn("hash_metadata_and_source_cards_preserved", alignment["failed_contract_ids"])
        self.assertIn("public_outputs_hide_private_review_data", alignment["failed_contract_ids"])
        self.assertIn("high_stakes_actions_not_started", alignment["failed_contract_ids"])
        self.assertIn("not_cleared_receipt_present", alignment["failed_contract_ids"])


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
