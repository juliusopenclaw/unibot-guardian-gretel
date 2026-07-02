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

from unibot.extraction_completion import build_extraction_completion_report  # noqa: E402
from unibot.extraction_receipt_journal import read_extraction_receipt_journal  # noqa: E402
from unibot.external_decision_journal import append_external_decision_journal_record  # noqa: E402
from unibot.private_extraction_runner import run_private_extraction_batch  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def valid_extraction_decision() -> dict[str, object]:
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
        "decision_reference": "synthetic private extraction runner decision",
    }


def write_minimal_docx(path: Path, text: str) -> None:
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)


def write_minimal_pptx(path: Path, text: str) -> None:
    slide_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        f"<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", slide_xml)


def write_minimal_pdf(path: Path, text: str) -> None:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("utf-8")
    compressed = zlib.compress(stream)
    path.write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        + f"5 0 obj << /Length {len(compressed)} /Filter /FlateDecode >> stream\n".encode("ascii")
        + compressed
        + b"\nendstream endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n"
    )


def write_private_runner_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    write_minimal_docx(root / "Week 1" / "Course setup.docx", "Jupyter setup and Python environment practice")
    write_minimal_pdf(root / "Week 1" / "Lecture text.pdf", "PDF text extraction for numpy and pandas")
    write_minimal_pptx(root / "Week 1" / "Intro slides.pptx", "Python lists loops pandas notebook workflow")


class UniBotPrivateExtractionRunnerTests(unittest.TestCase):
    def test_runner_blocks_without_valid_decision_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            root.mkdir()
            write_private_runner_fixture(root)

            report = run_private_extraction_batch(
                base_path=str(root),
                private_output_dir=Path(temp_dir) / "private",
            )

            self.assertEqual(report["artifact_type"], "course_private_extraction_run")
            self.assertEqual(report["status"], "blocked_until_valid_rights_privacy_decision")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_runner_extracts_supported_text_containers_and_stores_hash_only_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            output_dir = Path(temp_dir) / "private"
            journal_path = Path(temp_dir) / "receipts.jsonl"
            root.mkdir()
            write_private_runner_fixture(root)

            report = run_private_extraction_batch(
                base_path=str(root),
                decision_record=valid_extraction_decision(),
                receipt_journal_path=journal_path,
                private_output_dir=output_dir,
                max_jobs=4,
            )
            payload = json.dumps(report, ensure_ascii=False)
            journal = read_extraction_receipt_journal(journal_path)

            self.assertEqual(report["status"], "private_extraction_receipts_ready_for_human_review")
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertEqual(report["counts"]["selected_job_count"], 3)
            self.assertEqual(report["counts"]["extracted_private_count"], 3)
            self.assertEqual(report["counts"]["stored_receipt_count"], 3)
            self.assertTrue(report["private_artifact_map_written"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertEqual(journal["count"], 3)
            self.assertEqual(len(journal["receipts_for_progress"]), 3)
            self.assertNotIn(str(root), payload)
            self.assertNotIn(str(output_dir), payload)
            self.assertNotIn("Jupyter setup and Python environment practice", payload)
            self.assertNotIn("PDF text extraction for numpy and pandas", payload)
            self.assertNotIn("Python lists loops pandas notebook workflow", payload)
            self.assertIn(".pdf", report["supported_suffixes"])
            self.assertEqual(scan_text(payload, "private-extraction-runner-test")["status"], "pass")

    def test_api_route_and_reviewed_receipts_can_feed_completion_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            output_dir = Path(temp_dir) / "private"
            journal_path = Path(temp_dir) / "receipts.jsonl"
            root.mkdir()
            write_private_runner_fixture(root)

            status, report = route_request(
                "/api/unibot/course/private-extraction/run-batch",
                {
                    "base_path": str(root),
                    "decision_record": valid_extraction_decision(),
                    "receipt_journal_path": str(journal_path),
                    "private_output_dir": str(output_dir),
                    "human_review_status": "reviewed_for_private_tutor",
                    "max_jobs": 4,
                },
            )
            receipts = read_extraction_receipt_journal(journal_path)["receipts_for_progress"]
            completion = build_extraction_completion_report(
                base_path=str(root),
                decision_record=valid_extraction_decision(),
                receipts=receipts,
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "private_extraction_receipts_ready_for_human_review")
            self.assertEqual(report["counts"]["stored_receipt_count"], 3)
            self.assertEqual(completion["status"], "complete_by_reviewed_receipts")
            self.assertEqual(completion["job_summary"]["completed_by_reviewed_receipt_count"], 3)

    def test_runner_uses_hash_only_decision_record_journal_bridge_for_ocr_first(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            output_dir = Path(temp_dir) / "private"
            receipt_journal_path = Path(temp_dir) / "receipts.jsonl"
            decision_journal_path = Path(temp_dir) / "decision_records.jsonl"
            root.mkdir()
            write_private_runner_fixture(root)

            stored_decision = append_external_decision_journal_record(
                record_type="local_extraction_decision",
                record=valid_extraction_decision(),
                path=decision_journal_path,
            )
            status, report = route_request(
                "/api/unibot/course/private-extraction/run-batch",
                {
                    "base_path": str(root),
                    "decision_record_journal_path": str(decision_journal_path),
                    "receipt_journal_path": str(receipt_journal_path),
                    "private_output_dir": str(output_dir),
                    "max_jobs": 12,
                    "job_types": ["ocr"],
                },
            )
            payload = json.dumps(report, ensure_ascii=False)
            journal = read_extraction_receipt_journal(receipt_journal_path)

            self.assertEqual(stored_decision["status"], "stored")
            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "private_extraction_receipts_ready_for_human_review")
            self.assertEqual(report["decision_record_source"], "external_decision_record_journal")
            self.assertTrue(report["decision_record_journal_used"])
            self.assertFalse(report["raw_decision_record_returned"])
            self.assertEqual(report["counts"]["selected_job_count"], 3)
            self.assertEqual(report["counts"]["stored_receipt_count"], 3)
            self.assertEqual(journal["count"], 3)
            self.assertEqual(len(journal["receipts_for_progress"]), 3)
            self.assertNotIn("synthetic private extraction runner decision", payload)
            self.assertNotIn(str(root), payload)
            self.assertNotIn(str(output_dir), payload)
            self.assertNotIn(str(decision_journal_path), payload)
            self.assertEqual(scan_text(payload, "private-extraction-journal-bridge-test")["status"], "pass")

    def test_runner_blocks_when_journal_decision_does_not_allow_requested_job_type(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            decision_journal_path = Path(temp_dir) / "decision_records.jsonl"
            receipt_journal_path = Path(temp_dir) / "receipts.jsonl"
            root.mkdir()
            write_private_runner_fixture(root)
            transcription_only = dict(valid_extraction_decision())
            transcription_only["allowed_job_types"] = ["transcription"]

            stored_decision = append_external_decision_journal_record(
                record_type="local_extraction_decision",
                record=transcription_only,
                path=decision_journal_path,
            )
            status, report = route_request(
                "/api/unibot/course/private-extraction/run-batch",
                {
                    "base_path": str(root),
                    "decision_record_journal_path": str(decision_journal_path),
                    "receipt_journal_path": str(receipt_journal_path),
                    "max_jobs": 12,
                    "job_types": ["ocr"],
                },
            )

            self.assertEqual(stored_decision["status"], "stored")
            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "blocked_until_valid_rights_privacy_decision")
            self.assertIn("requested_job_type_not_allowed_by_decision", report["decision_validation"]["issues"])
            self.assertFalse(receipt_journal_path.exists())


if __name__ == "__main__":
    unittest.main()
