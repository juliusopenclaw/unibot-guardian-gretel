from __future__ import annotations

import copy
import json
import tempfile
import unittest

from unibot.python_exam_confirmed_local_export_draft import build_python_exam_confirmed_local_export_draft
from unibot.python_exam_draft_package_review_console import build_python_exam_draft_package_review_console
from unibot.server import route_request

from tests.test_unibot_python_exam_confirmed_local_export_draft import ready_preview


class UniBotPythonExamDraftPackageReviewConsoleTests(unittest.TestCase):
    def test_review_console_ready_for_written_draft(self) -> None:
        preview = ready_preview()
        with tempfile.TemporaryDirectory() as temp_dir:
            draft = build_python_exam_confirmed_local_export_draft(
                python_exam_evidence_export_preview=preview,
                export_draft_dir=temp_dir,
                operator_confirmed_local_export_draft_write=True,
            )
            report = build_python_exam_draft_package_review_console(
                python_exam_confirmed_local_export_draft=draft,
                python_exam_evidence_export_preview=preview,
            )

        self.assertEqual(report["artifact_type"], "python_exam_draft_package_review_console")
        self.assertEqual(report["status"], "python_exam_draft_package_review_console_ready")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertEqual(report["review_summary"]["draft_present_status"], "written")
        self.assertEqual(report["package_integrity"]["status"], "file_hash_integrity_pass")
        self.assertEqual(report["manifest_status"]["status"], "manifest_present")
        self.assertEqual(report["not_cleared_receipt_status"]["status"], "not_cleared_receipt_present")
        self.assertEqual(report["process_log_status"]["status"], "process_log_present")
        self.assertEqual(report["help_level_profile"]["status"], "a0_a2_only")
        self.assertEqual(report["review_chain_status"]["status"], "review_chain_integrity_pass")
        self.assertEqual(report["review_chain_status"]["issue_count"], 0)
        self.assertEqual(report["receipt_journal_status"]["accepted_record_count"], 1)
        self.assertGreaterEqual(report["operator_confirmation_status"]["open_operator_confirmation_count"], 1)
        self.assertGreater(len(report["review_questions"]), 0)
        self.assertFalse(report["local_paths_returned"])
        self.assertFalse(report["raw_text_returned"])
        self.assertFalse(report["notebook_code_returned"])
        self.assertFalse(report["values_returned"])
        self.assertFalse(report["solutions_returned"])
        self.assertFalse(report["automatic_grading_started"])
        self.assertFalse(report["proctoring_started"])
        self.assertFalse(report["ai_detection_started"])
        self.assertFalse(report["exam_clearance_claimed"])
        self.assertEqual(report["public_safety_status"], "pass")
        self.assertNotIn(temp_dir, json.dumps(report, ensure_ascii=False))

    def test_review_console_ready_for_preview_only_draft(self) -> None:
        preview = ready_preview()
        draft = build_python_exam_confirmed_local_export_draft(
            python_exam_evidence_export_preview=preview,
            operator_confirmed_local_export_draft_write=False,
        )
        report = build_python_exam_draft_package_review_console(
            python_exam_confirmed_local_export_draft=draft,
            python_exam_evidence_export_preview=preview,
        )

        self.assertEqual(report["status"], "python_exam_draft_package_review_console_ready")
        self.assertEqual(report["review_summary"]["draft_present_status"], "preview_only")
        self.assertFalse(report["local_export_draft_written"])
        self.assertEqual(report["package_integrity"]["status"], "file_hash_integrity_pass")
        self.assertEqual(report["public_safety_status"], "pass")

    def test_review_console_marks_hash_mismatch_attention(self) -> None:
        preview = ready_preview()
        draft = build_python_exam_confirmed_local_export_draft(
            python_exam_evidence_export_preview=preview,
            operator_confirmed_local_export_draft_write=False,
        )
        broken = copy.deepcopy(draft)
        broken["draft_file_manifest"][0]["sha256"] = "bad-hash"
        report = build_python_exam_draft_package_review_console(
            python_exam_confirmed_local_export_draft=broken,
            python_exam_evidence_export_preview=preview,
        )

        self.assertEqual(report["status"], "python_exam_draft_package_review_console_attention")
        self.assertEqual(report["package_integrity"]["status"], "file_hash_integrity_attention")
        self.assertTrue(report["package_integrity"]["mismatched_file_hashes"])
        self.assertEqual(report["public_safety_status"], "pass")

    def test_review_console_api_route(self) -> None:
        preview = ready_preview()
        draft = build_python_exam_confirmed_local_export_draft(
            python_exam_evidence_export_preview=preview,
            operator_confirmed_local_export_draft_write=False,
        )
        status, report = route_request(
            "/api/unibot/course/python-exam-draft-package-review-console",
            payload={
                "python_exam_confirmed_local_export_draft": draft,
                "python_exam_evidence_export_preview": preview,
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "python_exam_draft_package_review_console_ready")
        self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
