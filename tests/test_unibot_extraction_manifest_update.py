from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction import build_course_extraction_queue  # noqa: E402
from unibot.extraction_manifest_update import (  # noqa: E402
    build_extraction_manifest_update_plan,
    build_extraction_manifest_update_release_claim_alignment,
)
from unibot.materials import sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_manifest_update_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Videos").mkdir(parents=True)
    (root / "Week 1" / "lecture.pdf").write_bytes(b"%PDF-1.4\nfixture")
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
        "decision_reference": "synthetic manifest update decision",
    }


def receipt_for_job(job: dict[str, object], *, human_review_status: str = "reviewed_for_private_tutor") -> dict[str, object]:
    return {
        "job_id": job["job_id"],
        "material_id": job["material_id"],
        "job_type": job["job_type"],
        "extraction_status": "extracted_private",
        "raw_text_sha256": "d" * 64,
        "extracted_text_char_count": 1200,
        "private_artifact_reference": "private manifest update artifact ref",
        "human_review_status": human_review_status,
        "decision_reference_hash": sha256_text(str(valid_decision()["decision_reference"])),
    }


class UniBotExtractionManifestUpdateTests(unittest.TestCase):
    def test_manifest_update_plan_blocks_without_rights_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_manifest_update_fixture(fixture_root)

            plan = build_extraction_manifest_update_plan(base_path=str(fixture_root))
            payload = json.dumps(plan, ensure_ascii=False)

            self.assertEqual(plan["artifact_type"], "course_extraction_manifest_update_plan")
            self.assertEqual(plan["status"], "blocked_until_valid_rights_privacy_decision")
            self.assertEqual(plan["exam_deployment_status"], "not_cleared")
            self.assertEqual(plan["public_safety_status"], "pass")
            self.assertEqual(plan["candidate_summary"]["candidate_count"], 0)
            self.assertNotIn(str(fixture_root), payload)
            self.assertNotIn("solution_key.pdf", payload)
            self.assertEqual(scan_text(payload, "manifest-update-blocked-test")["status"], "pass")

    def test_manifest_update_plan_creates_private_metadata_candidates_after_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_manifest_update_fixture(fixture_root)
            queue = build_course_extraction_queue(
                base_path=str(fixture_root),
                rights_decision_reference=str(valid_decision()["decision_reference"]),
            )
            receipt = receipt_for_job(queue["jobs"][0])

            plan = build_extraction_manifest_update_plan(
                base_path=str(fixture_root),
                decision_record=valid_decision(),
                receipts=[receipt],
            )
            payload = json.dumps(plan, ensure_ascii=False)

            self.assertEqual(plan["status"], "ready_for_private_manifest_update")
            self.assertEqual(plan["candidate_summary"]["candidate_count"], 1)
            self.assertEqual(plan["candidate_summary"]["ready_to_apply_private_count"], 1)
            self.assertEqual(len(plan["manifest_update_candidates"]), 1)
            candidate = plan["manifest_update_candidates"][0]
            self.assertEqual(candidate["validation_status"], "ok")
            self.assertTrue(candidate["tutor_usable_after_apply"])
            self.assertFalse(candidate["public_release_allowed_after_apply"])
            self.assertFalse(candidate["raw_text_stored"])
            self.assertFalse(candidate["local_path_stored"])
            self.assertNotIn("private manifest update artifact ref", payload)
            self.assertEqual(scan_text(payload, "manifest-update-ready-test")["status"], "pass")

    def test_manifest_update_release_claim_alignment_links_private_metadata_boundaries(self) -> None:
        alignment = build_extraction_manifest_update_release_claim_alignment()

        self.assertEqual(
            alignment["schema_version"],
            "unibot-extraction-manifest-update-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["plan_public_safety_status"], "pass")
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertGreaterEqual(alignment["candidate_summary"]["candidate_count"], 1)
        self.assertGreaterEqual(alignment["candidate_summary"]["ready_to_apply_private_count"], 1)
        self.assertIn("extraction_manifest_update", alignment["required_readiness_check_ids"])
        self.assertIn("extraction_progress", alignment["required_readiness_check_ids"])
        self.assertIn("extraction_receipt_journal", alignment["required_readiness_check_ids"])
        self.assertIn("course_material_policy", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertTrue(alignment["contracts"]["execution_boundary_blocks_file_write_raw_and_paths"])
        self.assertTrue(alignment["contracts"]["candidates_private_metadata_only"])
        self.assertIn("manifest file write by planning", alignment["blocked_claims"])
        self.assertIn("public release by manifest update plan", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])

    def test_manifest_update_release_claim_alignment_blocks_public_release_or_apply_claims(self) -> None:
        plan = build_extraction_manifest_update_plan(
            decision_record=valid_decision(),
            receipts=[{"job_id": "job-1", "material_id": "material-1", "job_type": "ocr"}],
        )
        plan["status"] = "ready_for_private_manifest_update"
        plan["exam_deployment_status"] = "cleared"
        plan["execution_boundary"] = "This plan writes manifest files and clears deployment."
        plan["candidate_summary"] = {
            "candidate_count": 1,
            "blocked_candidate_count": 0,
            "source_job_metadata_missing_count": 0,
            "ready_to_apply_private_count": 1,
        }
        plan["manifest_update_candidates"] = [
            {
                "validation_status": "ok",
                "tutor_usable_after_apply": True,
                "public_release_allowed_after_apply": True,
                "raw_text_stored": True,
                "local_path_stored": True,
                "publish_policy_after_review": "public_excerpt_allowed",
                "permission_status_after_review": "owned_or_authorized",
                "sha256_after_review": "d" * 64,
            }
        ]

        alignment = build_extraction_manifest_update_release_claim_alignment(plan)

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("exam_deployment_not_cleared", alignment["failed_contract_ids"])
        self.assertIn("execution_boundary_blocks_file_write_raw_and_paths", alignment["failed_contract_ids"])
        self.assertIn("candidates_private_metadata_only", alignment["failed_contract_ids"])

    def test_manifest_update_plan_waits_for_human_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_manifest_update_fixture(fixture_root)
            queue = build_course_extraction_queue(
                base_path=str(fixture_root),
                rights_decision_reference=str(valid_decision()["decision_reference"]),
            )
            receipt = receipt_for_job(queue["jobs"][0], human_review_status="pending_review")

            plan = build_extraction_manifest_update_plan(
                base_path=str(fixture_root),
                decision_record=valid_decision(),
                receipts=[receipt],
            )

            self.assertEqual(plan["status"], "waiting_for_reviewed_receipts")
            self.assertEqual(plan["candidate_summary"]["candidate_count"], 0)

    def test_manifest_update_api_route(self) -> None:
        status, plan = route_request("/api/unibot/course/extraction-manifest-update-plan", {})

        self.assertEqual(status, 200)
        self.assertEqual(plan["artifact_type"], "course_extraction_manifest_update_plan")
        self.assertEqual(plan["exam_deployment_status"], "not_cleared")
        self.assertEqual(plan["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
