from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction import build_course_extraction_queue  # noqa: E402
from unibot.extraction_progress import (  # noqa: E402
    build_extraction_progress_release_claim_alignment,
    build_extraction_progress_report,
    progress_queue_hash,
    progress_review_hash,
    synthetic_extraction_progress_workspace_card,
)
from unibot.materials import sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_progress_fixture(root: Path) -> None:
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
        "decision_reference": "synthetic extraction progress decision",
    }


def receipt_for_job(job: dict[str, object], *, human_review_status: str = "pending_review") -> dict[str, object]:
    return {
        "job_id": job["job_id"],
        "material_id": job["material_id"],
        "job_type": job["job_type"],
        "extraction_status": "extracted_private",
        "raw_text_sha256": "c" * 64,
        "extracted_text_char_count": 777,
        "private_artifact_reference": "private progress artifact ref",
        "human_review_status": human_review_status,
        "decision_reference_hash": sha256_text(str(valid_decision()["decision_reference"])),
    }


class UniBotExtractionProgressTests(unittest.TestCase):
    def test_progress_report_blocks_without_valid_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_progress_fixture(fixture_root)

            report = build_extraction_progress_report(base_path=str(fixture_root))
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["artifact_type"], "course_extraction_progress_report")
            self.assertEqual(report["status"], "blocked_until_valid_rights_privacy_decision")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["queue_summary"]["job_count"], 3)
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertNotIn(str(fixture_root), payload)
            self.assertEqual(scan_text(payload, "extraction-progress-test")["status"], "pass")

    def test_progress_report_builds_human_review_queue_from_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_progress_fixture(fixture_root)
            queue = build_course_extraction_queue(
                base_path=str(fixture_root),
                rights_decision_reference=str(valid_decision()["decision_reference"]),
            )
            receipt = receipt_for_job(queue["jobs"][0])

            report = build_extraction_progress_report(
                base_path=str(fixture_root),
                decision_record=valid_decision(),
                receipts=[receipt],
                python_exam_local_cycle_operator_workspace_card=synthetic_extraction_progress_workspace_card(),
            )
            payload = json.dumps(report, ensure_ascii=False)
            workspace_card = report["local_cycle_operator_workspace_card"]

            self.assertEqual(report["status"], "receipts_ready_for_human_review")
            self.assertEqual(report["receipt_summary"]["valid_receipt_count"], 1)
            self.assertEqual(report["receipt_summary"]["ready_for_human_review_count"], 1)
            self.assertEqual(len(report["review_queue"]), 1)
            self.assertEqual(report["review_queue"][0]["job_id"], receipt["job_id"])
            self.assertEqual(workspace_card["status"], "python_exam_local_cycle_operator_workspace_card_ready")
            self.assertTrue(workspace_card["ready_for_operator_prefill"])
            self.assertEqual(workspace_card["checkpoint_hash"], progress_queue_hash(report))
            self.assertEqual(workspace_card["task_hash"], progress_review_hash(report))
            self.assertFalse(workspace_card["raw_workspace_card_returned"])
            self.assertNotIn("private progress artifact ref", payload)

    def test_progress_report_builds_manifest_candidates_after_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_progress_fixture(fixture_root)
            queue = build_course_extraction_queue(
                base_path=str(fixture_root),
                rights_decision_reference=str(valid_decision()["decision_reference"]),
            )
            receipt = receipt_for_job(queue["jobs"][0], human_review_status="reviewed_for_private_tutor")

            report = build_extraction_progress_report(
                base_path=str(fixture_root),
                decision_record=valid_decision(),
                receipts=[receipt],
            )

            self.assertEqual(report["status"], "receipts_reviewed_for_private_tutor")
            self.assertEqual(report["receipt_summary"]["eligible_for_private_tutor_index_count"], 1)
            self.assertEqual(len(report["manifest_update_candidates"]), 1)
            self.assertEqual(report["manifest_update_candidates"][0]["review_status_after_review"], "reviewed_for_private_tutor")

    def test_progress_release_claim_alignment_links_metadata_review_and_manifest_boundaries(self) -> None:
        alignment = build_extraction_progress_release_claim_alignment()

        self.assertEqual(
            alignment["schema_version"],
            "unibot-extraction-progress-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["report_public_safety_status"], "pass")
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertGreaterEqual(alignment["receipt_summary"]["valid_receipt_count"], 2)
        self.assertGreaterEqual(alignment["review_queue_count"], 1)
        self.assertGreaterEqual(alignment["manifest_update_candidate_count"], 1)
        self.assertIn("extraction_progress", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertIn("extraction_receipt_journal", alignment["required_readiness_check_ids"])
        self.assertIn("course_material_policy", alignment["required_readiness_check_ids"])
        self.assertIn("external_decision_state", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertTrue(alignment["contracts"]["review_queue_hash_only"])
        self.assertTrue(alignment["contracts"]["manifest_candidates_private_metadata_only"])
        self.assertTrue(alignment["contracts"]["workspace_card_progress_queue_gate_linked"])
        self.assertEqual(alignment["workspace_card_status"], "python_exam_local_cycle_operator_workspace_card_ready")
        self.assertEqual(alignment["workspace_card_selected_skill_tag"], "pandas")
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertTrue(alignment["workspace_card_progress_queue_gate_linked"])
        self.assertIn("raw extracted text in progress report", alignment["blocked_claims"])
        self.assertIn("tutor retrieval without manifest update", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])

    def test_progress_release_claim_alignment_rejects_unlinked_workspace_card_hashes(self) -> None:
        card = synthetic_extraction_progress_workspace_card()
        card["workspace_card_summary"]["checkpoint_hash"] = "x"
        card["workspace_card_summary"]["task_hash"] = "x"
        decision = valid_decision()
        report = build_extraction_progress_report(
            decision_record=decision,
            receipts=[
                receipt_for_job(
                    {"job_id": "job-1", "material_id": "material-1", "job_type": "ocr"},
                    human_review_status="pending_review",
                ),
                receipt_for_job(
                    {"job_id": "job-2", "material_id": "material-2", "job_type": "ocr"},
                    human_review_status="reviewed_for_private_tutor",
                ),
            ],
            python_exam_local_cycle_operator_workspace_card=card,
        )

        alignment = build_extraction_progress_release_claim_alignment(report)

        self.assertEqual(alignment["status"], "needs_review")
        self.assertFalse(alignment["workspace_card_progress_queue_gate_linked"])
        self.assertIn("workspace_card_progress_queue_gate_linked", alignment["failed_contract_ids"])

    def test_progress_release_claim_alignment_blocks_exam_deployment_claims(self) -> None:
        report = build_extraction_progress_report(
            decision_record=valid_decision(),
            receipts=[receipt_for_job({"job_id": "job-1", "material_id": "material-1", "job_type": "ocr"})],
        )
        report["exam_deployment_status"] = "cleared"
        report["policy"] = "Progress report authorizes direct tutor retrieval."

        alignment = build_extraction_progress_release_claim_alignment(report)

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("exam_deployment_not_cleared", alignment["failed_contract_ids"])
        self.assertIn("policy_blocks_raw_paths_and_direct_tutor_retrieval", alignment["failed_contract_ids"])

    def test_progress_report_blocks_invalid_receipts(self) -> None:
        receipt = {
            "job_id": "bad-job",
            "material_id": "bad-material",
            "job_type": "ocr",
            "extraction_status": "extracted_private",
            "raw_text": "raw OCR must not appear",
            "raw_text_sha256": "not-a-hash",
            "extracted_text_char_count": 0,
            "private_artifact_reference": "private progress artifact ref",
            "human_review_status": "pending_review",
            "decision_reference_hash": "bad",
        }

        report = build_extraction_progress_report(decision_record=valid_decision(), receipts=[receipt])

        self.assertEqual(report["status"], "blocked_invalid_receipts")
        self.assertEqual(report["receipt_summary"]["invalid_receipt_count"], 1)
        self.assertEqual(report["blocked_receipt_summaries"][0]["job_id"], "bad-job")
        self.assertEqual(report["public_safety_status"], "pass")

    def test_progress_api_route(self) -> None:
        status, report = route_request("/api/unibot/course/extraction-progress-report", {})

        self.assertEqual(status, 200)
        self.assertEqual(report["artifact_type"], "course_extraction_progress_report")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")


if __name__ == "__main__":
    unittest.main()
