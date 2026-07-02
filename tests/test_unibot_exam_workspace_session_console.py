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


if __name__ == "__main__":
    unittest.main()
