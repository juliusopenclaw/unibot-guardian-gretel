from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction_operator import (  # noqa: E402
    build_extraction_operator_packet,
    validate_extraction_receipt,
)
from unibot.materials import sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_operator_fixture(root: Path) -> None:
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
        "decision_reference": "synthetic signed extraction operator decision",
    }


def valid_receipt() -> dict[str, object]:
    decision_hash = sha256_text(str(valid_decision()["decision_reference"]))
    return {
        "job_id": "abc123",
        "material_id": "mat123",
        "job_type": "ocr",
        "extraction_status": "extracted_private",
        "raw_text_sha256": "a" * 64,
        "extracted_text_char_count": 1200,
        "private_artifact_reference": "private extraction workspace ref",
        "human_review_status": "pending_review",
        "decision_reference_hash": decision_hash,
    }


class UniBotExtractionOperatorTests(unittest.TestCase):
    def test_operator_packet_blocks_without_valid_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_operator_fixture(fixture_root)

            packet = build_extraction_operator_packet(base_path=str(fixture_root))
            payload = json.dumps(packet, ensure_ascii=False)

            self.assertEqual(packet["artifact_type"], "course_extraction_operator_packet")
            self.assertEqual(packet["status"], "blocked_until_valid_rights_privacy_decision")
            self.assertEqual(packet["exam_deployment_status"], "not_cleared")
            self.assertEqual(packet["public_safety_status"], "pass")
            self.assertEqual(packet["queue_summary"]["job_count"], 3)
            self.assertIn("receipt_contract", packet)
            self.assertNotIn(str(fixture_root), payload)
            self.assertEqual(scan_text(payload, "operator-packet-test")["status"], "pass")

    def test_operator_packet_ready_with_valid_decision_but_does_not_expose_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_operator_fixture(fixture_root)

            packet = build_extraction_operator_packet(
                base_path=str(fixture_root),
                decision_record=valid_decision(),
                job_limit=2,
            )
            payload = json.dumps(packet, ensure_ascii=False)

            self.assertEqual(packet["status"], "private_operator_ready")
            self.assertEqual(packet["job_batch_count"], 2)
            self.assertTrue(packet["job_batch_truncated"])
            self.assertEqual(packet["decision_validation"]["status"], "ok_authorizes_local_extraction")
            self.assertTrue(packet["decision_validation"]["rights_decision_reference_hash"])
            self.assertNotIn("synthetic signed extraction operator decision", payload)
            self.assertNotIn(str(fixture_root), payload)

    def test_receipt_validation_hashes_private_reference_and_requires_decision(self) -> None:
        validation = validate_extraction_receipt(valid_receipt(), decision_record=valid_decision())
        payload = json.dumps(validation, ensure_ascii=False)

        self.assertEqual(validation["status"], "ok_private_extraction_receipt")
        self.assertEqual(validation["public_safety_status"], "pass")
        self.assertTrue(validation["private_artifact_reference_hash"])
        self.assertTrue(validation["ready_for_human_review_queue"])
        self.assertFalse(validation["eligible_for_private_tutor_index"])
        self.assertFalse(validation["raw_text_stored_in_receipt"])
        self.assertNotIn("private extraction workspace ref", payload)

    def test_receipt_validation_blocks_raw_text_and_bad_decision(self) -> None:
        receipt = valid_receipt()
        receipt["raw_text"] = "copied raw OCR text must never be in the receipt"
        receipt["job_type"] = "cloud"
        receipt["decision_reference_hash"] = "bad"

        validation = validate_extraction_receipt(receipt, decision_record={})

        self.assertEqual(validation["status"], "blocked")
        self.assertIn("valid_extraction_decision_record_required", validation["issues"])
        self.assertIn("receipt_must_not_include_raw_text_fields", validation["issues"])
        self.assertIn("unsupported_job_type", validation["issues"])
        self.assertIn("decision_reference_hash_unverifiable", validation["issues"])
        self.assertTrue(validation["raw_text_stored_in_receipt"])

    def test_operator_api_routes(self) -> None:
        status, packet = route_request("/api/unibot/course/extraction-operator-packet", {})
        self.assertEqual(status, 200)
        self.assertEqual(packet["artifact_type"], "course_extraction_operator_packet")
        self.assertEqual(packet["exam_deployment_status"], "not_cleared")

        status, validation = route_request(
            "/api/unibot/course/extraction-receipt/validate",
            {"receipt": valid_receipt(), "decision_record": valid_decision()},
        )
        self.assertEqual(status, 200)
        self.assertEqual(validation["status"], "ok_private_extraction_receipt")


if __name__ == "__main__":
    unittest.main()
