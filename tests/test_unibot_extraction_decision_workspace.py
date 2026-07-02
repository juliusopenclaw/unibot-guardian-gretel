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


def write_workspace_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Week 1" / "pandas_boxplot_slides.pdf").write_bytes(b"%PDF-1.4\nfixture")
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
        "decision_reference": "synthetic local workspace decision",
    }


class UniBotExtractionDecisionWorkspaceTests(unittest.TestCase):
    def test_workspace_prepare_writes_template_and_returns_public_safe_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            workspace = Path(temp_dir) / "workspace"
            decision_journal = Path(temp_dir) / "decision_records.jsonl"
            receipt_journal = Path(temp_dir) / "receipts.jsonl"
            private_output = Path(temp_dir) / "private"
            root.mkdir()
            write_workspace_fixture(root)

            status, payload = route_request(
                "/api/unibot/course/extraction-decision/workspace/prepare",
                {
                    "base_path": str(root),
                    "workspace_dir": str(workspace),
                    "decision_record_journal_path": str(decision_journal),
                    "receipt_journal_path": str(receipt_journal),
                    "private_output_dir": str(private_output),
                    "job_types": ["ocr"],
                },
            )
            raw = json.dumps(payload, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(payload["artifact_type"], "course_local_extraction_decision_workspace")
            self.assertEqual(payload["status"], "workspace_waiting_for_local_decision_record")
            self.assertEqual(payload["exam_deployment_status"], "not_cleared")
            self.assertEqual(payload["public_safety_status"], "pass")
            self.assertEqual(payload["workspace_files"]["template"]["status"], "written")
            self.assertEqual(payload["workspace_files"]["manifest"]["status"], "written")
            self.assertEqual(payload["dry_run_receipt"]["status"], "waiting_for_valid_decision_or_receipts")
            self.assertFalse(payload["dry_run_receipt"]["real_ocr_started"])
            self.assertFalse(payload["raw_decision_record_stored_by_workspace"])
            self.assertFalse(payload["raw_decision_record_returned"])
            self.assertFalse(payload["raw_text_returned"])
            self.assertFalse(payload["local_paths_returned"])
            self.assertTrue((workspace / "local_extraction_decision.template.json").exists())
            self.assertTrue((workspace / "workspace_manifest.hash_only.json").exists())
            self.assertNotIn(str(root), raw)
            self.assertNotIn(str(workspace), raw)
            self.assertNotIn(str(decision_journal), raw)
            self.assertNotIn(str(receipt_journal), raw)
            self.assertNotIn("solution_key.pdf", raw)
            self.assertEqual(scan_text(raw, "workspace-prepare-test")["status"], "pass")

    def test_workspace_record_stores_hash_only_decision_and_sets_dry_run_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            workspace = Path(temp_dir) / "workspace"
            decision_journal = Path(temp_dir) / "decision_records.jsonl"
            receipt_journal = Path(temp_dir) / "receipts.jsonl"
            private_output = Path(temp_dir) / "private"
            root.mkdir()
            write_workspace_fixture(root)

            status, payload = route_request(
                "/api/unibot/course/extraction-decision/workspace/record",
                {
                    "base_path": str(root),
                    "decision_record": valid_decision(),
                    "workspace_dir": str(workspace),
                    "decision_record_journal_path": str(decision_journal),
                    "receipt_journal_path": str(receipt_journal),
                    "private_output_dir": str(private_output),
                    "job_types": ["ocr"],
                },
            )
            raw = json.dumps(payload, ensure_ascii=False)
            workspace_payload = payload["workspace"]

            self.assertEqual(status, 200)
            self.assertEqual(payload["artifact_type"], "course_local_extraction_decision_workspace_record_result")
            self.assertEqual(payload["status"], "workspace_decision_record_stored_hash_only")
            self.assertEqual(payload["public_safety_status"], "pass")
            self.assertEqual(payload["journal_append_status"], "stored")
            self.assertTrue(payload["journal_event"]["accepted_for_gate"])
            self.assertEqual(workspace_payload["status"], "workspace_ready_for_controlled_ocr_first_batch_1")
            self.assertEqual(payload["dry_run_receipt"]["status"], "ocr_first_batch_1_start_ready")
            self.assertTrue(payload["dry_run_receipt"]["decision_valid"])
            self.assertTrue(payload["dry_run_receipt"]["ocr_first_batch_1_start_ready"])
            self.assertTrue(payload["dry_run_receipt"]["receipt_journal_reachable"])
            self.assertTrue(payload["dry_run_receipt"]["post_run_reports_reachable"])
            self.assertFalse(payload["dry_run_receipt"]["real_ocr_started"])
            self.assertFalse(payload["raw_decision_record_stored_by_workspace"])
            self.assertFalse(payload["raw_decision_record_returned"])
            self.assertTrue(decision_journal.exists())
            self.assertNotIn("synthetic local workspace decision", raw)
            self.assertNotIn(str(root), raw)
            self.assertNotIn(str(workspace), raw)
            self.assertNotIn(str(decision_journal), raw)
            self.assertEqual(scan_text(raw, "workspace-record-test")["status"], "pass")

    def test_workspace_record_blocks_invalid_decision_without_journal_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            workspace = Path(temp_dir) / "workspace"
            decision_journal = Path(temp_dir) / "decision_records.jsonl"
            root.mkdir()
            write_workspace_fixture(root)

            status, payload = route_request(
                "/api/unibot/course/extraction-decision/workspace/record",
                {
                    "base_path": str(root),
                    "decision_record": {"decision_status": "approved_for_local_extraction"},
                    "workspace_dir": str(workspace),
                    "decision_record_journal_path": str(decision_journal),
                    "job_types": ["ocr"],
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "blocked_decision_record_not_stored")
            self.assertEqual(payload["journal_append_status"], "blocked")
            self.assertFalse(payload["dry_run_receipt"]["decision_valid"])
            self.assertFalse(payload["dry_run_receipt"]["real_ocr_started"])
            self.assertFalse(decision_journal.exists())
            self.assertEqual(payload["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
