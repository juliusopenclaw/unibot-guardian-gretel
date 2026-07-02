from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_manual_review_export_authorization_gate import (
    build_python_exam_manual_review_export_authorization_gate,
)
from unibot.python_exam_manual_review_export_preview import build_python_exam_manual_review_export_preview
from unibot.server import route_request

from tests.test_unibot_python_exam_manual_review_export_preview import export_preview_inputs


def authorization_gate_inputs(
    temp_dir: str,
    *,
    confirmed: bool,
    mode: str = "missing",
) -> tuple[dict, dict, dict, dict]:
    packet, timeline, ledger, intake, binder, launch_receipt, console = export_preview_inputs(
        temp_dir,
        confirmed=confirmed,
        mode=mode,
    )
    preview = build_python_exam_manual_review_export_preview(
        python_exam_manual_cycle_review_packet=packet,
        python_exam_manual_cycle_review_timeline=timeline,
        python_exam_manual_cycle_closure_ledger=ledger,
        python_exam_manual_post_cycle_receipt_intake=intake,
        python_exam_manual_cycle_evidence_binder=binder,
        python_exam_manual_cycle_launch_receipt=launch_receipt,
        python_exam_manual_confirmation_console=console,
        selected_skill_tag="python_lists",
    )
    return preview, packet, timeline, ledger


class UniBotPythonExamManualReviewExportAuthorizationGateTests(unittest.TestCase):
    def test_authorization_gate_keeps_open_preview_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            preview, packet, timeline, ledger = authorization_gate_inputs(temp_dir, confirmed=False)
            gate = build_python_exam_manual_review_export_authorization_gate(
                python_exam_manual_review_export_preview=preview,
                python_exam_manual_cycle_review_packet=packet,
                python_exam_manual_cycle_review_timeline=timeline,
                python_exam_manual_cycle_closure_ledger=ledger,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(gate, ensure_ascii=False)
            summary = gate["authorization_gate_summary"]

            self.assertEqual(gate["artifact_type"], "python_exam_manual_review_export_authorization_gate")
            self.assertEqual(gate["status"], "python_exam_manual_review_export_authorization_gate_ready")
            self.assertEqual(gate["exam_deployment_status"], "not_cleared")
            self.assertEqual(gate["authorization_gate_decision"], "keep_export_blocked")
            self.assertEqual(summary["export_preview_recommendation"], "keep_export_preview_open")
            self.assertTrue(summary["export_manifest_hash"])
            self.assertFalse(gate["export_created"])
            self.assertFalse(gate["export_authorized"])
            self.assertTrue(gate["manual_review_export_authorization_gate_receipt"]["not_cleared_receipt"])
            self.assertFalse(gate["local_writes_requested"])
            self.assertFalse(gate["local_execution_started"])
            self.assertTrue(gate["dry_run_default"])
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
                self.assertFalse(gate[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-manual-review-export-authorization-gate")["status"], "pass")
            self.assertEqual(gate["public_safety_status"], "pass")

    def test_authorization_gate_requests_hash_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            preview, packet, timeline, ledger = authorization_gate_inputs(temp_dir, confirmed=True)
            gate = build_python_exam_manual_review_export_authorization_gate(
                python_exam_manual_review_export_preview=preview,
                python_exam_manual_cycle_review_packet=packet,
                python_exam_manual_cycle_review_timeline=timeline,
                python_exam_manual_cycle_closure_ledger=ledger,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(gate["authorization_gate_decision"], "request_hash_completion")
            self.assertEqual(
                gate["authorization_gate_summary"]["export_preview_recommendation"],
                "request_hash_completion",
            )
            self.assertIn("notebook_checkpoint_hash", gate["authorization_gate_summary"]["missing_required_hashes"])
            self.assertFalse(gate["export_created"])
            self.assertFalse(gate["export_authorized"])
            self.assertEqual(gate["public_safety_status"], "pass")

    def test_authorization_gate_ready_for_manual_authorization_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            preview, packet, timeline, ledger = authorization_gate_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            gate = build_python_exam_manual_review_export_authorization_gate(
                python_exam_manual_review_export_preview=preview,
                python_exam_manual_cycle_review_packet=packet,
                python_exam_manual_cycle_review_timeline=timeline,
                python_exam_manual_cycle_closure_ledger=ledger,
                selected_skill_tag="python_lists",
            )
            summary = gate["authorization_gate_summary"]

            self.assertEqual(gate["authorization_gate_decision"], "ready_for_manual_export_authorization_review")
            self.assertEqual(summary["export_preview_recommendation"], "ready_for_human_export_review")
            self.assertEqual(summary["packet_recommendation"], "ready_for_human_packet_review")
            self.assertTrue(summary["accepted_post_cycle_hashes"]["notebook_checkpoint_hash"])
            self.assertTrue(summary["receipt_hashes"]["preview_receipt_hash"])
            self.assertTrue(summary["authorization_gate_hash"])
            self.assertFalse(gate["export_created"])
            self.assertFalse(gate["export_authorized"])
            self.assertEqual(gate["public_safety_status"], "pass")

    def test_authorization_gate_rejects_rejected_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            preview, packet, timeline, ledger = authorization_gate_inputs(
                temp_dir,
                confirmed=True,
                mode="reject",
            )
            gate = build_python_exam_manual_review_export_authorization_gate(
                python_exam_manual_review_export_preview=preview,
                python_exam_manual_cycle_review_packet=packet,
                python_exam_manual_cycle_review_timeline=timeline,
                python_exam_manual_cycle_closure_ledger=ledger,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(gate["authorization_gate_decision"], "reject_export_authorization")
            self.assertEqual(gate["authorization_gate_summary"]["export_preview_recommendation"], "reject_export_preview")
            self.assertFalse(gate["notebook_code_returned"])
            self.assertFalse(gate["export_created"])
            self.assertFalse(gate["export_authorized"])
            self.assertEqual(gate["public_safety_status"], "pass")

    def test_authorization_gate_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            preview, packet, timeline, ledger = authorization_gate_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            status, gate = route_request(
                "/api/unibot/course/python-exam-manual-review-export-authorization-gate",
                {
                    "python_exam_manual_review_export_preview": preview,
                    "python_exam_manual_cycle_review_packet": packet,
                    "python_exam_manual_cycle_review_timeline": timeline,
                    "python_exam_manual_cycle_closure_ledger": ledger,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(gate["status"], "python_exam_manual_review_export_authorization_gate_ready")
            self.assertEqual(gate["authorization_gate_decision"], "ready_for_manual_export_authorization_review")
            self.assertFalse(gate["export_created"])
            self.assertFalse(gate["export_authorized"])
            self.assertEqual(gate["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
