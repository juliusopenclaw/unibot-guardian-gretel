from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.exam_workspace_run_history import (  # noqa: E402
    build_exam_workspace_run_history_export_review,
    build_exam_workspace_run_history_release_claim_alignment,
    build_exam_workspace_run_history_workspace_card_receipt_alignment,
    exam_workspace_run_history_hash,
    exam_workspace_run_history_receipt_hash,
)
from unibot.exam_workspace_session_console import build_exam_workspace_session_console  # noqa: E402
from unibot.materials import build_material_manifest, sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402
from unibot.python_exam_local_cycle_operator_workspace_card import build_python_exam_local_cycle_operator_workspace_card  # noqa: E402
from unibot.python_exam_local_cycle_readiness_handoff import build_python_exam_local_cycle_readiness_handoff  # noqa: E402
from unibot.python_exam_local_cycle_readiness_review import build_python_exam_local_cycle_readiness_review  # noqa: E402
from unibot.python_exam_local_cycle_start_packet import build_python_exam_local_cycle_start_packet  # noqa: E402
from unibot.python_exam_operator_gate_decision_receipt import build_python_exam_operator_gate_decision_receipt  # noqa: E402
from unibot.python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate  # noqa: E402
from unibot.tutor_index import build_private_tutor_index_dry_run  # noqa: E402

from tests.test_unibot_python_exam_local_cycle_start_packet import ready_start_packet_inputs  # noqa: E402


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
        "retention_decision": "delete private extraction artifacts after reviewed metadata is accepted",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic history review decision",
    }


class UniBotExamWorkspaceRunHistoryTests(unittest.TestCase):
    def test_history_export_review_aggregates_console_reports_without_raw_data(self) -> None:
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
            first = build_exam_workspace_session_console(
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
            second = build_exam_workspace_session_console(
                base_path=str(root),
                review_policy="local_private_tutor",
                decision_record=valid_decision(),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                selected_skill_tag="python_lists",
                cell_source="own_checkpoint = ['next']\n",
                repeat_run_index=2,
                previous_console_receipts=[first["session_console_receipt"]],
                study_receipt={
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
                public_safe=True,
            )

            status, review = route_request(
                "/api/unibot/exam-workspace/run-history-export-review",
                {
                    "console_reports": [first, second],
                    "console_receipts": [first["session_console_receipt"]],
                    "build_current_console": False,
                },
            )
            payload = json.dumps(review, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(review["artifact_type"], "exam_workspace_run_history_export_review")
            self.assertEqual(review["status"], "exam_workspace_run_history_export_review_ready")
            self.assertEqual(review["exam_deployment_status"], "not_cleared")
            self.assertEqual(review["public_safety_status"], "pass")
            self.assertGreaterEqual(review["history_summary"]["run_count"], 2)
            self.assertIn("python_lists", review["history_summary"]["skill_tags"])
            self.assertGreaterEqual(review["history_summary"]["checkpoint_hash_count"], 2)
            self.assertEqual(review["history_summary"]["help_level_profile"]["A2"], 2)
            self.assertIn("operator_confirmations_open", review["history_summary"]["blocker_profile"])
            self.assertEqual(review["export_review_package"]["status"], "export_review_ready")
            self.assertTrue(review["export_review_package"]["human_reviewable_independence_evidence"])
            self.assertIn("reflection_evidence_present", review["export_review_package"]["review_items"]["reflection_statuses"])
            self.assertEqual(review["export_review_receipt"]["status"], "export_review_receipt_ready_not_exam_clearance")
            self.assertTrue(review["export_review_receipt"]["not_cleared_receipt"])
            self.assertFalse(review["raw_query_returned"])
            self.assertFalse(review["raw_cell_returned"])
            self.assertFalse(review["raw_text_returned"])
            self.assertFalse(review["raw_notebook_returned"])
            self.assertFalse(review["notebook_code_returned"])
            self.assertFalse(review["local_paths_returned"])
            self.assertFalse(review["automatic_grading_started"])
            self.assertFalse(review["proctoring_started"])
            self.assertFalse(review["ai_detection_started"])
            self.assertFalse(review["exam_clearance_claimed"])
            self.assertNotIn("own_checkpoint", payload)
            self.assertNotIn("Week 01 Python", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "run-history-export-review")["status"], "pass")

    def test_history_export_review_can_build_current_console_when_no_history_exists(self) -> None:
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

            review = build_exam_workspace_run_history_export_review(
                base_path=str(root),
                review_policy="local_private_tutor",
                decision_record=valid_decision(),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                selected_skill_tag="python_lists",
                cell_source="own_checkpoint = []\n",
                build_current_console=True,
                study_receipt={
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
                public_safe=True,
            )

            self.assertEqual(review["status"], "exam_workspace_run_history_export_review_ready")
            self.assertEqual(review["history_summary"]["run_count"], 1)
            self.assertEqual(review["run_history"][0]["skill_tag"], "python_lists")
            self.assertFalse(review["export_review_package"]["raw_query_returned"])
            self.assertFalse(review["export_review_receipt"]["local_paths_returned"])

    def test_history_export_review_tracks_local_cycle_workspace_card_when_present(self) -> None:
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
            with tempfile.TemporaryDirectory() as packet_temp_dir:
                console, _gate, _decision = ready_start_packet_inputs(packet_temp_dir)
                confirmed_gate = build_python_exam_safe_cycle_operator_gate(
                    python_exam_safe_cycle_console=console,
                    selected_skill_tag="python_lists",
                )
                confirmed_ids = [card["step_id"] for card in confirmed_gate["confirmation_cards"]]
                decision = build_python_exam_operator_gate_decision_receipt(
                    python_exam_safe_cycle_operator_gate=confirmed_gate,
                    confirmed_step_ids=confirmed_ids,
                    selected_skill_tag="python_lists",
                )
                start_packet = build_python_exam_local_cycle_start_packet(
                    python_exam_safe_cycle_console=console,
                    python_exam_safe_cycle_operator_gate=confirmed_gate,
                    python_exam_operator_gate_decision_receipt=decision,
                    selected_skill_tag="python_lists",
                )
                review = build_python_exam_local_cycle_readiness_review(
                    python_exam_local_cycle_start_packet=start_packet,
                    selected_skill_tag="python_lists",
                )
                handoff = build_python_exam_local_cycle_readiness_handoff(
                    python_exam_local_cycle_readiness_review=review,
                    python_exam_local_cycle_start_packet=start_packet,
                    selected_skill_tag="python_lists",
                )
                workspace_card = build_python_exam_local_cycle_operator_workspace_card(
                    python_exam_local_cycle_readiness_review=review,
                    python_exam_local_cycle_readiness_handoff=handoff,
                    python_exam_local_cycle_start_packet=start_packet,
                    selected_skill_tag="python_lists",
                )
                console_report = build_exam_workspace_session_console(
                    base_path=str(root),
                    review_policy="local_private_tutor",
                    decision_record=valid_decision(),
                    private_manifest_path=manifest_path,
                    tutor_index_path=index_path,
                    selected_skill_tag="python_lists",
                    cell_source="own_checkpoint = []\n",
                    python_exam_local_cycle_operator_workspace_card=workspace_card,
                    study_receipt={
                        "prediction_present": True,
                        "notebook_action_present": True,
                        "reflection_present": True,
                    },
                    public_safe=True,
                )
                review_report = build_exam_workspace_run_history_export_review(
                    console_reports=[console_report],
                    console_receipts=[console_report["session_console_receipt"]],
                    build_current_console=False,
                    public_safe=True,
                )

                self.assertTrue(review_report["history_summary"]["workspace_card_profile"])
                self.assertTrue(review_report["export_review_package"]["review_items"]["workspace_card_profile"])
                self.assertTrue(review_report["run_history"][0]["local_cycle_operator_workspace_card"])

    def test_history_release_claim_alignment_links_review_board_claims(self) -> None:
        alignment = build_exam_workspace_run_history_release_claim_alignment()
        payload = json.dumps(alignment, ensure_ascii=False)

        self.assertEqual(
            alignment["schema_version"],
            "unibot-exam-workspace-run-history-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["history_status"], "exam_workspace_run_history_export_review_ready")
        self.assertEqual(alignment["history_public_safety_status"], "pass")
        self.assertEqual(alignment["waiting_status"], "exam_workspace_run_history_waiting_for_session_history")
        self.assertEqual(alignment["waiting_public_safety_status"], "pass")
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertGreaterEqual(alignment["run_count"], 2)
        self.assertGreaterEqual(alignment["checkpoint_hash_count"], 2)
        self.assertIn("python_lists", alignment["skill_tags"])
        self.assertEqual(alignment["help_level_profile"]["A2"], 2)
        self.assertIn("operator_confirmations_open", alignment["blocker_profile"])
        self.assertGreaterEqual(alignment["open_operator_step_count"], 1)
        self.assertIn("python_exam_local_cycle_operator_workspace_card_ready", alignment["workspace_card_profile"])
        self.assertEqual(alignment["workspace_card_ready_entry_count"], 2)
        self.assertEqual(alignment["workspace_card_help_ledger_hash_count"], 2)
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertEqual(alignment["export_review_status"], "export_review_ready")
        self.assertTrue(alignment["human_reviewable_independence_evidence"])
        self.assertTrue(alignment["reflection_evidence_present"])
        self.assertEqual(alignment["export_receipt_status"], "export_review_receipt_ready_not_exam_clearance")
        self.assertTrue(alignment["export_receipt_not_cleared"])
        self.assertEqual(alignment["waiting_run_count"], 0)
        self.assertEqual(alignment["waiting_export_status"], "export_review_waiting_for_session_history")
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("exam_workspace_run_history", alignment["required_readiness_check_ids"])
        self.assertIn("exam_workspace_run", alignment["required_readiness_check_ids"])
        self.assertIn("exam_workspace_launch", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertIn("study_session", alignment["required_readiness_check_ids"])
        self.assertIn("review_board_packet", alignment["required_readiness_check_ids"])
        self.assertIn("external_decision_state", alignment["required_readiness_check_ids"])
        self.assertIn("evaluation_packet", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertTrue(alignment["contracts"]["history_public_safe"])
        self.assertTrue(alignment["contracts"]["waiting_history_public_safe"])
        self.assertTrue(alignment["contracts"]["run_history_hash_only_ready"])
        self.assertTrue(alignment["contracts"]["operator_reflection_and_blockers_preserved"])
        self.assertTrue(alignment["contracts"]["workspace_card_review_gate_linked"])
        self.assertTrue(alignment["contracts"]["export_review_package_human_reviewable"])
        self.assertTrue(alignment["contracts"]["export_review_receipt_not_exam_clearance"])
        self.assertTrue(alignment["contracts"]["waiting_history_has_no_reviewable_export"])
        self.assertTrue(alignment["contracts"]["public_outputs_hide_private_history_data"])
        self.assertTrue(alignment["contracts"]["high_stakes_actions_not_started"])
        self.assertIn("raw history returned", alignment["blocked_claims"])
        self.assertIn("raw notebook code returned", alignment["blocked_claims"])
        self.assertIn("automatic grading", alignment["blocked_claims"])
        self.assertIn("proctoring", alignment["blocked_claims"])
        self.assertIn("KI-detection evidence", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])
        self.assertIn("exam clearance", alignment["blocked_claims"])
        self.assertEqual(scan_text(payload, "run-history-alignment")["status"], "pass")

    def test_history_release_claim_alignment_blocks_overstated_history_claims(self) -> None:
        unsafe_history = {
            "status": "exam_workspace_run_history_export_review_ready",
            "public_safety_status": "pass",
            "exam_deployment_status": "cleared",
            "execution_boundary": "History export.",
            "run_history": [
                {
                    "raw_query_returned": True,
                    "raw_text_returned": True,
                    "raw_cell_returned": True,
                    "notebook_code_returned": True,
                    "local_paths_returned": True,
                }
            ],
            "history_summary": {
                "run_count": 1,
                "checkpoint_hash_count": 0,
                "raw_history_returned": True,
                "blocker_profile": {},
                "workspace_card_profile": {},
                "open_operator_step_count": 0,
            },
            "export_review_package": {
                "status": "ready_for_exam_deployment",
                "human_reviewable_independence_evidence": False,
                "review_items": {"reflection_statuses": [], "export_receipts": [{"not_cleared_receipt": False}]},
                "raw_query_returned": True,
                "raw_text_returned": True,
                "raw_cell_returned": True,
                "notebook_code_returned": True,
                "local_paths_returned": True,
                "automatic_grading_started": True,
            },
            "export_review_receipt": {
                "status": "exam_clearance_ready",
                "exam_deployment_status": "cleared",
                "not_cleared_receipt": False,
                "run_count": 1,
                "raw_query_returned": True,
                "raw_text_returned": True,
                "raw_cell_returned": True,
                "notebook_code_returned": True,
                "local_paths_returned": True,
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
        waiting = {
            "status": "exam_workspace_run_history_waiting_for_session_history",
            "public_safety_status": "pass",
            "history_summary": {"run_count": 0},
            "export_review_package": {
                "status": "export_review_waiting_for_session_history",
                "human_reviewable_independence_evidence": False,
            },
            "export_review_receipt": {"run_count": 0},
        }

        alignment = build_exam_workspace_run_history_release_claim_alignment(
            history_report=unsafe_history,
            waiting_report=waiting,
        )

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("run_history_hash_only_ready", alignment["failed_contract_ids"])
        self.assertIn("operator_reflection_and_blockers_preserved", alignment["failed_contract_ids"])
        self.assertIn("workspace_card_review_gate_linked", alignment["failed_contract_ids"])
        self.assertIn("export_review_package_human_reviewable", alignment["failed_contract_ids"])
        self.assertIn("export_review_receipt_not_exam_clearance", alignment["failed_contract_ids"])
        self.assertIn("public_outputs_hide_private_history_data", alignment["failed_contract_ids"])
        self.assertIn("high_stakes_actions_not_started", alignment["failed_contract_ids"])

    def test_history_workspace_card_receipt_alignment_links_hashes_and_receipts(self) -> None:
        alignment = build_exam_workspace_run_history_workspace_card_receipt_alignment()
        payload = json.dumps(alignment, ensure_ascii=False)

        self.assertEqual(
            alignment["schema_version"],
            "unibot-exam-workspace-run-history-workspace-card-history-receipt-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["history_public_safety_status"], "pass")
        self.assertEqual(alignment["waiting_public_safety_status"], "pass")
        self.assertEqual(alignment["history_status"], "exam_workspace_run_history_export_review_ready")
        self.assertEqual(alignment["waiting_status"], "exam_workspace_run_history_waiting_for_session_history")
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertTrue(alignment["history_hash"])
        self.assertTrue(alignment["history_receipt_hash"])
        self.assertTrue(alignment["waiting_history_receipt_hash"])
        self.assertGreaterEqual(alignment["run_count"], 2)
        self.assertGreaterEqual(alignment["session_console_receipt_count"], 2)
        self.assertGreaterEqual(alignment["hash_only_receipt_count"], 1)
        self.assertGreaterEqual(alignment["checkpoint_hash_count"], 2)
        self.assertEqual(alignment["help_level_profile"]["A2"], 2)
        self.assertTrue(alignment["reflection_evidence_present"])
        self.assertEqual(alignment["export_review_status"], "export_review_ready")
        self.assertEqual(alignment["export_receipt_status"], "export_review_receipt_ready_not_exam_clearance")
        self.assertTrue(alignment["export_receipt_not_cleared"])
        self.assertGreaterEqual(alignment["open_operator_step_count"], 1)
        self.assertEqual(alignment["waiting_run_count"], 0)
        self.assertEqual(alignment["waiting_export_status"], "export_review_waiting_for_session_history")
        self.assertEqual(alignment["workspace_card_status"], "python_exam_local_cycle_operator_workspace_card_ready")
        self.assertEqual(alignment["workspace_card_selected_skill_tag"], "python_lists")
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertTrue(alignment["workspace_card_history_receipt_gate_linked"])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("exam_workspace_run_history", alignment["required_readiness_check_ids"])
        self.assertIn("exam_workspace_run", alignment["required_readiness_check_ids"])
        self.assertIn("exam_workspace_session_console", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertIn("review_chain_integrity", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertTrue(alignment["contracts"]["history_export_review_ready"])
        self.assertTrue(alignment["contracts"]["session_console_receipts_preserved"])
        self.assertTrue(alignment["contracts"]["checkpoint_hashes_and_help_profile_preserved"])
        self.assertTrue(alignment["contracts"]["reflection_review_status_preserved"])
        self.assertTrue(alignment["contracts"]["export_receipt_reference_preserved"])
        self.assertTrue(alignment["contracts"]["operator_confirmation_boundary_preserved"])
        self.assertTrue(alignment["contracts"]["workspace_card_history_receipt_gate_linked"])
        self.assertTrue(alignment["contracts"]["history_receipt_hashes_present"])
        self.assertTrue(alignment["contracts"]["waiting_mode_no_reviewable_export"])
        self.assertTrue(alignment["contracts"]["metadata_only_safety_flags_false"])
        self.assertTrue(alignment["contracts"]["high_stakes_boundaries_blocked"])
        self.assertIn("raw history returned", alignment["blocked_claims"])
        self.assertIn("contact data publication", alignment["blocked_claims"])
        self.assertIn("provider call", alignment["blocked_claims"])
        self.assertIn("autonomous publication", alignment["blocked_claims"])
        self.assertIn("exam-clearance claim", alignment["blocked_claims"])
        self.assertIn("grading", alignment["blocked_claims"])
        self.assertIn("KI-detection evidence", alignment["blocked_claims"])
        self.assertEqual(scan_text(payload, "run-history-receipt-alignment")["status"], "pass")

    def test_history_workspace_card_receipt_alignment_blocks_broken_history_receipt(self) -> None:
        broken_history = {
            "status": "exam_workspace_run_history_export_review_ready",
            "public_safety_status": "pass",
            "exam_deployment_status": "cleared",
            "history_summary": {
                "run_count": 1,
                "checkpoint_hash_count": 0,
                "checkpoint_hashes": [],
                "help_level_profile": {"A2": 0},
                "blocker_profile": {},
                "workspace_card_profile": {},
                "open_operator_step_count": 0,
            },
            "run_history": [
                {
                    "entry_type": "session_console_report",
                    "receipt_id": "",
                    "receipt_hash": "",
                    "checkpoint_hash": "",
                    "skill_tag": "python_lists",
                    "reflection_status": "",
                    "operator_confirmations": {"local_writes_requested": False},
                    "local_cycle_operator_workspace_card": {
                        "status": "python_exam_local_cycle_operator_workspace_card_ready",
                        "selected_skill_tag": "wrong-skill",
                        "ready_for_operator_prefill": True,
                        "help_ledger_preview_status": "help_ledger_preview_ready",
                        "help_ledger_preview_hash": "1" * 64,
                        "task_hash": "",
                        "not_cleared_receipt": True,
                        "exam_deployment_status": "not_cleared",
                    },
                    "raw_query_returned": True,
                    "raw_text_returned": True,
                    "raw_cell_returned": True,
                    "notebook_code_returned": True,
                    "local_paths_returned": True,
                }
            ],
            "export_review_package": {
                "status": "ready_for_exam_deployment",
                "human_reviewable_independence_evidence": False,
                "review_items": {"reflection_statuses": [], "export_receipts": [{"not_cleared_receipt": False}]},
                "raw_query_returned": True,
                "raw_text_returned": True,
                "raw_cell_returned": True,
                "notebook_code_returned": True,
                "local_paths_returned": True,
                "automatic_grading_started": True,
            },
            "export_review_receipt": {
                "status": "exam_clearance_ready",
                "receipt_hash": "",
                "not_cleared_receipt": False,
                "run_count": 2,
            },
            "raw_query_returned": True,
            "raw_text_returned": False,
            "raw_cell_returned": False,
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
        waiting = {
            "status": "exam_workspace_run_history_waiting_for_session_history",
            "public_safety_status": "pass",
            "history_summary": {"run_count": 1},
            "export_review_package": {"status": "export_review_ready"},
            "export_review_receipt": {"run_count": 1},
        }

        alignment = build_exam_workspace_run_history_workspace_card_receipt_alignment(
            broken_history,
            waiting,
        )

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("history_export_review_ready", alignment["failed_contract_ids"])
        self.assertIn("session_console_receipts_preserved", alignment["failed_contract_ids"])
        self.assertIn("checkpoint_hashes_and_help_profile_preserved", alignment["failed_contract_ids"])
        self.assertIn("reflection_review_status_preserved", alignment["failed_contract_ids"])
        self.assertIn("export_receipt_reference_preserved", alignment["failed_contract_ids"])
        self.assertIn("operator_confirmation_boundary_preserved", alignment["failed_contract_ids"])
        self.assertIn("workspace_card_history_receipt_gate_linked", alignment["failed_contract_ids"])
        self.assertIn("waiting_mode_no_reviewable_export", alignment["failed_contract_ids"])
        self.assertIn("metadata_only_safety_flags_false", alignment["failed_contract_ids"])
        self.assertIn("high_stakes_boundaries_blocked", alignment["failed_contract_ids"])
        self.assertNotEqual(alignment["history_hash"], exam_workspace_run_history_hash({}))
        self.assertNotEqual(alignment["history_receipt_hash"], exam_workspace_run_history_receipt_hash({}))


if __name__ == "__main__":
    unittest.main()
