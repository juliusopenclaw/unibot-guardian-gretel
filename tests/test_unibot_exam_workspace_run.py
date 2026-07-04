from __future__ import annotations

import json
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.exam_workspace_run import (  # noqa: E402
    build_exam_workspace_run_dry_run,
    build_exam_workspace_run_release_claim_alignment,
    build_exam_workspace_run_workspace_card_receipt_alignment,
    exam_workspace_run_hash,
    exam_workspace_run_receipt_hash,
)
from unibot.extraction import build_course_extraction_queue  # noqa: E402
from unibot.materials import sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_exam_workspace_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Week 1" / "python_lists_and_loops.pdf").write_bytes(b"%PDF-1.4\nfixture")


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
        "decision_reference": "synthetic exam workspace decision",
    }


def reviewed_receipt_for_job(job: dict[str, object]) -> dict[str, object]:
    return {
        "job_id": job["job_id"],
        "material_id": job["material_id"],
        "job_type": job["job_type"],
        "extraction_status": "extracted_private",
        "raw_text_sha256": "f" * 64,
        "extracted_text_char_count": 1400,
        "private_artifact_reference": "private exam workspace artifact ref",
        "human_review_status": "reviewed_for_private_tutor",
        "decision_reference_hash": sha256_text(str(valid_decision()["decision_reference"])),
    }


def notebook_fixture() -> dict[str, object]:
    return {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": ["# Controlled exam workspace\n"]},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": ["values = [1, 2, 3]\n"]},
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


class UniBotExamWorkspaceRunTests(unittest.TestCase):
    def test_exam_workspace_run_waits_without_private_manifest_or_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "index.json"
            write_exam_workspace_fixture(root)

            report = build_exam_workspace_run_dry_run(
                "Wie pruefe ich Listen vor dem naechsten Notebook-Schritt?",
                base_path=str(root),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                notebook=notebook_fixture(),
                cell_index=1,
                student_reflection="Ich pruefe zuerst meine eigene Vorhersage.",
                public_safe=True,
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["artifact_type"], "exam_workspace_run_dry_run")
            self.assertEqual(report["status"], "exam_workspace_waiting_for_tutor_flow")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["session_summary"]["status"], "dry_run_not_started")
            self.assertEqual(report["material_freeze_summary"]["status"], "dry_run_not_frozen")
            self.assertEqual(report["notebook_checkpoint"]["run_status"], "dry_run_not_executed")
            self.assertFalse(report["exam_ledger_append_summary"]["ledger_written"])
            self.assertFalse(report["raw_query_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["raw_notebook_returned"])
            self.assertFalse(report["notebook_code_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(manifest_path.exists())
            self.assertFalse(index_path.exists())
            self.assertNotIn("Wie pruefe ich", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "exam-workspace-waiting")["status"], "pass")

    def test_exam_workspace_run_connects_notebook_tutor_ledger_and_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            course_id = f"exam-workspace-{uuid.uuid4().hex[:10]}"
            root = Path(temp_dir) / "materials"
            runtime_root = Path(temp_dir) / "exam_runtime"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            manifest_journal_path = Path(temp_dir) / "manifest_apply.jsonl"
            index_path = Path(temp_dir) / "index.json"
            index_journal_path = Path(temp_dir) / "index_journal.jsonl"
            help_ledger_path = Path(temp_dir) / "help_ledger.jsonl"
            write_exam_workspace_fixture(root)
            queue = build_course_extraction_queue(
                base_path=str(root),
                rights_decision_reference=str(valid_decision()["decision_reference"]),
            )
            receipt = reviewed_receipt_for_job(queue["jobs"][0])
            import exam_mode

            previous_exam_root = exam_mode.EXAM_ROOT
            exam_mode.EXAM_ROOT = runtime_root

            try:
                status, report = route_request(
                    "/api/unibot/exam-workspace/run-dry-run",
                    {
                        "course_id": course_id,
                        "query": "Wie pruefe ich Python Listen vor dem naechsten eigenen Check?",
                        "base_path": str(root),
                        "decision_record": valid_decision(),
                        "receipts": [receipt],
                        "private_manifest_path": str(manifest_path),
                        "manifest_apply_journal_path": str(manifest_journal_path),
                        "tutor_index_path": str(index_path),
                        "tutor_index_journal_path": str(index_journal_path),
                        "ledger_path": str(help_ledger_path),
                        "notebook": notebook_fixture(),
                        "cell_index": 1,
                        "cell_id": "cell-list-check",
                        "cell_type": "code",
                        "student_reflection": "Ich pruefe zuerst die erwartete Laenge selbst.",
                        "operator_confirmed_exam_workspace_run": True,
                        "operator_confirmed_manifest_apply": True,
                        "operator_confirmed_tutor_index_build": True,
                        "operator_confirmed_help_ledger_append": True,
                        "operator_confirmed_exam_ledger_append": True,
                        "requested_help_level": "A2",
                        "study_receipt": {
                            "prediction_present": True,
                            "notebook_action_present": True,
                            "reflection_present": True,
                        },
                    },
                )
            finally:
                exam_mode.EXAM_ROOT = previous_exam_root
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(report["artifact_type"], "exam_workspace_run_dry_run")
            self.assertEqual(report["status"], "exam_workspace_ready_with_exam_ledger")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["session_summary"]["status"], "started")
            self.assertEqual(report["material_freeze_summary"]["status"], "frozen")
            self.assertEqual(report["notebook_checkpoint"]["run_status"], "kernel-unavailable")
            self.assertEqual(report["tutor_sidecar"]["status"], "allowed")
            self.assertEqual(report["tutor_sidecar"]["effective_help_level"], "A2")
            self.assertEqual(
                report["private_tutor_use_flow_summary"]["study_receipt_validation"]["status"],
                "ok_study_session_receipt",
            )
            self.assertTrue(report["exam_ledger_append_summary"]["ledger_written"])
            self.assertTrue(report["export_package_summary"]["not_cleared_receipt"])
            self.assertTrue(report["export_package_summary"]["human_reviewable_independence_evidence"])
            self.assertFalse(report["export_package_summary"]["raw_transcripts_included"])
            self.assertFalse(report["export_package_summary"]["automatic_grading_included"])
            self.assertFalse(report["export_package_summary"]["proctoring_included"])
            self.assertFalse(report["export_package_summary"]["ai_detection_included"])
            self.assertFalse(report["raw_query_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["raw_notebook_returned"])
            self.assertFalse(report["notebook_code_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(report["exam_clearance_claimed"])
            self.assertEqual(report["workspace_card_run_receipt_alignment"]["status"], "ready")
            self.assertTrue(report["workspace_card_run_receipt_alignment"]["workspace_card_run_receipt_gate_linked"])
            self.assertTrue(manifest_path.exists())
            self.assertTrue(index_path.exists())
            self.assertTrue(help_ledger_path.exists())
            self.assertTrue(runtime_root.exists())
            self.assertNotIn("Wie pruefe ich", payload)
            self.assertNotIn("values = [1, 2, 3]", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertNotIn("private exam workspace artifact ref", payload)
            self.assertEqual(scan_text(payload, "exam-workspace-ready")["status"], "pass")

    def test_exam_workspace_run_release_claim_alignment_links_review_board_claims(self) -> None:
        alignment = build_exam_workspace_run_release_claim_alignment()
        payload = json.dumps(alignment, ensure_ascii=False)

        self.assertEqual(
            alignment["schema_version"],
            "unibot-exam-workspace-run-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["run_status"], "exam_workspace_ready_with_exam_ledger")
        self.assertEqual(alignment["run_public_safety_status"], "pass")
        self.assertEqual(alignment["waiting_status"], "exam_workspace_waiting_for_tutor_flow")
        self.assertEqual(alignment["waiting_public_safety_status"], "pass")
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertEqual(alignment["session_status"], "started")
        self.assertEqual(alignment["material_freeze_status"], "frozen")
        self.assertTrue(alignment["notebook_hash_present"])
        self.assertTrue(alignment["notebook_work_hash_present"])
        self.assertEqual(alignment["tutor_status"], "allowed")
        self.assertEqual(alignment["effective_help_level"], "A2")
        self.assertGreaterEqual(alignment["source_anchor_count"], 1)
        self.assertEqual(alignment["workspace_card_status"], "python_exam_local_cycle_operator_workspace_card_ready")
        self.assertEqual(alignment["workspace_card_selected_skill_tag"], "boxplots")
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertEqual(alignment["private_tutor_use_flow_status"], "private_tutor_use_flow_ready_with_ledger")
        self.assertEqual(alignment["study_receipt_status"], "ok_study_session_receipt")
        self.assertEqual(alignment["general_help_ledger_status"], "stored")
        self.assertTrue(alignment["general_help_ledger_written"])
        self.assertEqual(alignment["exam_ledger_status"], "appended")
        self.assertTrue(alignment["exam_ledger_written"])
        self.assertEqual(alignment["export_status"], "ready_for_human_review_not_exam_clearance")
        self.assertTrue(alignment["export_not_cleared_receipt"])
        self.assertTrue(alignment["human_reviewable_independence_evidence"])
        self.assertEqual(alignment["waiting_session_status"], "dry_run_not_started")
        self.assertFalse(alignment["waiting_freeze_written"])
        self.assertFalse(alignment["waiting_exam_ledger_written"])
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("exam_workspace_run", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertIn("exam_workspace_launch", alignment["required_readiness_check_ids"])
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
        self.assertTrue(alignment["contracts"]["run_public_safe"])
        self.assertTrue(alignment["contracts"]["waiting_run_public_safe"])
        self.assertTrue(alignment["contracts"]["session_material_notebook_checkpoint_hash_only"])
        self.assertTrue(alignment["contracts"]["private_tutor_study_and_ledger_linked"])
        self.assertTrue(alignment["contracts"]["workspace_card_execution_gate_linked"])
        self.assertTrue(alignment["contracts"]["operator_confirmed_local_write_boundaries"])
        self.assertTrue(alignment["contracts"]["waiting_mode_no_writes_no_paths"])
        self.assertTrue(alignment["contracts"]["export_receipt_not_exam_clearance"])
        self.assertTrue(alignment["contracts"]["public_outputs_hide_private_data"])
        self.assertTrue(alignment["contracts"]["high_stakes_actions_not_started"])
        self.assertIn("raw query returned", alignment["blocked_claims"])
        self.assertIn("raw notebook code returned", alignment["blocked_claims"])
        self.assertIn("automatic grading", alignment["blocked_claims"])
        self.assertIn("proctoring", alignment["blocked_claims"])
        self.assertIn("KI-detection evidence", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])
        self.assertIn("exam clearance", alignment["blocked_claims"])
        self.assertEqual(scan_text(payload, "exam-workspace-run-alignment")["status"], "pass")

    def test_exam_workspace_run_workspace_card_receipt_alignment_links_hashes_and_receipts(self) -> None:
        alignment = build_exam_workspace_run_workspace_card_receipt_alignment()
        payload = json.dumps(alignment, ensure_ascii=False)

        self.assertEqual(
            alignment["schema_version"],
            "unibot-exam-workspace-run-workspace-card-run-receipt-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["run_public_safety_status"], "pass")
        self.assertEqual(alignment["waiting_public_safety_status"], "pass")
        self.assertEqual(alignment["run_status"], "exam_workspace_ready_with_exam_ledger")
        self.assertEqual(alignment["waiting_status"], "exam_workspace_waiting_for_tutor_flow")
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertTrue(alignment["run_hash"])
        self.assertTrue(alignment["run_receipt_hash"])
        self.assertTrue(alignment["waiting_run_receipt_hash"])
        self.assertTrue(alignment["notebook_work_hash_present"])
        self.assertEqual(alignment["study_receipt_status"], "ok_study_session_receipt")
        self.assertEqual(alignment["tutor_status"], "allowed")
        self.assertEqual(alignment["effective_help_level"], "A2")
        self.assertEqual(alignment["general_help_ledger_status"], "stored")
        self.assertTrue(alignment["general_help_ledger_written"])
        self.assertEqual(alignment["exam_ledger_status"], "appended")
        self.assertTrue(alignment["exam_ledger_written"])
        self.assertEqual(alignment["export_status"], "ready_for_human_review_not_exam_clearance")
        self.assertTrue(alignment["export_not_cleared_receipt"])
        self.assertTrue(alignment["human_reviewable_independence_evidence"])
        self.assertEqual(alignment["waiting_session_status"], "dry_run_not_started")
        self.assertFalse(alignment["waiting_freeze_written"])
        self.assertFalse(alignment["waiting_exam_ledger_written"])
        self.assertEqual(alignment["workspace_card_status"], "python_exam_local_cycle_operator_workspace_card_ready")
        self.assertEqual(alignment["workspace_card_selected_skill_tag"], "boxplots")
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertTrue(alignment["workspace_card_run_receipt_gate_linked"])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("exam_workspace_run", alignment["required_readiness_check_ids"])
        self.assertIn("exam_workspace_launch", alignment["required_readiness_check_ids"])
        self.assertIn("notebook_checkpoint", alignment["required_readiness_check_ids"])
        self.assertIn("study_session", alignment["required_readiness_check_ids"])
        self.assertIn("private_tutor_use_flow", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertTrue(alignment["contracts"]["run_ready_with_receipts"])
        self.assertTrue(alignment["contracts"]["private_tutor_study_ledger_references_preserved"])
        self.assertTrue(alignment["contracts"]["notebook_checkpoint_hash_only_preserved"])
        self.assertTrue(alignment["contracts"]["run_receipt_hashes_present"])
        self.assertTrue(alignment["contracts"]["workspace_card_run_receipt_gate_linked"])
        self.assertTrue(alignment["contracts"]["operator_confirmed_local_write_boundary_preserved"])
        self.assertTrue(alignment["contracts"]["waiting_mode_no_write_boundary_preserved"])
        self.assertTrue(alignment["contracts"]["metadata_only_safety_flags_false"])
        self.assertTrue(alignment["contracts"]["high_stakes_boundaries_blocked"])
        self.assertIn("raw notebook code returned", alignment["blocked_claims"])
        self.assertIn("raw query returned", alignment["blocked_claims"])
        self.assertIn("provider call", alignment["blocked_claims"])
        self.assertIn("autonomous publication", alignment["blocked_claims"])
        self.assertIn("exam-clearance claim", alignment["blocked_claims"])
        self.assertEqual(scan_text(payload, "exam-workspace-run-receipt-alignment")["status"], "pass")

    def test_exam_workspace_run_workspace_card_receipt_alignment_blocks_broken_run_receipt(self) -> None:
        broken_run = {
            "status": "exam_workspace_ready_with_exam_ledger",
            "public_safety_status": "pass",
            "exam_deployment_status": "cleared",
            "operator_confirmations": {
                "exam_workspace_run": False,
                "manifest_apply": False,
                "tutor_index_build": False,
                "help_ledger_append": False,
                "exam_ledger_append": False,
            },
            "notebook_checkpoint": {
                "notebook_sha256": "",
                "cell_source_sha256": "",
                "notebook_work_sha256": "",
                "raw_notebook_returned": True,
                "notebook_code_returned": True,
                "local_path_returned": True,
            },
            "tutor_sidecar": {"status": "allowed", "effective_help_level": "A6", "selected_skill": {"skill_tag": ""}},
            "private_tutor_use_flow_summary": {
                "status": "private_tutor_use_flow_ready_with_ledger",
                "study_receipt_validation": {"status": "missing_study_session_receipt"},
                "ledger_append": {"status": "stored", "ledger_written": False, "event_hash": "", "path_returned": True},
            },
            "exam_ledger_append_summary": {
                "status": "appended",
                "ledger_written": False,
                "event_hash": "",
                "path_returned": True,
            },
            "export_package_summary": {
                "status": "ready_for_exam_deployment",
                "not_cleared_receipt": False,
                "human_reviewable_independence_evidence": False,
            },
            "raw_query_returned": True,
            "raw_text_returned": False,
            "raw_notebook_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
            "private_manifest_path_returned": False,
            "tutor_index_path_returned": False,
            "ledger_path_returned": False,
            "automatic_grading_started": True,
            "proctoring_started": False,
            "ai_detection_started": False,
            "exam_clearance_claimed": True,
        }
        waiting_report = {
            "status": "exam_workspace_waiting_for_tutor_flow",
            "public_safety_status": "pass",
            "session_summary": {"status": "started"},
            "material_freeze_summary": {"freeze_written": True},
            "exam_ledger_append_summary": {"ledger_written": True},
            "local_paths_returned": True,
        }
        broken_card = {
            "status": "python_exam_local_cycle_operator_workspace_card_ready",
            "not_cleared_receipt": True,
            "workspace_card_summary": {
                "selected_skill_tag": "wrong-skill",
                "ready_for_operator_prefill": True,
                "help_ledger_preview_status": "help_ledger_preview_ready",
                "task_hash": "",
                "help_ledger_preview_hash": "1" * 64,
            },
        }

        alignment = build_exam_workspace_run_workspace_card_receipt_alignment(
            broken_run,
            waiting_report,
            broken_card,
        )

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("run_ready_with_receipts", alignment["failed_contract_ids"])
        self.assertIn("private_tutor_study_ledger_references_preserved", alignment["failed_contract_ids"])
        self.assertIn("notebook_checkpoint_hash_only_preserved", alignment["failed_contract_ids"])
        self.assertIn("workspace_card_run_receipt_gate_linked", alignment["failed_contract_ids"])
        self.assertIn("operator_confirmed_local_write_boundary_preserved", alignment["failed_contract_ids"])
        self.assertIn("waiting_mode_no_write_boundary_preserved", alignment["failed_contract_ids"])
        self.assertIn("metadata_only_safety_flags_false", alignment["failed_contract_ids"])
        self.assertIn("high_stakes_boundaries_blocked", alignment["failed_contract_ids"])
        self.assertNotEqual(alignment["run_hash"], exam_workspace_run_hash({}))
        self.assertNotEqual(alignment["run_receipt_hash"], exam_workspace_run_receipt_hash({}))

    def test_exam_workspace_run_release_claim_alignment_blocks_overstated_run_claims(self) -> None:
        unsafe_run_report = {
            "status": "exam_workspace_ready_with_exam_ledger",
            "public_safety_status": "pass",
            "exam_deployment_status": "cleared",
            "execution_boundary": "Controlled run.",
            "operator_confirmations": {
                "exam_workspace_run": False,
                "manifest_apply": False,
                "tutor_index_build": False,
                "help_ledger_append": False,
                "exam_ledger_append": False,
            },
            "session_summary": {"status": "started", "session_id_returned": True},
            "material_freeze_summary": {"status": "frozen", "raw_text_returned": True, "local_path_returned": True},
            "notebook_checkpoint": {
                "notebook_sha256": "",
                "cell_source_sha256": "",
                "notebook_work_sha256": "",
                "raw_notebook_returned": True,
                "notebook_code_returned": True,
                "local_path_returned": True,
            },
            "tutor_sidecar": {"status": "allowed", "effective_help_level": "A6", "source_anchor_count": 0},
            "private_tutor_use_flow_summary": {
                "status": "private_tutor_use_flow_ready_with_ledger",
                "ledger_append": {"ledger_written": False, "path_returned": True},
                "study_receipt_validation": {"status": "missing_study_session_receipt"},
            },
            "cell_evidence_link": {
                "study_receipt_status": "missing_study_session_receipt",
                "eigenleistung_percentage_claimed": True,
            },
            "exam_ledger_append_summary": {"ledger_written": False, "path_returned": True},
            "export_package_summary": {
                "status": "ready_for_exam_deployment",
                "not_cleared_receipt": False,
                "human_reviewable_independence_evidence": False,
                "raw_transcripts_included": True,
                "automatic_grading_included": True,
                "proctoring_included": True,
                "ai_detection_included": True,
                "local_path_returned": True,
            },
            "raw_query_returned": True,
            "raw_text_returned": True,
            "raw_notebook_returned": True,
            "notebook_code_returned": True,
            "local_paths_returned": True,
            "automatic_grading_started": True,
            "proctoring_started": True,
            "ai_detection_started": True,
            "exam_clearance_claimed": True,
        }
        waiting_report = {
            "status": "exam_workspace_waiting_for_tutor_flow",
            "public_safety_status": "pass",
            "session_summary": {"status": "dry_run_not_started"},
            "material_freeze_summary": {"freeze_written": False},
            "exam_ledger_append_summary": {"ledger_written": False},
            "local_paths_returned": False,
        }

        alignment = build_exam_workspace_run_release_claim_alignment(
            run_report=unsafe_run_report,
            waiting_report=waiting_report,
        )

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("session_material_notebook_checkpoint_hash_only", alignment["failed_contract_ids"])
        self.assertIn("private_tutor_study_and_ledger_linked", alignment["failed_contract_ids"])
        self.assertIn("workspace_card_execution_gate_linked", alignment["failed_contract_ids"])
        self.assertIn("operator_confirmed_local_write_boundaries", alignment["failed_contract_ids"])
        self.assertIn("export_receipt_not_exam_clearance", alignment["failed_contract_ids"])
        self.assertIn("public_outputs_hide_private_data", alignment["failed_contract_ids"])
        self.assertIn("high_stakes_actions_not_started", alignment["failed_contract_ids"])


if __name__ == "__main__":
    unittest.main()
