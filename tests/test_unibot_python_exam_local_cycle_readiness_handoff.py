from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_local_cycle_readiness_handoff import (
    build_python_exam_local_cycle_readiness_handoff,
    build_python_exam_local_cycle_readiness_handoff_release_claim_alignment,
)
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

    def test_handoff_release_claim_alignment_links_review_board_claims(self) -> None:
        alignment = build_python_exam_local_cycle_readiness_handoff_release_claim_alignment()
        payload = json.dumps(alignment, ensure_ascii=False)

        self.assertEqual(
            alignment["schema_version"],
            "unibot-python-exam-local-cycle-readiness-handoff-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["ready_handoff_status"], "python_exam_local_cycle_readiness_handoff_ready")
        self.assertEqual(alignment["ready_handoff_public_safety_status"], "pass")
        self.assertEqual(alignment["attention_handoff_status"], "python_exam_local_cycle_readiness_handoff_attention")
        self.assertEqual(alignment["attention_handoff_public_safety_status"], "pass")
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertEqual(alignment["selected_skill_tag"], "python_lists")
        self.assertEqual(alignment["recommendation"], "request_missing_confirmation_review")
        self.assertEqual(alignment["recommendation_reason"], "open_confirmations_present")
        self.assertTrue(alignment["ready_for_operator_prefill"])
        self.assertEqual(alignment["operator_run_endpoint"], "/api/unibot/exam-workspace/operator-run")
        self.assertEqual(alignment["operator_run_method"], "POST")
        self.assertEqual(alignment["operator_prefill_status"], "prefill_ready")
        self.assertTrue(alignment["operator_prefill_hash_present"])
        self.assertEqual(alignment["manual_handoff_status"], "manual_local_cycle_handoff_ready")
        self.assertEqual(alignment["manual_next_operator_action"], "open_operator_run_prefill")
        self.assertEqual(alignment["attention_prefill_status"], "prefill_attention")
        self.assertEqual(alignment["attention_manual_handoff_status"], "manual_local_cycle_handoff_attention")
        self.assertTrue(alignment["task_hash_present"])
        self.assertTrue(alignment["checkpoint_hash_present"])
        self.assertEqual(alignment["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
        self.assertEqual(alignment["source_anchor_count"], 2)
        self.assertEqual(alignment["help_level"], "A2")
        self.assertEqual(alignment["handoff_receipt_status"], "local_cycle_readiness_handoff_receipt_ready_not_exam_clearance")
        self.assertTrue(alignment["handoff_receipt_hash_present"])
        self.assertTrue(alignment["not_cleared_receipt"])
        self.assertTrue(alignment["dry_run_default"])
        self.assertFalse(alignment["local_writes_requested"])
        self.assertFalse(alignment["local_execution_started"])
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
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
        self.assertTrue(alignment["contracts"]["ready_handoff_public_safe"])
        self.assertTrue(alignment["contracts"]["attention_handoff_public_safe"])
        self.assertTrue(alignment["contracts"]["operator_prefill_ready_metadata_only"])
        self.assertTrue(alignment["contracts"]["manual_handoff_ready_not_execution"])
        self.assertTrue(alignment["contracts"]["attention_handoff_stays_blocked"])
        self.assertTrue(alignment["contracts"]["hash_metadata_and_source_cards_preserved"])
        self.assertTrue(alignment["contracts"]["public_outputs_hide_private_handoff_data"])
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
        self.assertEqual(scan_text(payload, "handoff-alignment")["status"], "pass")

    def test_handoff_release_claim_alignment_flags_overstated_claims(self) -> None:
        unsafe_ready = {
            "status": "python_exam_local_cycle_readiness_handoff_ready",
            "public_safety_status": "pass",
            "exam_deployment_status": "cleared",
            "execution_boundary": "executes local writes and returns notebook code",
            "handoff_summary": {
                "selected_skill_tag": "python_lists",
                "recommendation": "ready",
                "recommendation_reason": "invented",
                "ready_for_operator_prefill": True,
                "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
                "operator_run_method": "POST",
                "task_hash": "",
                "checkpoint_hash": "",
                "source_card_ids": [],
                "source_anchor_count": 0,
            },
            "operator_run_prefill": {
                "status": "prefill_ready",
                "endpoint": "/api/unibot/exam-workspace/operator-run",
                "method": "POST",
                "selected_skill_tag": "python_lists",
                "requested_help_level": "A6",
                "operator_confirmations_default": "all_true",
                "prefill_hash": "",
                "task_hash": "",
                "checkpoint_hash": "",
                "source_card_ids": [],
                "source_anchor_count": 0,
                "raw_query_included": True,
                "raw_cell_included": True,
                "raw_source_text_included": True,
                "notebook_code_included": True,
                "local_paths_returned": True,
                "exam_deployment_status": "cleared",
            },
            "manual_local_cycle_handoff": {
                "status": "manual_local_cycle_handoff_ready",
                "next_operator_action": "execute_local_write",
                "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
                "operator_run_prefill_hash": "",
                "not_cleared_receipt": False,
                "exam_deployment_status": "cleared",
                "help_level": "A6",
            },
            "handoff_receipt": {
                "status": "local_cycle_readiness_handoff_receipt_ready_not_exam_clearance",
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
        unsafe_attention = {
            "status": "python_exam_local_cycle_readiness_handoff_ready",
            "public_safety_status": "pass",
            "handoff_summary": {"ready_for_operator_prefill": True},
            "operator_run_prefill": {"status": "prefill_ready"},
            "manual_local_cycle_handoff": {"status": "manual_local_cycle_handoff_ready"},
        }

        alignment = build_python_exam_local_cycle_readiness_handoff_release_claim_alignment(
            ready_handoff=unsafe_ready,
            attention_handoff=unsafe_attention,
        )

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("operator_prefill_ready_metadata_only", alignment["failed_contract_ids"])
        self.assertIn("manual_handoff_ready_not_execution", alignment["failed_contract_ids"])
        self.assertIn("attention_handoff_stays_blocked", alignment["failed_contract_ids"])
        self.assertIn("hash_metadata_and_source_cards_preserved", alignment["failed_contract_ids"])
        self.assertIn("public_outputs_hide_private_handoff_data", alignment["failed_contract_ids"])
        self.assertIn("high_stakes_actions_not_started", alignment["failed_contract_ids"])
        self.assertIn("not_cleared_receipt_present", alignment["failed_contract_ids"])


if __name__ == "__main__":
    unittest.main()
