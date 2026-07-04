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

from unibot.extraction_human_review import (  # noqa: E402
    build_extraction_human_review_apply_plan,
    build_extraction_human_review_release_claim_alignment,
    validate_extraction_human_review_decision,
)
from unibot.extraction_receipt_journal import read_extraction_receipt_journal  # noqa: E402
from unibot.materials import sha256_text  # noqa: E402
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
        "decision_reference": "synthetic human review decision",
    }


def valid_pending_receipt() -> dict[str, object]:
    return {
        "job_id": "review-job-1",
        "material_id": "review-material-1",
        "job_type": "ocr",
        "extraction_status": "extracted_private",
        "raw_text_sha256": "e" * 64,
        "extracted_text_char_count": 760,
        "private_artifact_reference": "local private artifact handle",
        "human_review_status": "pending_review",
        "decision_reference_hash": sha256_text(str(valid_decision()["decision_reference"])),
    }


def valid_review_decision(job_id: str) -> dict[str, object]:
    return {
        "job_id": job_id,
        "review_decision": "accepted_for_private_tutor",
        "reviewer_roles": ["approved_reviewer"],
        "review_reference": "synthetic local review checklist reference",
        "review_notes": "synthetic note hashed by the harness",
        "raw_text_reviewed_locally": True,
        "source_card_ids": ["dfg-gwp"],
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


class UniBotExtractionHumanReviewTests(unittest.TestCase):
    def test_review_decision_blocks_raw_text_and_local_path_fields(self) -> None:
        receipt = valid_pending_receipt()
        decision = {
            **valid_review_decision(str(receipt["job_id"])),
            "raw_text": "must not be persisted",
            "local_path": "/private/course/file.pdf",
        }

        validation = validate_extraction_human_review_decision(
            decision,
            receipt=receipt,
            decision_reference_hash=str(receipt["decision_reference_hash"]),
        )
        payload = json.dumps(validation, ensure_ascii=False)

        self.assertEqual(validation["status"], "blocked")
        self.assertIn("review_decision_must_not_include_raw_text_or_local_path_fields", validation["issues"])
        self.assertFalse(validation["raw_text_stored"])
        self.assertFalse(validation["local_path_stored"])
        self.assertNotIn("must not be persisted", payload)

    def test_apply_plan_waits_for_review_ready_receipts(self) -> None:
        plan = build_extraction_human_review_apply_plan(decision_record=valid_decision())

        self.assertEqual(plan["artifact_type"], "course_extraction_human_review_apply_plan")
        self.assertEqual(plan["status"], "waiting_for_review_ready_receipts")
        self.assertEqual(plan["exam_deployment_status"], "not_cleared")
        self.assertFalse(plan["manifest_written"])
        self.assertFalse(plan["tutor_indexing_started"])
        self.assertEqual(plan["public_safety_status"], "pass")

    def test_apply_plan_records_review_and_prepares_manifest_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            journal_path = Path(temp_dir) / "receipts.jsonl"
            review_journal_path = Path(temp_dir) / "reviews.jsonl"
            receipt = valid_pending_receipt()
            route_request(
                "/api/unibot/course/extraction-receipts/append",
                {
                    "decision_record": valid_decision(),
                    "receipt": receipt,
                    "receipt_journal_path": str(journal_path),
                },
            )

            status, plan = route_request(
                "/api/unibot/course/extraction-review/apply-plan",
                {
                    "decision_record": valid_decision(),
                    "receipt_journal_path": str(journal_path),
                    "review_journal_path": str(review_journal_path),
                    "review_decisions": [valid_review_decision(str(receipt["job_id"]))],
                },
            )
            payload = json.dumps(plan, ensure_ascii=False)
            journal = read_extraction_receipt_journal(journal_path)

            self.assertEqual(status, 200)
            self.assertEqual(plan["status"], "review_decisions_recorded_manifest_apply_plan_ready")
            self.assertEqual(plan["review_decision_summary"]["appended_review_receipt_count"], 1)
            self.assertEqual(plan["review_decision_summary"]["appended_review_record_count"], 1)
            self.assertEqual(plan["post_review_reports"]["progress"]["status"], "receipts_reviewed_for_private_tutor")
            self.assertEqual(plan["post_review_reports"]["manifest_update"]["status"], "ready_for_private_manifest_update")
            self.assertEqual(plan["post_review_reports"]["manifest_update"]["candidate_count"], 1)
            self.assertEqual(plan["manifest_apply_plan"]["candidate_summary"]["ready_to_apply_private_count"], 1)
            self.assertEqual(journal["count"], 2)
            self.assertEqual(len(journal["receipts_for_progress"]), 2)
            self.assertFalse(plan["raw_review_reference_returned"])
            self.assertFalse(plan["raw_review_notes_returned"])
            self.assertFalse(plan["raw_text_returned"])
            self.assertFalse(plan["local_paths_returned"])
            self.assertFalse(plan["manifest_written"])
            self.assertFalse(plan["tutor_indexing_started"])
            self.assertTrue(review_journal_path.exists())
            self.assertNotIn("synthetic local review checklist reference", payload)
            self.assertNotIn("synthetic note hashed by the harness", payload)
            self.assertNotIn("local private artifact handle", payload)
            self.assertEqual(scan_text(payload, "human-review-apply-test")["status"], "pass")

    def test_human_review_release_claim_alignment_links_review_completion_and_boundaries(self) -> None:
        alignment = build_extraction_human_review_release_claim_alignment()

        self.assertEqual(
            alignment["schema_version"],
            "unibot-extraction-human-review-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["plan_public_safety_status"], "pass")
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertEqual(alignment["plan_status"], "review_decisions_recorded_manifest_apply_plan_ready")
        self.assertGreaterEqual(alignment["stored_review_decision_count"], 1)
        self.assertEqual(alignment["invalid_review_decision_count"], 0)
        self.assertGreaterEqual(alignment["appended_review_receipt_count"], 1)
        self.assertGreaterEqual(alignment["appended_review_record_count"], 1)
        self.assertGreaterEqual(alignment["post_reviewed_for_private_tutor_count"], alignment["appended_review_receipt_count"])
        self.assertGreaterEqual(alignment["ready_to_apply_private_count"], alignment["appended_review_receipt_count"])
        self.assertIn("extraction_human_review", alignment["required_readiness_check_ids"])
        self.assertIn("extraction_completion", alignment["required_readiness_check_ids"])
        self.assertIn("extraction_manifest_update", alignment["required_readiness_check_ids"])
        self.assertIn("extraction_manifest_apply", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertTrue(alignment["contracts"]["review_decisions_recorded_hash_only"])
        self.assertTrue(alignment["contracts"]["local_private_artifact_review_required"])
        self.assertTrue(alignment["contracts"]["private_manifest_plan_only"])
        self.assertTrue(alignment["contracts"]["completion_evidence_linked"])
        self.assertIn("raw review notes storage", alignment["blocked_claims"])
        self.assertIn("manifest write by human review alone", alignment["blocked_claims"])
        self.assertIn("tutor indexing by human review alone", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])

    def test_human_review_release_claim_alignment_blocks_manifest_or_exam_claims(self) -> None:
        plan = build_extraction_human_review_apply_plan(
            decision_record=valid_decision(),
            receipts=[valid_pending_receipt()],
            review_decisions=[valid_review_decision(str(valid_pending_receipt()["job_id"]))],
        )
        plan["exam_deployment_status"] = "cleared"
        plan["execution_boundary"] = "Human review writes manifests and starts tutor indexing."
        plan["manifest_written"] = True
        plan["tutor_indexing_started"] = True
        plan["raw_text_returned"] = True
        plan["review_decision_summary"]["invalid_review_decision_count"] = 1

        alignment = build_extraction_human_review_release_claim_alignment(plan)

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("review_decisions_recorded_hash_only", alignment["failed_contract_ids"])
        self.assertIn("private_manifest_plan_only", alignment["failed_contract_ids"])
        self.assertIn("exam_deployment_not_cleared", alignment["failed_contract_ids"])

    def test_ocr_first_operator_receipts_flow_into_human_review_apply_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            workspace = Path(temp_dir) / "workspace"
            decision_journal = Path(temp_dir) / "decision_records.jsonl"
            receipt_journal = Path(temp_dir) / "receipts.jsonl"
            review_journal = Path(temp_dir) / "reviews.jsonl"
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
            route_request(
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
            ready = read_extraction_receipt_journal(receipt_journal)["receipts_for_progress"]
            decisions = [valid_review_decision(str(receipt["job_id"])) for receipt in ready]

            status, plan = route_request(
                "/api/unibot/course/extraction-review/apply-plan",
                {
                    "base_path": str(root),
                    "decision_record_journal_path": str(decision_journal),
                    "receipt_journal_path": str(receipt_journal),
                    "review_journal_path": str(review_journal),
                    "review_decisions": decisions,
                },
            )
            payload = json.dumps(plan, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(plan["status"], "review_decisions_recorded_manifest_apply_plan_ready")
            self.assertEqual(plan["review_queue_summary"]["pre_review_ready_count"], 3)
            self.assertEqual(plan["review_queue_summary"]["post_review_ready_count"], 0)
            self.assertEqual(plan["review_queue_summary"]["post_reviewed_for_private_tutor_count"], 3)
            self.assertEqual(plan["post_review_reports"]["manifest_update"]["candidate_count"], 3)
            self.assertIn(
                plan["post_review_reports"]["tutor_coverage"]["status"],
                {
                    "coverage_uplift_ready_after_private_manifest_update",
                    "candidate_metadata_ready_no_new_skill_uplift",
                },
            )
            self.assertFalse(plan["raw_text_returned"])
            self.assertFalse(plan["local_paths_returned"])
            self.assertNotIn(str(root), payload)
            self.assertNotIn(str(private_output), payload)
            self.assertNotIn("Python notebook setup", payload)
            self.assertEqual(scan_text(payload, "human-review-operator-flow-test")["status"], "pass")


if __name__ == "__main__":
    unittest.main()
