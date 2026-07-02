from __future__ import annotations

import json
import tempfile
import unittest

from unibot.materials import sha256_text
from unibot.public_safety import scan_text
from unibot.python_exam_manual_cycle_evidence_binder import build_python_exam_manual_cycle_evidence_binder
from unibot.python_exam_manual_post_cycle_receipt_intake import (
    build_python_exam_manual_post_cycle_receipt_intake,
)
from unibot.server import route_request

from tests.test_unibot_python_exam_manual_cycle_evidence_binder import evidence_binder_inputs


def intake_inputs(temp_dir: str, *, confirmed: bool) -> tuple[dict, dict, dict]:
    launch_receipt, console, chain_snapshot, workspace_card, _handoff = evidence_binder_inputs(
        temp_dir,
        confirmed=confirmed,
    )
    binder = build_python_exam_manual_cycle_evidence_binder(
        python_exam_manual_cycle_launch_receipt=launch_receipt,
        python_exam_manual_confirmation_console=console,
        python_exam_local_cycle_chain_snapshot=chain_snapshot,
        python_exam_local_cycle_operator_workspace_card=workspace_card,
        selected_skill_tag="python_lists",
    )
    return binder, launch_receipt, console


def complete_hash_metadata(binder: dict) -> dict:
    summary = binder["binder_summary"]
    return {
        "notebook_checkpoint_hash": sha256_text("human notebook checkpoint after manual cycle"),
        "help_ledger_entry_hash": sha256_text("human help ledger entry after manual cycle"),
        "task_hash": summary["task_hash"],
        "source_card_ids": summary["source_card_ids"],
        "source_anchor_hashes": [sha256_text("source anchor after manual cycle")],
        "source_anchor_count": 1,
        "operator_reflection_hash": sha256_text("short operator reflection hash only"),
        "post_cycle_receipt_hash": sha256_text("post cycle receipt"),
        "human_confirmation_hash": sha256_text("human confirmation"),
    }


class UniBotPythonExamManualPostCycleReceiptIntakeTests(unittest.TestCase):
    def test_intake_keeps_review_open_when_pre_cycle_binder_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            binder, launch_receipt, console = intake_inputs(temp_dir, confirmed=False)
            intake = build_python_exam_manual_post_cycle_receipt_intake(
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                selected_skill_tag="python_lists",
            )
            payload = json.dumps(intake, ensure_ascii=False)

            self.assertEqual(intake["artifact_type"], "python_exam_manual_post_cycle_receipt_intake")
            self.assertEqual(intake["status"], "python_exam_manual_post_cycle_receipt_intake_ready")
            self.assertEqual(intake["exam_deployment_status"], "not_cleared")
            self.assertEqual(intake["post_cycle_review_recommendation"], "keep_post_cycle_review_open")
            self.assertEqual(
                intake["post_cycle_intake_summary"]["post_cycle_review_reason"],
                "pre_cycle_stop_go_chain_not_ready_for_post_cycle_intake",
            )
            self.assertTrue(intake["manual_post_cycle_receipt_intake"]["not_cleared_receipt"])
            self.assertFalse(intake["local_writes_requested"])
            self.assertFalse(intake["local_execution_started"])
            self.assertTrue(intake["dry_run_default"])
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
                self.assertFalse(intake[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-manual-post-cycle-receipt-intake")["status"], "pass")
            self.assertEqual(intake["public_safety_status"], "pass")

    def test_intake_requests_missing_hashes_after_ready_pre_cycle_binder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            binder, launch_receipt, console = intake_inputs(temp_dir, confirmed=True)
            intake = build_python_exam_manual_post_cycle_receipt_intake(
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(intake["post_cycle_review_recommendation"], "request_missing_post_cycle_hashes")
            self.assertIn("notebook_checkpoint_hash", intake["post_cycle_intake_summary"]["missing_required_hashes"])
            self.assertEqual(intake["public_safety_status"], "pass")

    def test_intake_accepts_complete_hash_only_post_cycle_receipt_for_human_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            binder, launch_receipt, console = intake_inputs(temp_dir, confirmed=True)
            intake = build_python_exam_manual_post_cycle_receipt_intake(
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                post_cycle_hash_metadata=complete_hash_metadata(binder),
                selected_skill_tag="python_lists",
            )

            self.assertEqual(
                intake["post_cycle_review_recommendation"],
                "accept_hash_only_post_cycle_receipt_for_human_review",
            )
            self.assertEqual(intake["post_cycle_hash_metadata"]["status"], "post_cycle_hash_metadata_present")
            self.assertTrue(intake["post_cycle_hash_metadata"]["hash_only"])
            self.assertEqual(intake["post_cycle_intake_summary"]["source_anchor_hash_count"], 1)
            self.assertEqual(intake["public_safety_status"], "pass")

    def test_intake_rejects_raw_or_code_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            binder, launch_receipt, console = intake_inputs(temp_dir, confirmed=True)
            metadata = complete_hash_metadata(binder)
            metadata["notebook_code"] = "print('raw solution code')"
            intake = build_python_exam_manual_post_cycle_receipt_intake(
                python_exam_manual_cycle_evidence_binder=binder,
                python_exam_manual_cycle_launch_receipt=launch_receipt,
                python_exam_manual_confirmation_console=console,
                post_cycle_hash_metadata=metadata,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(intake["post_cycle_review_recommendation"], "reject_post_cycle_receipt")
            self.assertIn("notebook_code", intake["post_cycle_intake_summary"]["forbidden_metadata_keys"])
            self.assertFalse(intake["notebook_code_returned"])
            self.assertEqual(intake["public_safety_status"], "pass")

    def test_intake_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            binder, launch_receipt, console = intake_inputs(temp_dir, confirmed=True)
            status, intake = route_request(
                "/api/unibot/course/python-exam-manual-post-cycle-receipt-intake",
                {
                    "python_exam_manual_cycle_evidence_binder": binder,
                    "python_exam_manual_cycle_launch_receipt": launch_receipt,
                    "python_exam_manual_confirmation_console": console,
                    "post_cycle_hash_metadata": complete_hash_metadata(binder),
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(intake["status"], "python_exam_manual_post_cycle_receipt_intake_ready")
            self.assertEqual(
                intake["post_cycle_review_recommendation"],
                "accept_hash_only_post_cycle_receipt_for_human_review",
            )
            self.assertEqual(intake["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
