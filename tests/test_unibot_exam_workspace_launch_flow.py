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

from unibot.exam_workspace_launch_flow import (  # noqa: E402
    build_exam_workspace_launch_flow_dry_run,
    build_exam_workspace_launch_release_claim_alignment,
)
from unibot.materials import build_material_manifest, sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402
from unibot.tutor_index import build_private_tutor_index_dry_run  # noqa: E402


def write_gap_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Videos").mkdir(parents=True)
    (root / "Week 1" / "python_lists_slides.pdf").write_bytes(b"%PDF-1.4\nfixture")
    (root / "Videos" / "pandas_debugging.mov").write_bytes(b"video")


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
        "decision_reference": "synthetic launch flow decision",
    }


class UniBotExamWorkspaceLaunchFlowTests(unittest.TestCase):
    def test_launch_flow_waits_until_material_coverage_has_ready_start_point(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "missing_manifest.json"
            index_path = Path(temp_dir) / "missing_index.json"
            write_gap_fixture(root)

            report = build_exam_workspace_launch_flow_dry_run(
                base_path=str(root),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                focus_query="pandas",
                public_safe=True,
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["artifact_type"], "exam_workspace_launch_flow_dry_run")
            self.assertEqual(report["status"], "exam_workspace_launch_waiting_for_material_coverage")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["coverage_summary"]["start_point"]["status"], "not_ready")
            self.assertEqual(report["exam_workspace_run_summary"]["status"], "not_started_waiting_for_material_coverage")
            self.assertEqual(report["help_ledger_preview"]["status"], "not_started_waiting_for_material_coverage")
            self.assertTrue(report["export_receipt"]["not_cleared_receipt"])
            self.assertFalse(report["raw_query_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["raw_notebook_returned"])
            self.assertFalse(report["notebook_code_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(report["exam_clearance_claimed"])
            self.assertFalse(manifest_path.exists())
            self.assertFalse(index_path.exists())
            self.assertNotIn(str(temp_dir), payload)
            self.assertNotIn("pandas_debugging.mov", payload)
            self.assertEqual(scan_text(payload, "launch-flow-waiting")["status"], "pass")

    def test_launch_flow_preconfigures_exam_workspace_from_coverage_start_point(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            course_id = f"launch-flow-{uuid.uuid4().hex[:10]}"
            self.addCleanup(lambda: shutil.rmtree(ROOT / "unibot" / "knowledge" / "exam_workspace" / course_id, ignore_errors=True))
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "private_tutor_index.json"
            index_journal_path = Path(temp_dir) / "index_journal.jsonl"
            help_ledger_path = Path(temp_dir) / "help_ledger.jsonl"
            checkpoint_journal_path = Path(temp_dir) / "checkpoints.jsonl"
            cell_source = "own_boxplot_frame = None\n# eigener kleinster Check\n"
            write_ready_fixture(root)
            write_private_manifest(manifest_path, [reviewed_manifest_record()])
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                tutor_index_journal_path=index_journal_path,
                operator_confirmed_tutor_index_build=True,
            )

            status, report = route_request(
                "/api/unibot/exam-workspace/launch-flow/dry-run",
                {
                    "course_id": course_id,
                    "base_path": str(root),
                    "review_policy": "local_private_tutor",
                    "decision_record": valid_decision(),
                    "private_manifest_path": str(manifest_path),
                    "tutor_index_path": str(index_path),
                    "tutor_index_journal_path": str(index_journal_path),
                    "ledger_path": str(help_ledger_path),
                    "focus_query": "pandas boxplot",
                    "query": "Meine private Startfrage darf nicht im Report stehen.",
                    "requested_help_level": "A6",
                    "student_reflection": "Ich pruefe zuerst meine eigene Vorhersage.",
                    "cell_source": cell_source,
                    "cell_index": 3,
                    "cell_id": "private-local-cell",
                    "checkpoint_journal_path": str(checkpoint_journal_path),
                    "study_receipt": {
                        "prediction_present": True,
                        "notebook_action_present": True,
                        "reflection_present": True,
                    },
                },
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(report["artifact_type"], "exam_workspace_launch_flow_dry_run")
            self.assertEqual(report["status"], "exam_workspace_launch_dry_run_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertEqual(report["coverage_summary"]["start_point"]["status"], "ready")
            self.assertEqual(report["coverage_summary"]["start_point"]["recommended_endpoint"], "/api/unibot/exam-workspace/launch-flow/dry-run")
            self.assertEqual(report["launch_configuration"]["workspace_endpoint_used"], "/api/unibot/exam-workspace/run-dry-run")
            self.assertEqual(report["launch_configuration"]["help_level"], "A2")
            self.assertTrue(report["launch_configuration"]["requested_help_level_coerced"])
            self.assertIn("Welche Quelle", report["launch_configuration"]["query_template"])
            self.assertFalse(report["launch_configuration"]["actual_query_returned"])
            self.assertGreaterEqual(report["launch_configuration"]["source_anchor_hint"]["source_anchor_count"], 1)
            self.assertEqual(
                report["launch_configuration"]["notebook_cell_checkpoint"]["notebook_code_returned"],
                False,
            )
            self.assertEqual(report["exam_workspace_run_summary"]["status"], "exam_workspace_dry_run_ready")
            self.assertEqual(report["exam_workspace_run_summary"]["tutor_status"], "allowed")
            self.assertEqual(report["local_notebook_checkpoint"]["status"], "notebook_checkpoint_ready")
            self.assertEqual(report["local_notebook_checkpoint"]["notebook_work_sha256"], sha256_text(cell_source))
            self.assertFalse(report["local_notebook_checkpoint"]["notebook_code_returned"])
            self.assertFalse(report["local_notebook_checkpoint"]["raw_cell_returned"])
            self.assertEqual(report["help_ledger_preview"]["help_level"], "A2")
            self.assertFalse(report["help_ledger_preview"]["general_help_ledger_written"])
            self.assertFalse(report["help_ledger_preview"]["exam_ledger_written"])
            self.assertTrue(report["export_receipt"]["not_cleared_receipt"])
            self.assertTrue(report["export_receipt"]["human_reviewable_independence_evidence"])
            self.assertFalse(report["raw_query_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["raw_cell_returned"])
            self.assertFalse(report["raw_notebook_returned"])
            self.assertFalse(report["notebook_code_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(report["automatic_grading_started"])
            self.assertFalse(report["proctoring_started"])
            self.assertFalse(report["ai_detection_started"])
            self.assertFalse(report["exam_clearance_claimed"])
            self.assertFalse(help_ledger_path.exists())
            self.assertFalse(checkpoint_journal_path.exists())
            self.assertNotIn("Meine private Startfrage", payload)
            self.assertNotIn("own_boxplot_frame", payload)
            self.assertNotIn("private-local-cell", payload)
            self.assertNotIn("Week 01 pandas", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "launch-flow-ready")["status"], "pass")

    def test_launch_flow_stops_when_local_notebook_checkpoint_sees_final_solution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "private_tutor_index.json"
            index_journal_path = Path(temp_dir) / "index_journal.jsonl"
            write_ready_fixture(root)
            write_private_manifest(manifest_path, [reviewed_manifest_record()])
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                tutor_index_journal_path=index_journal_path,
                operator_confirmed_tutor_index_build=True,
            )

            status, report = route_request(
                "/api/unibot/exam-workspace/launch-flow/dry-run",
                {
                    "base_path": str(root),
                    "review_policy": "local_private_tutor",
                    "decision_record": valid_decision(),
                    "private_manifest_path": str(manifest_path),
                    "tutor_index_path": str(index_path),
                    "tutor_index_journal_path": str(index_journal_path),
                    "focus_query": "pandas boxplot",
                    "cell_source": "# final answer: complete solution\n",
                    "study_receipt": {
                        "prediction_present": True,
                        "notebook_action_present": True,
                        "reflection_present": True,
                    },
                },
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(
                report["status"],
                "exam_workspace_launch_notebook_checkpoint_repeat_task_required",
            )
            self.assertEqual(report["exam_workspace_run_summary"]["status"], "not_started_checkpoint_not_ready")
            self.assertEqual(report["local_notebook_checkpoint"]["status"], "notebook_checkpoint_repeat_task_required")
            self.assertTrue(report["local_notebook_checkpoint"]["solution_marker_detected"])
            self.assertFalse(report["raw_cell_returned"])
            self.assertFalse(report["notebook_code_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertNotIn("complete solution", payload.lower())
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "launch-flow-repeat")["status"], "pass")

    def test_launch_release_claim_alignment_links_review_board_claims(self) -> None:
        alignment = build_exam_workspace_launch_release_claim_alignment()
        payload = json.dumps(alignment, ensure_ascii=False)

        self.assertEqual(
            alignment["schema_version"],
            "unibot-exam-workspace-launch-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["launch_status"], "exam_workspace_launch_dry_run_ready")
        self.assertEqual(alignment["launch_public_safety_status"], "pass")
        self.assertEqual(alignment["blocked_public_safety_status"], "pass")
        self.assertEqual(
            alignment["blocked_launch_status"],
            "exam_workspace_launch_notebook_checkpoint_repeat_task_required",
        )
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertEqual(alignment["checkpoint_status"], "notebook_checkpoint_ready")
        self.assertTrue(alignment["checkpoint_hash_present"])
        self.assertEqual(alignment["study_receipt_status"], "ok_study_session_receipt")
        self.assertEqual(alignment["tutor_status"], "allowed")
        self.assertEqual(alignment["workspace_card_status"], "python_exam_local_cycle_operator_workspace_card_ready")
        self.assertEqual(alignment["workspace_card_selected_skill_tag"], "boxplots")
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertEqual(alignment["help_ledger_preview_status"], "preview_ready")
        self.assertFalse(alignment["general_help_ledger_written"])
        self.assertFalse(alignment["exam_ledger_written"])
        self.assertTrue(alignment["repeat_task_required"])
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("exam_workspace_launch", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertIn("notebook_checkpoint", alignment["required_readiness_check_ids"])
        self.assertIn("study_session", alignment["required_readiness_check_ids"])
        self.assertIn("private_tutor_use_flow", alignment["required_readiness_check_ids"])
        self.assertIn("evaluation_packet", alignment["required_readiness_check_ids"])
        self.assertIn("review_board_packet", alignment["required_readiness_check_ids"])
        self.assertIn("external_decision_state", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertTrue(alignment["contracts"]["launch_public_safe"])
        self.assertTrue(alignment["contracts"]["blocked_launch_public_safe"])
        self.assertTrue(alignment["contracts"]["notebook_checkpoint_linked_hash_only"])
        self.assertTrue(alignment["contracts"]["private_tutor_use_and_study_receipt_linked"])
        self.assertTrue(alignment["contracts"]["workspace_card_launch_gate_linked"])
        self.assertTrue(alignment["contracts"]["dry_run_operator_boundaries_hold"])
        self.assertTrue(alignment["contracts"]["blocked_checkpoint_stops_launch"])
        self.assertTrue(alignment["contracts"]["public_outputs_hide_private_data"])
        self.assertTrue(alignment["contracts"]["high_stakes_actions_not_started"])
        self.assertIn("raw notebook code returned", alignment["blocked_claims"])
        self.assertIn("raw cell text returned", alignment["blocked_claims"])
        self.assertIn("final solution acceptance", alignment["blocked_claims"])
        self.assertIn("automatic grading", alignment["blocked_claims"])
        self.assertIn("proctoring", alignment["blocked_claims"])
        self.assertIn("KI-detection evidence", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])
        self.assertIn("exam clearance", alignment["blocked_claims"])
        self.assertEqual(scan_text(payload, "launch-alignment")["status"], "pass")

    def test_launch_release_claim_alignment_blocks_overstated_launch_claims(self) -> None:
        unsafe_launch_report = {
            "status": "exam_workspace_launch_dry_run_ready",
            "public_safety_status": "pass",
            "exam_deployment_status": "cleared",
            "execution_boundary": "Launch flow.",
            "launch_configuration": {
                "requires_operator_confirmation_for_writes": False,
                "notebook_cell_checkpoint": {
                    "notebook_work_sha256": sha256_text("synthetic"),
                    "raw_notebook_returned": True,
                    "notebook_code_returned": True,
                    "local_path_returned": True,
                },
            },
            "local_notebook_checkpoint": {
                "status": "notebook_checkpoint_ready",
                "notebook_work_sha256": sha256_text("synthetic"),
            },
            "exam_workspace_run_summary": {
                "status": "exam_workspace_dry_run_ready",
                "tutor_status": "allowed",
                "study_receipt_status": "ok_study_session_receipt",
            },
            "help_ledger_preview": {
                "status": "preview_ready",
                "general_help_ledger_written": True,
                "exam_ledger_written": True,
            },
            "export_receipt": {"not_cleared_receipt": False},
            "raw_query_returned": True,
            "raw_text_returned": True,
            "raw_cell_returned": True,
            "raw_notebook_returned": True,
            "notebook_code_returned": True,
            "local_paths_returned": True,
            "automatic_grading_started": True,
            "proctoring_started": True,
            "ai_detection_started": True,
            "exam_clearance_claimed": True,
        }
        blocked_report = {
            "status": "exam_workspace_launch_notebook_checkpoint_repeat_task_required",
            "public_safety_status": "pass",
            "local_notebook_checkpoint": {"solution_marker_detected": True},
            "exam_workspace_run_summary": {"status": "not_started_checkpoint_not_ready"},
        }

        alignment = build_exam_workspace_launch_release_claim_alignment(
            launch_report=unsafe_launch_report,
            blocked_report=blocked_report,
        )

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("notebook_checkpoint_linked_hash_only", alignment["failed_contract_ids"])
        self.assertIn("private_tutor_use_and_study_receipt_linked", alignment["failed_contract_ids"])
        self.assertIn("workspace_card_launch_gate_linked", alignment["failed_contract_ids"])
        self.assertIn("dry_run_operator_boundaries_hold", alignment["failed_contract_ids"])
        self.assertIn("public_outputs_hide_private_data", alignment["failed_contract_ids"])
        self.assertIn("high_stakes_actions_not_started", alignment["failed_contract_ids"])


if __name__ == "__main__":
    unittest.main()
