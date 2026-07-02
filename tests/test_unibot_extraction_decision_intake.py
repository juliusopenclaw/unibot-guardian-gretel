from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction import build_course_extraction_queue  # noqa: E402
from unibot.extraction_receipt_journal import append_extraction_receipt_record  # noqa: E402
from unibot.materials import sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_intake_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Videos").mkdir(parents=True)
    (root / "Week 1" / "pandas_boxplot_slides.pdf").write_bytes(b"%PDF-1.4\nfixture")
    (root / "Videos" / "debugging_walkthrough.mov").write_bytes(b"video")
    (root / "Week 1" / "solution_key.pdf").write_bytes(b"%PDF-1.4\nsolution")


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
        "decision_reference": "synthetic local intake decision",
    }


def reviewed_receipt_for_job(job: dict[str, object]) -> dict[str, object]:
    return {
        "job_id": job["job_id"],
        "material_id": job["material_id"],
        "job_type": job["job_type"],
        "extraction_status": "extracted_private",
        "raw_text_sha256": "a" * 64,
        "extracted_text_char_count": 1800,
        "private_artifact_reference": "local-private-artifact:intake-test",
        "human_review_status": "reviewed_for_private_tutor",
        "decision_reference_hash": sha256_text(str(valid_decision()["decision_reference"])),
    }


class UniBotExtractionDecisionIntakeTests(unittest.TestCase):
    def test_intake_packet_waits_without_decision_and_exposes_no_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            decision_journal = Path(temp_dir) / "decision_records.jsonl"
            receipt_journal = Path(temp_dir) / "receipts.jsonl"
            root.mkdir()
            write_intake_fixture(root)

            status, packet = route_request(
                "/api/unibot/course/extraction-decision/local-intake",
                {
                    "base_path": str(root),
                    "decision_record_journal_path": str(decision_journal),
                    "receipt_journal_path": str(receipt_journal),
                    "job_types": ["ocr"],
                },
            )
            payload = json.dumps(packet, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(packet["artifact_type"], "course_local_extraction_decision_intake_packet")
            self.assertEqual(packet["status"], "waiting_for_local_rights_privacy_decision_record")
            self.assertEqual(packet["exam_deployment_status"], "not_cleared")
            self.assertEqual(packet["public_safety_status"], "pass")
            self.assertEqual(packet["decision_journal_summary"]["status"], "empty")
            self.assertEqual(packet["ocr_first_readiness"]["job_count"], 1)
            self.assertFalse(packet["raw_decision_record_returned"])
            self.assertFalse(packet["raw_text_returned"])
            self.assertFalse(packet["local_paths_returned"])
            self.assertNotIn(str(root), payload)
            self.assertNotIn(str(decision_journal), payload)
            self.assertNotIn(str(receipt_journal), payload)
            self.assertNotIn("solution_key.pdf", payload)
            self.assertEqual(scan_text(payload, "local-intake-waiting-test")["status"], "pass")

    def test_record_endpoint_stores_hash_only_decision_and_enables_ocr_first(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            decision_journal = Path(temp_dir) / "decision_records.jsonl"
            receipt_journal = Path(temp_dir) / "receipts.jsonl"
            root.mkdir()
            write_intake_fixture(root)

            status, result = route_request(
                "/api/unibot/course/extraction-decision/local-intake/record",
                {
                    "base_path": str(root),
                    "decision_record": valid_decision(),
                    "decision_record_journal_path": str(decision_journal),
                    "receipt_journal_path": str(receipt_journal),
                    "job_types": ["ocr"],
                },
            )
            payload = json.dumps(result, ensure_ascii=False)
            intake = result["intake_packet"]

            self.assertEqual(status, 200)
            self.assertEqual(result["artifact_type"], "course_local_extraction_decision_record_result")
            self.assertEqual(result["status"], "decision_record_stored_hash_only")
            self.assertTrue(result["journal_event"]["accepted_for_gate"])
            self.assertFalse(result["raw_decision_record_returned"])
            self.assertEqual(intake["status"], "decision_record_journal_ready_for_ocr_first")
            self.assertEqual(intake["decision_validation"]["decision_record_source"], "external_decision_record_journal")
            self.assertEqual(intake["ocr_first_readiness"]["status"], "ready_for_local_private_execution")
            self.assertEqual(intake["ocr_first_readiness"]["job_count"], 1)
            self.assertNotIn("synthetic local intake decision", payload)
            self.assertNotIn(str(root), payload)
            self.assertNotIn(str(decision_journal), payload)
            self.assertEqual(scan_text(payload, "local-intake-record-test")["status"], "pass")

    def test_reports_use_decision_journal_and_receipt_journal_without_raw_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            decision_journal = Path(temp_dir) / "decision_records.jsonl"
            receipt_journal = Path(temp_dir) / "receipts.jsonl"
            root.mkdir()
            write_intake_fixture(root)

            route_request(
                "/api/unibot/course/extraction-decision/local-intake/record",
                {
                    "base_path": str(root),
                    "decision_record": valid_decision(),
                    "decision_record_journal_path": str(decision_journal),
                    "receipt_journal_path": str(receipt_journal),
                    "job_types": ["ocr"],
                },
            )
            queue = build_course_extraction_queue(
                base_path=str(root),
                rights_decision_reference=str(valid_decision()["decision_reference"]),
            )
            pandas_job = next(job for job in queue["jobs"] if "pandas" in job.get("skill_tags", []))
            stored_receipt = append_extraction_receipt_record(
                reviewed_receipt_for_job(pandas_job),
                decision_reference_hash=sha256_text(str(valid_decision()["decision_reference"])),
                path=receipt_journal,
            )

            progress_status, progress = route_request(
                "/api/unibot/course/extraction-progress-report",
                {
                    "base_path": str(root),
                    "decision_record_journal_path": str(decision_journal),
                    "receipt_journal_path": str(receipt_journal),
                },
            )
            manifest_status, manifest = route_request(
                "/api/unibot/course/extraction-manifest-update-plan",
                {
                    "base_path": str(root),
                    "decision_record_journal_path": str(decision_journal),
                    "receipt_journal_path": str(receipt_journal),
                },
            )
            coverage_status, coverage = route_request(
                "/api/unibot/course/tutor-coverage-plan",
                {
                    "base_path": str(root),
                    "decision_record_journal_path": str(decision_journal),
                    "receipt_journal_path": str(receipt_journal),
                },
            )
            intake_status, intake = route_request(
                "/api/unibot/course/extraction-decision/local-intake",
                {
                    "base_path": str(root),
                    "decision_record_journal_path": str(decision_journal),
                    "receipt_journal_path": str(receipt_journal),
                    "job_types": ["ocr"],
                },
            )
            payload = json.dumps(
                {
                    "progress": progress,
                    "manifest": manifest,
                    "coverage": coverage,
                    "intake": intake,
                },
                ensure_ascii=False,
            )

            self.assertEqual(stored_receipt["status"], "stored")
            self.assertEqual(progress_status, 200)
            self.assertEqual(progress["status"], "receipts_reviewed_for_private_tutor")
            self.assertEqual(progress["decision_validation"]["decision_record_source"], "external_decision_record_journal")
            self.assertEqual(manifest_status, 200)
            self.assertEqual(manifest["status"], "ready_for_private_manifest_update")
            self.assertEqual(manifest["candidate_summary"]["ready_to_apply_private_count"], 1)
            self.assertEqual(coverage_status, 200)
            self.assertIn(coverage["status"], {"coverage_uplift_ready_after_private_manifest_update", "candidate_metadata_ready_no_new_skill_uplift"})
            self.assertEqual(intake_status, 200)
            self.assertEqual(intake["status"], "decision_record_and_receipt_journal_ready_for_review_reports")
            self.assertEqual(intake["post_run_report_summary"]["manifest_candidate_count"], 1)
            self.assertNotIn("synthetic local intake decision", payload)
            self.assertNotIn("local-private-artifact:intake-test", payload)
            self.assertNotIn(str(root), payload)
            self.assertEqual(scan_text(payload, "journal-report-chain-test")["status"], "pass")


if __name__ == "__main__":
    unittest.main()
