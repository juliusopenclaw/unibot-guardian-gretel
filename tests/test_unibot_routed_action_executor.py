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
from unibot.routed_action_executor import build_routed_action_executor  # noqa: E402
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
        "retention_decision": "synthetic routed executor decision",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic routed action executor decision",
    }


class UniBotRoutedActionExecutorTests(unittest.TestCase):
    def test_executor_runs_session_console_route_without_raw_data(self) -> None:
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

            report = build_routed_action_executor(
                base_path=str(root),
                review_policy="local_private_tutor",
                decision_record=valid_decision(),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                router_report=router,
                selected_route=router["selected_route"],
                selected_skill_tag="python_lists",
                cell_source="own_checkpoint = []\n",
                study_receipt={
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
                public_safe=True,
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["artifact_type"], "routed_action_executor")
            self.assertEqual(report["status"], "routed_action_executor_ready")
            self.assertEqual(report["selected_route"]["route_id"], "start_session_console_dry_run")
            self.assertEqual(report["execution_result_summary"]["artifact_type"], "exam_workspace_session_console")
            self.assertEqual(report["execution_result_summary"]["receipt"]["status"], "session_console_receipt_ready_not_exam_clearance")
            self.assertEqual(report["executor_receipt"]["status"], "executor_receipt_ready_not_exam_clearance")
            self.assertFalse(report["execution_result_summary"]["local_write_started"])
            self.assertFalse(report["raw_query_returned"])
            self.assertFalse(report["raw_cell_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["notebook_code_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertNotIn("own_checkpoint", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "routed-action-executor-session")["status"], "pass")

    def test_executor_runs_history_review_route_from_router(self) -> None:
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
                    "selected_skill_tag": "python_lists",
                    "console_reports": [console],
                    "console_receipts": [console["session_console_receipt"]],
                },
            )
            self.assertEqual(status, 200)
            status, report = route_request(
                "/api/unibot/course/routed-action-executor",
                {
                    "base_path": str(root),
                    "review_policy": "local_private_tutor",
                    "decision_record": valid_decision(),
                    "private_manifest_path": str(manifest_path),
                    "tutor_index_path": str(index_path),
                    "router_report": router,
                    "selected_route": router["selected_route"],
                    "selected_skill_tag": "python_lists",
                    "console_reports": [console],
                    "console_receipts": [console["session_console_receipt"]],
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["selected_route"]["route_id"], "review_open_operator_confirmations")
            self.assertEqual(report["executed_endpoint"], "/api/unibot/exam-workspace/run-history-export-review")
            self.assertEqual(report["execution_result_summary"]["artifact_type"], "exam_workspace_run_history_export_review")
            self.assertEqual(report["execution_result_summary"]["status"], "exam_workspace_run_history_export_review_ready")
            self.assertTrue(report["execution_result_summary"]["receipt"]["not_cleared_receipt"])
            self.assertFalse(report["automatic_grading_started"])
            self.assertFalse(report["proctoring_started"])
            self.assertFalse(report["ai_detection_started"])
            self.assertFalse(report["exam_clearance_claimed"])
            self.assertEqual(report["public_safety_status"], "pass")

    def test_executor_keeps_private_extraction_waiting_without_operator_confirmation(self) -> None:
        route = {
            "skill_tag": "python_lists",
            "route_id": "prepare_ocr_harness",
            "endpoint": "/api/unibot/course/private-extraction/run-batch",
            "dry_run_by_default": True,
            "requested_help_level": "A2",
            "requires_operator_confirmation_for_local_writes": True,
            "open_operator_confirmation_count": 0,
        }

        report = build_routed_action_executor(
            selected_skill_tag="python_lists",
            selected_route=route,
            operator_confirmed_private_extraction_run=False,
            public_safe=True,
        )

        self.assertEqual(report["status"], "routed_action_executor_ready")
        self.assertEqual(report["execution_result_summary"]["artifact_type"], "course_private_extraction_run")
        self.assertEqual(report["execution_result_summary"]["status"], "dry_run_waiting_for_operator_confirmation")
        self.assertFalse(report["execution_result_summary"]["local_write_started"])
        self.assertEqual(report["executor_receipt"]["status"], "executor_receipt_ready_not_exam_clearance")
        self.assertFalse(report["raw_text_returned"])
        self.assertFalse(report["local_paths_returned"])


if __name__ == "__main__":
    unittest.main()
