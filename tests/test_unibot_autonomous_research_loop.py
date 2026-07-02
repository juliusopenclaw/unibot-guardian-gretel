from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.autonomous_research_loop import (  # noqa: E402
    build_autonomous_research_loop,
    build_autonomous_research_markdown,
    build_unibot_intent_contract,
)
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotAutonomousResearchLoopTests(unittest.TestCase):
    def test_intent_contract_names_user_intent_and_always_use_standards(self) -> None:
        contract = build_unibot_intent_contract()
        intent_ids = {item["intent_id"] for item in contract["product_intents"]}

        self.assertEqual(contract["owner"], "Gretel")
        self.assertIn("bachelor-thesis-level research project", contract["north_star"])
        self.assertIn("socratic_integrity_layer", intent_ids)
        self.assertIn("open_science_reproducibility", intent_ids)
        self.assertIn("glm_scientific_engineering", intent_ids)
        self.assertIn("autonomous_quality_loop", intent_ids)
        self.assertIn("public-safety scan", contract["always_use_standards"])
        self.assertIn("readiness check", contract["always_use_standards"])
        self.assertIn("Gretel/GLM proposal-only lane", contract["always_use_standards"])

    def test_autonomous_loop_is_budgeted_public_safe_and_not_external(self) -> None:
        loop = build_autonomous_research_loop()
        payload = json.dumps(loop, ensure_ascii=False)

        self.assertEqual(loop["schema_version"], "unibot-gretel-autonomous-research-loop-v1")
        self.assertEqual(loop["status"], "ready_for_budgeted_recurring_local_runs")
        self.assertEqual(loop["public_safety_status"], "pass")
        self.assertEqual(scan_text(payload, "autonomous-loop")["status"], "pass")
        self.assertEqual(loop["budget_policy"]["cadence"]["recommended_cron"], "every_6_hours")
        self.assertEqual(loop["budget_policy"]["token_policy"]["default_reasoning_effort"], "low")
        self.assertFalse(loop["safety"]["provider_call_executed"])
        self.assertFalse(loop["safety"]["autonomous_github_push"])
        self.assertFalse(loop["safety"]["mail_calendar_chat_actions"])
        self.assertFalse(loop["safety"]["final_go"])
        self.assertIn("publish or push to GitHub without explicit human review", loop["budget_policy"]["blocked_autonomous_actions"])
        self.assertNotIn("/" + "Users/", payload)
        self.assertNotIn("api" + "_key", payload.lower())

    def test_work_queue_is_small_testable_and_harnessed(self) -> None:
        loop = build_autonomous_research_loop()
        queue = loop["work_queue"]
        by_id = {item["work_id"]: item for item in queue}

        self.assertGreaterEqual(len(queue), 13)
        self.assertEqual(by_id["intent_contract_regression_pack"]["status"], "closed_harnessed")
        self.assertEqual(by_id["intent_contract_regression_pack"]["closure_evidence"]["commit"], "fa942b0")
        self.assertEqual(by_id["scientific_evaluation_depth"]["status"], "closed_harnessed")
        self.assertEqual(by_id["scientific_evaluation_depth"]["closure_evidence"]["commit"], "2b6473b")
        self.assertEqual(by_id["github_review_packet_hardening"]["status"], "closed_harnessed")
        self.assertEqual(by_id["github_review_packet_hardening"]["closure_evidence"]["commit"], "9a28675")
        self.assertEqual(by_id["autonomy_progress_memory"]["status"], "closed_harnessed")
        self.assertEqual(by_id["autonomy_progress_memory"]["closure_evidence"]["commit"], "5d16846")
        self.assertEqual(by_id["readiness_perf_guard"]["status"], "closed_harnessed")
        self.assertEqual(by_id["readiness_perf_guard"]["closure_evidence"]["commit"], "c6581a3")
        self.assertEqual(by_id["source_card_drift_guard"]["status"], "closed_harnessed")
        self.assertEqual(by_id["source_card_drift_guard"]["closure_evidence"]["commit"], "afeb0d5")
        self.assertEqual(by_id["bachelor_thesis_evidence_index"]["status"], "closed_harnessed")
        self.assertEqual(by_id["bachelor_thesis_evidence_index"]["closure_evidence"]["commit"], "400fc92")
        self.assertEqual(by_id["readiness_evidence_snapshot"]["status"], "closed_harnessed")
        self.assertEqual(by_id["readiness_evidence_snapshot"]["closure_evidence"]["commit"], "19d6f8c")
        self.assertEqual(by_id["review_board_evidence_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["review_board_evidence_alignment"]["closure_evidence"]["commit"], "f449f88")
        self.assertEqual(by_id["feedback_issue_evidence_traceability"]["status"], "closed_harnessed")
        self.assertEqual(by_id["feedback_issue_evidence_traceability"]["closure_evidence"]["commit"], "99d36ff")
        self.assertEqual(by_id["release_runbook_evidence_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["release_runbook_evidence_alignment"]["closure_evidence"]["commit"], "be671ff")
        self.assertEqual(by_id["compliance_drift_evidence_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["compliance_drift_evidence_alignment"]["closure_evidence"]["commit"], "92cb2f1")
        self.assertEqual(by_id["pilot_protocol_evidence_alignment"]["status"], "ready")
        self.assertEqual(by_id["pilot_protocol_evidence_alignment"]["review_gate"], "pilot_ethics_data_human_review_traceability")
        self.assertEqual(loop["next_recommended_work_id"], "pilot_protocol_evidence_alignment")
        self.assertEqual(loop["receipt"]["closed_harnessed_work_items"], 12)
        self.assertLessEqual(loop["budget_policy"]["cadence"]["max_active_work_item_per_run"], 1)
        for item in queue:
            self.assertIn("acceptance_tests", item)
            self.assertTrue(item["acceptance_tests"])
            self.assertIn("review_gate", item)
            self.assertLessEqual(len(item["allowed_files"]), 4)

    def test_markdown_and_api_routes(self) -> None:
        markdown = build_autonomous_research_markdown()

        self.assertIn("# UniBot Gretel Autonomous Research Loop", markdown)
        self.assertIn("Public safety: pass", markdown)
        self.assertIn("Default reasoning effort: low", markdown)
        self.assertIn("Autonomous GitHub push: False", markdown)
        self.assertIn("Closed harnessed items: 12", markdown)
        self.assertIn("Next recommended work: pilot_protocol_evidence_alignment", markdown)

        status, loop = route_request("/api/unibot/autonomous-research-loop", {})
        self.assertEqual(status, 200)
        self.assertEqual(loop["status"], "ready_for_budgeted_recurring_local_runs")

        status, response = route_request("/api/unibot/autonomous-research-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("North Star", response["markdown"])


if __name__ == "__main__":
    unittest.main()
