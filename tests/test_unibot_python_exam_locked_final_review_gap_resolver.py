from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_locked_final_review_gap_resolver import (
    build_python_exam_locked_final_review_gap_resolver,
)
from unibot.server import route_request

from tests.test_unibot_python_exam_locked_final_review_board import (
    locked_final_review_board_inputs,
)


def gap_support_artifacts(*, action_key: str = "review_operator_confirmation") -> tuple[dict, dict]:
    gap_coach = {
        "artifact_type": "python_exam_rehearsal_playback_gap_coach",
        "status": "python_exam_rehearsal_playback_gap_coach_ready",
        "exam_deployment_status": "not_cleared",
        "selected_skill_tag": "python_lists",
        "next_safe_action_key": action_key,
        "playback_summary": {
            "selected_skill_tag": "python_lists",
            "next_safe_action_key": action_key,
        },
        "gap_profile": {
            "missing_or_attention_count": 0,
            "operator_confirmation_gap": action_key == "review_operator_confirmation",
            "source_gap": False,
            "notebook_checkpoint_gap": False,
            "a0_a2_profile_gap": False,
            "ready_for_human_review_packet": action_key == "ready_for_human_review_packet",
        },
        "source_anchor_metadata": {
            "source_card_ids": ["source-card-python-lists"],
            "source_anchor_count": 2,
        },
        "a0_a2_help_status": {"status": "a0_a2_only", "profile": {"A2": 1}},
        "evidence_playback": {
            "evidence_preview_status": "python_exam_evidence_export_preview_ready",
            "human_handoff_status": "python_exam_human_handoff_packet_ready",
            "human_handoff_markdown_hash": "handoff-markdown-hash",
        },
        "playback_receipt": {
            "receipt_hash": "gap-coach-receipt-hash",
            "not_cleared_receipt": True,
        },
    }
    surface = {
        "artifact_type": "python_exam_guided_loop_control_surface",
        "status": "python_exam_guided_loop_control_surface_ready",
        "exam_deployment_status": "not_cleared",
        "selected_skill_tag": "python_lists",
        "control_summary": {
            "selected_skill_tag": "python_lists",
            "action_key": action_key,
            "next_safe_click": "review_operator_confirmation_cards"
            if action_key == "review_operator_confirmation"
            else "open_human_review_packet_metadata",
            "prefill_hash": "guided-loop-prefill-hash",
        },
        "source_anchor_status": {"source_anchor_count": 2},
        "notebook_checkpoint_status": {"checkpoint_hash_count": 1},
        "operator_confirmation_status": {
            "open_operator_confirmation_count": 1 if action_key == "review_operator_confirmation" else 0,
        },
        "surface_receipt": {
            "receipt_hash": "guided-loop-surface-receipt-hash",
            "not_cleared_receipt": True,
        },
    }
    return gap_coach, surface


def gap_resolver_inputs(
    temp_dir: str,
    *,
    confirmed: bool,
    mode: str = "missing",
    support_ready: bool = False,
    action_key: str = "review_operator_confirmation",
) -> tuple[dict, dict, dict, dict, dict]:
    lock, console, gate, ledger, draft, handoff, rehearsal = locked_final_review_board_inputs(
        temp_dir,
        confirmed=confirmed,
        mode=mode,
        support_ready=support_ready,
    )
    from unibot.python_exam_locked_final_review_board import build_python_exam_locked_final_review_board

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
    gap_coach, surface = gap_support_artifacts(action_key=action_key)
    return board, lock, rehearsal, gap_coach, surface


class UniBotPythonExamLockedFinalReviewGapResolverTests(unittest.TestCase):
    def test_gap_resolver_keeps_open_without_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            board, lock, rehearsal, gap_coach, surface = gap_resolver_inputs(
                temp_dir,
                confirmed=False,
                support_ready=False,
            )
            resolver = build_python_exam_locked_final_review_gap_resolver(
                python_exam_locked_final_review_board=board,
                python_exam_final_manual_review_action_lock=lock,
                python_exam_full_local_rehearsal_pack=rehearsal,
                python_exam_rehearsal_playback_gap_coach=gap_coach,
                python_exam_guided_loop_control_surface=surface,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(resolver, ensure_ascii=False)
            summary = resolver["locked_final_review_gap_resolver_summary"]
            card = resolver["prioritized_repair_card"]

            self.assertEqual(resolver["artifact_type"], "python_exam_locked_final_review_gap_resolver")
            self.assertEqual(resolver["status"], "python_exam_locked_final_review_gap_resolver_ready")
            self.assertEqual(resolver["exam_deployment_status"], "not_cleared")
            self.assertEqual(resolver["locked_final_review_gap_resolver_recommendation"], "keep_gap_resolver_open")
            self.assertEqual(summary["locked_final_review_board_recommendation"], "keep_final_board_open")
            self.assertEqual(summary["final_manual_review_action_lock_recommendation"], "keep_action_locked")
            self.assertEqual(summary["gap_coach_next_safe_action_key"], "review_operator_confirmation")
            self.assertEqual(summary["affected_review_layer"], "notebook_checkpoint_hash")
            self.assertEqual(card["repair_action"], "review_notebook_checkpoint_hash_chain")
            self.assertIn("notebook_checkpoint_hash", summary["missing_required_hashes"])
            self.assertEqual(summary["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["help_level"], "A2")
            self.assertEqual(summary["ledger_event_count"], 5)
            self.assertTrue(summary["locked_final_review_gap_resolver_hash"])
            self.assertFalse(resolver["export_created"])
            self.assertFalse(resolver["archive_created"])
            self.assertFalse(resolver["submission_started"])
            self.assertTrue(resolver["locked_final_review_gap_resolver_receipt"]["not_cleared_receipt"])
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
                self.assertFalse(resolver[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-locked-final-review-gap-resolver")["status"], "pass")
            self.assertEqual(resolver["public_safety_status"], "pass")

    def test_gap_resolver_requests_manual_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            board, lock, rehearsal, gap_coach, surface = gap_resolver_inputs(
                temp_dir,
                confirmed=True,
                support_ready=False,
            )
            resolver = build_python_exam_locked_final_review_gap_resolver(
                python_exam_locked_final_review_board=board,
                python_exam_final_manual_review_action_lock=lock,
                python_exam_full_local_rehearsal_pack=rehearsal,
                python_exam_rehearsal_playback_gap_coach=gap_coach,
                python_exam_guided_loop_control_surface=surface,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(resolver["locked_final_review_gap_resolver_recommendation"], "request_manual_reconciliation")
            self.assertEqual(
                resolver["locked_final_review_gap_resolver_summary"]["locked_final_review_board_recommendation"],
                "request_manual_reconciliation",
            )
            self.assertFalse(resolver["archive_created"])
            self.assertFalse(resolver["submission_started"])
            self.assertEqual(resolver["public_safety_status"], "pass")

    def test_gap_resolver_ready_for_manual_rehearsal_recheck(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            board, lock, rehearsal, gap_coach, surface = gap_resolver_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
                support_ready=True,
                action_key="ready_for_human_review_packet",
            )
            resolver = build_python_exam_locked_final_review_gap_resolver(
                python_exam_locked_final_review_board=board,
                python_exam_final_manual_review_action_lock=lock,
                python_exam_full_local_rehearsal_pack=rehearsal,
                python_exam_rehearsal_playback_gap_coach=gap_coach,
                python_exam_guided_loop_control_surface=surface,
                selected_skill_tag="python_lists",
            )
            summary = resolver["locked_final_review_gap_resolver_summary"]

            self.assertEqual(resolver["locked_final_review_gap_resolver_recommendation"], "ready_for_manual_rehearsal_recheck")
            self.assertEqual(summary["locked_final_review_board_recommendation"], "ready_for_human_final_board_review")
            self.assertEqual(summary["affected_review_layer"], "manual_rehearsal_recheck")
            self.assertFalse(summary["missing_required_hashes"])
            self.assertFalse(summary["mismatched_hashes"])
            self.assertEqual(
                summary["prioritized_repair_card"]["repair_action"],
                "manual_rehearsal_recheck",
            )
            self.assertFalse(resolver["archive_created"])
            self.assertFalse(resolver["submission_started"])
            self.assertEqual(resolver["public_safety_status"], "pass")

    def test_gap_resolver_rejects_rejected_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            board, lock, rehearsal, gap_coach, surface = gap_resolver_inputs(
                temp_dir,
                confirmed=True,
                mode="reject",
                support_ready=True,
            )
            resolver = build_python_exam_locked_final_review_gap_resolver(
                python_exam_locked_final_review_board=board,
                python_exam_final_manual_review_action_lock=lock,
                python_exam_full_local_rehearsal_pack=rehearsal,
                python_exam_rehearsal_playback_gap_coach=gap_coach,
                python_exam_guided_loop_control_surface=surface,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(resolver["locked_final_review_gap_resolver_recommendation"], "reject_gap_resolution")
            self.assertEqual(
                resolver["locked_final_review_gap_resolver_summary"]["locked_final_review_board_recommendation"],
                "reject_final_board",
            )
            self.assertFalse(resolver["notebook_code_returned"])
            self.assertFalse(resolver["archive_created"])
            self.assertFalse(resolver["submission_started"])
            self.assertEqual(resolver["public_safety_status"], "pass")

    def test_gap_resolver_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            board, lock, rehearsal, gap_coach, surface = gap_resolver_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
                support_ready=True,
                action_key="ready_for_human_review_packet",
            )
            status, resolver = route_request(
                "/api/unibot/course/python-exam-locked-final-review-gap-resolver",
                {
                    "python_exam_locked_final_review_board": board,
                    "python_exam_final_manual_review_action_lock": lock,
                    "python_exam_full_local_rehearsal_pack": rehearsal,
                    "python_exam_rehearsal_playback_gap_coach": gap_coach,
                    "python_exam_guided_loop_control_surface": surface,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(resolver["status"], "python_exam_locked_final_review_gap_resolver_ready")
            self.assertEqual(resolver["locked_final_review_gap_resolver_recommendation"], "ready_for_manual_rehearsal_recheck")
            self.assertFalse(resolver["archive_created"])
            self.assertFalse(resolver["submission_started"])
            self.assertEqual(resolver["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
