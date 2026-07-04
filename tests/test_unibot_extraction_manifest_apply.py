from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction import build_course_extraction_queue  # noqa: E402
from unibot.extraction_manifest_apply import (  # noqa: E402
    build_private_manifest_apply_dry_run,
    build_private_manifest_apply_release_claim_alignment,
)
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

    def test_private_manifest_apply_release_claim_alignment_links_dry_run_and_confirmed_apply(self) -> None:
        alignment = build_private_manifest_apply_release_claim_alignment()

        self.assertEqual(
            alignment["schema_version"],
            "unibot-extraction-manifest-apply-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["dry_run_public_safety_status"], "pass")
        self.assertEqual(alignment["confirmed_public_safety_status"], "pass")
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertEqual(alignment["dry_run_status"], "manifest_apply_dry_run_ready")
        self.assertEqual(alignment["confirmed_status"], "private_manifest_applied")
        self.assertGreaterEqual(alignment["dry_run_records_to_apply_count"], 1)
        self.assertGreaterEqual(alignment["confirmed_applied_count"], 1)
        self.assertEqual(alignment["workspace_card_status"], "python_exam_local_cycle_operator_workspace_card_ready")
        self.assertEqual(alignment["workspace_card_selected_skill_tag"], "pandas")
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertTrue(alignment["workspace_card_manifest_gate_linked"])
        self.assertIn("extraction_manifest_apply", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertIn("extraction_manifest_update", alignment["required_readiness_check_ids"])
        self.assertIn("extraction_receipt_journal", alignment["required_readiness_check_ids"])
        self.assertIn("course_material_policy", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertTrue(alignment["contracts"]["dry_run_does_not_write"])
        self.assertTrue(alignment["contracts"]["confirmed_write_requires_operator_confirmation"])
        self.assertTrue(alignment["contracts"]["workspace_card_manifest_gate_linked"])
        self.assertTrue(alignment["contracts"]["public_outputs_hide_paths_and_raw_text"])
        self.assertTrue(alignment["contracts"]["tutor_indexing_never_started"])
        self.assertIn("raw extracted text returned", alignment["blocked_claims"])
        self.assertIn("local path returned", alignment["blocked_claims"])
        self.assertIn("tutor indexing started by apply", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])

    def test_private_manifest_apply_release_claim_alignment_blocks_unsafe_output_claims(self) -> None:
        dry_run = {
            "status": "manifest_apply_dry_run_ready",
            "public_safety_status": "pass",
            "operator_confirmed_manifest_apply": False,
            "manifest_written": True,
            "manifest_apply_journal_written": True,
            "apply_result": {
                "manifest_written": True,
                "journal_written": True,
                "private_manifest_path_returned": True,
                "journal_path_returned": True,
            },
            "raw_text_returned": True,
            "local_paths_returned": True,
            "private_manifest_path_returned": True,
            "tutor_indexing_started": True,
            "exam_deployment_status": "cleared",
            "candidate_summary": {"records_to_apply_count": 1},
            "delta_preview": {"delta_hash": "abc"},
            "local_cycle_operator_workspace_card": {
                "status": "python_exam_local_cycle_operator_workspace_card_ready",
                "selected_skill_tag": "pandas",
                "ready_for_operator_prefill": True,
                "help_ledger_preview_status": "help_ledger_preview_ready",
                "help_ledger_preview_hash": "x",
                "checkpoint_hash": "x",
                "task_hash": "x",
                "not_cleared_receipt": True,
                "raw_workspace_card_returned": False,
            },
            "exam_scope_preview": {"projected_scope_summary": {}},
            "tutor_coverage_preview": {"priority_skill_gaps": []},
            "execution_boundary": "unsafe apply",
        }
        confirmed = {
            **dry_run,
            "status": "private_manifest_applied",
            "operator_confirmed_manifest_apply": True,
        }

        alignment = build_private_manifest_apply_release_claim_alignment(dry_run, confirmed)

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("dry_run_does_not_write", alignment["failed_contract_ids"])
        self.assertIn("workspace_card_manifest_gate_linked", alignment["failed_contract_ids"])
        self.assertIn("public_outputs_hide_paths_and_raw_text", alignment["failed_contract_ids"])
        self.assertIn("tutor_indexing_never_started", alignment["failed_contract_ids"])
        self.assertIn("exam_deployment_not_cleared", alignment["failed_contract_ids"])


if __name__ == "__main__":
    unittest.main()
