from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction_receipt_journal import read_extraction_receipt_journal  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


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
        "decision_reference": "synthetic ocr first operator decision",
    }


def write_operator_fixture(root: Path) -> None:
    root.mkdir(parents=True)
    docx_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>Python notebook setup and pandas source checks</w:t></w:r></w:p></w:body></w:document>"
    )
    pptx_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        "<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>Loops lists numpy dataframe practice</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>"
    )
    pdf_stream = zlib.compress(b"BT /F1 12 Tf 72 720 Td (PDF text extraction for course practice) Tj ET")
    with zipfile.ZipFile(root / "setup.docx", "w") as archive:
        archive.writestr("word/document.xml", docx_xml)
    with zipfile.ZipFile(root / "slides.pptx", "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", pptx_xml)
    (root / "lecture.pdf").write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        + f"5 0 obj << /Length {len(pdf_stream)} /Filter /FlateDecode >> stream\n".encode("ascii")
        + pdf_stream
        + b"\nendstream endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n"
    )


class UniBotOcrFirstOperatorTests(unittest.TestCase):
    def test_operator_blocks_until_workspace_dry_run_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            workspace = Path(temp_dir) / "workspace"
            decision_journal = Path(temp_dir) / "decision_records.jsonl"
            receipt_journal = Path(temp_dir) / "receipts.jsonl"
            private_output = Path(temp_dir) / "private"
            write_operator_fixture(root)

            status, report = route_request(
                "/api/unibot/course/ocr-first/operator-run",
                {
                    "base_path": str(root),
                    "workspace_dir": str(workspace),
                    "decision_record_journal_path": str(decision_journal),
                    "receipt_journal_path": str(receipt_journal),
                    "private_output_dir": str(private_output),
                    "operator_confirmed_dry_run": True,
                },
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(report["artifact_type"], "course_ocr_first_batch_1_operator_run")
            self.assertEqual(report["status"], "blocked_until_workspace_dry_run_ready")
            self.assertFalse(report["private_ocr_started"])
            self.assertFalse(report["real_ocr_started"])
            self.assertFalse(receipt_journal.exists())
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertNotIn(str(root), payload)
            self.assertNotIn(str(private_output), payload)
            self.assertEqual(scan_text(payload, "ocr-operator-blocked-test")["status"], "pass")

    def test_operator_waits_for_confirmation_after_valid_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            workspace = Path(temp_dir) / "workspace"
            decision_journal = Path(temp_dir) / "decision_records.jsonl"
            receipt_journal = Path(temp_dir) / "receipts.jsonl"
            private_output = Path(temp_dir) / "private"
            write_operator_fixture(root)
            route_request(
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

            status, report = route_request(
                "/api/unibot/course/ocr-first/operator-run",
                {
                    "base_path": str(root),
                    "workspace_dir": str(workspace),
                    "decision_record_journal_path": str(decision_journal),
                    "receipt_journal_path": str(receipt_journal),
                    "private_output_dir": str(private_output),
                    "operator_confirmed_dry_run": False,
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "waiting_for_operator_confirmation_after_dry_run")
            self.assertTrue(report["workspace_dry_run_receipt"]["ocr_first_batch_1_start_ready"])
            self.assertFalse(report["private_ocr_started"])
            self.assertFalse(report["real_ocr_started"])
            self.assertFalse(receipt_journal.exists())
            self.assertEqual(report["public_safety_status"], "pass")

    def test_operator_runs_batch_1_and_builds_post_run_reports_after_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            workspace = Path(temp_dir) / "workspace"
            decision_journal = Path(temp_dir) / "decision_records.jsonl"
            receipt_journal = Path(temp_dir) / "receipts.jsonl"
            private_output = Path(temp_dir) / "private"
            write_operator_fixture(root)
            route_request(
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

            status, report = route_request(
                "/api/unibot/course/ocr-first/operator-run",
                {
                    "base_path": str(root),
                    "workspace_dir": str(workspace),
                    "decision_record_journal_path": str(decision_journal),
                    "receipt_journal_path": str(receipt_journal),
                    "private_output_dir": str(private_output),
                    "operator_confirmed_dry_run": True,
                },
            )
            payload = json.dumps(report, ensure_ascii=False)
            journal = read_extraction_receipt_journal(receipt_journal)

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "ocr_first_batch_1_receipts_ready_for_human_review")
            self.assertTrue(report["private_ocr_started"])
            self.assertTrue(report["real_ocr_started"])
            self.assertEqual(report["selected_batch"]["job_count"], 3)
            self.assertEqual(report["selected_batch"]["job_id_count"], 3)
            self.assertEqual(report["private_run_summary"]["selected_job_count"], 3)
            self.assertEqual(report["private_run_summary"]["stored_receipt_count"], 3)
            self.assertEqual(report["private_run_summary"]["job_id_filter_count"], 3)
            self.assertEqual(report["post_run_reports"]["progress"]["status"], "receipts_ready_for_human_review")
            self.assertEqual(report["post_run_reports"]["progress"]["ready_for_human_review_count"], 3)
            self.assertEqual(report["post_run_reports"]["manifest_update"]["status"], "waiting_for_reviewed_receipts")
            self.assertEqual(report["post_run_reports"]["tutor_coverage"]["status"], "waiting_for_reviewed_manifest_candidates")
            self.assertEqual(journal["count"], 3)
            self.assertFalse(report["raw_decision_record_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertNotIn("synthetic ocr first operator decision", payload)
            self.assertNotIn("Python notebook setup", payload)
            self.assertNotIn(str(root), payload)
            self.assertNotIn(str(private_output), payload)
            self.assertEqual(scan_text(payload, "ocr-operator-run-test")["status"], "pass")


if __name__ == "__main__":
    unittest.main()
