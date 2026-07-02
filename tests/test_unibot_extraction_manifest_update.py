from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction import build_course_extraction_queue  # noqa: E402
from unibot.extraction_manifest_update import build_extraction_manifest_update_plan  # noqa: E402
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
