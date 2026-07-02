from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction import build_course_extraction_queue  # noqa: E402
from unibot.extraction_manifest_apply import build_private_manifest_apply_dry_run  # noqa: E402
from unibot.extraction_receipt_journal import append_extraction_receipt_record  # noqa: E402
from unibot.materials import sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_apply_fixture(root: Path) -> None:
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
        "decision_reference": "synthetic private manifest apply decision",
    }


def reviewed_receipt_for_job(job: dict[str, object]) -> dict[str, object]:
    return {
        "job_id": job["job_id"],
        "material_id": job["material_id"],
        "job_type": job["job_type"],
        "extraction_status": "extracted_private",
        "raw_text_sha256": "f" * 64,
        "extracted_text_char_count": 1500,
        "private_artifact_reference": "private manifest apply artifact ref",
        "human_review_status": "reviewed_for_private_tutor",
        "decision_reference_hash": sha256_text(str(valid_decision()["decision_reference"])),
    }


class UniBotExtractionManifestApplyTests(unittest.TestCase):
    def test_private_manifest_apply_blocks_without_rights_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_apply_fixture(fixture_root)

            report = build_private_manifest_apply_dry_run(base_path=str(fixture_root))
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["artifact_type"], "course_private_manifest_apply_dry_run")
            self.assertEqual(report["status"], "blocked_until_valid_rights_privacy_decision")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertFalse(report["manifest_written"])
            self.assertFalse(report["tutor_indexing_started"])
            self.assertFalse(report["local_paths_returned"])
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertNotIn(str(fixture_root), payload)
            self.assertNotIn("solution_key.pdf", payload)

    def test_private_manifest_apply_dry_run_previews_delta_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            journal_path = Path(temp_dir) / "apply_journal.jsonl"
            write_apply_fixture(fixture_root)
            queue = build_course_extraction_queue(
                base_path=str(fixture_root),
                rights_decision_reference=str(valid_decision()["decision_reference"]),
            )
            pandas_job = next(job for job in queue["jobs"] if "pandas" in job.get("skill_tags", []))
            receipt = reviewed_receipt_for_job(pandas_job)

            report = build_private_manifest_apply_dry_run(
                base_path=str(fixture_root),
                decision_record=valid_decision(),
                receipts=[receipt],
                private_manifest_path=manifest_path,
                manifest_apply_journal_path=journal_path,
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["status"], "manifest_apply_dry_run_ready")
            self.assertEqual(report["candidate_summary"]["records_to_apply_count"], 1)
            self.assertEqual(report["delta_preview"]["records_to_apply"][0]["review_status"], "reviewed_for_private_tutor")
            self.assertGreaterEqual(report["exam_scope_preview"]["projected_scope_summary"]["ready_skill_uplift"], 1)
            self.assertFalse(report["manifest_written"])
            self.assertFalse(report["manifest_apply_journal_written"])
            self.assertFalse(report["tutor_indexing_started"])
            self.assertFalse(manifest_path.exists())
            self.assertFalse(journal_path.exists())
            self.assertNotIn("private manifest apply artifact ref", payload)
            self.assertNotIn(str(fixture_root), payload)
            self.assertNotIn(str(manifest_path), payload)
            self.assertEqual(scan_text(payload, "manifest-apply-dry-run-test")["status"], "pass")

    def test_private_manifest_apply_confirmation_writes_private_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir) / "materials"
            receipt_journal = Path(temp_dir) / "receipts.jsonl"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            apply_journal = Path(temp_dir) / "apply_journal.jsonl"
            write_apply_fixture(fixture_root)
            queue = build_course_extraction_queue(
                base_path=str(fixture_root),
                rights_decision_reference=str(valid_decision()["decision_reference"]),
            )
            receipt = reviewed_receipt_for_job(queue["jobs"][0])
            append_extraction_receipt_record(
                receipt,
                decision_record=valid_decision(),
                path=receipt_journal,
            )

            status, report = route_request(
                "/api/unibot/course/extraction-manifest/apply-dry-run",
                {
                    "base_path": str(fixture_root),
                    "decision_record": valid_decision(),
                    "receipt_journal_path": str(receipt_journal),
                    "private_manifest_path": str(manifest_path),
                    "manifest_apply_journal_path": str(apply_journal),
                    "operator_confirmed_manifest_apply": True,
                },
            )
            payload = json.dumps(report, ensure_ascii=False)
            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_text = json.dumps(manifest_payload, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "private_manifest_applied")
            self.assertEqual(report["apply_result"]["applied_count"], 1)
            self.assertTrue(report["manifest_written"])
            self.assertTrue(report["manifest_apply_journal_written"])
            self.assertFalse(report["private_manifest_path_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["tutor_indexing_started"])
            self.assertTrue(manifest_path.exists())
            self.assertTrue(apply_journal.exists())
            self.assertEqual(manifest_payload["artifact_type"], "course_private_material_manifest")
            self.assertGreaterEqual(manifest_payload["tutor_usable_count"], 1)
            self.assertNotIn("private manifest apply artifact ref", payload)
            self.assertNotIn("private manifest apply artifact ref", manifest_text)
            self.assertNotIn(str(fixture_root), payload)
            self.assertNotIn(str(fixture_root), manifest_text)
            self.assertEqual(scan_text(payload, "manifest-apply-confirmed-test")["status"], "pass")
            self.assertEqual(scan_text(manifest_text, "private-manifest-written-test")["status"], "pass")


if __name__ == "__main__":
    unittest.main()
