from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.gretel_glm_evolve import (  # noqa: E402
    build_glm_evolve_markdown,
    build_glm_evolve_work_packet,
    build_glm_provider_redaction_alignment,
    build_glm_rsi_workboard,
    build_public_knowledge_inventory,
    validate_glm_evolve_proposal,
)
from unibot.public_safety import scan_text  # noqa: E402
from unibot.publication import build_publication_package  # noqa: E402
from unibot.readiness import run_readiness_check  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotGretelGlmEvolveTests(unittest.TestCase):
    def test_public_knowledge_inventory_summarizes_existing_unibot_contracts(self) -> None:
        inventory = build_public_knowledge_inventory()
        doc_names = set(inventory["public_docs"])
        rule_ids = [rule["rule_id"] for rule in inventory["golden_rules"]]

        self.assertEqual(inventory["status"], "ready")
        self.assertEqual(rule_ids, ["GR1", "GR2", "GR3"])
        self.assertIn("docs/unibot/UNIBOT_GOLDEN_RULES.md", doc_names)
        self.assertIn("docs/unibot/UNIBOT_PIPELINE.md", doc_names)
        self.assertIn("unibot/public_safety.py", inventory["public_code_surfaces"])

    def test_work_packet_is_public_safe_and_proposal_only(self) -> None:
        packet = build_glm_evolve_work_packet()
        payload = json.dumps(packet, ensure_ascii=False)

        self.assertEqual(packet["schema_version"], "unibot-gretel-glm-evolve-v1")
        self.assertEqual(packet["status"], "prepared_no_provider_call")
        self.assertEqual(packet["model_hint"], "zai/glm-5.2")
        self.assertFalse(packet["provider_call_executed"])
        self.assertFalse(packet["raw_private_context_shared"])
        self.assertFalse(packet["autonomous_apply"])
        self.assertEqual(packet["external_actions_allowed"], [])
        self.assertEqual(packet["public_safety_status"], "pass")
        self.assertEqual(scan_text(payload, "glm-evolve-packet")["status"], "pass")
        self.assertNotIn("/" + "Users/", payload)
        self.assertNotIn("FM Loge", payload)
        self.assertNotIn("solution_key", payload)
        self.assertIn("receipt", packet)
        self.assertEqual(packet["receipt"]["provider_call_executed"], False)

    def test_provider_redaction_alignment_maps_glm_locks_to_review_gates(self) -> None:
        packet = build_glm_evolve_work_packet()
        workboard = build_glm_rsi_workboard()
        alignment = build_glm_provider_redaction_alignment(packet, workboard)
        by_section = {section["section_id"]: section for section in alignment["sections"]}

        self.assertEqual(alignment["schema_version"], "unibot-glm-provider-redaction-alignment-v1")
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["missing_packet_keys"], [])
        self.assertEqual(alignment["missing_workboard_keys"], [])
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertTrue(alignment["contracts"]["redaction_receipt_ready"])
        self.assertTrue(alignment["contracts"]["provider_call_locked"])
        self.assertTrue(alignment["contracts"]["proposal_only_route"])
        self.assertTrue(alignment["contracts"]["external_actions_locked"])
        self.assertTrue(alignment["contracts"]["final_go_locked"])
        self.assertIn("provider_call_requires_explicit_go_and_redaction_receipt", alignment["required_human_gates"])
        self.assertIn("gretel_glm_rsi_visibility_workboard", alignment["required_readiness_check_ids"])
        self.assertIn("zai-glm-52", by_section["glm_source_basis"]["source_card_ids"])
        self.assertIn("blocked_context", by_section["redaction_receipt"]["packet_keys"])

    def test_validator_accepts_safe_proposal_and_blocks_unsafe_proposal(self) -> None:
        safe = {
            "recommendation": "Add one public-source regression test.",
            "patch_outline": ["Add a test fixture for source-card completeness."],
            "test_plan": ["Run focused source-card tests."],
            "risk_flags": ["Exam deployment remains not cleared."],
            "confidence": "medium",
        }
        accepted = validate_glm_evolve_proposal(safe)
        self.assertEqual(accepted["status"], "ok")
        self.assertEqual(accepted["blockers"], [])

        unsafe = {
            **safe,
            "autonomous_apply": True,
            "raw_private_context_shared": True,
            "final_go": True,
            "external_actions": ["publish_issue"],
        }
        blocked = validate_glm_evolve_proposal(unsafe)
        self.assertEqual(blocked["status"], "blocked")
        self.assertIn("autonomous_apply_requested", blocked["blockers"])
        self.assertIn("raw_private_context_requested_or_shared", blocked["blockers"])
        self.assertIn("final_go_requested", blocked["blockers"])
        self.assertIn("external_actions_requested", blocked["blockers"])

    def test_api_routes_return_work_packet_validation_and_markdown(self) -> None:
        status, packet = route_request("/api/unibot/gretel-glm-evolve/work-packet", {})
        self.assertEqual(status, 200)
        self.assertEqual(packet["status"], "prepared_no_provider_call")

        status, validation = route_request(
            "/api/unibot/gretel-glm-evolve/validate-proposal",
            {
                "proposal": {
                    "recommendation": "Keep it proposal-only.",
                    "patch_outline": [],
                    "test_plan": [],
                    "risk_flags": [],
                    "confidence": "high",
                }
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(validation["status"], "ok")

        status, response = route_request("/api/unibot/gretel-glm-evolve/markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("UniBot Gretel GLM Evolve Lane", response["markdown"])
        self.assertIn("Provider call executed: False", build_glm_evolve_markdown())
        self.assertIn("Provider Redaction Alignment", build_glm_evolve_markdown())

    def test_glm_rsi_workboard_is_visible_and_proposal_only(self) -> None:
        workboard = build_glm_rsi_workboard()
        payload = json.dumps(workboard, ensure_ascii=False)

        self.assertEqual("unibot-gretel-glm-rsi-workboard-v1", workboard["schema_version"])
        self.assertEqual("visible", workboard["status"])
        self.assertEqual("pass", workboard["public_safety_status"])
        self.assertGreaterEqual(workboard["active_item_count"], 1)
        self.assertGreaterEqual(workboard["blocked_item_count"], 1)
        self.assertFalse(workboard["safety"]["provider_call_executed"])
        self.assertFalse(workboard["safety"]["provider_call_allowed_now"])
        self.assertFalse(workboard["safety"]["autonomous_apply"])
        self.assertFalse(workboard["safety"]["final_go"])
        self.assertFalse(workboard["visibility_surfaces"]["chrome_extension_dependency"])
        self.assertNotIn("/" + "Users/", payload)
        self.assertNotIn("api" + "_key:", payload)
        self.assertNotIn("solution key", payload.lower())

    def test_workboard_api_route(self) -> None:
        status, workboard = route_request("/api/unibot/gretel-glm-evolve/workboard", {})

        self.assertEqual(status, 200)
        self.assertEqual(workboard["status"], "visible")
        self.assertEqual(workboard["public_safety_status"], "pass")
        self.assertFalse(workboard["safety"]["provider_call_executed"])

    def test_publication_and_readiness_gate_the_evolve_lane(self) -> None:
        package = build_publication_package()
        readiness = run_readiness_check()
        check_ids = {check["check_id"] for check in readiness["checks"]}

        self.assertIn("gretel_glm_evolve_lane", package)
        self.assertIn("gretel_glm_rsi_workboard", package)
        self.assertTrue(package["release_gates"]["gretel_glm_evolve_lane_ready"])
        self.assertTrue(package["release_gates"]["gretel_glm_rsi_workboard_ready"])
        self.assertIn("gretel_glm_evolve_lane", package["included_artifacts"])
        self.assertIn("gretel_glm_rsi_workboard", package["included_artifacts"])
        self.assertIn("gretel_glm_evolve_lane", check_ids)
        self.assertIn("gretel_glm_rsi_visibility_workboard", check_ids)
        glm_check = next(check for check in readiness["checks"] if check["check_id"] == "gretel_glm_evolve_lane")
        self.assertEqual(glm_check["evidence"]["provider_redaction_alignment_status"], "ready")
        self.assertEqual(readiness["status"], "public_draft_ready")


if __name__ == "__main__":
    unittest.main()
