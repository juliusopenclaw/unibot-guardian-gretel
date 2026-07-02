from __future__ import annotations

import copy
import unittest

from unibot.python_exam_readiness_console import build_python_exam_readiness_console
from unibot.server import route_request


def readiness_inputs() -> dict[str, dict]:
    dashboard = {
        "artifact_type": "course_exam_coverage_dashboard",
        "status": "course_exam_coverage_dashboard_ready",
        "exam_deployment_status": "not_cleared",
        "dashboard_summary": {
            "workspace_ready_skill_count": 1,
            "source_anchor_count": 5,
            "checkpoint_hash_count": 1,
            "open_operator_confirmation_count": 2,
            "help_level_profile": {"A2": 1},
        },
        "skill_dashboard": [
            {
                "skill_tag": "python_lists",
                "title": "Python Lists",
                "workspace_readiness": "ready_for_exam_workspace_dry_run",
                "source_anchor_count": 3,
                "reviewed_notebook_anchor_count": 1,
                "source_card_ids": ["lecture-python-lists"],
                "latest_checkpoint_hashes": ["c" * 64],
                "help_level_profile": {"A2": 1},
                "open_operator_confirmation_count": 2,
                "coverage_gap_status": "coverage_ready_for_dry_run",
                "next_safe_step": "review latest checkpoint hash, help-level profile, and export receipt",
            }
        ],
    }
    drilldown = {
        "artifact_type": "exam_skill_drilldown",
        "status": "exam_skill_drilldown_ready_for_workspace",
        "exam_deployment_status": "not_cleared",
        "selected_skill": {
            "skill_tag": "python_lists",
            "title": "Python Lists",
            "exam_workspace_readiness": "ready_for_exam_workspace_dry_run",
            "current_readiness": "ready",
            "projected_readiness": "ready",
            "source_anchor_count": 3,
            "reviewed_notebook_anchor_count": 1,
            "source_card_ids": ["lecture-python-lists"],
            "allowed_exam_help": ["A0", "A1", "A2"],
            "recommended_help_level": "A2",
            "start_button_enabled": True,
        },
    }
    chain = {
        "artifact_type": "review_chain_integrity_check",
        "status": "review_chain_integrity_pass",
        "exam_deployment_status": "not_cleared",
        "chain_integrity_summary": {
            "status": "review_chain_integrity_pass",
            "issue_count": 0,
            "missing_count": 0,
            "contradiction_count": 0,
            "duplicate_count": 0,
            "checked_link_count": 4,
            "skill_tags": ["python_lists"],
            "counts": {
                "timeline_event_count": 1,
                "review_event_count": 1,
                "journal_event_count": 1,
                "timeline_checkpoint_hash_count": 1,
                "reviewer_question_count": 6,
            },
            "help_level_profiles": {
                "packet": {"A2": 1},
                "timeline": {"A2": 1},
                "review": {"A2": 1},
                "journal": {"A2": 1},
            },
            "open_operator_confirmation_counts": {
                "packet": 2,
                "timeline": 2,
                "review": 2,
                "journal": 2,
            },
            "next_safe_action": "Proceed to human review using the metadata-only chain; keep exam_deployment_status not_cleared.",
        },
    }
    journal = {
        "artifact_type": "timeline_export_receipt_journal_summary",
        "status": "ok",
        "record_count": 1,
        "accepted_record_count": 1,
        "blocked_record_count": 0,
        "skill_tags": ["python_lists"],
        "event_count": 1,
        "checkpoint_hash_count": 1,
        "reviewer_question_count": 6,
        "open_operator_confirmation_count": 2,
        "help_level_profile": {"A2": 1},
        "exam_deployment_status": "not_cleared",
    }
    return {
        "dashboard": dashboard,
        "drilldown": drilldown,
        "chain": chain,
        "journal": journal,
    }


class UniBotPythonExamReadinessConsoleTests(unittest.TestCase):
    def test_console_combines_ready_skill_evidence(self) -> None:
        inputs = readiness_inputs()
        report = build_python_exam_readiness_console(
            course_exam_coverage_dashboard=inputs["dashboard"],
            exam_skill_drilldown=inputs["drilldown"],
            review_chain_integrity_check=inputs["chain"],
            timeline_export_receipt_journal_summary=inputs["journal"],
            selected_skill_tag="python_lists",
        )
        summary = report["readiness_summary"]
        self.assertEqual(report["artifact_type"], "python_exam_readiness_console")
        self.assertEqual(report["status"], "python_exam_readiness_console_ready")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertEqual(summary["selected_skill_tag"], "python_lists")
        self.assertTrue(summary["skill_ready_for_workspace"])
        self.assertTrue(summary["source_anchored"])
        self.assertTrue(summary["review_chain_pass"])
        self.assertEqual(summary["latest_notebook_checkpoint_hash"], "c" * 64)
        self.assertEqual(report["a0_a2_help_status"]["status"], "a0_a2_only")
        self.assertEqual(report["operator_confirmation_status"]["open_operator_confirmation_count"], 2)
        self.assertFalse(report["raw_query_returned"])
        self.assertFalse(report["raw_text_returned"])
        self.assertFalse(report["notebook_code_returned"])
        self.assertFalse(report["local_paths_returned"])
        self.assertFalse(report["exam_clearance_claimed"])
        self.assertEqual(report["public_safety_status"], "pass")

    def test_console_marks_chain_attention_without_exposing_raw_data(self) -> None:
        inputs = readiness_inputs()
        chain = copy.deepcopy(inputs["chain"])
        chain["status"] = "review_chain_integrity_attention_required"
        chain["chain_integrity_summary"]["issue_count"] = 1
        chain["chain_integrity_summary"]["contradiction_count"] = 1
        chain["chain_integrity_summary"]["next_safe_action"] = "Resolve journal_review_receipt_id before relying on the review chain."
        report = build_python_exam_readiness_console(
            course_exam_coverage_dashboard=inputs["dashboard"],
            exam_skill_drilldown=inputs["drilldown"],
            review_chain_integrity_check=chain,
            timeline_export_receipt_journal_summary=inputs["journal"],
            selected_skill_tag="python_lists",
        )
        self.assertEqual(report["status"], "python_exam_readiness_console_chain_attention")
        self.assertEqual(report["review_chain_status"]["issue_count"], 1)
        self.assertIn("Resolve journal_review_receipt_id", report["readiness_summary"]["next_safe_action"])
        self.assertEqual(report["public_safety_status"], "pass")

    def test_console_api_route(self) -> None:
        inputs = readiness_inputs()
        status, report = route_request(
            "/api/unibot/course/python-exam-readiness-console",
            payload={
                "course_exam_coverage_dashboard": inputs["dashboard"],
                "exam_skill_drilldown": inputs["drilldown"],
                "review_chain_integrity_check": inputs["chain"],
                "timeline_export_receipt_journal_summary": inputs["journal"],
                "selected_skill_tag": "python_lists",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "python_exam_readiness_console_ready")
        self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
