from __future__ import annotations

import json
import tempfile
import unittest

from unibot.public_safety import scan_text
from unibot.python_exam_manual_cycle_review_packet import build_python_exam_manual_cycle_review_packet
from unibot.python_exam_manual_review_export_preview import build_python_exam_manual_review_export_preview
from unibot.server import route_request

from tests.test_unibot_python_exam_manual_cycle_review_packet import review_packet_inputs


def export_preview_inputs(temp_dir: str, *, confirmed: bool, mode: str = "missing") -> tuple[dict, dict, dict, dict, dict, dict, dict]:
    timeline, ledger, intake, binder, launch_receipt, console = review_packet_inputs(
        temp_dir,
        confirmed=confirmed,
        mode=mode,
    )
    packet = build_python_exam_manual_cycle_review_packet(
        python_exam_manual_cycle_review_timeline=timeline,
        python_exam_manual_cycle_closure_ledger=ledger,
        python_exam_manual_post_cycle_receipt_intake=intake,
        python_exam_manual_cycle_evidence_binder=binder,
        python_exam_manual_cycle_launch_receipt=launch_receipt,
        python_exam_manual_confirmation_console=console,
        selected_skill_tag="python_lists",
    )
    return packet, timeline, ledger, intake, binder, launch_receipt, console


class UniBotPythonExamManualReviewExportPreviewTests(unittest.TestCase):
    def test_export_preview_keeps_open_packet_open_without_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            packet, timeline, ledger, intake, binder, launch_receipt, console = export_preview_inputs(
                temp_dir,
                confirmed=False,
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
            payload = json.dumps(preview, ensure_ascii=False)
            summary = preview["export_preview_summary"]

            self.assertEqual(preview["artifact_type"], "python_exam_manual_review_export_preview")
            self.assertEqual(preview["status"], "python_exam_manual_review_export_preview_ready")
            self.assertEqual(preview["exam_deployment_status"], "not_cleared")
            self.assertEqual(preview["export_preview_recommendation"], "keep_export_preview_open")
            self.assertEqual(summary["packet_recommendation"], "keep_review_packet_open")
            self.assertTrue(summary["export_manifest_hash"])
            self.assertFalse(preview["export_created"])
            self.assertTrue(preview["manual_review_export_preview_receipt"]["not_cleared_receipt"])
            self.assertFalse(preview["local_writes_requested"])
            self.assertFalse(preview["local_execution_started"])
            self.assertTrue(preview["dry_run_default"])
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
                self.assertFalse(preview[flag], flag)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "python-exam-manual-review-export-preview")["status"], "pass")
            self.assertEqual(preview["public_safety_status"], "pass")

    def test_export_preview_requests_hash_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            packet, timeline, ledger, intake, binder, launch_receipt, console = export_preview_inputs(
                temp_dir,
                confirmed=True,
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

            self.assertEqual(preview["export_preview_recommendation"], "request_hash_completion")
            self.assertEqual(preview["export_preview_summary"]["packet_recommendation"], "request_hash_completion")
            self.assertIn("notebook_checkpoint_hash", preview["export_preview_summary"]["missing_required_hashes"])
            self.assertFalse(preview["export_created"])
            self.assertEqual(preview["public_safety_status"], "pass")

    def test_export_preview_ready_for_human_export_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            packet, timeline, ledger, intake, binder, launch_receipt, console = export_preview_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
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
            accepted = preview["export_preview_summary"]["accepted_post_cycle_hashes"]

            self.assertEqual(preview["export_preview_recommendation"], "ready_for_human_export_review")
            self.assertEqual(preview["export_preview_summary"]["packet_recommendation"], "ready_for_human_packet_review")
            self.assertTrue(accepted["notebook_checkpoint_hash"])
            self.assertTrue(preview["export_preview_summary"]["operator_reflection_hash"])
            self.assertTrue(preview["export_preview_summary"]["export_manifest_hash"])
            self.assertFalse(preview["export_created"])
            self.assertEqual(preview["public_safety_status"], "pass")

    def test_export_preview_rejects_rejected_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            packet, timeline, ledger, intake, binder, launch_receipt, console = export_preview_inputs(
                temp_dir,
                confirmed=True,
                mode="reject",
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

            self.assertEqual(preview["export_preview_recommendation"], "reject_export_preview")
            self.assertEqual(preview["export_preview_summary"]["packet_recommendation"], "reject_review_packet")
            self.assertFalse(preview["notebook_code_returned"])
            self.assertFalse(preview["export_created"])
            self.assertEqual(preview["public_safety_status"], "pass")

    def test_export_preview_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            packet, timeline, ledger, intake, binder, launch_receipt, console = export_preview_inputs(
                temp_dir,
                confirmed=True,
                mode="complete",
            )
            status, preview = route_request(
                "/api/unibot/course/python-exam-manual-review-export-preview",
                {
                    "python_exam_manual_cycle_review_packet": packet,
                    "python_exam_manual_cycle_review_timeline": timeline,
                    "python_exam_manual_cycle_closure_ledger": ledger,
                    "python_exam_manual_post_cycle_receipt_intake": intake,
                    "python_exam_manual_cycle_evidence_binder": binder,
                    "python_exam_manual_cycle_launch_receipt": launch_receipt,
                    "python_exam_manual_confirmation_console": console,
                    "selected_skill_tag": "python_lists",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(preview["status"], "python_exam_manual_review_export_preview_ready")
            self.assertEqual(preview["export_preview_recommendation"], "ready_for_human_export_review")
            self.assertFalse(preview["export_created"])
            self.assertEqual(preview["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
