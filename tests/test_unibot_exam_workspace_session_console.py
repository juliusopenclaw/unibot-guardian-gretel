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

from unibot.exam_workspace_session_console import (  # noqa: E402
    build_exam_workspace_session_console,
    build_exam_workspace_session_console_release_claim_alignment,
)
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
        "decision_reference": "synthetic session console decision",
    }


class UniBotExamWorkspaceSessionConsoleTests(unittest.TestCase):
    def test_session_console_summarizes_ready_workspace_without_raw_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            course_id = f"session-console-{uuid.uuid4().hex[:10]}"
            self.addCleanup(lambda: shutil.rmtree(ROOT / "unibot" / "knowledge" / "exam_workspace" / course_id, ignore_errors=True))
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "private_tutor_index.json"
            index_journal_path = Path(temp_dir) / "index_journal.jsonl"
            help_ledger_path = Path(temp_dir) / "help_ledger.jsonl"
            checkpoint_journal_path = Path(temp_dir) / "checkpoints.jsonl"
            cell_source = "own_prediction = ['a', 'b']\n# local checkpoint only\n"
            write_ready_fixture(root)
            write_private_manifest(manifest_path, [reviewed_manifest_record()])
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                tutor_index_journal_path=index_journal_path,
                operator_confirmed_tutor_index_build=True,
            )

            status, report = route_request(
                "/api/unibot/exam-workspace/session-console",
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
                    "selected_skill_tag": "python_lists",
                    "focus_query": "python_lists",
                    "query": "private query must not be echoed",
                    "cell_source": cell_source,
                    "requested_help_level": "A2",
                    "student_reflection": "Ich pruefe den naechsten Schritt selbst.",
                    "study_receipt": {
                        "prediction_present": True,
                        "notebook_action_present": True,
                        "reflection_present": True,
                    },
                },
            )
            payload = json.dumps(report, ensure_ascii=False)
            console = report["session_console"]

            self.assertEqual(status, 200)
            self.assertEqual(report["artifact_type"], "exam_workspace_session_console")
            self.assertEqual(report["status"], "exam_workspace_session_console_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertEqual(console["title"], "Exam Workspace Session Console")
            self.assertEqual(console["status"], "ready_dry_run")
            self.assertEqual(console["selected_skill"]["skill_tag"], "python_lists")
            self.assertEqual(console["workspace_status"]["workspace_run_status"], "exam_workspace_dry_run_ready")
            self.assertEqual(console["notebook_checkpoint"]["status"], "notebook_checkpoint_ready")
            self.assertEqual(console["notebook_checkpoint"]["notebook_work_sha256"], sha256_text(cell_source))
            self.assertEqual(console["tutor_state"]["effective_help_level"], "A2")
            self.assertEqual(console["tutor_state"]["allowed_help_boundary"], "A0-A2")
            self.assertEqual(console["help_ledger_preview"]["help_level"], "A2")
            self.assertTrue(console["export_receipt"]["not_cleared_receipt"])
            self.assertTrue(console["operator_confirmations"]["open_steps"])
            self.assertEqual(console["repeat_dry_run"]["repeat_run_index"], 1)
            self.assertTrue(console["repeat_dry_run"]["supported"])
            self.assertEqual(report["session_console_receipt"]["status"], "session_console_receipt_ready_not_exam_clearance")
            self.assertTrue(report["session_console_receipt"]["supports_repeated_dry_runs"])
            self.assertIn("# Exam Workspace Session Console", report["session_console_markdown"])
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
            self.assertNotIn("private query", payload)
            self.assertNotIn("own_prediction", payload)
            self.assertNotIn("Week 01 Python", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "session-console-ready")["status"], "pass")

    def test_session_console_supports_repeated_dry_runs_with_hash_only_previous_receipt(self) -> None:
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
                cell_source="own_checkpoint = []\n",
                repeat_run_index=2,
                previous_console_receipts=[first["session_console_receipt"]],
                study_receipt={
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
                public_safe=True,
            )

            self.assertEqual(second["status"], "exam_workspace_session_console_ready")
            self.assertEqual(second["session_console"]["repeat_dry_run"]["repeat_run_index"], 2)
            self.assertEqual(second["session_console_receipt"]["previous_console_receipt_count"], 1)
            self.assertEqual(
                second["session_console_receipt"]["previous_console_receipt_hashes_returned"],
                [first["session_console_receipt"]["receipt_hash"]],
            )
            self.assertFalse(second["session_console_receipt"]["raw_text_returned"])
            self.assertFalse(second["session_console_receipt"]["local_paths_returned"])

    def test_session_console_includes_local_cycle_workspace_card_when_provided(self) -> None:
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

                status, report = route_request(
                    "/api/unibot/exam-workspace/session-console",
                    {
                        "course_id": "session-console-workspace-card",
                        "base_path": str(root),
                        "review_policy": "local_private_tutor",
                        "decision_record": valid_decision(),
                        "private_manifest_path": str(manifest_path),
                        "tutor_index_path": str(index_path),
                        "selected_skill_tag": "python_lists",
                        "focus_query": "python_lists",
                        "query": "python_lists",
                        "python_exam_local_cycle_operator_workspace_card": workspace_card,
                        "cell_source": "own_checkpoint = []\n",
                        "study_receipt": {
                            "prediction_present": True,
                            "notebook_action_present": True,
                            "reflection_present": True,
                        },
                        "public_safe": True,
                    },
                )

                self.assertEqual(status, 200)
                self.assertEqual(report["local_cycle_operator_workspace_card"]["status"], "python_exam_local_cycle_operator_workspace_card_ready")
                self.assertEqual(report["local_cycle_operator_workspace_card"]["help_ledger_preview_status"], "help_ledger_preview_ready")
                self.assertEqual(
                    report["local_cycle_operator_workspace_card"]["next_safe_action"],
                    review["readiness_review_summary"]["next_safe_action"],
                )
                self.assertIn("Local Cycle Workspace Card", report["session_console_markdown"])
                self.assertFalse(report["session_console_receipt"]["workspace_card_hash"] == "")

    def test_session_console_release_claim_alignment_links_review_board_claims(self) -> None:
        alignment = build_exam_workspace_session_console_release_claim_alignment()
        payload = json.dumps(alignment, ensure_ascii=False)

        self.assertEqual(
            alignment["schema_version"],
            "unibot-exam-workspace-session-console-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["console_status"], "exam_workspace_session_console_ready")
        self.assertEqual(alignment["console_public_safety_status"], "pass")
        self.assertEqual(alignment["repeat_status"], "exam_workspace_session_console_repeat_task_required")
        self.assertEqual(alignment["repeat_public_safety_status"], "pass")
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertEqual(alignment["session_console_status"], "ready_dry_run")
        self.assertEqual(alignment["selected_skill_tag"], "pandas")
        self.assertEqual(alignment["workspace_status"], "exam_workspace_dry_run_ready")
        self.assertEqual(alignment["operator_status"], "exam_workspace_operator_dry_run_ready")
        self.assertTrue(alignment["operator_receipt_id"])
        self.assertEqual(alignment["receipt_status"], "session_console_receipt_ready_not_exam_clearance")
        self.assertTrue(alignment["receipt_not_cleared"])
        self.assertTrue(alignment["receipt_hash_present"])
        self.assertEqual(alignment["checkpoint_status"], "notebook_checkpoint_ready")
        self.assertTrue(alignment["checkpoint_hash_present"])
        self.assertEqual(alignment["tutor_status"], "allowed")
        self.assertEqual(alignment["study_receipt_status"], "ok_study_session_receipt")
        self.assertEqual(alignment["help_ledger_preview_status"], "preview_ready")
        self.assertTrue(alignment["export_not_cleared_receipt"])
        self.assertEqual(alignment["confirmation_status"], "all_steps_dry_run")
        self.assertEqual(alignment["confirmed_count"], 0)
        self.assertEqual(alignment["write_step_count"], 6)
        self.assertFalse(alignment["local_writes_requested"])
        self.assertEqual(alignment["reflection_status"], "ok_study_session_receipt")
        self.assertEqual(alignment["workspace_card_status"], "python_exam_local_cycle_operator_workspace_card_ready")
        self.assertEqual(alignment["workspace_card_selected_skill_tag"], "pandas")
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertTrue(alignment["not_cleared_receipt"])
        self.assertEqual(alignment["repeat_checkpoint_status"], "notebook_checkpoint_repeat_task_required")
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("exam_workspace_session_console", alignment["required_readiness_check_ids"])
        self.assertIn("exam_workspace_operator_run", alignment["required_readiness_check_ids"])
        self.assertIn("exam_workspace_run_history", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertIn("review_board_packet", alignment["required_readiness_check_ids"])
        self.assertIn("study_session", alignment["required_readiness_check_ids"])
        self.assertIn("external_decision_state", alignment["required_readiness_check_ids"])
        self.assertIn("evaluation_packet", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertTrue(alignment["contracts"]["console_public_safe"])
        self.assertTrue(alignment["contracts"]["repeat_public_safe"])
        self.assertTrue(alignment["contracts"]["session_console_receipt_hash_only_ready"])
        self.assertTrue(alignment["contracts"]["operator_run_receipt_linked"])
        self.assertTrue(alignment["contracts"]["workspace_card_and_reflection_preserved"])
        self.assertTrue(alignment["contracts"]["workspace_card_readiness_gate_linked"])
        self.assertTrue(alignment["contracts"]["repeat_task_blocks_console_ready"])
        self.assertTrue(alignment["contracts"]["public_outputs_hide_private_console_data"])
        self.assertTrue(alignment["contracts"]["high_stakes_actions_not_started"])
        self.assertTrue(alignment["contracts"]["not_cleared_receipt_present"])
        self.assertIn("raw notebook code returned", alignment["blocked_claims"])
        self.assertIn("raw run history returned", alignment["blocked_claims"])
        self.assertIn("automatic grading", alignment["blocked_claims"])
        self.assertIn("proctoring", alignment["blocked_claims"])
        self.assertIn("KI-detection evidence", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])
        self.assertNotIn("synthetic private session-console question", payload)
        self.assertNotIn("own_groupby_checkpoint", payload)
        self.assertEqual(scan_text(payload, "session-console-alignment")["status"], "pass")

    def test_session_console_release_claim_alignment_flags_overstated_claims(self) -> None:
        unsafe_ready = {
            "status": "exam_workspace_session_console_ready",
            "public_safety_status": "pass",
            "exam_deployment_status": "cleared",
            "execution_boundary": "returns everything",
            "session_console_markdown": "# unsafe",
            "session_console": {
                "status": "ready_dry_run",
                "selected_skill": {"skill_tag": "pandas", "raw_source_text_returned": True},
                "workspace_status": {
                    "workspace_run_status": "exam_workspace_dry_run_ready",
                    "exam_deployment_status": "cleared",
                    "tutor_status": "allowed",
                },
                "notebook_checkpoint": {"status": "notebook_checkpoint_ready"},
                "tutor_state": {"study_receipt_status": "missing", "allowed_help_boundary": "A0-A2"},
                "help_ledger_preview": {"status": "written", "raw_help_text_returned": True},
                "export_receipt": {"not_cleared_receipt": False, "raw_export_returned": True},
                "operator_confirmations": {
                    "status": "operator_confirmations_present",
                    "confirmed_count": 2,
                    "write_step_count": 6,
                    "local_writes_requested": True,
                },
            },
            "session_console_receipt": {
                "status": "session_console_receipt_ready_not_exam_clearance",
                "receipt_hash": "",
                "operator_receipt_id": "",
                "not_cleared_receipt": False,
                "raw_query_returned": True,
                "raw_text_returned": True,
                "raw_cell_returned": True,
                "notebook_code_returned": True,
                "local_paths_returned": True,
            },
            "operator_summary": {
                "artifact_type": "exam_workspace_operator_run_dry_run",
                "status": "exam_workspace_operator_dry_run_ready",
                "receipt_id": "different",
                "not_cleared_receipt": False,
            },
            "local_cycle_operator_workspace_card": {"status": "missing"},
            "local_cycle_operator_workspace_card_source": {"artifact_type": "missing"},
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
            "status": "exam_workspace_session_console_ready",
            "public_safety_status": "pass",
            "session_console": {
                "status": "ready_dry_run",
                "notebook_checkpoint": {"status": "notebook_checkpoint_ready"},
            },
        }

        alignment = build_exam_workspace_session_console_release_claim_alignment(
            ready_report=unsafe_ready,
            repeat_report=repeat_report,
            workspace_card_report={"status": "missing"},
        )

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("session_console_receipt_hash_only_ready", alignment["failed_contract_ids"])
        self.assertIn("operator_run_receipt_linked", alignment["failed_contract_ids"])
        self.assertIn("workspace_card_and_reflection_preserved", alignment["failed_contract_ids"])
        self.assertIn("workspace_card_readiness_gate_linked", alignment["failed_contract_ids"])
        self.assertIn("repeat_task_blocks_console_ready", alignment["failed_contract_ids"])
        self.assertIn("public_outputs_hide_private_console_data", alignment["failed_contract_ids"])
        self.assertIn("high_stakes_actions_not_started", alignment["failed_contract_ids"])
        self.assertIn("not_cleared_receipt_present", alignment["failed_contract_ids"])


if __name__ == "__main__":
    unittest.main()
