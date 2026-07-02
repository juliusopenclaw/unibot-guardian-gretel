from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction import build_course_extraction_queue  # noqa: E402
from unibot.extraction_receipt_journal import (  # noqa: E402
    append_extraction_receipt_record,
    extraction_receipts_for_progress,
    read_extraction_receipt_journal,
    sanitize_extraction_receipt_record,
    summarize_extraction_receipt_journal,
)
from unibot.materials import sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_journal_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Videos").mkdir(parents=True)
    (root / "Week 1" / "lecture.pdf").write_bytes(b"%PDF-1.4\nfixture")
    (root / "Videos" / "lecture.mov").write_bytes(b"video")


def valid_decision() -> dict[str, object]:
    return {
        "decision_status": "approved_for_local_extraction",
        "scope": "local_private_course_extraction",
        "allowed_job_types": ["ocr", "transcription"],
        "storage_policy": "local_private_only",
        "cloud_processing_allowed": False,
        "raw_text_public_release_allowed": False,
        "human_review_before_tutor_index": True,
        "retention_decision": "delete private extraction artifacts after reviewed metadata is accepted",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic extraction receipt journal decision",
    }


def receipt_for_job(job: dict[str, object], *, human_review_status: str = "pending_review") -> dict[str, object]:
    return {
        "job_id": job["job_id"],
        "material_id": job["material_id"],
        "job_type": job["job_type"],
        "extraction_status": "extracted_private",
        "raw_text_sha256": "d" * 64,
        "extracted_text_char_count": 640,
        "private_artifact_reference": "local private extraction artifact reference",
        "human_review_status": human_review_status,
        "decision_reference_hash": sha256_text(str(valid_decision()["decision_reference"])),
    }


class UniBotExtractionReceiptJournalTests(unittest.TestCase):
    def test_receipt_journal_record_is_hash_only_and_public_safe(self) -> None:
        receipt = {
            "job_id": "job-1",
            "material_id": "material-1",
            "job_type": "ocr",
            "extraction_status": "extracted_private",
            "raw_text_sha256": "d" * 64,
            "extracted_text_char_count": 640,
            "private_artifact_reference": "local private extraction artifact reference",
            "human_review_status": "pending_review",
            "decision_reference_hash": sha256_text(str(valid_decision()["decision_reference"])),
        }

        record = sanitize_extraction_receipt_record(receipt, decision_record=valid_decision())
        payload = json.dumps(record, ensure_ascii=False)

        self.assertEqual(record["artifact_type"], "course_extraction_receipt_journal_record")
        self.assertEqual(record["status"], "accepted")
        self.assertEqual(record["public_safety_status"], "pass")
        self.assertFalse(record["event"]["raw_text_stored"])
        self.assertFalse(record["event"]["local_path_stored"])
        self.assertTrue(record["event"]["private_artifact_reference_hash"])
        self.assertNotIn("local private extraction artifact reference", payload)
        self.assertEqual(scan_text(payload, "extraction-receipt-journal-test")["status"], "pass")

    def test_receipt_journal_append_read_summary_and_progress_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            journal_path = Path(temp_dir) / "extraction_receipts.jsonl"
            receipt = {
                "job_id": "job-1",
                "material_id": "material-1",
                "job_type": "ocr",
                "extraction_status": "extracted_private",
                "raw_text_sha256": "d" * 64,
                "extracted_text_char_count": 640,
                "private_artifact_reference": "local private extraction artifact reference",
                "human_review_status": "reviewed_for_private_tutor",
                "decision_reference_hash": sha256_text(str(valid_decision()["decision_reference"])),
            }

            stored = append_extraction_receipt_record(
                receipt,
                decision_record=valid_decision(),
                path=journal_path,
            )
            self.assertEqual(stored["status"], "stored")

            listed = read_extraction_receipt_journal(journal_path)
            self.assertEqual(listed["count"], 1)
            self.assertEqual(len(listed["receipts_for_progress"]), 1)
            progress_receipts = extraction_receipts_for_progress(path=journal_path)
            self.assertEqual(progress_receipts[0]["job_id"], "job-1")
            self.assertIn("private-artifact-hash:", progress_receipts[0]["private_artifact_reference"])

            summary = summarize_extraction_receipt_journal(journal_path)
            self.assertEqual(summary["record_count"], 1)
            self.assertEqual(summary["accepted_record_count"], 1)
            self.assertEqual(summary["eligible_for_private_tutor_index_count"], 1)
            self.assertEqual(summary["progress_receipt_count"], 1)
            self.assertEqual(summary["public_safety_status"], "pass")

    def test_receipt_journal_does_not_store_blocked_raw_text_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            journal_path = Path(temp_dir) / "extraction_receipts.jsonl"
            receipt = {
                "job_id": "job-1",
                "material_id": "material-1",
                "job_type": "ocr",
                "extraction_status": "extracted_private",
                "raw_text": "raw OCR must not be stored",
                "raw_text_sha256": "bad",
                "extracted_text_char_count": 0,
                "private_artifact_reference": "local private extraction artifact reference",
                "human_review_status": "pending_review",
                "decision_reference_hash": "bad",
            }

            stored = append_extraction_receipt_record(
                receipt,
                decision_record=valid_decision(),
                path=journal_path,
            )

            self.assertEqual(stored["status"], "blocked")
            self.assertFalse(journal_path.exists())
            self.assertIn("receipt_validation_blocked", stored["record"]["event"]["issues"])

    def test_receipt_journal_api_can_feed_progress_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir) / "course"
            journal_path = Path(temp_dir) / "extraction_receipts.jsonl"
            write_journal_fixture(fixture_root)
            queue = build_course_extraction_queue(
                base_path=str(fixture_root),
                rights_decision_reference=str(valid_decision()["decision_reference"]),
            )
            receipt = receipt_for_job(queue["jobs"][0])

            status, stored = route_request(
                "/api/unibot/course/extraction-receipts/append",
                {
                    "receipt": receipt,
                    "decision_record": valid_decision(),
                    "receipt_journal_path": str(journal_path),
                },
            )
            self.assertEqual(status, 200)
            self.assertEqual(stored["status"], "stored")

            status, listed = route_request(
                "/api/unibot/course/extraction-receipts/list",
                {"receipt_journal_path": str(journal_path)},
            )
            self.assertEqual(status, 200)
            self.assertEqual(listed["count"], 1)

            status, summary = route_request(
                "/api/unibot/course/extraction-receipts/summary",
                {"receipt_journal_path": str(journal_path)},
            )
            self.assertEqual(status, 200)
            self.assertEqual(summary["ready_for_human_review_count"], 1)

            status, report = route_request(
                "/api/unibot/course/extraction-progress-report",
                {
                    "base_path": str(fixture_root),
                    "decision_record": valid_decision(),
                    "receipt_journal_path": str(journal_path),
                },
            )
            self.assertEqual(status, 200)
            self.assertEqual(report["receipt_summary"]["valid_receipt_count"], 1)
            self.assertEqual(report["receipt_summary"]["ready_for_human_review_count"], 1)

            status, response = route_request(
                "/api/unibot/course/extraction-receipts/append",
                {"receipt": []},
            )
            self.assertEqual(status, 400)
            self.assertEqual(response["status"], "invalid-receipt")


if __name__ == "__main__":
    unittest.main()
