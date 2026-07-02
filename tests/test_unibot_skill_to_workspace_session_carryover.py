from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from unibot.public_safety import scan_text
from unibot.server import route_request
from unibot.skill_to_workspace_live_flow import build_skill_to_workspace_live_flow
from unibot.skill_to_workspace_session_carryover import build_skill_to_workspace_session_carryover
from unibot.tutor_index import build_private_tutor_index_dry_run

from tests.test_unibot_exam_skill_drilldown import (
    reviewed_manifest_record,
    valid_decision,
    write_private_manifest,
    write_ready_fixture,
)


def ready_live_flow(temp_dir: str) -> dict:
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
    return build_skill_to_workspace_live_flow(
        base_path=str(root),
        review_policy="local_private_tutor",
        decision_record=valid_decision(),
        private_manifest_path=manifest_path,
        tutor_index_path=index_path,
        tutor_index_journal_path=index_journal_path,
        selected_skill_tag="python_lists",
        requested_help_level="A2",
        student_reflection="Ich pruefe zuerst meine eigene Vorhersage.",
        cell_source="own_attempt = []\n# private checkpoint only\n",
        study_receipt={
            "prediction_present": True,
            "notebook_action_present": True,
            "reflection_present": True,
        },
    )


class UniBotSkillToWorkspaceSessionCarryoverTests(unittest.TestCase):
    def test_carryover_links_live_flow_to_session_evidence_and_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            live_flow = ready_live_flow(temp_dir)
            report = build_skill_to_workspace_session_carryover(skill_to_workspace_live_flow=live_flow)
            summary = report["carryover_summary"]
            packet = report["carryover_packet"]
            artifacts = report["carryover_artifacts"]
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["artifact_type"], "skill_to_workspace_session_carryover")
            self.assertEqual(report["status"], "skill_to_workspace_session_carryover_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(summary["selected_skill_tag"], "python_lists")
            self.assertEqual(summary["session_status"], "exam_workspace_session_console_ready")
            self.assertEqual(summary["run_history_status"], "exam_workspace_run_history_export_review_ready")
            self.assertEqual(summary["evidence_preview_status"], "python_exam_evidence_export_preview_ready")
            self.assertEqual(summary["human_handoff_status"], "python_exam_human_handoff_packet_ready")
            self.assertTrue(summary["operator_receipt_id"])
            self.assertTrue(summary["session_receipt_id"])
            self.assertTrue(summary["checkpoint_hash_present"])
            self.assertEqual(summary["help_status"], "a0_a2_only")
            self.assertGreaterEqual(summary["source_card_count"], 1)
            self.assertGreaterEqual(summary["source_anchor_count"], 1)
            self.assertGreaterEqual(summary["open_operator_confirmation_count"], 1)
            self.assertFalse(summary["local_writes_requested"])
            self.assertEqual(packet["operator_receipt"]["receipt_id"], summary["operator_receipt_id"])
            self.assertEqual(packet["session_receipt"]["receipt_id"], summary["session_receipt_id"])
            self.assertEqual(packet["evidence_preview"]["status"], "python_exam_evidence_export_preview_ready")
            self.assertEqual(packet["human_handoff"]["status"], "python_exam_human_handoff_packet_ready")
            self.assertTrue(packet["human_handoff"]["markdown_hash"])
            self.assertEqual(artifacts["session_console"]["artifact_type"], "exam_workspace_session_console")
            self.assertEqual(artifacts["run_history_export_review"]["artifact_type"], "exam_workspace_run_history_export_review")
            self.assertEqual(artifacts["python_exam_evidence_export_preview"]["artifact_type"], "python_exam_evidence_export_preview")
            self.assertEqual(artifacts["python_exam_human_handoff_packet"]["artifact_type"], "python_exam_human_handoff_packet")
            self.assertTrue(report["dry_run_default"])
            self.assertFalse(report["raw_query_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["raw_cell_returned"])
            self.assertFalse(report["raw_notebook_returned"])
            self.assertFalse(report["notebook_code_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(report["values_returned"])
            self.assertFalse(report["solutions_returned"])
            self.assertFalse(report["final_interpretations_returned"])
            self.assertFalse(report["automatic_grading_started"])
            self.assertFalse(report["proctoring_started"])
            self.assertFalse(report["ai_detection_started"])
            self.assertFalse(report["exam_clearance_claimed"])
            self.assertNotIn("own_attempt", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "skill-to-workspace-session-carryover")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_carryover_api_can_build_live_flow_when_not_supplied(self) -> None:
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
                "/api/unibot/course/skill-to-workspace-session-carryover",
                {
                    "base_path": str(root),
                    "review_policy": "local_private_tutor",
                    "decision_record": valid_decision(),
                    "private_manifest_path": str(manifest_path),
                    "tutor_index_path": str(index_path),
                    "tutor_index_journal_path": str(index_journal_path),
                    "selected_skill_tag": "python_lists",
                    "requested_help_level": "A6",
                    "cell_source": "private_cell = 'do not echo'",
                    "study_receipt": {
                        "prediction_present": True,
                        "notebook_action_present": True,
                        "reflection_present": True,
                    },
                },
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "skill_to_workspace_session_carryover_ready")
            self.assertEqual(report["carryover_packet"]["operator_receipt"]["help_level"], "A2")
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertNotIn("private_cell", payload)
            self.assertNotIn(str(temp_dir), payload)


if __name__ == "__main__":
    unittest.main()
