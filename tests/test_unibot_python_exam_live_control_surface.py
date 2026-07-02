from __future__ import annotations

import copy
import tempfile
import unittest

from unibot.python_exam_cockpit_flow import build_python_exam_cockpit_flow
from unibot.python_exam_live_control_surface import build_python_exam_live_control_surface
from unibot.python_exam_local_cycle_operator_workspace_card import build_python_exam_local_cycle_operator_workspace_card
from unibot.python_exam_local_cycle_readiness_handoff import build_python_exam_local_cycle_readiness_handoff
from unibot.python_exam_local_cycle_readiness_review import build_python_exam_local_cycle_readiness_review
from unibot.python_exam_local_cycle_start_packet import build_python_exam_local_cycle_start_packet
from unibot.python_exam_operator_gate_decision_receipt import build_python_exam_operator_gate_decision_receipt
from unibot.python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate
from unibot.server import route_request

from tests.test_unibot_python_exam_cockpit_flow import cockpit_inputs
from tests.test_unibot_python_exam_local_cycle_start_packet import ready_start_packet_inputs


class UniBotPythonExamLiveControlSurfaceTests(unittest.TestCase):
    def test_live_control_surface_maps_cockpit_steps_to_safe_actions(self) -> None:
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
        report = build_python_exam_live_control_surface(
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
        actions = report["control_actions"]
        endpoints = {item["safe_action_id"]: item["endpoint"] for item in actions}

        self.assertEqual(report["artifact_type"], "python_exam_live_control_surface")
        self.assertEqual(report["status"], "python_exam_live_control_surface_ready")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertTrue(report["sidepanel_first"])
        self.assertEqual(report["selected_skill_tag"], "python_lists")
        self.assertEqual(report["control_summary"]["action_count"], 9)
        self.assertEqual(report["control_summary"]["enabled_action_count"], 9)
        self.assertEqual(report["control_summary"]["current_step_id"], "export_receipt_summary")
        self.assertEqual(report["status_lights"]["overall"], "green")
        self.assertEqual(report["status_lights"]["a0_a2"], "green")
        self.assertEqual(report["status_lights"]["review_chain"], "green")
        self.assertEqual(report["status_lights"]["receipt_journal"], "green")
        self.assertEqual(report["next_safe_action"], "Use the sidepanel actions for metadata-only review; keep dry-run, A0-A2, and not_cleared.")
        self.assertEqual(endpoints["readiness_refresh"], "/api/unibot/course/python-exam-readiness-console")
        self.assertEqual(endpoints["operator_dry_run"], "/api/unibot/exam-workspace/operator-run")
        self.assertEqual(endpoints["session_console_refresh"], "/api/unibot/exam-workspace/session-console")
        self.assertEqual(endpoints["notebook_checkpoint_hash"], "/api/unibot/exam-workspace/notebook-checkpoint/adapt")
        self.assertEqual(endpoints["ledger_preview_check"], "/api/unibot/exam-workspace/session-console")
        self.assertEqual(endpoints["review_chain_check"], "/api/unibot/course/review-chain-integrity-check")
        self.assertEqual(endpoints["receipt_summary_refresh"], "/api/unibot/course/timeline-export-receipt-journal/summary")
        self.assertEqual(report["operator_confirmation_status"]["open_operator_confirmation_count"], 2)
        self.assertTrue(actions[2]["requires_operator_confirmation_for_local_writes"])
        self.assertIn("confirmExamWorkspaceRun", actions[2]["local_write_confirmation_keys"])
        self.assertFalse(report["local_writes_executed_by_surface"])
        self.assertFalse(report["raw_query_returned"])
        self.assertFalse(report["raw_text_returned"])
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

    def test_live_control_surface_includes_local_cycle_workspace_card(self) -> None:
        inputs = cockpit_inputs()
        with tempfile.TemporaryDirectory() as temp_dir:
            console, gate, _decision = ready_start_packet_inputs(temp_dir)
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
            report = build_python_exam_live_control_surface(
                python_exam_cockpit_flow=cockpit,
                python_exam_readiness_console=inputs["readiness"],
                exam_skill_drilldown=inputs["drilldown"],
                python_exam_local_cycle_operator_workspace_card=workspace_card,
                exam_workspace_operator_run=inputs["operator"],
                exam_workspace_session_console=inputs["session"],
                review_chain_integrity_check=inputs["chain"],
                timeline_export_review_packet=inputs["review"],
                timeline_export_receipt_journal_summary=inputs["journal"],
                selected_skill_tag="python_lists",
            )

            self.assertEqual(report["local_cycle_operator_workspace_card"]["status"], "python_exam_local_cycle_operator_workspace_card_ready")
            self.assertEqual(report["local_cycle_operator_workspace_card"]["help_ledger_preview_status"], "help_ledger_preview_ready")
            self.assertEqual(report["local_cycle_operator_workspace_card"]["next_safe_action"], review["readiness_review_summary"]["next_safe_action"])
            self.assertEqual(report["next_safe_action"], review["readiness_review_summary"]["next_safe_action"])

    def test_live_control_surface_marks_attention_from_cockpit_step(self) -> None:
        inputs = cockpit_inputs()
        chain = copy.deepcopy(inputs["chain"])
        chain["status"] = "review_chain_integrity_attention_required"
        chain["chain_integrity_summary"]["issue_count"] = 1
        chain["chain_integrity_summary"]["next_safe_action"] = "Resolve review-chain finding before continuing."
        cockpit = build_python_exam_cockpit_flow(
            python_exam_readiness_console=inputs["readiness"],
            exam_skill_drilldown=inputs["drilldown"],
            exam_workspace_operator_run=inputs["operator"],
            exam_workspace_session_console=inputs["session"],
            review_chain_integrity_check=chain,
            timeline_export_review_packet=inputs["review"],
            timeline_export_receipt_journal_summary=inputs["journal"],
            selected_skill_tag="python_lists",
        )
        report = build_python_exam_live_control_surface(
            python_exam_cockpit_flow=cockpit,
            python_exam_readiness_console=inputs["readiness"],
            exam_skill_drilldown=inputs["drilldown"],
            exam_workspace_operator_run=inputs["operator"],
            exam_workspace_session_console=inputs["session"],
            review_chain_integrity_check=chain,
            timeline_export_review_packet=inputs["review"],
            timeline_export_receipt_journal_summary=inputs["journal"],
            selected_skill_tag="python_lists",
        )

        self.assertEqual(report["status"], "python_exam_live_control_surface_attention")
        self.assertEqual(report["status_lights"]["overall"], "amber")
        self.assertIn("Resolve review-chain", report["next_safe_action"])
        self.assertEqual(report["public_safety_status"], "pass")

    def test_live_control_surface_api_route(self) -> None:
        inputs = cockpit_inputs()
        with tempfile.TemporaryDirectory() as temp_dir:
            console, gate, _decision = ready_start_packet_inputs(temp_dir)
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
        status, report = route_request(
            "/api/unibot/course/python-exam-live-control-surface",
            payload={
                "python_exam_cockpit_flow": cockpit,
                "python_exam_readiness_console": inputs["readiness"],
                "exam_skill_drilldown": inputs["drilldown"],
                "python_exam_local_cycle_operator_workspace_card": workspace_card,
                "exam_workspace_operator_run": inputs["operator"],
                "exam_workspace_session_console": inputs["session"],
                "review_chain_integrity_check": inputs["chain"],
                "timeline_export_review_packet": inputs["review"],
                "timeline_export_receipt_journal_summary": inputs["journal"],
                "selected_skill_tag": "python_lists",
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "python_exam_live_control_surface_ready")
        self.assertEqual(report["local_cycle_operator_workspace_card"]["status"], "python_exam_local_cycle_operator_workspace_card_ready")
        self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
