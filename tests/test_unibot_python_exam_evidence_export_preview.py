from __future__ import annotations

import copy
import unittest

from unibot.python_exam_cockpit_flow import build_python_exam_cockpit_flow
from unibot.python_exam_evidence_export_preview import build_python_exam_evidence_export_preview
from unibot.python_exam_live_control_surface import build_python_exam_live_control_surface
from unibot.server import route_request

from tests.test_unibot_python_exam_cockpit_flow import cockpit_inputs


def preview_inputs() -> dict[str, dict]:
    inputs = cockpit_inputs()
    cockpit = build_python_exam_cockpit_flow(
        python_exam_readiness_console=inputs["readiness"],
        exam_skill_drilldown=inputs["drilldown"],
        exam_workspace_operator_run=inputs["operator"],
        exam_workspace_session_console=inputs["session"],
        review_chain_integrity_check=inputs["chain"],
        timeline_export_review_packet=inputs["review"],
        timeline_export_receipt_journal_summary=inputs["journal"],
        selected_skill_tag="python_lists",
    )
    live_control = build_python_exam_live_control_surface(
        python_exam_cockpit_flow=cockpit,
        python_exam_readiness_console=inputs["readiness"],
        exam_skill_drilldown=inputs["drilldown"],
        exam_workspace_operator_run=inputs["operator"],
        exam_workspace_session_console=inputs["session"],
        review_chain_integrity_check=inputs["chain"],
        timeline_export_review_packet=inputs["review"],
        timeline_export_receipt_journal_summary=inputs["journal"],
        selected_skill_tag="python_lists",
    )
    inputs["cockpit"] = cockpit
    inputs["live_control"] = live_control
    return inputs


class UniBotPythonExamEvidenceExportPreviewTests(unittest.TestCase):
    def test_evidence_export_preview_builds_human_review_manifest(self) -> None:
        inputs = preview_inputs()
        report = build_python_exam_evidence_export_preview(
            python_exam_live_control_surface=inputs["live_control"],
            python_exam_cockpit_flow=inputs["cockpit"],
            python_exam_readiness_console=inputs["readiness"],
            exam_skill_drilldown=inputs["drilldown"],
            exam_workspace_operator_run=inputs["operator"],
            exam_workspace_session_console=inputs["session"],
            review_chain_integrity_check=inputs["chain"],
            timeline_export_review_packet=inputs["review"],
            timeline_export_receipt_journal_summary=inputs["journal"],
            selected_skill_tag="python_lists",
        )
        summary = report["preview_summary"]
        manifest = report["preview_manifest"]
        receipt = report["preview_receipt"]

        self.assertEqual(report["artifact_type"], "python_exam_evidence_export_preview")
        self.assertEqual(report["status"], "python_exam_evidence_export_preview_ready")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertEqual(report["selected_skill_tag"], "python_lists")
        self.assertTrue(report["dry_run_default"])
        self.assertTrue(report["export_preview_only"])
        self.assertFalse(report["local_export_package_written"])
        self.assertTrue(report["operator_confirmation_required_for_export_write"])
        self.assertFalse(report["operator_confirmed_export_write"])
        self.assertEqual(summary["cockpit_step_count"], 9)
        self.assertEqual(summary["live_control_action_count"], 9)
        self.assertEqual(summary["help_status"], "a0_a2_only")
        self.assertEqual(summary["review_chain_status"], "review_chain_integrity_pass")
        self.assertTrue(summary["notebook_checkpoint_hash_present"])
        self.assertEqual(summary["receipt_journal_accepted_record_count"], 1)
        self.assertEqual(manifest["notebook_checkpoint"]["notebook_checkpoint_hash"], "c" * 64)
        self.assertEqual(manifest["evidence_receipts"]["operator_receipt_id"], "operator-1")
        self.assertEqual(manifest["operator_confirmation_profile"]["open_operator_confirmation_count"], 2)
        self.assertEqual(report["human_review_packet"]["status"], "ready_for_human_review")
        self.assertEqual(receipt["status"], "python_exam_evidence_export_preview_receipt_ready_not_exam_clearance")
        self.assertTrue(receipt["receipt_id"])
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
        self.assertEqual(report["public_safety_status"], "pass")

    def test_evidence_export_preview_marks_attention_when_chain_has_issue(self) -> None:
        inputs = preview_inputs()
        chain = copy.deepcopy(inputs["chain"])
        chain["status"] = "review_chain_integrity_attention_required"
        chain["chain_integrity_summary"]["issue_count"] = 1
        report = build_python_exam_evidence_export_preview(
            python_exam_live_control_surface=inputs["live_control"],
            python_exam_cockpit_flow=inputs["cockpit"],
            python_exam_readiness_console=inputs["readiness"],
            exam_skill_drilldown=inputs["drilldown"],
            exam_workspace_operator_run=inputs["operator"],
            exam_workspace_session_console=inputs["session"],
            review_chain_integrity_check=chain,
            timeline_export_review_packet=inputs["review"],
            timeline_export_receipt_journal_summary=inputs["journal"],
            selected_skill_tag="python_lists",
        )

        self.assertEqual(report["status"], "python_exam_evidence_export_preview_attention")
        self.assertEqual(report["human_review_packet"]["status"], "needs_attention_before_human_review")
        self.assertEqual(report["preview_summary"]["review_chain_issue_count"], 1)
        self.assertEqual(report["public_safety_status"], "pass")

    def test_evidence_export_preview_api_route(self) -> None:
        inputs = preview_inputs()
        status, report = route_request(
            "/api/unibot/course/python-exam-evidence-export-preview",
            payload={
                "python_exam_live_control_surface": inputs["live_control"],
                "python_exam_cockpit_flow": inputs["cockpit"],
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
        self.assertEqual(report["status"], "python_exam_evidence_export_preview_ready")
        self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
