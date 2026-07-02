from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction import build_course_extraction_queue  # noqa: E402
from unibot.extraction_progress import build_extraction_progress_report  # noqa: E402
from unibot.materials import sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_progress_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Videos").mkdir(parents=True)
    (root / "Week 1" / "lecture.pdf").write_bytes(b"%PDF-1.4\nfixture")
    (root / "Week 1" / "slides.pptx").write_bytes(b"pptx fixture")
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
        "decision_reference": "synthetic extraction progress decision",
    }


def receipt_for_job(job: dict[str, object], *, human_review_status: str = "pending_review") -> dict[str, object]:
    return {
        "job_id": job["job_id"],
        "material_id": job["material_id"],
        "job_type": job["job_type"],
        "extraction_status": "extracted_private",
        "raw_text_sha256": "c" * 64,
        "extracted_text_char_count": 777,
        "private_artifact_reference": "private progress artifact ref",
        "human_review_status": human_review_status,
        "decision_reference_hash": sha256_text(str(valid_decision()["decision_reference"])),
    }


class UniBotExtractionProgressTests(unittest.TestCase):
    def test_progress_report_blocks_without_valid_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_progress_fixture(fixture_root)

            report = build_extraction_progress_report(base_path=str(fixture_root))
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["artifact_type"], "course_extraction_progress_report")
            self.assertEqual(report["status"], "blocked_until_valid_rights_privacy_decision")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["queue_summary"]["job_count"], 3)
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertNotIn(str(fixture_root), payload)
            self.assertEqual(scan_text(payload, "extraction-progress-test")["status"], "pass")

    def test_progress_report_builds_human_review_queue_from_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_progress_fixture(fixture_root)
            queue = build_course_extraction_queue(
                base_path=str(fixture_root),
                rights_decision_reference=str(valid_decision()["decision_reference"]),
            )
            receipt = receipt_for_job(queue["jobs"][0])

            report = build_extraction_progress_report(
                base_path=str(fixture_root),
                decision_record=valid_decision(),
                receipts=[receipt],
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["status"], "receipts_ready_for_human_review")
            self.assertEqual(report["receipt_summary"]["valid_receipt_count"], 1)
            self.assertEqual(report["receipt_summary"]["ready_for_human_review_count"], 1)
            self.assertEqual(len(report["review_queue"]), 1)
            self.assertEqual(report["review_queue"][0]["job_id"], receipt["job_id"])
            self.assertNotIn("private progress artifact ref", payload)

    def test_progress_report_builds_manifest_candidates_after_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_progress_fixture(fixture_root)
            queue = build_course_extraction_queue(
                base_path=str(fixture_root),
                rights_decision_reference=str(valid_decision()["decision_reference"]),
            )
            receipt = receipt_for_job(queue["jobs"][0], human_review_status="reviewed_for_private_tutor")

            report = build_extraction_progress_report(
                base_path=str(fixture_root),
                decision_record=valid_decision(),
                receipts=[receipt],
            )

            self.assertEqual(report["status"], "receipts_reviewed_for_private_tutor")
            self.assertEqual(report["receipt_summary"]["eligible_for_private_tutor_index_count"], 1)
            self.assertEqual(len(report["manifest_update_candidates"]), 1)
            self.assertEqual(report["manifest_update_candidates"][0]["review_status_after_review"], "reviewed_for_private_tutor")

    def test_progress_report_blocks_invalid_receipts(self) -> None:
        receipt = {
            "job_id": "bad-job",
            "material_id": "bad-material",
            "job_type": "ocr",
            "extraction_status": "extracted_private",
            "raw_text": "raw OCR must not appear",
            "raw_text_sha256": "not-a-hash",
            "extracted_text_char_count": 0,
            "private_artifact_reference": "private progress artifact ref",
            "human_review_status": "pending_review",
            "decision_reference_hash": "bad",
        }

        report = build_extraction_progress_report(decision_record=valid_decision(), receipts=[receipt])

        self.assertEqual(report["status"], "blocked_invalid_receipts")
        self.assertEqual(report["receipt_summary"]["invalid_receipt_count"], 1)
        self.assertEqual(report["blocked_receipt_summaries"][0]["job_id"], "bad-job")
        self.assertEqual(report["public_safety_status"], "pass")

    def test_progress_api_route(self) -> None:
        status, report = route_request("/api/unibot/course/extraction-progress-report", {})

        self.assertEqual(status, 200)
        self.assertEqual(report["artifact_type"], "course_extraction_progress_report")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")


if __name__ == "__main__":
    unittest.main()
