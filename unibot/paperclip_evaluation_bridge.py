from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .gretel_glm_evolve import GLM_EVOLVE_MODEL_HINT, build_glm_evolve_work_packet
from .public_safety import scan_text


PAPERCLIP_BRIDGE_SCHEMA_VERSION = "unibot-paperclip-evaluation-bridge-v1"
PAPERCLIP_RECEIPT_SCHEMA_VERSION = "unibot-paperclip-evaluation-receipt-v1"
DEFAULT_PROJECT_NAME = "UniBot Socratic Mantel"
ALLOWED_AGENT_ROLES = {
    "GLM Proposal Reviewer",
    "Harness Engineer",
    "Extension QA",
    "Docs/Source-Card Reviewer",
}
ALLOWED_TICKET_STATUSES = {"proposal_ready", "blocked", "needs_codex_review", "discarded"}


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def paperclip_status() -> dict[str, Any]:
    return {
        "schema_version": "unibot-paperclip-status-v1",
        "status": "optional_not_active",
        "paperclip_role": "optional_local_multi_agent_control_board",
        "critical_path": False,
        "chrome_extension_dependency": False,
        "provider_call_executed": False,
        "installation_attempted": False,
        "external_side_effects": False,
        "allowed_ticket_statuses": sorted(ALLOWED_TICKET_STATUSES),
        "allowed_agent_roles": sorted(ALLOWED_AGENT_ROLES),
        "answer": "Paperclip may be evaluated as an optional control plane; UniBot and GLM do not depend on it.",
    }


def build_paperclip_evaluation_request(
    *,
    goal: str = "Review UniBot Socratic Mantel architecture and harness next steps.",
    agent_role: str = "GLM Proposal Reviewer",
    budget_class: str = "small",
    model_hint: str = GLM_EVOLVE_MODEL_HINT,
    work_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    packet = work_packet or build_glm_evolve_work_packet(model_hint=model_hint)
    receipt = packet.get("receipt") if isinstance(packet.get("receipt"), dict) else {}
    work_packet_hash = str(receipt.get("packet_hash") or stable_hash(packet))
    public_code_surfaces = list(((packet.get("knowledge_inventory") or {}).get("public_code_surfaces") or [])[:10])
    public_test_surfaces = list(((packet.get("knowledge_inventory") or {}).get("public_test_surfaces") or [])[:10])
    request = {
        "schema_version": PAPERCLIP_BRIDGE_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "needs_codex_review",
        "project_name": DEFAULT_PROJECT_NAME,
        "agent_role": agent_role if agent_role in ALLOWED_AGENT_ROLES else "GLM Proposal Reviewer",
        "goal": goal[:220],
        "budget_class": budget_class if budget_class in {"small", "medium", "large"} else "small",
        "model_hint": model_hint,
        "work_packet_hash": work_packet_hash,
        "allowed_files": public_code_surfaces,
        "allowed_tests": public_test_surfaces,
        "review_gate": "codex_and_human_review_required_before_apply",
        "critical_path": False,
        "chrome_extension_dependency": False,
        "browser_permissions_requested": [],
        "provider_call_executed": False,
        "paperclip_execution_requested": False,
        "raw_private_context_shared": False,
        "autonomous_apply": False,
        "external_actions_allowed": [],
        "final_go": False,
        "blocked_context": [
            "raw chats",
            "private course data",
            "real exam work",
            "health or accommodation records",
            "credentials",
            "local private paths",
            "confidential Gretel case material",
        ],
        "allowed_output": [
            "proposal summary",
            "patch outline",
            "test plan",
            "risk flags",
            "discarded reason",
        ],
    }
    scan = scan_text(json.dumps(request, ensure_ascii=False), "unibot-paperclip-evaluation-request")
    request["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        request["status"] = "blocked"
        request["public_safety_findings"] = scan.get("findings", [])
    request["receipt"] = build_paperclip_evaluation_receipt(request)
    return request


def validate_paperclip_evaluation_request(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        return {"status": "blocked", "blockers": ["invalid_request_type"]}
    blockers: list[str] = []
    if request.get("agent_role") not in ALLOWED_AGENT_ROLES:
        blockers.append("unsupported_agent_role")
    if bool(request.get("critical_path")) or bool(request.get("chrome_extension_dependency")):
        blockers.append("paperclip_made_critical_path")
    if request.get("browser_permissions_requested"):
        blockers.append("browser_permissions_requested")
    if bool(request.get("provider_call_executed")):
        blockers.append("provider_call_executed")
    if bool(request.get("paperclip_execution_requested")):
        blockers.append("paperclip_execution_requested")
    if bool(request.get("raw_private_context_shared")):
        blockers.append("raw_private_context_requested_or_shared")
    if bool(request.get("autonomous_apply")):
        blockers.append("autonomous_apply_requested")
    if bool(request.get("final_go")):
        blockers.append("final_go_requested")
    if request.get("external_actions_allowed"):
        blockers.append("external_actions_requested")
    text_scan = scan_text(json.dumps(request, ensure_ascii=False), "unibot-paperclip-evaluation-validation")
    if text_scan["status"] != "pass":
        blockers.append("public_safety_scan_failed")
    return {
        "schema_version": "unibot-paperclip-evaluation-validation-v1",
        "status": "blocked" if blockers else "ok",
        "blockers": blockers,
        "public_safety_status": text_scan["status"],
        "public_safety_findings": text_scan.get("findings", []),
        "review_policy": "optional_control_plane_only_codex_and_human_apply_gate",
    }


def build_paperclip_evaluation_receipt(
    request: dict[str, Any],
    *,
    ticket_status: str = "needs_codex_review",
    proposal_available: bool = False,
) -> dict[str, Any]:
    status = ticket_status if ticket_status in ALLOWED_TICKET_STATUSES else "blocked"
    request_hash = stable_hash(
        {
            key: value
            for key, value in request.items()
            if key not in {"generated_at_utc", "receipt", "public_safety_findings"}
        }
    )
    return {
        "schema_version": PAPERCLIP_RECEIPT_SCHEMA_VERSION,
        "project_name_hash": hashlib.sha256(DEFAULT_PROJECT_NAME.encode("utf-8")).hexdigest()[:16],
        "ticket_id_hash": request_hash[:24],
        "agent_role": str(request.get("agent_role") or "GLM Proposal Reviewer"),
        "status": status,
        "cost_class": str(request.get("budget_class") or "small"),
        "model_hint": str(request.get("model_hint") or GLM_EVOLVE_MODEL_HINT),
        "proposal_available": bool(proposal_available),
        "work_packet_hash": str(request.get("work_packet_hash") or "")[:64],
        "provider_call_executed": False,
        "paperclip_execution_executed": False,
        "raw_private_context_shared": False,
        "autonomous_apply": False,
        "external_actions_executed": False,
        "final_go": False,
        "next_local_action": "codex_review_before_any_paperclip_or_provider_execution",
    }


def build_paperclip_evaluation_markdown() -> str:
    status = paperclip_status()
    request = build_paperclip_evaluation_request()
    receipt = request["receipt"]
    roles = "\n".join(f"- {role}" for role in status["allowed_agent_roles"])
    return (
        "# UniBot Paperclip Evaluation Bridge\n\n"
        f"Status: {status['status']}\n\n"
        f"Project: {DEFAULT_PROJECT_NAME}\n\n"
        f"Critical path: {status['critical_path']}\n\n"
        f"Chrome extension dependency: {status['chrome_extension_dependency']}\n\n"
        f"Provider call executed: {request['provider_call_executed']}\n\n"
        f"Ticket status: {receipt['status']}\n\n"
        "## Allowed Agent Roles\n\n"
        f"{roles}\n\n"
        "Policy: Paperclip is an optional local control plane only. It may hold tickets and review roles, "
        "but must not apply code, request private context, publish to GitHub, send messages, or become a browser-extension dependency.\n"
    )
