from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.course_per_skill_action_router import build_course_per_skill_action_router  # noqa: E402
from unibot.exam_workspace_session_console import build_exam_workspace_session_console  # noqa: E402
from unibot.materials import build_material_manifest, sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402
from unibot.tutor_index import build_private_tutor_index_dry_run  # noqa: E402


def write_ready_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Week 1" / "lists_intro.md").write_text(
        "Python lists dictionary tuple index slice loop function notebook",
        encoding="utf-8",
    )


def reviewed_manifest_record() -> dict[str, object]:
    return {
        "material_id": "week-01-python-lists-notebook",
        "title": "Week 01 Python lists notebook",
        "source_kind": "notebook",
        "permission_status": "private_course_use_only",
        "publish_policy": "private_only",
        "extraction_status": "text_extracted",
        "review_status": "reviewed_for_private_tutor",
        "skill_tags": ["python_lists", "control_flow", "debugging"],
        "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
        "page_or_timestamp": "week 01",
        "sha256": sha256_text("week 01 python lists notebook reviewed locally"),
    }


def write_private_manifest(path: Path, records: list[dict[str, object]]) -> None:
    manifest = build_material_manifest(records)
    manifest["artifact_type"] = "course_private_material_manifest"
    manifest["exam_deployment_status"] = "not_cleared"
    manifest["storage_policy"] = "hash-only private material metadata; no raw text or local paths"
    path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")


def valid_decision() -> dict[str, object]:
    return {
        "decision_status": "approved_for_local_extraction",
        "scope": "local_private_course_extraction",
        "allowed_job_types": ["ocr", "transcription"],
        "storage_policy": "local_private_only",
        "cloud_processing_allowed": False,
        "raw_text_public_release_allowed": False,
        "human_review_before_tutor_index": True,
        "retention_decision": "synthetic action router decision",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic per skill action router decision",
    }


class UniBotCoursePerSkillActionRouterTests(unittest.TestCase):
    def test_router_routes_ready_skill_without_history_to_session_console(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "private_tutor_index.json"
            write_ready_fixture(root)
            write_private_manifest(manifest_path, [reviewed_manifest_record()])
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                operator_confirmed_tutor_index_build=True,
            )

            router = build_course_per_skill_action_router(
                base_path=str(root),
                review_policy="local_private_tutor",
                decision_record=valid_decision(),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                selected_skill_tag="python_lists",
                focus_query="Python Listen",
                public_safe=True,
            )

            self.assertEqual(router["artifact_type"], "course_per_skill_action_router")
            self.assertEqual(router["status"], "course_per_skill_action_router_ready")
            self.assertEqual(router["exam_deployment_status"], "not_cleared")
            self.assertEqual(router["public_safety_status"], "pass")
            self.assertEqual(router["selected_route"]["route_id"], "start_session_console_dry_run")
            self.assertEqual(router["selected_route"]["endpoint"], "/api/unibot/exam-workspace/session-console")
            self.assertTrue(router["selected_route"]["dry_run_by_default"])
            self.assertEqual(router["selected_route"]["requested_help_level"], "A2")
            self.assertTrue(router["selected_route"]["safety_contract"]["a0_a2_only"])
            self.assertEqual(router["router_receipt"]["status"], "router_receipt_ready_not_exam_clearance")
            self.assertFalse(router["raw_query_returned"])
            self.assertFalse(router["raw_text_returned"])
            self.assertFalse(router["notebook_code_returned"])
            self.assertFalse(router["local_paths_returned"])

    def test_router_routes_history_with_open_confirmations_to_export_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "private_tutor_index.json"
            write_ready_fixture(root)
            write_private_manifest(manifest_path, [reviewed_manifest_record()])
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                operator_confirmed_tutor_index_build=True,
            )
            console = build_exam_workspace_session_console(
                base_path=str(root),
                review_policy="local_private_tutor",
                decision_record=valid_decision(),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                selected_skill_tag="python_lists",
                cell_source="own_checkpoint = []\n",
                repeat_run_index=1,
                study_receipt={
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
                public_safe=True,
            )

            status, router = route_request(
                "/api/unibot/course/per-skill-action-router",
                {
                    "base_path": str(root),
                    "review_policy": "local_private_tutor",
                    "decision_record": valid_decision(),
                    "private_manifest_path": str(manifest_path),
                    "tutor_index_path": str(index_path),
                    "focus_query": "Python Listen",
                    "selected_skill_tag": "python_lists",
                    "console_reports": [console],
                    "console_receipts": [console["session_console_receipt"]],
                    "build_current_console": False,
                },
            )
            payload = json.dumps(router, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(router["artifact_type"], "course_per_skill_action_router")
            self.assertEqual(router["status"], "course_per_skill_action_router_ready")
            self.assertEqual(router["selected_skill"]["skill_tag"], "python_lists")
            self.assertEqual(router["selected_route"]["route_id"], "review_open_operator_confirmations")
            self.assertEqual(router["selected_route"]["endpoint"], "/api/unibot/exam-workspace/run-history-export-review")
            self.assertGreaterEqual(router["selected_route"]["open_operator_confirmation_count"], 1)
            self.assertGreaterEqual(router["router_summary"]["open_operator_confirmation_route_count"], 1)
            self.assertTrue(router["selected_route"]["payload_template"]["console_reports_required"])
            self.assertTrue(router["router_receipt"]["not_cleared_receipt"])
            self.assertFalse(router["raw_query_returned"])
            self.assertFalse(router["raw_cell_returned"])
            self.assertFalse(router["raw_text_returned"])
            self.assertFalse(router["raw_notebook_returned"])
            self.assertFalse(router["notebook_code_returned"])
            self.assertFalse(router["local_paths_returned"])
            self.assertFalse(router["automatic_grading_started"])
            self.assertFalse(router["proctoring_started"])
            self.assertFalse(router["ai_detection_started"])
            self.assertFalse(router["exam_clearance_claimed"])
            self.assertNotIn("own_checkpoint", payload)
            self.assertNotIn("Week 01 Python", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "course-per-skill-action-router")["status"], "pass")


if __name__ == "__main__":
    unittest.main()
