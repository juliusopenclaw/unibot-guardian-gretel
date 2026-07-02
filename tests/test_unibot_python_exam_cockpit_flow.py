from __future__ import annotations

import copy
import unittest

from unibot.python_exam_cockpit_flow import build_python_exam_cockpit_flow
from unibot.server import route_request


def cockpit_inputs() -> dict[str, dict]:
    readiness = {
        "artifact_type": "python_exam_readiness_console",
        "status": "python_exam_readiness_console_ready",
        "exam_deployment_status": "not_cleared",
        "readiness_summary": {
            "selected_skill_tag": "python_lists",
            "skill_ready_for_workspace": True,
            "review_chain_pass": True,
            "receipt_journal_ready": True,
            "latest_notebook_checkpoint_hash": "c" * 64,
            "next_safe_action": "Use the selected skill workspace with A0-A2 support, review evidence, and keep not_cleared.",
        },
        "a0_a2_help_status": {
            "recommended_help_level": "A2",
            "status": "a0_a2_only",
        },
        "operator_confirmation_status": {
            "open_operator_confirmation_count": 2,
        },
    }
    drilldown = {
        "artifact_type": "exam_skill_drilldown",
        "status": "exam_skill_drilldown_ready_for_workspace",
        "exam_deployment_status": "not_cleared",
        "selected_skill": {"skill_tag": "python_lists"},
        "workspace_start_action": {"status": "ready"},
    }
    operator = {
        "artifact_type": "exam_workspace_operator_run_dry_run",
        "status": "exam_workspace_operator_dry_run_ready",
        "exam_deployment_status": "not_cleared",
        "dry_run_receipt": {
            "receipt_id": "operator-1",
            "selected_skill_tag": "python_lists",
            "effective_help_level": "A2",
        },
        "operator_confirmation_matrix": {
            "confirmed_count": 0,
            "write_step_count": 6,
            "steps": {
                "checkpoint_store": {"confirmed": False, "writes_local": True},
                "exam_workspace_run": {"confirmed": False, "writes_local": True},
            },
        },
        "help_ledger_preview": {"status": "dry_run_ready"},
    }
    session = {
        "artifact_type": "exam_workspace_session_console",
        "status": "exam_workspace_session_console_ready",
        "exam_deployment_status": "not_cleared",
        "session_console": {
            "status": "ready_dry_run",
            "selected_skill": {"skill_tag": "python_lists"},
            "notebook_checkpoint": {
                "status": "notebook_checkpoint_ready",
                "notebook_work_sha256": "c" * 64,
            },
            "tutor_state": {
                "tutor_status": "allowed",
                "effective_help_level": "A2",
            },
            "help_ledger_preview": {
                "status": "dry_run_ready",
                "general_help_ledger_written": False,
                "exam_ledger_written": False,
                "event_hash": "h" * 64,
            },
            "export_receipt": {
                "status": "export_review_ready",
                "not_cleared_receipt": True,
            },
        },
        "session_console_receipt": {
            "receipt_id": "session-1",
            "repeat_run_index": 1,
        },
    }
    chain = {
        "artifact_type": "review_chain_integrity_check",
        "status": "review_chain_integrity_pass",
        "exam_deployment_status": "not_cleared",
        "chain_integrity_summary": {
            "issue_count": 0,
            "checked_link_count": 4,
            "next_safe_action": "Proceed to human review using the metadata-only chain; keep exam_deployment_status not_cleared.",
        },
    }
    review = {
        "artifact_type": "timeline_export_review_packet",
        "status": "timeline_export_review_packet_ready",
        "exam_deployment_status": "not_cleared",
        "local_export_receipt": {
            "receipt_id": "review-1",
            "status": "timeline_export_review_packet_receipt_ready_not_exam_clearance",
        },
    }
    journal = {
        "artifact_type": "timeline_export_receipt_journal_summary",
        "status": "ok",
        "record_count": 1,
        "accepted_record_count": 1,
        "blocked_record_count": 0,
        "exam_deployment_status": "not_cleared",
    }
    return {
        "readiness": readiness,
        "drilldown": drilldown,
        "operator": operator,
        "session": session,
        "chain": chain,
        "review": review,
        "journal": journal,
    }


class UniBotPythonExamCockpitFlowTests(unittest.TestCase):
    def test_cockpit_flow_builds_ready_step_bar(self) -> None:
        inputs = cockpit_inputs()
        report = build_python_exam_cockpit_flow(
            python_exam_readiness_console=inputs["readiness"],
            exam_skill_drilldown=inputs["drilldown"],
            exam_workspace_operator_run=inputs["operator"],
            exam_workspace_session_console=inputs["session"],
            review_chain_integrity_check=inputs["chain"],
            timeline_export_review_packet=inputs["review"],
            timeline_export_receipt_journal_summary=inputs["journal"],
            selected_skill_tag="python_lists",
        )
        summary = report["cockpit_summary"]
        self.assertEqual(report["artifact_type"], "python_exam_cockpit_flow")
        self.assertEqual(report["status"], "python_exam_cockpit_flow_ready")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertEqual(report["selected_skill_tag"], "python_lists")
        self.assertEqual(summary["step_count"], 9)
        self.assertEqual(summary["complete_step_count"], 9)
        self.assertEqual(summary["attention_step_count"], 0)
        self.assertEqual(report["operator_confirmation_status"]["confirmed_local_write_step_count"], 0)
        self.assertTrue(report["dry_run_default"])
        self.assertFalse(report["local_writes_executed_by_cockpit"])
        self.assertEqual(report["evidence_receipts"]["notebook_checkpoint_hash"], "c" * 64)
        self.assertFalse(report["raw_query_returned"])
        self.assertFalse(report["raw_text_returned"])
        self.assertFalse(report["notebook_code_returned"])
        self.assertFalse(report["local_paths_returned"])
        self.assertFalse(report["exam_clearance_claimed"])
        self.assertEqual(report["public_safety_status"], "pass")

    def test_cockpit_flow_marks_chain_attention(self) -> None:
        inputs = cockpit_inputs()
        chain = copy.deepcopy(inputs["chain"])
        chain["status"] = "review_chain_integrity_attention_required"
        chain["chain_integrity_summary"]["issue_count"] = 1
        chain["chain_integrity_summary"]["next_safe_action"] = "Resolve review-chain finding before continuing."
        report = build_python_exam_cockpit_flow(
            python_exam_readiness_console=inputs["readiness"],
            exam_skill_drilldown=inputs["drilldown"],
            exam_workspace_operator_run=inputs["operator"],
            exam_workspace_session_console=inputs["session"],
            review_chain_integrity_check=chain,
            timeline_export_review_packet=inputs["review"],
            timeline_export_receipt_journal_summary=inputs["journal"],
            selected_skill_tag="python_lists",
        )
        self.assertEqual(report["status"], "python_exam_cockpit_flow_attention")
        self.assertEqual(report["cockpit_summary"]["attention_step_count"], 1)
        self.assertIn("Resolve review-chain", report["next_safe_action"])
        self.assertEqual(report["public_safety_status"], "pass")

    def test_cockpit_flow_api_route(self) -> None:
        inputs = cockpit_inputs()
        status, report = route_request(
            "/api/unibot/course/python-exam-cockpit-flow",
            payload={
                "python_exam_readiness_console": inputs["readiness"],
                "exam_skill_drilldown": inputs["drilldown"],
                "exam_workspace_operator_run": inputs["operator"],
                "exam_workspace_session_console": inputs["session"],
                "review_chain_integrity_check": inputs["chain"],
                "timeline_export_review_packet": inputs["review"],
                "timeline_export_receipt_journal_summary": inputs["journal"],
                "selected_skill_tag": "python_lists",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "python_exam_cockpit_flow_ready")
        self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
