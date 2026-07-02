from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.materials import (  # noqa: E402
    build_demo_material_manifest,
    build_material_manifest,
    build_material_public_boundary_alignment,
    build_public_material_summary,
    normalize_material_record,
    sha256_text,
    validate_material_record,
)
from unibot.server import route_request  # noqa: E402


class UniBotMaterialsTests(unittest.TestCase):
    def test_demo_manifest_separates_public_demo_from_private_staging(self) -> None:
        manifest = build_demo_material_manifest()

        self.assertEqual(manifest["schema_version"], "unibot-course-material-manifest-v1")
        self.assertEqual(manifest["status"], "ok")
        self.assertEqual(manifest["record_count"], 2)
        self.assertEqual(manifest["public_release_allowed_count"], 1)
        self.assertEqual(manifest["tutor_usable_count"], 1)

        records = {record["material_id"]: record for record in manifest["records"]}
        self.assertTrue(records["python-lists-demo"]["public_release_allowed"])
        self.assertFalse(records["course-slides-staged"]["public_release_allowed"])
        self.assertFalse(records["course-slides-staged"]["tutor_usable"])
        self.assertEqual(manifest["material_public_boundary_alignment"]["status"], "ready")
        self.assertEqual(manifest["material_public_boundary_alignment"]["public_safety_status"], "pass")
        self.assertEqual(manifest["material_public_boundary_alignment"]["missing_material_ids"], [])
        self.assertEqual(manifest["material_public_boundary_alignment"]["failed_contract_ids"], [])

    def test_material_public_boundary_alignment_maps_public_and_private_boundaries(self) -> None:
        manifest = build_demo_material_manifest()
        summary = build_public_material_summary(manifest["records"])
        alignment = build_material_public_boundary_alignment(manifest, summary)

        self.assertEqual(
            alignment["schema_version"],
            "unibot-course-material-public-boundary-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["missing_material_ids"], [])
        self.assertEqual(alignment["missing_summary_material_ids"], [])
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertTrue(all(alignment["contracts"].values()))
        self.assertIn("adaptive_task_plan", alignment["required_readiness_check_ids"])
        self.assertIn("course_material_policy", alignment["required_readiness_check_ids"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])

        sections = {section["section_id"]: section for section in alignment["sections"]}
        self.assertIn("python-lists-demo", sections["synthetic_public_demo"]["material_ids"])
        self.assertIn("course-slides-staged", sections["private_course_placeholder"]["material_ids"])
        self.assertEqual(alignment["release_boundary"], "public_metadata_and_authorized_synthetic_excerpt_only")

    def test_material_validation_blocks_unknown_permission_and_unsafe_excerpt(self) -> None:
        record = normalize_material_record(
            {
                "material_id": "unsafe-public",
                "title": "Unsafe public excerpt",
                "source_kind": "slide_pdf",
                "permission_status": "unknown",
                "publish_policy": "public_excerpt_allowed",
                "extraction_status": "text_extracted",
                "review_status": "reviewed_public_safe",
                "sha256": sha256_text("demo"),
                "public_excerpt": f"Contact: {'student'}@example.invalid",
            }
        )
        validation = validate_material_record(record)

        self.assertEqual(validation["status"], "blocked")
        self.assertIn("public_excerpt_not_public_safe", validation["issues"])
        self.assertIn("unknown_permission_cannot_be_reviewed_for_use", validation["issues"])
        self.assertIn("public_policy_requires_public_or_authorized_permission", validation["issues"])

    def test_public_summary_removes_public_excerpt_when_validation_blocks_record(self) -> None:
        record = {
            "material_id": "unsafe-demo",
            "title": "Unsafe demo",
            "source_kind": "synthetic_demo",
            "permission_status": "synthetic",
            "publish_policy": "synthetic_public",
            "extraction_status": "text_extracted",
            "review_status": "reviewed_public_safe",
            "skill_tags": ["debugging"],
            "source_card_ids": ["vanlehn-2011"],
            "sha256": sha256_text("unsafe"),
            "public_excerpt": f"Contact: {'student'}@example.invalid",
        }
        summary = build_public_material_summary([record])
        payload = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary["public_release_allowed_count"], 0)
        self.assertNotIn("public_excerpt", summary["records"][0])
        self.assertNotIn("student" + "@example.invalid", payload)

    def test_public_summary_redacts_local_paths_and_private_text(self) -> None:
        record = {
            "material_id": "local-course-file",
            "title": "Local course file",
            "source_kind": "exercise_sheet",
            "permission_status": "private_course_use_only",
            "publish_policy": "private_only",
            "extraction_status": "text_extracted",
            "review_status": "reviewed_for_private_tutor",
            "skill_tags": ["python_lists"],
            "sha256": sha256_text("private local exercise"),
            "local_path": "/" + "Users/student/private/course.pdf",
            "public_excerpt": "",
        }
        summary = build_public_material_summary([record])
        payload = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary["status"], "public_summary_only")
        self.assertEqual(summary["public_release_allowed_count"], 0)
        self.assertNotIn("/" + "Users/student", payload)
        self.assertNotIn("private local exercise", payload)
        self.assertIn("local-course-file", payload)

    def test_material_manifest_and_api_routes(self) -> None:
        record = {
            "material_id": "caption-demo",
            "title": "Caption demo",
            "source_kind": "video_caption",
            "permission_status": "owned_or_authorized",
            "publish_policy": "public_excerpt_allowed",
            "extraction_status": "captions_available",
            "review_status": "reviewed_public_safe",
            "skill_tags": ["debugging"],
            "source_card_ids": ["dfg-gwp"],
            "sha256": sha256_text("caption demo"),
            "public_excerpt": "Explain the next debugging question before changing code.",
        }
        manifest = build_material_manifest([record])

        self.assertEqual(manifest["status"], "ok")
        self.assertEqual(manifest["public_release_allowed_count"], 1)

        status, response = route_request("/api/unibot/materials/manifest", {"records": [record]})
        self.assertEqual(status, 200)
        self.assertEqual(response["record_count"], 1)
        self.assertEqual(response["public_release_allowed_count"], 1)

        status, response = route_request("/api/unibot/materials/public-summary", {"records": [record]})
        self.assertEqual(status, 200)
        self.assertEqual(response["records"][0]["public_excerpt"], record["public_excerpt"])

        status, response = route_request("/api/unibot/materials/validate", {"record": record})
        self.assertEqual(status, 200)
        self.assertEqual(response["validation"]["status"], "ok")

    def test_material_api_rejects_invalid_payloads(self) -> None:
        status, response = route_request("/api/unibot/materials/manifest", {"records": "not-list"})
        self.assertEqual(status, 400)
        self.assertEqual(response["status"], "invalid-records")

        status, response = route_request("/api/unibot/materials/validate", {"record": "not-record"})
        self.assertEqual(status, 400)
        self.assertEqual(response["status"], "invalid-record")


if __name__ == "__main__":
    unittest.main()
