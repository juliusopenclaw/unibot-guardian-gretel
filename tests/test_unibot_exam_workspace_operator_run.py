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

from unibot.exam_workspace_operator_run import (  # noqa: E402
    build_exam_workspace_operator_run_dry_run,
    build_exam_workspace_operator_run_release_claim_alignment,
    synthetic_operator_workspace_card,
)
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
            workspace_card = synthetic_operator_workspace_card()

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
                    "python_exam_local_cycle_operator_workspace_card": workspace_card,
                },
            )
            payload = json.dumps(report, ensure_ascii=False)
            control = report["operator_control_references"]

            self.assertEqual(status, 200)
            self.assertEqual(report["artifact_type"], "exam_workspace_operator_run_dry_run")
            self.assertEqual(report["status"], "exam_workspace_operator_dry_run_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertEqual(report["start_exam_workspace_view"]["title"], "Start Exam Workspace")
            self.assertEqual(report["start_exam_workspace_view"]["status"], "ready_to_start_dry_run")
            self.assertEqual(
                report["start_exam_workspace_view"]["local_cycle_operator_workspace_card"]["status"],
                "python_exam_local_cycle_operator_workspace_card_ready",
            )
            self.assertTrue(
                report["start_exam_workspace_view"]["local_cycle_operator_workspace_card"]["ready_for_operator_prefill"]
            )
            self.assertIn("# Start Exam Workspace", report["start_exam_workspace_markdown"])
            self.assertEqual(control["status"], "operator_control_references_ready")
            self.assertTrue(control["hash_only"])
            self.assertEqual(control["operator_run_endpoint"], "/api/unibot/exam-workspace/operator-run")
            self.assertEqual(control["launch_endpoint"], "/api/unibot/exam-workspace/launch-flow/dry-run")
            self.assertEqual(control["workspace_run_endpoint"], "/api/unibot/exam-workspace/run-dry-run")
            self.assertEqual(control["session_console_endpoint"], "/api/unibot/exam-workspace/session-console")
            self.assertEqual(control["confirmation_status"], "all_steps_dry_run")
            self.assertEqual(control["confirmed_count"], 0)
            self.assertEqual(control["write_step_count"], 6)
            self.assertTrue(control["workspace_card_hash_present"])
            self.assertTrue(control["help_ledger_preview_hash_present"])
            self.assertFalse(control["raw_workspace_card_returned"])
            self.assertFalse(control["raw_confirmation_text_returned"])
            self.assertFalse(control["local_paths_returned"])
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

    def test_operator_run_release_claim_alignment_links_review_board_claims(self) -> None:
        alignment = build_exam_workspace_operator_run_release_claim_alignment()
        payload = json.dumps(alignment, ensure_ascii=False)

        self.assertEqual(
            alignment["schema_version"],
            "unibot-exam-workspace-operator-run-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["operator_status"], "exam_workspace_operator_dry_run_ready")
        self.assertEqual(alignment["operator_public_safety_status"], "pass")
        self.assertEqual(alignment["repeat_status"], "exam_workspace_operator_repeat_task_required")
        self.assertEqual(alignment["repeat_public_safety_status"], "pass")
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertEqual(alignment["view_status"], "ready_to_start_dry_run")
        self.assertEqual(alignment["receipt_status"], "ready_for_human_review_not_exam_clearance")
        self.assertTrue(alignment["receipt_not_cleared"])
        self.assertEqual(alignment["confirmation_status"], "all_steps_dry_run")
        self.assertEqual(alignment["confirmed_count"], 0)
        self.assertEqual(alignment["write_step_count"], 6)
        self.assertFalse(alignment["local_writes_requested"])
        self.assertEqual(alignment["checkpoint_status"], "notebook_checkpoint_ready")
        self.assertTrue(alignment["checkpoint_hash_present"])
        self.assertEqual(alignment["workspace_status"], "exam_workspace_dry_run_ready")
        self.assertEqual(alignment["tutor_status"], "allowed")
        self.assertEqual(alignment["study_receipt_status"], "ok_study_session_receipt")
        self.assertEqual(alignment["workspace_card_status"], "python_exam_local_cycle_operator_workspace_card_ready")
        self.assertEqual(alignment["workspace_card_selected_skill_tag"], "boxplots")
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertEqual(alignment["help_ledger_preview_status"], "preview_ready")
        self.assertFalse(alignment["general_help_ledger_written"])
        self.assertFalse(alignment["exam_ledger_written"])
        self.assertTrue(alignment["export_not_cleared_receipt"])
        self.assertEqual(alignment["repeat_checkpoint_status"], "notebook_checkpoint_repeat_task_required")
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("exam_workspace_operator_run", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertIn("exam_workspace_launch", alignment["required_readiness_check_ids"])
        self.assertIn("exam_workspace_run", alignment["required_readiness_check_ids"])
        self.assertIn("exam_workspace_run_history", alignment["required_readiness_check_ids"])
        self.assertIn("review_board_packet", alignment["required_readiness_check_ids"])
        self.assertIn("notebook_checkpoint", alignment["required_readiness_check_ids"])
        self.assertIn("study_session", alignment["required_readiness_check_ids"])
        self.assertIn("external_decision_state", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertTrue(alignment["contracts"]["operator_ready_public_safe"])
        self.assertTrue(alignment["contracts"]["repeat_boundary_public_safe"])
        self.assertTrue(alignment["contracts"]["start_view_hash_only_ready"])
        self.assertTrue(alignment["contracts"]["workspace_card_start_view_gate_linked"])
        self.assertTrue(alignment["contracts"]["individual_confirmations_default_to_dry_run"])
        self.assertTrue(alignment["contracts"]["receipt_and_export_not_exam_clearance"])
        self.assertTrue(alignment["contracts"]["help_ledger_preview_not_written"])
        self.assertTrue(alignment["contracts"]["repeat_task_stops_operator_start"])
        self.assertTrue(alignment["contracts"]["markdown_boundary_mentions_no_high_stakes_claims"])
        self.assertTrue(alignment["contracts"]["public_outputs_hide_private_operator_data"])
        self.assertTrue(alignment["contracts"]["high_stakes_actions_not_started"])
        self.assertTrue(alignment["contracts"]["operator_control_references_hash_only_linked"])
        self.assertEqual(alignment["operator_control_reference_status"], "operator_control_references_ready")
        self.assertEqual(
            alignment["operator_control_reference_session_console_endpoint"],
            "/api/unibot/exam-workspace/session-console",
        )
        self.assertTrue(alignment["operator_control_reference_workspace_card_hash_present"])
        self.assertTrue(alignment["operator_control_reference_help_ledger_hash_present"])
        self.assertTrue(alignment["operator_control_reference_hash_only"])
        self.assertIn("unconfirmed local write", alignment["blocked_claims"])
        self.assertIn("raw notebook code returned", alignment["blocked_claims"])
        self.assertIn("automatic grading", alignment["blocked_claims"])
        self.assertIn("proctoring", alignment["blocked_claims"])
        self.assertIn("KI-detection evidence", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])
        self.assertIn("exam clearance", alignment["blocked_claims"])
        self.assertEqual(scan_text(payload, "operator-run-alignment")["status"], "pass")

    def test_operator_run_release_claim_alignment_blocks_overstated_operator_claims(self) -> None:
        unsafe_ready = {
            "status": "exam_workspace_operator_dry_run_ready",
            "public_safety_status": "pass",
            "exam_deployment_status": "cleared",
            "execution_boundary": "Operator run.",
            "start_exam_workspace_view": {
                "status": "ready_to_start_dry_run",
                "raw_query_returned": True,
                "raw_cell_returned": True,
                "notebook_code_returned": True,
                "local_paths_returned": True,
            },
            "start_exam_workspace_markdown": "Start Exam Workspace",
            "operator_confirmation_matrix": {
                "status": "operator_confirmations_present",
                "default_policy": "auto_write",
                "confirmed_count": 6,
                "write_step_count": 6,
                "local_writes_requested": True,
                "raw_confirmation_text_returned": True,
                "steps": {
                    "checkpoint_store": {"confirmed": True, "requires_individual_confirmation": False}
                },
            },
            "dry_run_receipt": {
                "status": "ready_for_exam_clearance",
                "receipt_id": "",
                "exam_deployment_status": "cleared",
                "not_cleared_receipt": False,
                "human_reviewable_independence_evidence": False,
            },
            "local_notebook_checkpoint": {"status": "notebook_checkpoint_ready", "notebook_work_sha256": ""},
            "exam_workspace_run_summary": {
                "status": "exam_workspace_dry_run_ready",
                "tutor_status": "allowed",
                "study_receipt_status": "ok_study_session_receipt",
            },
            "help_ledger_preview": {
                "status": "preview_ready",
                "general_help_ledger_written": True,
                "exam_ledger_written": True,
                "raw_query_returned": True,
                "raw_response_returned": True,
                "local_path_returned": True,
            },
            "export_receipt": {
                "not_cleared_receipt": False,
                "human_reviewable_independence_evidence": False,
            },
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
        repeat_report = {
            "status": "exam_workspace_operator_repeat_task_required",
            "public_safety_status": "pass",
            "start_exam_workspace_view": {"status": "repeat_task_required_before_start"},
            "local_notebook_checkpoint": {"status": "notebook_checkpoint_repeat_task_required"},
            "exam_workspace_run_summary": {"status": "not_started_checkpoint_not_ready"},
        }

        alignment = build_exam_workspace_operator_run_release_claim_alignment(
            ready_report=unsafe_ready,
            repeat_report=repeat_report,
        )

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("start_view_hash_only_ready", alignment["failed_contract_ids"])
        self.assertIn("workspace_card_start_view_gate_linked", alignment["failed_contract_ids"])
        self.assertIn("individual_confirmations_default_to_dry_run", alignment["failed_contract_ids"])
        self.assertIn("receipt_and_export_not_exam_clearance", alignment["failed_contract_ids"])
        self.assertIn("help_ledger_preview_not_written", alignment["failed_contract_ids"])
        self.assertIn("markdown_boundary_mentions_no_high_stakes_claims", alignment["failed_contract_ids"])
        self.assertIn("public_outputs_hide_private_operator_data", alignment["failed_contract_ids"])
        self.assertIn("high_stakes_actions_not_started", alignment["failed_contract_ids"])
        self.assertIn("operator_control_references_hash_only_linked", alignment["failed_contract_ids"])


if __name__ == "__main__":
    unittest.main()
