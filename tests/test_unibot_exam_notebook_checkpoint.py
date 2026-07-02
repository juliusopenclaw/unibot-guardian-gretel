from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.exam_notebook_checkpoint import build_exam_notebook_checkpoint_adapter_dry_run  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
