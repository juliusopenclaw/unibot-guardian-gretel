from __future__ import annotations

import copy
import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_final_review_ledger_integrity_gate import (
    build_python_exam_final_review_ledger_integrity_gate,
)
from unibot.server import route_request

from tests.test_unibot_python_exam_manual_final_review_receipt_ledger import (
    final_review_receipt_ledger_inputs,
)
from unibot.python_exam_manual_final_review_receipt_ledger import (
    build_python_exam_manual_final_review_receipt_ledger,
)


def integrity_gate_inputs(
    temp_dir: str,
    *,
    confirmed: bool,
    mode: str = "missing",
) -> tuple[dict, dict, dict, dict, dict]:
    handoff, draft, reviewer, queue = final_review_receipt_ledger_inputs(
        temp_dir,
        confirmed=confirmed,
        mode=mode,
    )
    ledger = build_python_exam_manual_final_review_receipt_ledger(
        python_exam_manual_final_review_handoff=handoff,
        python_exam_manual_archive_decision_draft=draft,
        python_exam_manual_export_reviewer_packet=reviewer,
        python_exam_manual_export_review_queue=queue,
        selected_skill_tag="python_lists",
    )
    return ledger, handoff, draft, reviewer, queue


class UniBotPythonExamFinalReviewLedgerIntegrityGateTests(unittest.TestCase):
    def test_integrity_gate_keeps_open_without_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger, handoff, draft, reviewer, queue = integrity_gate_inputs(temp_dir, confirmed=False)
            gate = build_python_exam_final_review_ledger_integrity_gate(
                python_exam_manual_final_review_receipt_ledger=ledger,
                python_exam_manual_final_review_handoff=handoff,
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(gate, ensure_ascii=False)
            summary = gate["final_review_ledger_integrity_gate_summary"]

            self.assertEqual(gate["artifact_type"], "python_exam_final_review_ledger_integrity_gate")
            self.assertEqual(gate["status"], "python_exam_final_review_ledger_integrity_gate_ready")
            self.assertEqual(gate["exam_deployment_status"], "not_cleared")
            self.assertEqual(gate["final_review_ledger_integrity_gate_recommendation"], "keep_integrity_gate_open")
            self.assertEqual(summary["final_review_receipt_ledger_recommendation"], "keep_final_ledger_open")
            self.assertEqual(summary["final_review_handoff_recommendation"], "keep_final_handoff_open")
            self.assertGreaterEqual(summary["chain_issue_count"], 1)
            self.assertIn("notebook_checkpoint_hash", summary["missing_required_hashes"])
            self.assertFalse(summary["mismatched_hashes"])
            self.assertEqual(summary["ledger_event_count"], 5)
            self.assertTrue(summary["final_review_ledger_integrity_gate_hash"])
            self.assertFalse(gate["export_created"])
            self.assertFalse(gate["export_authorized"])
            self.assertFalse(gate["archive_created"])
            self.assertFalse(gate["submission_started"])
            self.assertTrue(gate["final_review_ledger_integrity_gate_receipt"]["not_cleared_receipt"])
            self.assertTrue(gate["dry_run_default"])
            self.assertFalse(gate["local_writes_requested"])
            self.assertFalse(gate["local_execution_started"])
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
            self.assertEqual(scan_text(payload, "python-exam-final-review-ledger-integrity-gate")["status"], "pass")
            self.assertEqual(gate["public_safety_status"], "pass")

    def test_integrity_gate_requests_hash_reconciliation_for_missing_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger, handoff, draft, reviewer, queue = integrity_gate_inputs(temp_dir, confirmed=True)
            gate = build_python_exam_final_review_ledger_integrity_gate(
                python_exam_manual_final_review_receipt_ledger=ledger,
                python_exam_manual_final_review_handoff=handoff,
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(gate["final_review_ledger_integrity_gate_recommendation"], "request_hash_reconciliation")
            self.assertIn(
                "notebook_checkpoint_hash",
                gate["final_review_ledger_integrity_gate_summary"]["missing_required_hashes"],
            )
            self.assertFalse(gate["archive_created"])
            self.assertFalse(gate["submission_started"])
            self.assertEqual(gate["public_safety_status"], "pass")

    def test_integrity_gate_ready_for_manual_integrity_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger, handoff, draft, reviewer, queue = integrity_gate_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            gate = build_python_exam_final_review_ledger_integrity_gate(
                python_exam_manual_final_review_receipt_ledger=ledger,
                python_exam_manual_final_review_handoff=handoff,
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                selected_skill_tag="python_lists",
            )
            summary = gate["final_review_ledger_integrity_gate_summary"]

            self.assertEqual(gate["final_review_ledger_integrity_gate_recommendation"], "ready_for_manual_integrity_review")
            self.assertEqual(summary["final_review_receipt_ledger_recommendation"], "ready_for_manual_final_ledger_review")
            self.assertEqual(summary["chain_issue_count"], 0)
            self.assertTrue(summary["accepted_post_cycle_hashes"]["notebook_checkpoint_hash"])
            self.assertTrue(summary["source_hashes"]["final_review_handoff_hash"])
            self.assertEqual(summary["ledger_event_count"], 5)
            self.assertFalse(gate["archive_created"])
            self.assertFalse(gate["submission_started"])
            self.assertEqual(gate["public_safety_status"], "pass")

    def test_integrity_gate_requests_reconciliation_for_mismatched_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger, handoff, draft, reviewer, queue = integrity_gate_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            broken_ledger = copy.deepcopy(ledger)
            broken_ledger["final_review_receipt_ledger_summary"]["queue_hash"] = "0" * 64
            gate = build_python_exam_final_review_ledger_integrity_gate(
                python_exam_manual_final_review_receipt_ledger=broken_ledger,
                python_exam_manual_final_review_handoff=handoff,
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(gate["final_review_ledger_integrity_gate_recommendation"], "request_hash_reconciliation")
            self.assertIn("queue_hash", gate["final_review_ledger_integrity_gate_summary"]["mismatched_hashes"])
            self.assertFalse(gate["archive_created"])
            self.assertFalse(gate["submission_started"])
            self.assertEqual(gate["public_safety_status"], "pass")

    def test_integrity_gate_rejects_rejected_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger, handoff, draft, reviewer, queue = integrity_gate_inputs(
                temp_dir,
                confirmed=True,
                mode="reject",
            )
            gate = build_python_exam_final_review_ledger_integrity_gate(
                python_exam_manual_final_review_receipt_ledger=ledger,
                python_exam_manual_final_review_handoff=handoff,
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(gate["final_review_ledger_integrity_gate_recommendation"], "reject_integrity_chain")
            self.assertEqual(
                gate["final_review_ledger_integrity_gate_summary"]["final_review_receipt_ledger_recommendation"],
                "reject_final_ledger",
            )
            self.assertFalse(gate["notebook_code_returned"])
            self.assertFalse(gate["archive_created"])
            self.assertFalse(gate["submission_started"])
            self.assertEqual(gate["public_safety_status"], "pass")

    def test_integrity_gate_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger, handoff, draft, reviewer, queue = integrity_gate_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            status, gate = route_request(
                "/api/unibot/course/python-exam-final-review-ledger-integrity-gate",
                {
                    "python_exam_manual_final_review_receipt_ledger": ledger,
                    "python_exam_manual_final_review_handoff": handoff,
                    "python_exam_manual_archive_decision_draft": draft,
                    "python_exam_manual_export_reviewer_packet": reviewer,
                    "python_exam_manual_export_review_queue": queue,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(gate["status"], "python_exam_final_review_ledger_integrity_gate_ready")
            self.assertEqual(gate["final_review_ledger_integrity_gate_recommendation"], "ready_for_manual_integrity_review")
            self.assertFalse(gate["archive_created"])
            self.assertFalse(gate["submission_started"])
            self.assertEqual(gate["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
