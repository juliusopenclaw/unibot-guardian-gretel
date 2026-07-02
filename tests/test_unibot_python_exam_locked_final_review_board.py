from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_final_manual_review_action_lock import (
    build_python_exam_final_manual_review_action_lock,
)
from unibot.python_exam_locked_final_review_board import build_python_exam_locked_final_review_board
from unibot.server import route_request

from tests.test_unibot_python_exam_final_manual_review_action_lock import (
    final_manual_review_action_lock_inputs,
)


def board_support_artifacts(*, ready: bool) -> tuple[dict, dict, dict]:
    draft_status = (
        "python_exam_draft_package_review_console_ready"
        if ready
        else "python_exam_draft_package_review_console_attention"
    )
    handoff_status = (
        "python_exam_human_handoff_packet_ready"
        if ready
        else "python_exam_human_handoff_packet_attention"
    )
    rehearsal_status = (
        "python_exam_full_local_rehearsal_pack_ready"
        if ready
        else "python_exam_full_local_rehearsal_pack_attention"
    )
    draft_console = {
        "artifact_type": "python_exam_draft_package_review_console",
        "status": draft_status,
        "exam_deployment_status": "not_cleared",
        "review_summary": {
            "status": draft_status,
            "draft_present_status": "written" if ready else "preview_only",
            "draft_package_hash": "draft-package-hash",
            "file_hash_integrity_status": "file_hash_integrity_pass" if ready else "file_hash_integrity_attention",
            "next_safe_action": "review_draft_package_hashes",
        },
        "package_integrity": {
            "status": "file_hash_integrity_pass" if ready else "file_hash_integrity_attention",
            "draft_package_hash": "draft-package-hash",
            "missing_file_hashes": [] if ready else ["manifest_hash"],
            "mismatched_file_hashes": [],
        },
    }
    handoff = {
        "artifact_type": "python_exam_human_handoff_packet",
        "status": handoff_status,
        "exam_deployment_status": "not_cleared",
        "handoff_summary": {
            "status": handoff_status,
            "draft_package_id": "draft-package",
            "file_hash_integrity_status": "file_hash_integrity_pass",
            "notebook_checkpoint_hash_present": ready,
            "next_safe_action": "review_handoff_packet",
        },
        "copy_export_view": {
            "markdown_hash": "handoff-markdown-hash",
            "local_paths_included": False,
            "raw_text_included": False,
            "notebook_code_included": False,
        },
    }
    rehearsal = {
        "artifact_type": "python_exam_full_local_rehearsal_pack",
        "status": rehearsal_status,
        "exam_deployment_status": "not_cleared",
        "selected_skill_tag": "python_lists",
        "rehearsal_summary": {
            "status": rehearsal_status,
            "selected_skill_tag": "python_lists",
            "ready_step_count": 10 if ready else 8,
            "attention_step_count": 0 if ready else 2,
            "missing_step_count": 0,
            "human_handoff_status": handoff_status,
            "evidence_preview_status": "python_exam_evidence_export_preview_ready",
            "next_safe_action": "review_full_rehearsal_pack",
        },
        "source_anchor_metadata": {
            "source_card_ids": ["source-card-python-lists"],
            "source_anchor_count": 2,
        },
        "evidence_chain": {
            "human_handoff_markdown_hash": "handoff-markdown-hash",
            "evidence_preview_receipt_hash": "evidence-preview-receipt-hash",
        },
    }
    return draft_console, handoff, rehearsal


def locked_final_review_board_inputs(
    temp_dir: str,
    *,
    confirmed: bool,
    mode: str = "missing",
    support_ready: bool = False,
) -> tuple[dict, dict, dict, dict, dict, dict, dict]:
    console, gate, ledger = final_manual_review_action_lock_inputs(
        temp_dir,
        confirmed=confirmed,
        mode=mode,
    )
    lock = build_python_exam_final_manual_review_action_lock(
        python_exam_final_manual_review_console=console,
        python_exam_final_review_ledger_integrity_gate=gate,
        python_exam_manual_final_review_receipt_ledger=ledger,
        selected_skill_tag="python_lists",
    )
    draft, handoff, rehearsal = board_support_artifacts(ready=support_ready)
    return lock, console, gate, ledger, draft, handoff, rehearsal


class UniBotPythonExamLockedFinalReviewBoardTests(unittest.TestCase):
    def test_locked_final_review_board_keeps_open_without_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lock, console, gate, ledger, draft, handoff, rehearsal = locked_final_review_board_inputs(
                temp_dir,
                confirmed=False,
                support_ready=False,
            )
            board = build_python_exam_locked_final_review_board(
                python_exam_final_manual_review_action_lock=lock,
                python_exam_final_manual_review_console=console,
                python_exam_final_review_ledger_integrity_gate=gate,
                python_exam_manual_final_review_receipt_ledger=ledger,
                python_exam_draft_package_review_console=draft,
                python_exam_human_handoff_packet=handoff,
                python_exam_full_local_rehearsal_pack=rehearsal,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(board, ensure_ascii=False)
            summary = board["locked_final_review_board_summary"]

            self.assertEqual(board["artifact_type"], "python_exam_locked_final_review_board")
            self.assertEqual(board["status"], "python_exam_locked_final_review_board_ready")
            self.assertEqual(board["exam_deployment_status"], "not_cleared")
            self.assertEqual(board["locked_final_review_board_recommendation"], "keep_final_board_open")
            self.assertEqual(summary["final_manual_review_action_lock_recommendation"], "keep_action_locked")
            self.assertEqual(summary["final_manual_review_console_recommendation"], "keep_final_console_open")
            self.assertEqual(summary["final_review_ledger_integrity_gate_recommendation"], "keep_integrity_gate_open")
            self.assertEqual(summary["final_review_receipt_ledger_recommendation"], "keep_final_ledger_open")
            self.assertEqual(summary["draft_review_status"], "python_exam_draft_package_review_console_attention")
            self.assertEqual(summary["human_handoff_status"], "python_exam_human_handoff_packet_attention")
            self.assertEqual(summary["full_local_rehearsal_status"], "python_exam_full_local_rehearsal_pack_attention")
            self.assertGreaterEqual(summary["integrity_issue_count"], 1)
            self.assertIn("notebook_checkpoint_hash", summary["missing_required_hashes"])
            self.assertEqual(summary["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["help_level"], "A2")
            self.assertEqual(summary["ledger_event_count"], 5)
            self.assertTrue(summary["locked_final_review_board_hash"])
            self.assertFalse(board["export_created"])
            self.assertFalse(board["export_authorized"])
            self.assertFalse(board["archive_created"])
            self.assertFalse(board["submission_started"])
            self.assertTrue(board["locked_final_review_board_receipt"]["not_cleared_receipt"])
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
                self.assertFalse(board[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-locked-final-review-board")["status"], "pass")
            self.assertEqual(board["public_safety_status"], "pass")

    def test_locked_final_review_board_requests_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lock, console, gate, ledger, draft, handoff, rehearsal = locked_final_review_board_inputs(
                temp_dir,
                confirmed=True,
                support_ready=False,
            )
            board = build_python_exam_locked_final_review_board(
                python_exam_final_manual_review_action_lock=lock,
                python_exam_final_manual_review_console=console,
                python_exam_final_review_ledger_integrity_gate=gate,
                python_exam_manual_final_review_receipt_ledger=ledger,
                python_exam_draft_package_review_console=draft,
                python_exam_human_handoff_packet=handoff,
                python_exam_full_local_rehearsal_pack=rehearsal,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(board["locked_final_review_board_recommendation"], "request_manual_reconciliation")
            self.assertEqual(
                board["locked_final_review_board_summary"]["final_manual_review_action_lock_recommendation"],
                "request_manual_reconciliation",
            )
            self.assertFalse(board["archive_created"])
            self.assertFalse(board["submission_started"])
            self.assertEqual(board["public_safety_status"], "pass")

    def test_locked_final_review_board_ready_for_human_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lock, console, gate, ledger, draft, handoff, rehearsal = locked_final_review_board_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
                support_ready=True,
            )
            board = build_python_exam_locked_final_review_board(
                python_exam_final_manual_review_action_lock=lock,
                python_exam_final_manual_review_console=console,
                python_exam_final_review_ledger_integrity_gate=gate,
                python_exam_manual_final_review_receipt_ledger=ledger,
                python_exam_draft_package_review_console=draft,
                python_exam_human_handoff_packet=handoff,
                python_exam_full_local_rehearsal_pack=rehearsal,
                selected_skill_tag="python_lists",
            )
            summary = board["locked_final_review_board_summary"]

            self.assertEqual(board["locked_final_review_board_recommendation"], "ready_for_human_final_board_review")
            self.assertEqual(summary["final_manual_review_action_lock_recommendation"], "ready_for_manual_action_review")
            self.assertEqual(summary["draft_review_status"], "python_exam_draft_package_review_console_ready")
            self.assertEqual(summary["human_handoff_status"], "python_exam_human_handoff_packet_ready")
            self.assertEqual(summary["full_local_rehearsal_status"], "python_exam_full_local_rehearsal_pack_ready")
            self.assertEqual(summary["integrity_issue_count"], 0)
            self.assertFalse(summary["missing_required_hashes"])
            self.assertFalse(summary["mismatched_hashes"])
            self.assertEqual(summary["next_safe_human_review_action"], "present_locked_final_review_board_to_human_reviewer")
            self.assertFalse(board["archive_created"])
            self.assertFalse(board["submission_started"])
            self.assertEqual(board["public_safety_status"], "pass")

    def test_locked_final_review_board_rejects_rejected_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lock, console, gate, ledger, draft, handoff, rehearsal = locked_final_review_board_inputs(
                temp_dir,
                confirmed=True,
                mode="reject",
                support_ready=True,
            )
            board = build_python_exam_locked_final_review_board(
                python_exam_final_manual_review_action_lock=lock,
                python_exam_final_manual_review_console=console,
                python_exam_final_review_ledger_integrity_gate=gate,
                python_exam_manual_final_review_receipt_ledger=ledger,
                python_exam_draft_package_review_console=draft,
                python_exam_human_handoff_packet=handoff,
                python_exam_full_local_rehearsal_pack=rehearsal,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(board["locked_final_review_board_recommendation"], "reject_final_board")
            self.assertEqual(
                board["locked_final_review_board_summary"]["final_manual_review_action_lock_recommendation"],
                "reject_action_path",
            )
            self.assertFalse(board["notebook_code_returned"])
            self.assertFalse(board["archive_created"])
            self.assertFalse(board["submission_started"])
            self.assertEqual(board["public_safety_status"], "pass")

    def test_locked_final_review_board_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lock, console, gate, ledger, draft, handoff, rehearsal = locked_final_review_board_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
                support_ready=True,
            )
            status, board = route_request(
                "/api/unibot/course/python-exam-locked-final-review-board",
                {
                    "python_exam_final_manual_review_action_lock": lock,
                    "python_exam_final_manual_review_console": console,
                    "python_exam_final_review_ledger_integrity_gate": gate,
                    "python_exam_manual_final_review_receipt_ledger": ledger,
                    "python_exam_draft_package_review_console": draft,
                    "python_exam_human_handoff_packet": handoff,
                    "python_exam_full_local_rehearsal_pack": rehearsal,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(board["status"], "python_exam_locked_final_review_board_ready")
            self.assertEqual(board["locked_final_review_board_recommendation"], "ready_for_human_final_board_review")
            self.assertFalse(board["archive_created"])
            self.assertFalse(board["submission_started"])
            self.assertEqual(board["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
