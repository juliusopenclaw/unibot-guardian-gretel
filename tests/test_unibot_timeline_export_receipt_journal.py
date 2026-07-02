from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402
from unibot.timeline_export_receipt_journal import (  # noqa: E402
    build_timeline_export_receipt_journal_append,
    read_timeline_export_receipt_journal,
    summarize_timeline_export_receipt_journal,
)


def review_packet() -> dict[str, object]:
    return {
        "schema_version": "unibot-timeline-export-review-packet-v1",
        "artifact_type": "timeline_export_review_packet",
        "status": "timeline_export_review_packet_ready",
        "exam_deployment_status": "not_cleared",
        "public_safety_status": "pass",
        "export_review_summary": {
            "timeline_count": 1,
            "event_count": 1,
            "skill_count": 1,
            "skill_tags": ["python_lists"],
            "packet_receipt_count": 1,
            "timeline_receipt_count": 1,
            "checkpoint_hash_count": 1,
            "help_level_profile": {"A2": 1},
            "open_operator_confirmation_count": 2,
            "reflection_statuses": ["reflection_evidence_present"],
            "reviewer_question_count": 6,
            "exam_deployment_status": "not_cleared",
        },
        "local_export_receipt": {
            "status": "timeline_export_review_packet_receipt_ready_not_exam_clearance",
            "receipt_id": "timeline-review-123",
            "receipt_hash": "a" * 64,
            "local_write_started": False,
            "exam_deployment_status": "not_cleared",
            "not_cleared_receipt": True,
        },
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
    }


class UniBotTimelineExportReceiptJournalTests(unittest.TestCase):
    def test_preview_does_not_write_and_exposes_no_local_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            journal_path = Path(temp_dir) / "timeline_export_receipts.jsonl"
            preview = build_timeline_export_receipt_journal_append(
                review_packet=review_packet(),
                journal_path=journal_path,
                operator_confirmed_timeline_export_receipt_journal_append=False,
            )
            payload = json.dumps(preview, ensure_ascii=False)

            self.assertEqual(preview["artifact_type"], "timeline_export_receipt_journal_append")
            self.assertEqual(preview["status"], "write_preview_ready")
            self.assertFalse(preview["journal_written"])
            self.assertFalse(journal_path.exists())
            self.assertEqual(preview["write_preview"]["receipt_id"], "timeline-review-123")
            self.assertEqual(preview["write_preview"]["skill_tags"], ["python_lists"])
            self.assertEqual(preview["write_preview"]["checkpoint_hash_count"], 1)
            self.assertFalse(preview["raw_text_returned"])
            self.assertFalse(preview["notebook_code_returned"])
            self.assertFalse(preview["local_paths_returned"])
            self.assertFalse(preview["exam_clearance_claimed"])
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "timeline-export-receipt-preview")["status"], "pass")

    def test_confirmed_append_writes_safe_record_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            journal_path = Path(temp_dir) / "timeline_export_receipts.jsonl"
            stored = build_timeline_export_receipt_journal_append(
                review_packet=review_packet(),
                journal_path=journal_path,
                operator_confirmed_timeline_export_receipt_journal_append=True,
            )
            payload = json.dumps(stored, ensure_ascii=False)

            self.assertEqual(stored["status"], "stored")
            self.assertTrue(stored["journal_written"])
            self.assertTrue(journal_path.exists())
            self.assertNotIn(str(temp_dir), payload)
            self.assertFalse(stored["local_paths_returned"])

            journal = read_timeline_export_receipt_journal(journal_path)
            self.assertEqual(journal["count"], 1)
            self.assertEqual(journal["records"][0]["event"]["receipt_id"], "timeline-review-123")
            self.assertFalse(journal["records"][0]["event"]["raw_text_stored"])
            self.assertFalse(journal["records"][0]["event"]["notebook_code_stored"])
            self.assertFalse(journal["records"][0]["event"]["local_path_stored"])

            summary = summarize_timeline_export_receipt_journal(journal_path)
            summary_payload = json.dumps(summary, ensure_ascii=False)
            self.assertEqual(summary["artifact_type"], "timeline_export_receipt_journal_summary")
            self.assertEqual(summary["record_count"], 1)
            self.assertEqual(summary["accepted_record_count"], 1)
            self.assertIn("python_lists", summary["skill_tags"])
            self.assertEqual(summary["event_count"], 1)
            self.assertEqual(summary["checkpoint_hash_count"], 1)
            self.assertEqual(summary["reviewer_question_count"], 6)
            self.assertEqual(summary["help_level_profile"]["A2"], 1)
            self.assertEqual(summary["open_operator_confirmation_count"], 2)
            self.assertIn("reflection_evidence_present", summary["reflection_statuses"])
            self.assertEqual(summary["exam_deployment_status"], "not_cleared")
            self.assertFalse(summary["raw_text_returned"])
            self.assertFalse(summary["notebook_code_returned"])
            self.assertFalse(summary["local_paths_returned"])
            self.assertFalse(summary["exam_clearance_claimed"])
            self.assertNotIn(str(temp_dir), summary_payload)
            self.assertEqual(scan_text(summary_payload, "timeline-export-receipt-summary")["status"], "pass")

    def test_api_preview_append_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            journal_path = str(Path(temp_dir) / "timeline_export_receipts.jsonl")
            status, preview = route_request(
                "/api/unibot/course/timeline-export-receipt-journal/append",
                {
                    "timeline_export_receipt_journal_path": journal_path,
                    "review_packet": review_packet(),
                    "operator_confirmed_timeline_export_receipt_journal_append": False,
                },
            )
            self.assertEqual(status, 200)
            self.assertEqual(preview["status"], "write_preview_ready")
            self.assertFalse(preview["journal_written"])
            self.assertNotIn(temp_dir, json.dumps(preview, ensure_ascii=False))

            status, stored = route_request(
                "/api/unibot/course/timeline-export-receipt-journal/append",
                {
                    "timeline_export_receipt_journal_path": journal_path,
                    "review_packet": review_packet(),
                    "operator_confirmed_timeline_export_receipt_journal_append": True,
                },
            )
            self.assertEqual(status, 200)
            self.assertEqual(stored["status"], "stored")
            self.assertTrue(stored["journal_written"])
            self.assertNotIn(temp_dir, json.dumps(stored, ensure_ascii=False))

            status, summary = route_request(
                "/api/unibot/course/timeline-export-receipt-journal/summary",
                {"timeline_export_receipt_journal_path": journal_path},
            )
            self.assertEqual(status, 200)
            self.assertEqual(summary["record_count"], 1)
            self.assertFalse(summary["local_paths_returned"])
            self.assertNotIn(temp_dir, json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
