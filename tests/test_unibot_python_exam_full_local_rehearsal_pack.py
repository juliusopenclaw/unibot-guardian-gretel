from __future__ import annotations

import copy
import json
import unittest

from unibot.python_exam_full_local_rehearsal_pack import build_python_exam_full_local_rehearsal_pack
from unibot.public_safety import scan_text
from unibot.server import route_request

from tests.test_unibot_python_exam_cockpit_flow import cockpit_inputs


def full_rehearsal_inputs() -> dict[str, dict]:
    inputs = cockpit_inputs()
    inputs["drilldown"] = copy.deepcopy(inputs["drilldown"])
    inputs["drilldown"]["selected_skill"]["source_card_ids"] = ["dfg-gwp", "vanlehn-2011"]
    inputs["drilldown"]["selected_skill"]["source_anchor_count"] = 2
    inputs["local_review"] = {
        "artifact_type": "python_exam_local_cycle_readiness_review",
        "status": "python_exam_local_cycle_readiness_review_ready",
        "selected_skill_tag": "python_lists",
        "exam_deployment_status": "not_cleared",
        "readiness_review_summary": {
            "recommendation": "ready_for_manual_local_cycle_review",
            "task_hash": "t" * 64,
            "checkpoint_hash": "c" * 64,
            "gate_receipt_hash": "g" * 64,
            "decision_receipt_hash": "d" * 64,
            "start_receipt_hash": "s" * 64,
            "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
            "source_anchor_count": 2,
            "help_level": "A2",
        },
        "readiness_review_receipt": {"receipt_hash": "r" * 64},
    }
    inputs["local_handoff"] = {
        "artifact_type": "python_exam_local_cycle_readiness_handoff",
        "status": "python_exam_local_cycle_readiness_handoff_ready",
        "selected_skill_tag": "python_lists",
        "exam_deployment_status": "not_cleared",
        "handoff_summary": {
            "ready_for_operator_prefill": True,
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "task_hash": "t" * 64,
            "checkpoint_hash": "c" * 64,
            "help_level": "A2",
        },
        "operator_run_prefill": {"prefill_hash": "p" * 64},
        "handoff_receipt": {"receipt_hash": "h" * 64},
    }
    inputs["workspace_card"] = {
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "python_lists",
        "exam_deployment_status": "not_cleared",
        "workspace_card_summary": {
            "status": "python_exam_local_cycle_operator_workspace_card_ready",
            "selected_skill_tag": "python_lists",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "help_ledger_preview_hash": "l" * 64,
            "task_hash": "t" * 64,
            "checkpoint_hash": "c" * 64,
            "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
            "source_anchor_count": 2,
            "help_level": "A2",
            "next_safe_action": "Open the operator-run prefill.",
        },
    }
    inputs["run_history"] = {
        "artifact_type": "exam_workspace_run_history_export_review",
        "status": "exam_workspace_run_history_export_review_ready",
        "exam_deployment_status": "not_cleared",
        "history_summary": {"run_count": 1, "help_level_profile": {"A2": 1}},
    }
    inputs["exam_run_packet"] = {
        "artifact_type": "exam_run_packet",
        "status": "exam_run_packet_ready",
        "selected_skill_tag": "python_lists",
        "exam_deployment_status": "not_cleared",
        "packet_receipt": {
            "receipt_id": "packet-1",
            "receipt_hash": "e" * 64,
            "status": "exam_run_packet_receipt_ready_not_exam_clearance",
        },
    }
    inputs["exam_packet_timeline"] = {
        "artifact_type": "exam_packet_timeline",
        "status": "exam_packet_timeline_ready",
        "exam_deployment_status": "not_cleared",
        "timeline_summary": {"skill_tags": ["python_lists"], "event_count": 1},
        "timeline_receipt": {
            "receipt_id": "timeline-1",
            "receipt_hash": "m" * 64,
            "status": "exam_packet_timeline_receipt_ready_not_exam_clearance",
        },
    }
    return inputs


class UniBotPythonExamFullLocalRehearsalPackTests(unittest.TestCase):
    def test_full_local_rehearsal_pack_compacts_complete_exam_cycle(self) -> None:
        inputs = full_rehearsal_inputs()
        report = build_python_exam_full_local_rehearsal_pack(
            exam_skill_drilldown=inputs["drilldown"],
            python_exam_local_cycle_readiness_review=inputs["local_review"],
            python_exam_local_cycle_readiness_handoff=inputs["local_handoff"],
            python_exam_local_cycle_operator_workspace_card=inputs["workspace_card"],
            exam_workspace_operator_run=inputs["operator"],
            exam_workspace_session_console=inputs["session"],
            exam_workspace_run_history_export_review=inputs["run_history"],
            exam_run_packet=inputs["exam_run_packet"],
            exam_packet_timeline=inputs["exam_packet_timeline"],
            timeline_export_review_packet=inputs["review"],
            timeline_export_receipt_journal_summary=inputs["journal"],
            review_chain_integrity_check=inputs["chain"],
            python_exam_readiness_console=inputs["readiness"],
            selected_skill_tag="python_lists",
        )
        payload = json.dumps(report, ensure_ascii=False)
        summary = report["rehearsal_summary"]

        self.assertEqual(report["artifact_type"], "python_exam_full_local_rehearsal_pack")
        self.assertEqual(report["status"], "python_exam_full_local_rehearsal_pack_ready")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertEqual(summary["ready_step_count"], 12)
        self.assertEqual(summary["attention_step_count"], 0)
        self.assertEqual(report["source_anchor_metadata"]["source_card_ids"], ["dfg-gwp", "vanlehn-2011"])
        self.assertEqual(report["a0_a2_help_status"]["status"], "a0_a2_only")
        self.assertEqual(report["evidence_chain"]["exam_run_packet_receipt_id"], "packet-1")
        self.assertEqual(report["evidence_chain"]["exam_packet_timeline_receipt_id"], "timeline-1")
        self.assertTrue(report["evidence_chain"]["local_cycle_chain_snapshot_hash"])
        self.assertTrue(report["evidence_chain"]["human_handoff_markdown_hash"])
        self.assertTrue(report["dry_run_default"])
        self.assertFalse(report["local_writes_executed_by_rehearsal_pack"])
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
        self.assertNotIn("own_checkpoint", payload)
        self.assertEqual(scan_text(payload, "python-exam-full-local-rehearsal-pack")["status"], "pass")
        self.assertEqual(report["public_safety_status"], "pass")

    def test_full_local_rehearsal_pack_api_route(self) -> None:
        inputs = full_rehearsal_inputs()
        status, report = route_request(
            "/api/unibot/course/python-exam-full-local-rehearsal-pack",
            payload={
                "exam_skill_drilldown": inputs["drilldown"],
                "python_exam_local_cycle_readiness_review": inputs["local_review"],
                "python_exam_local_cycle_readiness_handoff": inputs["local_handoff"],
                "python_exam_local_cycle_operator_workspace_card": inputs["workspace_card"],
                "exam_workspace_operator_run": inputs["operator"],
                "exam_workspace_session_console": inputs["session"],
                "exam_workspace_run_history_export_review": inputs["run_history"],
                "exam_run_packet": inputs["exam_run_packet"],
                "exam_packet_timeline": inputs["exam_packet_timeline"],
                "timeline_export_review_packet": inputs["review"],
                "timeline_export_receipt_journal_summary": inputs["journal"],
                "review_chain_integrity_check": inputs["chain"],
                "python_exam_readiness_console": inputs["readiness"],
                "selected_skill_tag": "python_lists",
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "python_exam_full_local_rehearsal_pack_ready")
        self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
