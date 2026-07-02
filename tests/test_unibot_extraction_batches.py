from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction_batches import build_extraction_batch_plan, build_extraction_batch_receipt_packet  # noqa: E402
from unibot.materials import sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_batch_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Videos").mkdir(parents=True)
    (root / "Week 1" / "pandas_intro.md").write_text("pandas DataFrame boxplot", encoding="utf-8")
    (root / "Week 1" / "lecture.pdf").write_bytes(b"%PDF-1.4\nfixture")
    (root / "Week 1" / "slides.pptx").write_bytes(b"pptx fixture")
    (root / "Videos" / "lecture.mov").write_bytes(b"video")
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
        "decision_reference": "synthetic signed extraction batch decision",
    }


def receipt_for_job(job: dict[str, object]) -> dict[str, object]:
    return {
        "job_id": job["job_id"],
        "material_id": job["material_id"],
        "job_type": job["job_type"],
        "extraction_status": "extracted_private",
        "raw_text_sha256": "c" * 64,
        "extracted_text_char_count": 900,
        "private_artifact_reference": "private batch workspace artifact",
        "human_review_status": "pending_review",
        "decision_reference_hash": sha256_text(str(valid_decision()["decision_reference"])),
    }


class UniBotExtractionBatchTests(unittest.TestCase):
    def test_batch_plan_is_metadata_only_and_blocked_without_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_batch_fixture(fixture_root)

            plan = build_extraction_batch_plan(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                batch_size=2,
            )
            payload = json.dumps(plan, ensure_ascii=False)

            self.assertEqual(plan["artifact_type"], "course_extraction_batch_plan")
            self.assertEqual(plan["status"], "blocked_until_valid_rights_privacy_decision")
            self.assertEqual(plan["exam_deployment_status"], "not_cleared")
            self.assertEqual(plan["public_safety_status"], "pass")
            self.assertEqual(plan["coverage"]["job_count"], 3)
            self.assertEqual(plan["coverage"]["batch_count"], 2)
            self.assertEqual(plan["coverage"]["ocr_job_count"], 2)
            self.assertEqual(plan["coverage"]["transcription_job_count"], 1)
            self.assertTrue(all(batch["status"] == "blocked_until_valid_rights_privacy_decision" for batch in plan["batches"]))
            self.assertNotIn(str(fixture_root), payload)
            self.assertNotIn("solution_key.pdf", payload)
            self.assertEqual(scan_text(payload, "batch-plan-blocked-test")["status"], "pass")

    def test_batch_plan_ready_with_decision_and_tracks_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_batch_fixture(fixture_root)

            ready = build_extraction_batch_plan(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                decision_record=valid_decision(),
                batch_size=2,
            )
            self.assertEqual(ready["status"], "ready_for_local_private_execution")
            self.assertEqual(ready["receipt_backlog"]["expected_receipt_count"], 3)
            self.assertEqual(ready["receipt_backlog"]["missing_receipt_count"], 3)
            self.assertTrue(ready["decision_validation"]["rights_decision_reference_hash"])
            self.assertNotIn("synthetic signed extraction batch decision", json.dumps(ready, ensure_ascii=False))

            first_job = ready["batches"][0]["jobs"][0]
            partial = build_extraction_batch_plan(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                decision_record=valid_decision(),
                receipts=[receipt_for_job(first_job)],
                batch_size=2,
            )

            self.assertEqual(partial["status"], "partially_receipted")
            self.assertEqual(partial["receipt_backlog"]["valid_receipt_count"], 1)
            self.assertEqual(partial["receipt_backlog"]["ready_for_human_review_count"], 1)
            self.assertEqual(partial["receipt_backlog"]["missing_receipt_count"], 2)
            self.assertEqual(partial["batches"][0]["status"], "ready_for_human_review")

    def test_batch_plan_can_filter_ocr_jobs_for_first_supported_slice(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_batch_fixture(fixture_root)

            plan = build_extraction_batch_plan(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                batch_size=5,
                job_types=["ocr"],
            )

            self.assertEqual(plan["coverage"]["job_type_filter"], ["ocr"])
            self.assertEqual(plan["coverage"]["unfiltered_job_count"], 3)
            self.assertEqual(plan["coverage"]["job_count"], 2)
            self.assertEqual(plan["coverage"]["ocr_job_count"], 2)
            self.assertEqual(plan["coverage"]["transcription_job_count"], 0)
            self.assertEqual(plan["receipt_backlog"]["expected_receipt_count"], 2)
            self.assertTrue(all(job["job_type"] == "ocr" for batch in plan["batches"] for job in batch["jobs"]))

    def test_batch_receipt_packet_is_blocked_without_decision_and_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_batch_fixture(fixture_root)

            packet = build_extraction_batch_receipt_packet(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                batch_size=2,
                batch_index=1,
            )
            payload = json.dumps(packet, ensure_ascii=False)

            self.assertEqual(packet["artifact_type"], "course_extraction_batch_receipt_packet")
            self.assertEqual(packet["status"], "blocked_until_valid_rights_privacy_decision")
            self.assertEqual(packet["exam_deployment_status"], "not_cleared")
            self.assertEqual(packet["public_safety_status"], "pass")
            self.assertEqual(packet["selected_batch"]["job_count"], 2)
            self.assertEqual(len(packet["receipt_templates"]), 2)
            self.assertTrue(all(template["decision_reference_hash"] == "" for template in packet["receipt_templates"]))
            self.assertNotIn(str(fixture_root), payload)
            self.assertNotIn("solution_key.pdf", payload)
            self.assertNotIn("pandas DataFrame boxplot", payload)
            self.assertEqual(scan_text(payload, "batch-receipt-packet-blocked-test")["status"], "pass")

    def test_batch_receipt_packet_tracks_ready_review_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_batch_fixture(fixture_root)

            packet = build_extraction_batch_receipt_packet(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                decision_record=valid_decision(),
                batch_size=2,
                batch_index=1,
            )
            self.assertEqual(packet["status"], "ready_for_local_private_execution")
            self.assertEqual(packet["selected_batch"]["job_count"], 2)
            self.assertEqual(len(packet["receipt_templates"]), 2)
            self.assertTrue(all(template["decision_reference_hash"] for template in packet["receipt_templates"]))

            receipt = receipt_for_job(packet["receipt_templates"][0])
            partial = build_extraction_batch_receipt_packet(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                decision_record=valid_decision(),
                receipts=[receipt],
                batch_size=2,
                batch_index=1,
            )

            self.assertEqual(partial["status"], "ready_for_human_review")
            self.assertEqual(partial["receipt_validation_summary"]["valid_receipt_count"], 1)
            self.assertEqual(partial["receipt_validation_summary"]["ready_for_human_review_count"], 1)
            self.assertIn("receipt_contract", partial)
            self.assertEqual(scan_text(json.dumps(partial, ensure_ascii=False), "batch-receipt-ready-test")["status"], "pass")

    def test_batch_receipt_packet_can_filter_ocr_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_batch_fixture(fixture_root)

            packet = build_extraction_batch_receipt_packet(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                batch_size=5,
                batch_index=1,
                job_types=["ocr"],
            )

            self.assertEqual(packet["selected_batch"]["job_type_counts"], {"ocr": 2})
            self.assertEqual(len(packet["receipt_templates"]), 2)
            self.assertTrue(all(template["job_type"] == "ocr" for template in packet["receipt_templates"]))

    def test_batch_plan_api_route(self) -> None:
        status, plan = route_request("/api/unibot/course/extraction-batch-plan", {"batch_size": 5})

        self.assertEqual(status, 200)
        self.assertEqual(plan["artifact_type"], "course_extraction_batch_plan")
        self.assertEqual(plan["exam_deployment_status"], "not_cleared")
        self.assertEqual(plan["public_safety_status"], "pass")

    def test_batch_plan_api_route_accepts_job_type_filter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_batch_fixture(fixture_root)

            status, plan = route_request(
                "/api/unibot/course/extraction-batch-plan",
                {
                    "base_path": str(fixture_root),
                    "review_policy": "local_private_tutor",
                    "batch_size": 5,
                    "job_types": ["ocr"],
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(plan["coverage"]["job_type_filter"], ["ocr"])
            self.assertEqual(plan["coverage"]["ocr_job_count"], 2)
            self.assertEqual(plan["coverage"]["transcription_job_count"], 0)

    def test_batch_receipt_packet_api_route(self) -> None:
        status, packet = route_request("/api/unibot/course/extraction-batch-receipt-packet", {"batch_size": 5})

        self.assertEqual(status, 200)
        self.assertEqual(packet["artifact_type"], "course_extraction_batch_receipt_packet")
        self.assertEqual(packet["exam_deployment_status"], "not_cleared")
        self.assertEqual(packet["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
