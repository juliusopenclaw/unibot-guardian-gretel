from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .gretel_glm_evolve import GLM_EVOLVE_MODEL_HINT, build_glm_evolve_work_packet
from .public_safety import scan_text


PAPERCLIP_BRIDGE_SCHEMA_VERSION = "unibot-paperclip-evaluation-bridge-v1"
PAPERCLIP_RECEIPT_SCHEMA_VERSION = "unibot-paperclip-evaluation-receipt-v1"
PAPERCLIP_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-paperclip-evaluation-bridge-workspace-card-control-alignment-v1"
)
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


def paperclip_control_hash(status_payload: dict[str, Any]) -> str:
    return stable_hash(
        {
            "schema_version": status_payload.get("schema_version", ""),
            "status": status_payload.get("status", ""),
            "paperclip_role": status_payload.get("paperclip_role", ""),
            "critical_path": status_payload.get("critical_path", None),
            "chrome_extension_dependency": status_payload.get("chrome_extension_dependency", None),
            "provider_call_executed": status_payload.get("provider_call_executed", None),
            "installation_attempted": status_payload.get("installation_attempted", None),
            "external_side_effects": status_payload.get("external_side_effects", None),
            "allowed_ticket_statuses": status_payload.get("allowed_ticket_statuses", []),
            "allowed_agent_roles": status_payload.get("allowed_agent_roles", []),
        }
    )


def paperclip_request_receipt_hash(request: dict[str, Any]) -> str:
    return stable_hash(
        {
            "schema_version": request.get("schema_version", ""),
            "status": request.get("status", ""),
            "agent_role": request.get("agent_role", ""),
            "budget_class": request.get("budget_class", ""),
            "model_hint": request.get("model_hint", ""),
            "work_packet_hash": request.get("work_packet_hash", ""),
            "review_gate": request.get("review_gate", ""),
            "receipt": request.get("receipt", {}),
            "critical_path": request.get("critical_path", None),
            "chrome_extension_dependency": request.get("chrome_extension_dependency", None),
            "provider_call_executed": request.get("provider_call_executed", None),
            "paperclip_execution_requested": request.get("paperclip_execution_requested", None),
            "raw_private_context_shared": request.get("raw_private_context_shared", None),
            "autonomous_apply": request.get("autonomous_apply", None),
            "external_actions_allowed": request.get("external_actions_allowed", []),
            "final_go": request.get("final_go", None),
        }
    )


def synthetic_paperclip_workspace_card() -> dict[str, Any]:
    preview_hash = hashlib.sha256(b"synthetic paperclip workspace card").hexdigest()
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "pandas",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic Paperclip control-plane prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "pandas",
            "next_safe_action": "review_paperclip_control_hashes_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_paperclip_status_and_receipt_before_public_claim_use",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__PAPERCLIP_REQUEST_RECEIPT_HASH__",
            "checkpoint_hash": "__PAPERCLIP_CONTROL_HASH__",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "zai-glm-52"],
            "source_anchor_count": 3,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": "A2",
            "preview_hash": preview_hash,
        },
    }


def safe_paperclip_workspace_card(
    workspace_card: dict[str, Any],
    *,
    control_hash: str = "",
    request_receipt_hash: str = "",
) -> dict[str, Any]:
    summary = workspace_card.get("workspace_card_summary", {}) if isinstance(workspace_card.get("workspace_card_summary"), dict) else {}
    ledger = workspace_card.get("help_ledger_preview", {}) if isinstance(workspace_card.get("help_ledger_preview"), dict) else {}
    if not summary and (
        workspace_card.get("help_ledger_preview_hash") is not None
        or workspace_card.get("ready_for_operator_prefill") is not None
        or workspace_card.get("help_ledger_preview_status") is not None
    ):
        summary = workspace_card
    checkpoint_hash = str(summary.get("checkpoint_hash", ""))
    task_hash = str(summary.get("task_hash", ""))
    if control_hash and checkpoint_hash == "__PAPERCLIP_CONTROL_HASH__":
        checkpoint_hash = control_hash
    if request_receipt_hash and task_hash == "__PAPERCLIP_REQUEST_RECEIPT_HASH__":
        task_hash = request_receipt_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", "keep_blocked")),
        "recommendation_reason": str(summary.get("recommendation_reason", "missing_paperclip_control_gate")),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "help_ledger_preview_status": str(summary.get("help_ledger_preview_status", ledger.get("status", "missing"))),
        "next_safe_action": str(summary.get("next_safe_action", "")),
        "next_safe_user_action": str(summary.get("next_safe_user_action", "")),
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", "")),
        "operator_run_method": str(summary.get("operator_run_method", "POST")),
        "help_level": str(summary.get("help_level", ledger.get("help_level", "A2"))),
        "task_hash": task_hash,
        "checkpoint_hash": checkpoint_hash,
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "help_ledger_preview_hash": str(summary.get("help_ledger_preview_hash", ledger.get("preview_hash", ""))),
        "not_cleared_receipt": bool(workspace_card.get("not_cleared_receipt", True)),
        "exam_deployment_status": "not_cleared",
        "raw_workspace_card_returned": False,
    }


def build_paperclip_workspace_card_control_alignment(
    request: dict[str, Any] | None = None,
    status_payload: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status_payload = status_payload if isinstance(status_payload, dict) else paperclip_status()
    request = request if isinstance(request, dict) else build_paperclip_evaluation_request()
    control_hash = paperclip_control_hash(status_payload)
    receipt_hash = paperclip_request_receipt_hash(request)
    workspace_card = safe_paperclip_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else synthetic_paperclip_workspace_card(),
        control_hash=control_hash,
        request_receipt_hash=receipt_hash,
    )
    receipt = request.get("receipt", {}) if isinstance(request.get("receipt"), dict) else {}
    workspace_card_readiness_gate_linked = (
        workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and workspace_card.get("help_ledger_preview_hash") != ""
        and workspace_card.get("exam_deployment_status") == "not_cleared"
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card.get("raw_workspace_card_returned") is False
    )
    contracts = {
        "paperclip_optional_control_plane_only": status_payload.get("status") == "optional_not_active"
        and status_payload.get("critical_path") is False
        and status_payload.get("chrome_extension_dependency") is False
        and status_payload.get("provider_call_executed") is False
        and status_payload.get("installation_attempted") is False
        and status_payload.get("external_side_effects") is False,
        "paperclip_request_proposal_only": request.get("status") == "needs_codex_review"
        and request.get("public_safety_status") == "pass"
        and request.get("critical_path") is False
        and request.get("chrome_extension_dependency") is False
        and request.get("browser_permissions_requested") == []
        and request.get("provider_call_executed") is False
        and request.get("paperclip_execution_requested") is False
        and request.get("raw_private_context_shared") is False
        and request.get("autonomous_apply") is False
        and request.get("external_actions_allowed") == []
        and request.get("final_go") is False,
        "paperclip_receipt_no_execution": receipt.get("status") in ALLOWED_TICKET_STATUSES
        and receipt.get("provider_call_executed") is False
        and receipt.get("paperclip_execution_executed") is False
        and receipt.get("raw_private_context_shared") is False
        and receipt.get("autonomous_apply") is False
        and receipt.get("external_actions_executed") is False
        and receipt.get("final_go") is False,
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_paperclip_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("checkpoint_hash") == control_hash
        and workspace_card.get("task_hash") == receipt_hash,
        "workspace_card_public_metadata_only": workspace_card.get("raw_workspace_card_returned") is False,
        "high_stakes_boundaries_blocked": workspace_card.get("exam_deployment_status") == "not_cleared",
    }
    alignment = {
        "schema_version": PAPERCLIP_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION,
        "status": "ready",
        "paperclip_status": status_payload.get("status", "missing"),
        "request_status": request.get("status", "missing"),
        "ticket_status": receipt.get("status", "missing"),
        "control_hash": control_hash,
        "request_receipt_hash": receipt_hash,
        "model_hint": request.get("model_hint", ""),
        "agent_role": request.get("agent_role", ""),
        "budget_class": request.get("budget_class", ""),
        "critical_path": request.get("critical_path", None),
        "chrome_extension_dependency": request.get("chrome_extension_dependency", None),
        "provider_call_executed": request.get("provider_call_executed", None),
        "paperclip_execution_requested": request.get("paperclip_execution_requested", None),
        "raw_private_context_shared": request.get("raw_private_context_shared", None),
        "autonomous_apply": request.get("autonomous_apply", None),
        "final_go": request.get("final_go", None),
        "required_readiness_check_ids": [
            "paperclip_evaluation_bridge",
            "python_exam_local_cycle_operator_workspace_card",
            "gretel_glm_evolve_lane",
            "gretel_autonomous_research_loop",
        ],
        "required_human_gates": [
            "codex_review_required_before_apply",
            "human_review_required_before_provider_call",
            "public_safety_required",
            "paperclip_runtime_activation_requires_explicit_go",
            "exam_clearance_requires_written_authority_clearance",
        ],
        "blocked_claims": [
            "raw private course text publication",
            "contact data publication",
            "local path publication",
            "provider call",
            "Paperclip runtime activation",
            "autonomous publication",
            "approval claim",
            "exam clearance claim",
            "grading",
            "proctoring",
            "KI-detection evidence",
            "exam deployment",
        ],
        "contracts": contracts,
        "failed_contract_ids": sorted(contract_id for contract_id, passed in contracts.items() if not passed),
        "workspace_card_status": workspace_card["status"],
        "workspace_card_selected_skill_tag": workspace_card["selected_skill_tag"],
        "workspace_card_ready_for_operator_prefill": workspace_card["ready_for_operator_prefill"],
        "workspace_card_help_ledger_status": workspace_card["help_ledger_preview_status"],
        "workspace_card_help_ledger_hash_present": workspace_card["help_ledger_preview_hash"] != "",
        "workspace_card_operator_prefill_hash_present": workspace_card["task_hash"] != ""
        and workspace_card["checkpoint_hash"] != "",
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_paperclip_gate_linked": contracts["workspace_card_paperclip_gate_linked"],
        "workspace_card_readiness_gate_claim_linked": "python_exam_local_cycle_operator_workspace_card"
        in [
            "paperclip_evaluation_bridge",
            "python_exam_local_cycle_operator_workspace_card",
            "gretel_glm_evolve_lane",
            "gretel_autonomous_research_loop",
        ],
        "raw_workspace_card_returned": workspace_card["raw_workspace_card_returned"],
        "public_language": (
            "Paperclip bridge claims are hash-only review aids for optional control-plane status and request receipts; "
            "they do not authorize runtime activation, provider calls, public release, university submission, or exam use."
        ),
    }
    if alignment["failed_contract_ids"]:
        alignment["status"] = "blocked"
    scan = scan_text(json.dumps(alignment, ensure_ascii=False), "paperclip-workspace-card-control-alignment")
    alignment["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked"
        alignment["public_safety_findings"] = scan["findings"]
    return alignment


def build_paperclip_evaluation_markdown() -> str:
    status = paperclip_status()
    request = build_paperclip_evaluation_request()
    alignment = build_paperclip_workspace_card_control_alignment(request, status)
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
        f"Workspace-card gate linked: {alignment['workspace_card_paperclip_gate_linked']}\n\n"
        "## Allowed Agent Roles\n\n"
        f"{roles}\n\n"
        "Policy: Paperclip is an optional local control plane only. It may hold tickets and review roles, "
        "but must not apply code, request private context, publish to GitHub, send messages, or become a browser-extension dependency.\n"
    )
