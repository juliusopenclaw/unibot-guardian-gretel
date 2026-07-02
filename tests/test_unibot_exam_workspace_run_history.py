from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.exam_workspace_run_history import build_exam_workspace_run_history_export_review  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
