from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.exam_notebook_checkpoint import (  # noqa: E402
    build_exam_notebook_checkpoint_adapter_dry_run,
    build_notebook_checkpoint_release_claim_alignment,
)
from unibot.materials import sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotExamNotebookCheckpointTests(unittest.TestCase):
    def test_checkpoint_adapter_hashes_local_cell_without_returning_code(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            checkpoint_journal = Path(temp_dir) / "checkpoints.jsonl"
            cell_source = "own_values = [1, 2, 3]\nlen(own_values)\n"

            status, report = route_request(
                "/api/unibot/exam-workspace/notebook-checkpoint/adapt",
                {
                    "task_id": "task-pandas-check",
                    "skill_tag": "pandas",
                    "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
                    "cell_source": cell_source,
                    "cell_index": 2,
                    "cell_id": "private-cell-id",
                    "requested_help_level": "A2",
                    "prediction_present": True,
                    "retrieval_response_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                    "checkpoint_journal_path": str(checkpoint_journal),
                },
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(report["artifact_type"], "exam_notebook_checkpoint_adapter_dry_run")
            self.assertEqual(report["status"], "notebook_checkpoint_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertEqual(report["notebook_checkpoint"]["cell_source_sha256"], sha256_text(cell_source))
            self.assertEqual(report["notebook_checkpoint"]["notebook_work_sha256"], sha256_text(cell_source))
            self.assertEqual(report["study_receipt_summary"]["status"], "ok_study_session_receipt")
            self.assertEqual(report["help_ledger_preview"]["help_level"], "A2")
            self.assertFalse(report["help_ledger_preview"]["ledger_written"])
            self.assertFalse(report["checkpoint_journal_summary"]["checkpoint_journal_written"])
            self.assertFalse(report["raw_cell_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["raw_notebook_returned"])
            self.assertFalse(report["notebook_code_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(report["automatic_grading_started"])
            self.assertFalse(report["proctoring_started"])
            self.assertFalse(report["ai_detection_started"])
            self.assertFalse(report["exam_clearance_claimed"])
            self.assertFalse(checkpoint_journal.exists())
            self.assertNotIn("own_values", payload)
            self.assertNotIn("private-cell-id", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "checkpoint-adapter-ready")["status"], "pass")

    def test_checkpoint_adapter_can_store_hash_only_event_with_operator_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            checkpoint_journal = Path(temp_dir) / "checkpoints.jsonl"
            cell_source = "result = sum([1, 2, 3])\n"

            report = build_exam_notebook_checkpoint_adapter_dry_run(
                task_id="task-lists-check",
                skill_tag="python_lists",
                source_card_ids=["dfg-gwp"],
                cell_source=cell_source,
                prediction_present=True,
                retrieval_response_present=True,
                notebook_action_present=True,
                reflection_present=True,
                checkpoint_journal_path=checkpoint_journal,
                operator_confirmed_checkpoint_store=True,
                public_safe=True,
            )
            payload = json.dumps(report, ensure_ascii=False)
            stored = checkpoint_journal.read_text(encoding="utf-8")

            self.assertEqual(report["status"], "notebook_checkpoint_ready")
            self.assertTrue(report["checkpoint_journal_summary"]["checkpoint_journal_written"])
            self.assertIn(sha256_text(cell_source), stored)
            self.assertNotIn("result = sum", stored)
            self.assertNotIn("result = sum", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "checkpoint-adapter-stored")["status"], "pass")

    def test_checkpoint_adapter_blocks_final_solution_marker_without_leaking_cell(self) -> None:
        cell_source = "# final answer: use this exact completed solution\n"
        report = build_exam_notebook_checkpoint_adapter_dry_run(
            task_id="task-repeat",
            skill_tag="pandas",
            source_card_ids=["dfg-gwp"],
            cell_source=cell_source,
            prediction_present=True,
            retrieval_response_present=True,
            notebook_action_present=True,
            reflection_present=True,
            public_safe=True,
        )
        payload = json.dumps(report, ensure_ascii=False)

        self.assertEqual(report["status"], "notebook_checkpoint_repeat_task_required")
        self.assertTrue(report["solution_marker_detected"])
        self.assertEqual(report["study_receipt_summary"]["status"], "repeat_task_required")
        self.assertFalse(report["raw_cell_returned"])
        self.assertFalse(report["notebook_code_returned"])
        self.assertNotIn("final answer", payload.lower())
        self.assertEqual(scan_text(payload, "checkpoint-adapter-repeat")["status"], "pass")

    def test_notebook_checkpoint_release_claim_alignment_links_hashes_and_boundaries(self) -> None:
        alignment = build_notebook_checkpoint_release_claim_alignment()

        self.assertEqual(
            alignment["schema_version"],
            "unibot-notebook-checkpoint-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["ready_public_safety_status"], "pass")
        self.assertEqual(alignment["stored_public_safety_status"], "pass")
        self.assertEqual(alignment["repeat_public_safety_status"], "pass")
        self.assertEqual(alignment["ready_checkpoint_status"], "notebook_checkpoint_ready")
        self.assertEqual(alignment["stored_checkpoint_status"], "notebook_checkpoint_ready")
        self.assertEqual(alignment["repeat_checkpoint_status"], "notebook_checkpoint_repeat_task_required")
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertEqual(alignment["study_receipt_status"], "ok_study_session_receipt")
        self.assertTrue(alignment["checkpoint_hash_present"])
        self.assertEqual(alignment["workspace_card_status"], "python_exam_local_cycle_operator_workspace_card_ready")
        self.assertEqual(alignment["workspace_card_selected_skill_tag"], "pandas")
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertTrue(alignment["workspace_card_checkpoint_gate_linked"])
        self.assertEqual(alignment["checkpoint_journal_status"], "stored")
        self.assertTrue(alignment["checkpoint_journal_written"])
        self.assertEqual(alignment["repeat_receipt_status"], "repeat_task_required")
        self.assertTrue(alignment["repeat_task_required"])
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("notebook_checkpoint", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertIn("study_session", alignment["required_readiness_check_ids"])
        self.assertIn("private_tutor_use_flow", alignment["required_readiness_check_ids"])
        self.assertIn("evaluation_packet", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertTrue(alignment["contracts"]["hash_only_checkpoint_ready"])
        self.assertTrue(alignment["contracts"]["operator_confirmed_journal_hash_only"])
        self.assertTrue(alignment["contracts"]["a6_or_final_solution_forces_repeat"])
        self.assertTrue(alignment["contracts"]["workspace_card_checkpoint_gate_linked"])
        self.assertTrue(alignment["contracts"]["public_outputs_hide_private_notebook_data"])
        self.assertTrue(alignment["contracts"]["high_stakes_actions_not_started"])
        self.assertIn("raw notebook code returned", alignment["blocked_claims"])
        self.assertIn("checkpoint journal write without operator confirmation", alignment["blocked_claims"])
        self.assertIn("final solution acceptance", alignment["blocked_claims"])
        self.assertIn("Eigenleistung percentage claim", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])

    def test_notebook_checkpoint_release_claim_alignment_blocks_raw_or_exam_claims(self) -> None:
        ready = build_exam_notebook_checkpoint_adapter_dry_run(
            task_id="bad-checkpoint",
            skill_tag="pandas",
            source_card_ids=["dfg-gwp"],
            cell_source="x = 1\n",
            prediction_present=True,
            retrieval_response_present=True,
            notebook_action_present=True,
            reflection_present=True,
            public_safe=True,
        )
        stored = dict(ready)
        repeat = dict(ready)
        ready["exam_deployment_status"] = "cleared"
        ready["execution_boundary"] = "Notebook checkpoint returns raw notebook code and clears exams."
        ready["raw_cell_returned"] = True
        ready["notebook_code_returned"] = True
        ready["automatic_grading_started"] = True
        ready["notebook_checkpoint"]["raw_cell_returned"] = True
        ready["notebook_checkpoint"]["notebook_code_returned"] = True
        stored["operator_confirmations"] = {"checkpoint_store": False}
        stored["checkpoint_journal_summary"] = {"status": "stored", "checkpoint_journal_written": True, "path_returned": True}
        repeat["status"] = "notebook_checkpoint_ready"
        repeat["solution_marker_detected"] = False
        repeat["study_receipt_summary"] = {"status": "ok_study_session_receipt", "repeat_task_required": False}

        alignment = build_notebook_checkpoint_release_claim_alignment(ready, stored, repeat)

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("hash_only_checkpoint_ready", alignment["failed_contract_ids"])
        self.assertIn("operator_confirmed_journal_hash_only", alignment["failed_contract_ids"])
        self.assertIn("a6_or_final_solution_forces_repeat", alignment["failed_contract_ids"])
        self.assertIn("workspace_card_checkpoint_gate_linked", alignment["failed_contract_ids"])
        self.assertIn("public_outputs_hide_private_notebook_data", alignment["failed_contract_ids"])
        self.assertIn("high_stakes_actions_not_started", alignment["failed_contract_ids"])


if __name__ == "__main__":
    unittest.main()
