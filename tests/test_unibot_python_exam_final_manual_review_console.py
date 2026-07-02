from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_final_manual_review_console import build_python_exam_final_manual_review_console
from unibot.python_exam_final_review_ledger_integrity_gate import (
    build_python_exam_final_review_ledger_integrity_gate,
)
from unibot.server import route_request

from tests.test_unibot_python_exam_final_review_ledger_integrity_gate import integrity_gate_inputs


def final_manual_review_console_inputs(
    temp_dir: str,
    *,
    confirmed: bool,
    mode: str = "missing",
) -> tuple[dict, dict, dict, dict, dict, dict]:
    ledger, handoff, draft, reviewer, queue = integrity_gate_inputs(temp_dir, confirmed=confirmed, mode=mode)
    gate = build_python_exam_final_review_ledger_integrity_gate(
        python_exam_manual_final_review_receipt_ledger=ledger,
        python_exam_manual_final_review_handoff=handoff,
        python_exam_manual_archive_decision_draft=draft,
        python_exam_manual_export_reviewer_packet=reviewer,
        python_exam_manual_export_review_queue=queue,
        selected_skill_tag="python_lists",
    )
    return gate, ledger, handoff, draft, reviewer, queue


class UniBotPythonExamFinalManualReviewConsoleTests(unittest.TestCase):
    def test_final_manual_review_console_keeps_open_without_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            gate, ledger, handoff, draft, reviewer, queue = final_manual_review_console_inputs(
                temp_dir,
                confirmed=False,
            )
            console = build_python_exam_final_manual_review_console(
                python_exam_final_review_ledger_integrity_gate=gate,
                python_exam_manual_final_review_receipt_ledger=ledger,
                python_exam_manual_final_review_handoff=handoff,
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(console, ensure_ascii=False)
            summary = console["final_manual_review_console_summary"]

            self.assertEqual(console["artifact_type"], "python_exam_final_manual_review_console")
            self.assertEqual(console["status"], "python_exam_final_manual_review_console_ready")
            self.assertEqual(console["exam_deployment_status"], "not_cleared")
            self.assertEqual(console["final_manual_review_console_recommendation"], "keep_final_console_open")
            self.assertEqual(summary["final_review_ledger_integrity_gate_recommendation"], "keep_integrity_gate_open")
            self.assertEqual(summary["final_review_receipt_ledger_recommendation"], "keep_final_ledger_open")
            self.assertEqual(summary["final_review_handoff_recommendation"], "keep_final_handoff_open")
            self.assertEqual(summary["archive_decision_draft_recommendation"], "keep_archive_decision_draft_open")
            self.assertEqual(summary["reviewer_packet_recommendation"], "keep_reviewer_packet_open")
            self.assertEqual(summary["queue_recommendation"], "keep_queue_open")
            self.assertGreaterEqual(summary["integrity_issue_count"], 1)
            self.assertIn("notebook_checkpoint_hash", summary["missing_required_hashes"])
            self.assertFalse(summary["mismatched_hashes"])
            self.assertEqual(summary["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["help_level"], "A2")
            self.assertEqual(summary["ledger_event_count"], 5)
            self.assertTrue(summary["final_manual_review_console_hash"])
            self.assertFalse(console["export_created"])
            self.assertFalse(console["export_authorized"])
            self.assertFalse(console["archive_created"])
            self.assertFalse(console["submission_started"])
            self.assertTrue(console["final_manual_review_console_receipt"]["not_cleared_receipt"])
            self.assertTrue(console["dry_run_default"])
            self.assertFalse(console["local_writes_requested"])
            self.assertFalse(console["local_execution_started"])
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
            self.assertEqual(scan_text(payload, "python-exam-final-manual-review-console")["status"], "pass")
            self.assertEqual(console["public_safety_status"], "pass")

    def test_final_manual_review_console_requests_integrity_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            gate, ledger, handoff, draft, reviewer, queue = final_manual_review_console_inputs(
                temp_dir,
                confirmed=True,
            )
            console = build_python_exam_final_manual_review_console(
                python_exam_final_review_ledger_integrity_gate=gate,
                python_exam_manual_final_review_receipt_ledger=ledger,
                python_exam_manual_final_review_handoff=handoff,
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(console["final_manual_review_console_recommendation"], "request_integrity_reconciliation")
            self.assertEqual(
                console["final_manual_review_console_summary"]["final_review_ledger_integrity_gate_recommendation"],
                "request_hash_reconciliation",
            )
            self.assertIn(
                "notebook_checkpoint_hash",
                console["final_manual_review_console_summary"]["missing_required_hashes"],
            )
            self.assertFalse(console["archive_created"])
            self.assertFalse(console["submission_started"])
            self.assertEqual(console["public_safety_status"], "pass")

    def test_final_manual_review_console_ready_for_manual_console_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            gate, ledger, handoff, draft, reviewer, queue = final_manual_review_console_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            console = build_python_exam_final_manual_review_console(
                python_exam_final_review_ledger_integrity_gate=gate,
                python_exam_manual_final_review_receipt_ledger=ledger,
                python_exam_manual_final_review_handoff=handoff,
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                selected_skill_tag="python_lists",
            )
            summary = console["final_manual_review_console_summary"]

            self.assertEqual(console["final_manual_review_console_recommendation"], "ready_for_manual_console_review")
            self.assertEqual(summary["final_review_ledger_integrity_gate_recommendation"], "ready_for_manual_integrity_review")
            self.assertEqual(summary["integrity_issue_count"], 0)
            self.assertTrue(summary["accepted_post_cycle_hashes"]["notebook_checkpoint_hash"])
            self.assertEqual(summary["next_safe_human_review_action"], "present_final_hash_only_console_to_human_reviewer")
            self.assertFalse(console["archive_created"])
            self.assertFalse(console["submission_started"])
            self.assertEqual(console["public_safety_status"], "pass")

    def test_final_manual_review_console_rejects_rejected_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            gate, ledger, handoff, draft, reviewer, queue = final_manual_review_console_inputs(
                temp_dir,
                confirmed=True,
                mode="reject",
            )
            console = build_python_exam_final_manual_review_console(
                python_exam_final_review_ledger_integrity_gate=gate,
                python_exam_manual_final_review_receipt_ledger=ledger,
                python_exam_manual_final_review_handoff=handoff,
                python_exam_manual_archive_decision_draft=draft,
                python_exam_manual_export_reviewer_packet=reviewer,
                python_exam_manual_export_review_queue=queue,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(console["final_manual_review_console_recommendation"], "reject_final_console")
            self.assertEqual(
                console["final_manual_review_console_summary"]["final_review_ledger_integrity_gate_recommendation"],
                "reject_integrity_chain",
            )
            self.assertFalse(console["notebook_code_returned"])
            self.assertFalse(console["archive_created"])
            self.assertFalse(console["submission_started"])
            self.assertEqual(console["public_safety_status"], "pass")

    def test_final_manual_review_console_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            gate, ledger, handoff, draft, reviewer, queue = final_manual_review_console_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            status, console = route_request(
                "/api/unibot/course/python-exam-final-manual-review-console",
                {
                    "python_exam_final_review_ledger_integrity_gate": gate,
                    "python_exam_manual_final_review_receipt_ledger": ledger,
                    "python_exam_manual_final_review_handoff": handoff,
                    "python_exam_manual_archive_decision_draft": draft,
                    "python_exam_manual_export_reviewer_packet": reviewer,
                    "python_exam_manual_export_review_queue": queue,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(console["status"], "python_exam_final_manual_review_console_ready")
            self.assertEqual(console["final_manual_review_console_recommendation"], "ready_for_manual_console_review")
            self.assertFalse(console["archive_created"])
            self.assertFalse(console["submission_started"])
            self.assertEqual(console["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
