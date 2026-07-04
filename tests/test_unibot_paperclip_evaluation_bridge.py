from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.paperclip_evaluation_bridge import (  # noqa: E402
    ALLOWED_TICKET_STATUSES,
    build_paperclip_workspace_card_control_alignment,
    build_paperclip_evaluation_markdown,
    build_paperclip_evaluation_request,
    paperclip_control_hash,
    paperclip_request_receipt_hash,
    paperclip_status,
    synthetic_paperclip_workspace_card,
    validate_paperclip_evaluation_request,
)
from unibot.public_safety import scan_text  # noqa: E402
from unibot.publication import build_publication_package  # noqa: E402
from unibot.readiness import run_readiness_check  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotPaperclipEvaluationBridgeTests(unittest.TestCase):
    def test_status_is_optional_and_not_extension_dependency(self) -> None:
        status = paperclip_status()

        self.assertEqual("optional_not_active", status["status"])
        self.assertFalse(status["critical_path"])
        self.assertFalse(status["chrome_extension_dependency"])
        self.assertFalse(status["provider_call_executed"])
        self.assertFalse(status["installation_attempted"])

    def test_evaluation_request_is_public_safe_proposal_only(self) -> None:
        request = build_paperclip_evaluation_request(
            goal="Review UniBot Chrome Extension safety and harness routing.",
            agent_role="Extension QA",
            budget_class="small",
        )
        payload = json.dumps(request, ensure_ascii=False)

        self.assertEqual("unibot-paperclip-evaluation-bridge-v1", request["schema_version"])
        self.assertEqual("needs_codex_review", request["status"])
        self.assertEqual("Extension QA", request["agent_role"])
        self.assertEqual("small", request["budget_class"])
        self.assertEqual("zai/glm-5.2", request["model_hint"])
        self.assertFalse(request["critical_path"])
        self.assertFalse(request["chrome_extension_dependency"])
        self.assertEqual([], request["browser_permissions_requested"])
        self.assertFalse(request["provider_call_executed"])
        self.assertFalse(request["paperclip_execution_requested"])
        self.assertFalse(request["raw_private_context_shared"])
        self.assertFalse(request["autonomous_apply"])
        self.assertFalse(request["final_go"])
        self.assertEqual("pass", request["public_safety_status"])
        self.assertIn(request["receipt"]["status"], ALLOWED_TICKET_STATUSES)
        self.assertEqual("pass", scan_text(payload, "paperclip-bridge-test")["status"])
        self.assertNotIn("/" + "Users/", payload)
        self.assertNotIn("F" + "M Loge", payload)
        self.assertNotIn("api_key", payload)

    def test_validator_blocks_critical_path_private_context_and_autonomous_actions(self) -> None:
        request = build_paperclip_evaluation_request()
        unsafe = {
            **request,
            "critical_path": True,
            "chrome_extension_dependency": True,
            "browser_permissions_requested": ["activeTab"],
            "provider_call_executed": True,
            "paperclip_execution_requested": True,
            "raw_private_context_shared": True,
            "autonomous_apply": True,
            "final_go": True,
            "external_actions_allowed": ["publish_github_issue"],
        }

        validation = validate_paperclip_evaluation_request(unsafe)

        self.assertEqual("blocked", validation["status"])
        self.assertIn("paperclip_made_critical_path", validation["blockers"])
        self.assertIn("browser_permissions_requested", validation["blockers"])
        self.assertIn("provider_call_executed", validation["blockers"])
        self.assertIn("paperclip_execution_requested", validation["blockers"])
        self.assertIn("raw_private_context_requested_or_shared", validation["blockers"])
        self.assertIn("autonomous_apply_requested", validation["blockers"])
        self.assertIn("final_go_requested", validation["blockers"])
        self.assertIn("external_actions_requested", validation["blockers"])

    def test_workspace_card_control_alignment_links_status_and_receipt_hashes(self) -> None:
        status = paperclip_status()
        request = build_paperclip_evaluation_request()

        alignment = build_paperclip_workspace_card_control_alignment(request, status)

        self.assertEqual(
            "unibot-paperclip-evaluation-bridge-workspace-card-control-alignment-v1",
            alignment["schema_version"],
        )
        self.assertEqual("ready", alignment["status"])
        self.assertEqual("pass", alignment["public_safety_status"])
        self.assertEqual([], alignment["failed_contract_ids"])
        self.assertEqual("optional_not_active", alignment["paperclip_status"])
        self.assertEqual("needs_codex_review", alignment["request_status"])
        self.assertEqual("needs_codex_review", alignment["ticket_status"])
        self.assertEqual(paperclip_control_hash(status), alignment["control_hash"])
        self.assertEqual(paperclip_request_receipt_hash(request), alignment["request_receipt_hash"])
        self.assertIn("paperclip_evaluation_bridge", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertIn("paperclip_runtime_activation_requires_explicit_go", alignment["required_human_gates"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertTrue(alignment["workspace_card_paperclip_gate_linked"])
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual("help_ledger_preview_ready", alignment["workspace_card_help_ledger_status"])
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_operator_prefill_hash_present"])
        self.assertFalse(alignment["raw_workspace_card_returned"])
        self.assertIn("Paperclip runtime activation", alignment["blocked_claims"])

    def test_workspace_card_control_alignment_rejects_unlinked_hashes(self) -> None:
        status = paperclip_status()
        request = build_paperclip_evaluation_request()
        workspace_card = synthetic_paperclip_workspace_card()
        workspace_card["workspace_card_summary"]["checkpoint_hash"] = "wrong-control-hash"
        workspace_card["workspace_card_summary"]["task_hash"] = "wrong-request-hash"

        alignment = build_paperclip_workspace_card_control_alignment(request, status, workspace_card)

        self.assertEqual("blocked", alignment["status"])
        self.assertIn("workspace_card_paperclip_gate_linked", alignment["failed_contract_ids"])
        self.assertFalse(alignment["workspace_card_paperclip_gate_linked"])
        self.assertFalse(alignment["raw_workspace_card_returned"])

    def test_api_routes_publication_and_readiness_include_paperclip_bridge(self) -> None:
        status_code, status = route_request("/api/unibot/paperclip/status", {})
        self.assertEqual(200, status_code)
        self.assertEqual("optional_not_active", status["status"])

        status_code, request = route_request("/api/unibot/paperclip/evaluation-request", {})
        self.assertEqual(200, status_code)
        self.assertEqual("needs_codex_review", request["status"])

        status_code, validation = route_request("/api/unibot/paperclip/validate-request", {"request": request})
        self.assertEqual(200, status_code)
        self.assertEqual("ok", validation["status"])

        status_code, markdown = route_request("/api/unibot/paperclip/markdown", {})
        self.assertEqual(200, status_code)
        self.assertIn("UniBot Paperclip Evaluation Bridge", markdown["markdown"])
        self.assertIn("Provider call executed: False", build_paperclip_evaluation_markdown())
        self.assertIn("Workspace-card gate linked: True", build_paperclip_evaluation_markdown())

        package = build_publication_package()
        readiness = run_readiness_check()
        check_ids = {check["check_id"] for check in readiness["checks"]}

        self.assertIn("paperclip_evaluation_bridge", package)
        self.assertTrue(package["release_gates"]["paperclip_evaluation_bridge_ready"])
        self.assertIn("paperclip_evaluation_bridge", package["included_artifacts"])
        self.assertIn("paperclip_evaluation_bridge", check_ids)
        self.assertEqual("public_draft_ready", readiness["status"])
        paperclip = next(check for check in readiness["checks"] if check["check_id"] == "paperclip_evaluation_bridge")
        self.assertEqual("ready", paperclip["evidence"]["workspace_card_control_alignment_status"])
        self.assertTrue(paperclip["evidence"]["workspace_card_paperclip_gate_linked"])
        self.assertFalse(paperclip["evidence"]["raw_workspace_card_returned"])


if __name__ == "__main__":
    unittest.main()
