from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.course_exam_coverage_dashboard import (  # noqa: E402
    build_course_exam_coverage_dashboard,
    build_course_exam_coverage_dashboard_workspace_card_alignment,
    course_exam_coverage_dashboard_hash,
    course_exam_coverage_dashboard_receipt_hash,
    synthetic_course_exam_coverage_dashboard_workspace_card,
)
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
        "retention_decision": "synthetic dashboard decision",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic course exam coverage dashboard decision",
    }


class UniBotCourseExamCoverageDashboardTests(unittest.TestCase):
    def test_dashboard_merges_coverage_console_and_history_without_raw_data(self) -> None:
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

            status, dashboard = route_request(
                "/api/unibot/course/exam-coverage-dashboard",
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
            payload = json.dumps(dashboard, ensure_ascii=False)
            python_lists = next(row for row in dashboard["skill_dashboard"] if row["skill_tag"] == "python_lists")

            self.assertEqual(status, 200)
            self.assertEqual(dashboard["artifact_type"], "course_exam_coverage_dashboard")
            self.assertEqual(dashboard["status"], "course_exam_coverage_dashboard_ready")
            self.assertEqual(dashboard["dashboard_title"], "Course Exam Coverage Dashboard")
            self.assertEqual(dashboard["exam_deployment_status"], "not_cleared")
            self.assertEqual(dashboard["public_safety_status"], "pass")
            self.assertGreaterEqual(dashboard["dashboard_summary"]["skill_count"], 1)
            self.assertGreaterEqual(dashboard["dashboard_summary"]["workspace_ready_skill_count"], 1)
            self.assertGreaterEqual(dashboard["dashboard_summary"]["skills_with_history_count"], 1)
            self.assertGreaterEqual(dashboard["dashboard_summary"]["checkpoint_hash_count"], 1)
            self.assertGreaterEqual(dashboard["dashboard_summary"]["open_operator_confirmation_count"], 1)
            self.assertEqual(dashboard["dashboard_summary"]["help_level_profile"]["A2"], 1)
            self.assertEqual(python_lists["workspace_readiness"], "ready_for_exam_workspace_dry_run")
            self.assertGreaterEqual(python_lists["source_anchor_count"], 1)
            self.assertGreaterEqual(python_lists["reviewed_notebook_anchor_count"], 1)
            self.assertEqual(python_lists["checkpoint_hash_count"], 1)
            self.assertEqual(python_lists["help_level_profile"]["A2"], 1)
            self.assertGreaterEqual(python_lists["open_operator_confirmation_count"], 1)
            self.assertIn("next_safe_step", python_lists)
            self.assertIn("A2", " ".join(python_lists["allowed_exam_help"]))
            self.assertEqual(dashboard["coverage_receipt"]["status"], "dashboard_receipt_ready_not_exam_clearance")
            self.assertTrue(dashboard["coverage_receipt"]["not_cleared_receipt"])
            alignment = dashboard["workspace_card_dashboard_alignment"]
            self.assertEqual(
                alignment["schema_version"],
                "unibot-course-exam-coverage-dashboard-workspace-card-dashboard-alignment-v1",
            )
            self.assertEqual(alignment["status"], "ready")
            self.assertEqual(alignment["alignment_public_safety_status"], "pass")
            self.assertEqual(alignment["failed_contract_ids"], [])
            self.assertEqual(
                alignment["course_exam_coverage_dashboard_hash"],
                course_exam_coverage_dashboard_hash(dashboard),
            )
            self.assertEqual(
                alignment["course_exam_coverage_dashboard_receipt_hash"],
                course_exam_coverage_dashboard_receipt_hash(dashboard),
            )
            self.assertEqual(alignment["dashboard_status"], "course_exam_coverage_dashboard_ready")
            self.assertEqual(alignment["receipt_status"], "dashboard_receipt_ready_not_exam_clearance")
            self.assertGreaterEqual(alignment["skill_count"], 1)
            self.assertGreaterEqual(alignment["visible_skill_count"], 1)
            self.assertGreaterEqual(alignment["workspace_ready_skill_count"], 1)
            self.assertGreaterEqual(alignment["checkpoint_hash_count"], 1)
            self.assertGreaterEqual(alignment["open_operator_confirmation_count"], 1)
            self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
            self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
            self.assertTrue(alignment["workspace_card_course_exam_dashboard_gate_linked"])
            self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
            self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
            self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
            self.assertFalse(alignment["raw_workspace_card_returned"])
            self.assertFalse(dashboard["raw_query_returned"])
            self.assertFalse(dashboard["raw_cell_returned"])
            self.assertFalse(dashboard["raw_text_returned"])
            self.assertFalse(dashboard["raw_notebook_returned"])
            self.assertFalse(dashboard["notebook_code_returned"])
            self.assertFalse(dashboard["local_paths_returned"])
            self.assertFalse(dashboard["automatic_grading_started"])
            self.assertFalse(dashboard["proctoring_started"])
            self.assertFalse(dashboard["ai_detection_started"])
            self.assertFalse(dashboard["exam_clearance_claimed"])
            self.assertNotIn("own_checkpoint", payload)
            self.assertNotIn("Week 01 Python", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "course-exam-coverage-dashboard")["status"], "pass")

    def test_dashboard_can_be_called_directly_without_session_history(self) -> None:
        dashboard = build_course_exam_coverage_dashboard(public_safe=True)

        self.assertEqual(dashboard["artifact_type"], "course_exam_coverage_dashboard")
        self.assertEqual(dashboard["status"], "course_exam_coverage_dashboard_ready")
        self.assertEqual(dashboard["exam_deployment_status"], "not_cleared")
        self.assertEqual(dashboard["run_history_summary"].get("run_count", 0), 0)
        self.assertFalse(dashboard["raw_text_returned"])
        self.assertFalse(dashboard["local_paths_returned"])

    def test_dashboard_workspace_card_alignment_blocks_when_prefill_hashes_do_not_match(self) -> None:
        dashboard = build_course_exam_coverage_dashboard(public_safe=True)
        if not dashboard.get("skill_dashboard"):
            dashboard["skill_dashboard"] = [
                {
                    "skill_tag": "python_lists",
                    "workspace_readiness": "ready_for_exam_workspace_dry_run",
                    "source_anchor_count": 1,
                    "reviewed_notebook_anchor_count": 1,
                    "checkpoint_hash_count": 0,
                    "open_operator_confirmation_count": 0,
                    "exam_deployment_status": "not_cleared",
                    "raw_query_returned": False,
                    "raw_text_returned": False,
                    "raw_cell_returned": False,
                    "notebook_code_returned": False,
                    "local_paths_returned": False,
                }
            ]
            dashboard["dashboard_summary"] = {
                "skill_count": 1,
                "workspace_ready_skill_count": 1,
                "checkpoint_hash_count": 0,
                "open_operator_confirmation_count": 0,
                "exam_deployment_status": "not_cleared",
            }
            dashboard["coverage_receipt"]["receipt_id"] = sha256_text("dashboard broken hash receipt")[:20]
        workspace_card = synthetic_course_exam_coverage_dashboard_workspace_card()
        workspace_card["workspace_card_summary"]["checkpoint_hash"] = "wrong-dashboard-hash"
        workspace_card["workspace_card_summary"]["task_hash"] = "wrong-receipt-hash"

        alignment = build_course_exam_coverage_dashboard_workspace_card_alignment(dashboard, workspace_card)

        self.assertEqual(alignment["status"], "blocked")
        self.assertIn("workspace_card_course_exam_dashboard_gate_linked", alignment["failed_contract_ids"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertFalse(alignment["workspace_card_course_exam_dashboard_gate_linked"])
        self.assertEqual(alignment["alignment_public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
