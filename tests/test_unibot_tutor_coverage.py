from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction import build_course_extraction_queue  # noqa: E402
from unibot.materials import sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402
from unibot.tutor_coverage import build_course_tutor_coverage_plan  # noqa: E402


def write_coverage_fixture(root: Path) -> None:
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
        "decision_reference": "synthetic tutor coverage decision",
    }


def receipt_for_job(job: dict[str, object]) -> dict[str, object]:
    return {
        "job_id": job["job_id"],
        "material_id": job["material_id"],
        "job_type": job["job_type"],
        "extraction_status": "extracted_private",
        "raw_text_sha256": "e" * 64,
        "extracted_text_char_count": 1500,
        "private_artifact_reference": "private tutor coverage artifact ref",
        "human_review_status": "reviewed_for_private_tutor",
        "decision_reference_hash": sha256_text(str(valid_decision()["decision_reference"])),
    }


class UniBotTutorCoverageTests(unittest.TestCase):
    def test_coverage_plan_blocks_without_rights_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_coverage_fixture(fixture_root)

            plan = build_course_tutor_coverage_plan(base_path=str(fixture_root))
            payload = json.dumps(plan, ensure_ascii=False)

            self.assertEqual(plan["artifact_type"], "course_tutor_coverage_plan")
            self.assertEqual(plan["status"], "blocked_until_valid_rights_privacy_decision")
            self.assertEqual(plan["exam_deployment_status"], "not_cleared")
            self.assertEqual(plan["public_safety_status"], "pass")
            self.assertEqual(plan["projected_scope_summary"]["candidate_material_count"], 0)
            self.assertNotIn(str(fixture_root), payload)
            self.assertNotIn("solution_key.pdf", payload)
            self.assertEqual(scan_text(payload, "tutor-coverage-blocked-test")["status"], "pass")

    def test_coverage_plan_forecasts_skill_uplift_from_reviewed_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_coverage_fixture(fixture_root)
            queue = build_course_extraction_queue(
                base_path=str(fixture_root),
                rights_decision_reference=str(valid_decision()["decision_reference"]),
            )
            pandas_job = next(job for job in queue["jobs"] if "pandas" in job.get("skill_tags", []))
            receipt = receipt_for_job(pandas_job)

            plan = build_course_tutor_coverage_plan(
                base_path=str(fixture_root),
                decision_record=valid_decision(),
                receipts=[receipt],
            )
            coverage = {item["skill_tag"]: item for item in plan["skill_coverage"]}
            payload = json.dumps(plan, ensure_ascii=False)

            self.assertEqual(plan["status"], "coverage_uplift_ready_after_private_manifest_update")
            self.assertEqual(plan["projected_scope_summary"]["candidate_material_count"], 1)
            self.assertGreaterEqual(plan["projected_scope_summary"]["ready_skill_uplift"], 1)
            self.assertEqual(coverage["pandas"]["projected_readiness"], "ready_for_private_tutor")
            self.assertGreaterEqual(coverage["pandas"]["coverage_delta"], 1)
            self.assertNotIn("private tutor coverage artifact ref", payload)
            self.assertEqual(scan_text(payload, "tutor-coverage-uplift-test")["status"], "pass")

    def test_tutor_coverage_api_route(self) -> None:
        status, plan = route_request("/api/unibot/course/tutor-coverage-plan", {})

        self.assertEqual(status, 200)
        self.assertEqual(plan["artifact_type"], "course_tutor_coverage_plan")
        self.assertEqual(plan["exam_deployment_status"], "not_cleared")
        self.assertEqual(plan["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
