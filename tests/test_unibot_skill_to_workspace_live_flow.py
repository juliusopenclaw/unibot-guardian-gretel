from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from unibot.public_safety import scan_text
from unibot.server import route_request
from unibot.skill_to_workspace_live_flow import build_skill_to_workspace_live_flow
from unibot.tutor_index import build_private_tutor_index_dry_run

from tests.test_unibot_exam_skill_drilldown import (
    reviewed_manifest_record,
    valid_decision,
    write_private_manifest,
    write_ready_fixture,
)


class UniBotSkillToWorkspaceLiveFlowTests(unittest.TestCase):
    def test_live_flow_prefills_and_runs_operator_dry_run_from_selected_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "private_tutor_index.json"
            index_journal_path = Path(temp_dir) / "index_journal.jsonl"
            ledger_path = Path(temp_dir) / "help_ledger.jsonl"
            checkpoint_journal_path = Path(temp_dir) / "checkpoints.jsonl"
            cell_source = "own_attempt = []\n# local checkpoint only\n"
            write_ready_fixture(root)
            write_private_manifest(manifest_path, [reviewed_manifest_record()])
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                tutor_index_journal_path=index_journal_path,
                operator_confirmed_tutor_index_build=True,
            )

            report = build_skill_to_workspace_live_flow(
                base_path=str(root),
                review_policy="local_private_tutor",
                decision_record=valid_decision(),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                tutor_index_journal_path=index_journal_path,
                ledger_path=ledger_path,
                checkpoint_journal_path=checkpoint_journal_path,
                selected_skill_tag="python_lists",
                requested_help_level="A6",
                student_reflection="Ich pruefe zuerst meine eigene Vorhersage.",
                cell_source=cell_source,
                study_receipt={
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["artifact_type"], "skill_to_workspace_live_flow")
            self.assertEqual(report["status"], "skill_to_workspace_live_flow_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["drilldown_status"], "exam_skill_drilldown_ready_for_workspace")
            self.assertEqual(report["operator_run_status"], "exam_workspace_operator_dry_run_ready")
            self.assertEqual(report["selected_skill"]["skill_tag"], "python_lists")
            self.assertEqual(report["operator_prefill"]["status"], "prefill_ready")
            self.assertEqual(report["operator_prefill"]["endpoint"], "/api/unibot/exam-workspace/operator-run")
            self.assertEqual(report["operator_prefill"]["requested_help_level"], "A2")
            self.assertEqual(report["notebook_checkpoint_template"]["status"], "template_ready")
            self.assertEqual(report["help_ledger_preview_template"]["help_level"], "A2")
            self.assertEqual(report["operator_confirmation_matrix"]["status"], "all_steps_dry_run")
            self.assertEqual(report["operator_confirmation_matrix"]["confirmed_count"], 0)
            self.assertFalse(report["operator_confirmation_matrix"]["local_writes_requested"])
            self.assertEqual(report["start_exam_workspace_view"]["title"], "Start Exam Workspace")
            self.assertEqual(report["dry_run_receipt"]["effective_help_level"], "A2")
            self.assertTrue(report["dry_run_receipt"]["not_cleared_receipt"])
            self.assertTrue(report["a0_a2_only"])
            self.assertFalse(report["local_writes_requested"])
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
            self.assertFalse(ledger_path.exists())
            self.assertFalse(checkpoint_journal_path.exists())
            self.assertNotIn("own_attempt", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "skill-to-workspace-live-flow")["status"], "pass")
            self.assertEqual(report["public_safety_status"], "pass")

    def test_live_flow_route_returns_waiting_when_skill_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            (root / "Videos").mkdir(parents=True)
            (root / "Videos" / "debugging.mov").write_bytes(b"video")

            status, report = route_request(
                "/api/unibot/course/skill-to-workspace-live-flow",
                {
                    "base_path": str(root),
                    "selected_skill_tag": "debugging",
                    "requested_help_level": "A2",
                    "query": "private question must not echo",
                },
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "skill_to_workspace_live_flow_waiting_for_skill_readiness")
            self.assertEqual(report["operator_run_status"], "not_started_skill_not_ready")
            self.assertEqual(report["operator_prefill"]["status"], "prefill_waiting_for_skill_readiness")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertFalse(report["raw_query_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertNotIn("private question", payload)
            self.assertNotIn("debugging.mov", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
