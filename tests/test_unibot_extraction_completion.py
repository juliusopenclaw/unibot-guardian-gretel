from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction import build_course_extraction_queue  # noqa: E402
from unibot.extraction_completion import (  # noqa: E402
    build_extraction_completion_report,
    validate_extraction_deferral_record,
)
from unibot.materials import sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_completion_fixture(root: Path) -> None:
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
        "decision_reference": "synthetic extraction completion decision",
    }


def valid_deferral() -> dict[str, object]:
    return {
        "deferral_scope": "course_material_extraction",
        "decision_status": "approved_deferral",
        "deferred_job_types": ["ocr", "transcription"],
        "deferral_reason": "current public draft can proceed with reviewed anchors while remaining extraction is deferred",
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic extraction deferral decision",
        "human_review_before_future_tutor_use": True,
        "raw_text_public_release_allowed": False,
        "exam_deployment_status": "not_cleared",
    }


def reviewed_receipt_for_job(job: dict[str, object]) -> dict[str, object]:
    return {
        "job_id": job["job_id"],
        "material_id": job["material_id"],
        "job_type": job["job_type"],
        "extraction_status": "extracted_private",
        "raw_text_sha256": "f" * 64,
        "extracted_text_char_count": 900,
        "private_artifact_reference": "private completion artifact ref",
        "human_review_status": "reviewed_for_private_tutor",
        "decision_reference_hash": sha256_text(str(valid_decision()["decision_reference"])),
    }


class UniBotExtractionCompletionTests(unittest.TestCase):
    def test_deferral_validation_is_hash_only_and_public_safe(self) -> None:
        validation = validate_extraction_deferral_record(valid_deferral())
        payload = json.dumps(validation, ensure_ascii=False)

        self.assertEqual(validation["artifact_type"], "course_extraction_deferral_validation")
        self.assertEqual(validation["status"], "ok_extraction_deferral_record")
        self.assertEqual(validation["public_safety_status"], "pass")
        self.assertTrue(validation["decision_reference_hash"])
        self.assertFalse(validation["raw_decision_reference_stored"])
        self.assertFalse(validation["raw_deferral_reason_stored"])
        self.assertNotIn("synthetic extraction deferral decision", payload)
        self.assertNotIn("current public draft can proceed", payload)
        self.assertEqual(scan_text(payload, "extraction-deferral-test")["status"], "pass")

    def test_completion_report_stays_open_without_receipts_or_deferral(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_completion_fixture(fixture_root)

            report = build_extraction_completion_report(
                base_path=str(fixture_root),
                decision_record=valid_decision(),
            )

            self.assertEqual(report["artifact_type"], "course_extraction_completion_report")
            self.assertEqual(report["status"], "open_extraction_jobs_require_receipts_or_deferral")
            self.assertEqual(report["job_summary"]["open_job_count"], 2)
            self.assertEqual(report["job_summary"]["missing_job_count"], 2)
            self.assertEqual(report["public_safety_status"], "pass")

    def test_completion_report_accepts_valid_intentional_deferral(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_completion_fixture(fixture_root)

            report = build_extraction_completion_report(
                base_path=str(fixture_root),
                decision_record=valid_decision(),
                deferral_record=valid_deferral(),
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["status"], "complete_intentionally_deferred")
            self.assertEqual(report["job_summary"]["open_job_count"], 2)
            self.assertEqual(report["job_summary"]["deferred_job_count"], 2)
            self.assertEqual(report["job_summary"]["missing_job_count"], 0)
            self.assertEqual(report["deferral_summary"]["status"], "ok_extraction_deferral_record")
            self.assertNotIn(str(fixture_root), payload)
            self.assertEqual(scan_text(payload, "extraction-completion-deferral-test")["status"], "pass")

    def test_completion_report_accepts_reviewed_receipts_for_all_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_completion_fixture(fixture_root)
            queue = build_course_extraction_queue(
                base_path=str(fixture_root),
                rights_decision_reference=str(valid_decision()["decision_reference"]),
            )
            receipts = [reviewed_receipt_for_job(job) for job in queue["jobs"]]

            report = build_extraction_completion_report(
                base_path=str(fixture_root),
                decision_record=valid_decision(),
                receipts=receipts,
            )

            self.assertEqual(report["status"], "complete_by_reviewed_receipts")
            self.assertEqual(report["job_summary"]["completed_by_reviewed_receipt_count"], 2)
            self.assertEqual(report["receipt_summary"]["eligible_for_private_tutor_index_count"], 2)

    def test_completion_api_routes_and_blocked_deferral(self) -> None:
        status, validation = route_request(
            "/api/unibot/course/extraction-deferral/validate",
            {"deferral_record": valid_deferral()},
        )
        self.assertEqual(status, 200)
        self.assertEqual(validation["status"], "ok_extraction_deferral_record")

        invalid = valid_deferral()
        invalid["raw_text_public_release_allowed"] = True
        status, validation = route_request(
            "/api/unibot/course/extraction-deferral/validate",
            {"deferral_record": invalid},
        )
        self.assertEqual(status, 200)
        self.assertEqual(validation["status"], "blocked")
        self.assertIn("raw_text_public_release_must_remain_false", validation["issues"])

        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_completion_fixture(fixture_root)
            status, report = route_request(
                "/api/unibot/course/extraction-completion-report",
                {
                    "base_path": str(fixture_root),
                    "decision_record": valid_decision(),
                    "deferral_record": valid_deferral(),
                },
            )
        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "complete_intentionally_deferred")

        status, response = route_request(
            "/api/unibot/course/extraction-completion-report",
            {"receipts": "not-a-list"},
        )
        self.assertEqual(status, 400)
        self.assertEqual(response["status"], "invalid-receipts")


if __name__ == "__main__":
    unittest.main()
