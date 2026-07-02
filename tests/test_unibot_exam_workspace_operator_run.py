from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.exam_workspace_operator_run import build_exam_workspace_operator_run_dry_run  # noqa: E402
from unibot.materials import build_material_manifest, sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402
from unibot.tutor_index import build_private_tutor_index_dry_run  # noqa: E402


def write_ready_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Week 1" / "pandas_intro.md").write_text(
        "pandas DataFrame read_csv columns dtypes debugging boxplot",
        encoding="utf-8",
    )


def reviewed_manifest_record() -> dict[str, object]:
    return {
        "material_id": "week-01-pandas-notebook",
        "title": "Week 01 pandas and boxplot notebook",
        "source_kind": "notebook",
        "permission_status": "private_course_use_only",
        "publish_policy": "private_only",
        "extraction_status": "text_extracted",
        "review_status": "reviewed_for_private_tutor",
        "skill_tags": ["pandas", "boxplots", "debugging"],
        "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
        "page_or_timestamp": "week 01",
        "sha256": sha256_text("week 01 pandas notebook reviewed locally"),
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
        "retention_decision": "delete private extraction artifacts after reviewed metadata is accepted",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic operator run decision",
    }


class UniBotExamWorkspaceOperatorRunTests(unittest.TestCase):
    def test_operator_run_merges_launch_into_start_exam_workspace_view(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            course_id = f"operator-run-{uuid.uuid4().hex[:10]}"
            self.addCleanup(lambda: shutil.rmtree(ROOT / "unibot" / "knowledge" / "exam_workspace" / course_id, ignore_errors=True))
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "private_tutor_index.json"
            index_journal_path = Path(temp_dir) / "index_journal.jsonl"
            help_ledger_path = Path(temp_dir) / "help_ledger.jsonl"
            checkpoint_journal_path = Path(temp_dir) / "checkpoints.jsonl"
            cell_source = "own_frame = None\n# local checkpoint only\n"
            write_ready_fixture(root)
            write_private_manifest(manifest_path, [reviewed_manifest_record()])
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                tutor_index_journal_path=index_journal_path,
                operator_confirmed_tutor_index_build=True,
            )

            status, report = route_request(
                "/api/unibot/exam-workspace/operator-run",
                {
                    "course_id": course_id,
                    "base_path": str(root),
                    "review_policy": "local_private_tutor",
                    "decision_record": valid_decision(),
                    "private_manifest_path": str(manifest_path),
                    "tutor_index_path": str(index_path),
                    "tutor_index_journal_path": str(index_journal_path),
                    "ledger_path": str(help_ledger_path),
                    "checkpoint_journal_path": str(checkpoint_journal_path),
                    "focus_query": "pandas boxplot",
                    "query": "Diese private Startfrage darf nicht erscheinen.",
                    "cell_source": cell_source,
                    "cell_index": 1,
                    "cell_id": "private-local-cell",
                    "requested_help_level": "A2",
                    "student_reflection": "Ich pruefe zuerst meine eigene Vorhersage.",
                    "study_receipt": {
                        "prediction_present": True,
                        "notebook_action_present": True,
                        "reflection_present": True,
                    },
                },
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(report["artifact_type"], "exam_workspace_operator_run_dry_run")
            self.assertEqual(report["status"], "exam_workspace_operator_dry_run_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertEqual(report["start_exam_workspace_view"]["title"], "Start Exam Workspace")
            self.assertEqual(report["start_exam_workspace_view"]["status"], "ready_to_start_dry_run")
            self.assertIn("# Start Exam Workspace", report["start_exam_workspace_markdown"])
            self.assertEqual(report["dry_run_receipt"]["status"], "ready_for_human_review_not_exam_clearance")
            self.assertEqual(report["dry_run_receipt"]["notebook_work_sha256"], sha256_text(cell_source))
            self.assertEqual(report["dry_run_receipt"]["effective_help_level"], "A2")
            self.assertTrue(report["dry_run_receipt"]["not_cleared_receipt"])
            self.assertEqual(report["operator_confirmation_matrix"]["status"], "all_steps_dry_run")
            self.assertFalse(report["operator_confirmation_matrix"]["local_writes_requested"])
            self.assertFalse(report["operator_confirmation_matrix"]["steps"]["checkpoint_store"]["confirmed"])
            self.assertEqual(report["coverage_summary"]["start_point"]["status"], "ready")
            self.assertEqual(report["local_notebook_checkpoint"]["status"], "notebook_checkpoint_ready")
            self.assertEqual(report["exam_workspace_run_summary"]["status"], "exam_workspace_dry_run_ready")
            self.assertEqual(report["help_ledger_preview"]["help_level"], "A2")
            self.assertTrue(report["export_receipt"]["not_cleared_receipt"])
            self.assertFalse(report["raw_query_returned"])
            self.assertFalse(report["raw_cell_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["raw_notebook_returned"])
            self.assertFalse(report["notebook_code_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(report["automatic_grading_started"])
            self.assertFalse(report["proctoring_started"])
            self.assertFalse(report["ai_detection_started"])
            self.assertFalse(report["exam_clearance_claimed"])
            self.assertFalse(help_ledger_path.exists())
            self.assertFalse(checkpoint_journal_path.exists())
            self.assertNotIn("Diese private Startfrage", payload)
            self.assertNotIn("own_frame", payload)
            self.assertNotIn("private-local-cell", payload)
            self.assertNotIn("Week 01 pandas", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "operator-run-ready")["status"], "pass")

    def test_operator_run_stops_on_repeat_task_checkpoint(self) -> None:
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

            report = build_exam_workspace_operator_run_dry_run(
                base_path=str(root),
                review_policy="local_private_tutor",
                decision_record=valid_decision(),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                focus_query="pandas boxplot",
                cell_source="# final answer: complete solution\n",
                study_receipt={
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
                public_safe=True,
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["status"], "exam_workspace_operator_repeat_task_required")
            self.assertEqual(report["start_exam_workspace_view"]["status"], "repeat_task_required_before_start")
            self.assertEqual(report["local_notebook_checkpoint"]["status"], "notebook_checkpoint_repeat_task_required")
            self.assertEqual(report["exam_workspace_run_summary"]["status"], "not_started_checkpoint_not_ready")
            self.assertFalse(report["raw_cell_returned"])
            self.assertFalse(report["notebook_code_returned"])
            self.assertNotIn("final answer:", payload.lower())
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "operator-run-repeat")["status"], "pass")


if __name__ == "__main__":
    unittest.main()
