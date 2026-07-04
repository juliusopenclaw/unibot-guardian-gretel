from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .python_exam_operator_gate_decision_receipt import build_python_exam_operator_gate_decision_receipt
from .python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate
from .public_safety import scan_text
from .source_cards import get_source_card


PYTHON_EXAM_LOCAL_CYCLE_START_PACKET_SCHEMA_VERSION = "unibot-python-exam-local-cycle-start-packet-v1"
PYTHON_EXAM_LOCAL_CYCLE_START_PACKET_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-python-exam-local-cycle-start-packet-release-review-board-claim-alignment-v1"
)
PYTHON_EXAM_LOCAL_CYCLE_START_PACKET_ENDPOINT = "/api/unibot/course/python-exam-local-cycle-start-packet"


def build_python_exam_local_cycle_start_packet(
    *,
    python_exam_safe_cycle_console: dict[str, Any] | None = None,
    python_exam_safe_cycle_operator_gate: dict[str, Any] | None = None,
    python_exam_operator_gate_decision_receipt: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    console = python_exam_safe_cycle_console if isinstance(python_exam_safe_cycle_console, dict) else {}
    gate = python_exam_safe_cycle_operator_gate if isinstance(python_exam_safe_cycle_operator_gate, dict) else {}
    decision = python_exam_operator_gate_decision_receipt if isinstance(python_exam_operator_gate_decision_receipt, dict) else {}
    selected = effective_selected_skill(selected_skill_tag, decision, gate, console)
    cycle = safe_cycle(console)
    gate_view = safe_gate(gate)
    decision_view = safe_decision(decision)
    summary = start_summary(
        selected_skill_tag=selected,
        cycle=cycle,
        gate=gate_view,
        decision=decision_view,
    )
    packet = {
        "schema_version": PYTHON_EXAM_LOCAL_CYCLE_START_PACKET_SCHEMA_VERSION,
        "artifact_type": "python_exam_local_cycle_start_packet",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_local_cycle_start_packet_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Local Cycle Start Packet. It combines Safe Cycle Console, Operator Gate, and Operator "
            "Gate Decision Receipt into one final metadata-only start packet for the next local exam work cycle. "
            "It only states whether the local cycle is still blocked for confirmation or would be ready after human "
            "confirmation. It contains skill tag, next safe action, task/checkpoint hashes, Source-Card anchors, "
            "A0-A2 help level, Gate and Decision receipt hashes, open confirmations, confirmed hash metadata, and "
            "the next safe user action. It never executes a local action and never returns raw queries, course raw "
            "text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, "
            "rankings, grades, proctoring, AI detection, automatic grading, or exam clearance."
        ),
        "local_cycle_start_packet_endpoint": PYTHON_EXAM_LOCAL_CYCLE_START_PACKET_ENDPOINT,
        "selected_skill_tag": selected,
        "local_cycle_start_summary": summary,
        "start_packet": {
            "selected_skill_tag": selected,
            "start_status": summary["start_status"],
            "next_safe_action": summary["next_safe_action"],
            "task_hash": summary["selected_task_hash"],
            "checkpoint_hash": summary["checkpoint_hash"],
            "source_card_ids": cycle["source_card_ids"],
            "source_anchor_count": cycle["source_anchor_count"],
            "help_level": summary["help_level"],
            "gate_receipt_id": gate_view["gate_receipt_id"],
            "gate_receipt_hash": gate_view["gate_receipt_hash"],
            "decision_receipt_id": decision_view["decision_receipt_id"],
            "decision_receipt_hash": decision_view["decision_receipt_hash"],
            "open_confirmations": decision_view["open_confirmations"],
            "confirmed_hash_metadata": decision_view["confirmed_hash_metadata"],
            "next_safe_user_action": summary["next_safe_user_action"],
            "blocked_reason": summary["blocked_reason"],
            "a0_a2_only": True,
            "dry_run_default": True,
            "local_writes_requested": False,
            "local_execution_started": False,
            "not_cleared_receipt": True,
            "exam_deployment_status": "not_cleared",
        },
        "source_reports": {
            "safe_cycle_console_status": console.get("status", "missing"),
            "operator_gate_status": gate.get("status", "missing"),
            "decision_receipt_status": decision.get("status", "missing"),
        },
        "local_cycle_start_receipt": start_receipt(summary, cycle, gate_view, decision_view),
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "operator_confirmation_required_for_local_write": True,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "values_returned": False,
        "solutions_returned": False,
        "final_interpretations_returned": False,
        "score_returned": False,
        "percentage_returned": False,
        "ranking_returned": False,
        "grade_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; das Local Cycle Start Packet bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(packet, public_safe=public_safe)
    return packet


def build_python_exam_local_cycle_start_packet_release_claim_alignment(
    open_report: dict[str, Any] | None = None,
    confirmed_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if open_report is None or confirmed_report is None:
        console = synthetic_local_cycle_safe_cycle_console()
        gate = build_python_exam_safe_cycle_operator_gate(
            python_exam_safe_cycle_console=console,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        open_decision = build_python_exam_operator_gate_decision_receipt(
            python_exam_safe_cycle_operator_gate=gate,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        confirmed_decision = build_python_exam_operator_gate_decision_receipt(
            python_exam_safe_cycle_operator_gate=gate,
            confirmed_step_ids=[card["step_id"] for card in gate.get("confirmation_cards", [])],
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        open_report = open_report or build_python_exam_local_cycle_start_packet(
            python_exam_safe_cycle_console=console,
            python_exam_safe_cycle_operator_gate=gate,
            python_exam_operator_gate_decision_receipt=open_decision,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        confirmed_report = confirmed_report or build_python_exam_local_cycle_start_packet(
            python_exam_safe_cycle_console=console,
            python_exam_safe_cycle_operator_gate=gate,
            python_exam_operator_gate_decision_receipt=confirmed_decision,
            selected_skill_tag="python_lists",
            public_safe=True,
        )

    sections = [
        {
            "section_id": "safe_cycle_gate_decision_trace",
            "summary_claim": "start packet derives from safe-cycle console, operator gate, and decision receipt metadata",
            "source_card_ids": ["dfg-gwp", "vanlehn-2011", "dsk-ai-privacy-2024"],
            "readiness_check_ids": [
                "python_exam_local_cycle_start_packet",
                "exam_workspace_session_console",
                "exam_workspace_operator_run",
                "review_board_packet",
            ],
            "human_gates": ["human_submission_review_required", "datenschutz_review_required_before_real_pilot"],
        },
        {
            "section_id": "operator_confirmation_boundary_trace",
            "summary_claim": "open confirmations keep the local cycle blocked and confirmed packets still do not execute local writes",
            "source_card_ids": ["dfg-gwp", "uoc-hilfsmittel"],
            "readiness_check_ids": ["python_exam_local_cycle_start_packet", "study_session", "exam_boundary"],
            "human_gates": ["human_submission_review_required", "written_university_clearance_required_before_exam_use"],
        },
        {
            "section_id": "hash_only_start_receipt_trace",
            "summary_claim": "start packet publishes only skill tag, safe action, source-card ids, and receipt/checkpoint hashes",
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024"],
            "readiness_check_ids": [
                "python_exam_local_cycle_start_packet",
                "exam_workspace_session_console",
                "external_decision_state",
            ],
            "human_gates": ["public_safety_required", "datenschutz_review_required_before_real_pilot"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "start packet does not publish notebooks, grade, proctor, detect AI use, or clear exam deployment",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": [
                "python_exam_local_cycle_start_packet",
                "evaluation_packet",
                "exam_boundary",
            ],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    open_summary = (
        open_report.get("local_cycle_start_summary", {})
        if isinstance(open_report.get("local_cycle_start_summary"), dict)
        else {}
    )
    open_packet = open_report.get("start_packet", {}) if isinstance(open_report.get("start_packet"), dict) else {}
    open_receipt = (
        open_report.get("local_cycle_start_receipt", {})
        if isinstance(open_report.get("local_cycle_start_receipt"), dict)
        else {}
    )
    open_sources = open_report.get("source_reports", {}) if isinstance(open_report.get("source_reports"), dict) else {}
    confirmed_summary = (
        confirmed_report.get("local_cycle_start_summary", {})
        if isinstance(confirmed_report.get("local_cycle_start_summary"), dict)
        else {}
    )
    confirmed_packet = (
        confirmed_report.get("start_packet", {}) if isinstance(confirmed_report.get("start_packet"), dict) else {}
    )
    confirmed_receipt = (
        confirmed_report.get("local_cycle_start_receipt", {})
        if isinstance(confirmed_report.get("local_cycle_start_receipt"), dict)
        else {}
    )
    blocked_claims = [
        "raw query returned",
        "raw source text returned",
        "raw notebook code returned",
        "raw cell text returned",
        "raw notebook returned",
        "local path returned",
        "unconfirmed local write",
        "local execution started",
        "final solution acceptance",
        "complete code outsourcing",
        "inserted values",
        "final interpretation",
        "score",
        "percentage",
        "ranking",
        "grade",
        "automatic grading",
        "proctoring",
        "KI-detection evidence",
        "Eigenleistung percentage claim",
        "cloud processing",
        "exam deployment",
        "exam clearance",
    ]
    boundary = str(open_report.get("execution_boundary", ""))
    contracts = {
        "open_packet_public_safe": open_report.get("public_safety_status") == "pass",
        "confirmed_packet_public_safe": confirmed_report.get("public_safety_status") == "pass",
        "start_packet_metadata_only_ready": open_report.get("status") == "python_exam_local_cycle_start_packet_ready"
        and open_packet.get("selected_skill_tag") == "python_lists"
        and open_packet.get("source_card_ids") == ["dfg-gwp", "vanlehn-2011"]
        and bool(open_packet.get("task_hash"))
        and bool(open_packet.get("checkpoint_hash"))
        and bool(open_packet.get("gate_receipt_hash"))
        and bool(open_packet.get("decision_receipt_hash"))
        and open_receipt.get("status") == "local_cycle_start_packet_receipt_ready_not_exam_clearance"
        and bool(open_receipt.get("receipt_hash"))
        and open_report.get("dry_run_default") is True
        and open_packet.get("a0_a2_only") is True
        and open_packet.get("help_level") == "A2",
        "open_confirmations_block_local_cycle": open_summary.get("start_status") == "blocked_for_confirmation"
        and open_summary.get("blocked_reason") == "operator_confirmations_open"
        and int(open_summary.get("open_confirmation_count", -1) or 0) == 5
        and int(open_summary.get("confirmed_count", -1) or 0) == 0
        and len(open_packet.get("open_confirmations", [])) == 5
        and open_packet.get("confirmed_hash_metadata") == []
        and open_packet.get("local_writes_requested") is False
        and open_packet.get("local_execution_started") is False,
        "confirmed_packet_still_no_execution": confirmed_summary.get("start_status")
        == "ready_after_human_confirmation"
        and int(confirmed_summary.get("open_confirmation_count", -1) or 0) == 0
        and int(confirmed_summary.get("confirmed_count", -1) or 0) == 5
        and len(confirmed_packet.get("confirmed_hash_metadata", [])) == 5
        and confirmed_report.get("local_writes_requested") is False
        and confirmed_report.get("local_execution_started") is False
        and confirmed_packet.get("local_execution_started") is False
        and confirmed_packet.get("not_cleared_receipt") is True
        and confirmed_receipt.get("not_cleared_receipt") is True,
        "source_gate_decision_receipts_linked": open_sources.get("safe_cycle_console_status")
        == "python_exam_safe_cycle_console_ready"
        and open_sources.get("operator_gate_status") == "python_exam_safe_cycle_operator_gate_ready"
        and open_sources.get("decision_receipt_status") == "python_exam_operator_gate_decision_receipt_ready"
        and open_packet.get("gate_receipt_id")
        and open_packet.get("decision_receipt_id")
        and open_packet.get("not_cleared_receipt") is True
        and open_report.get("operator_confirmation_required_for_local_write") is True,
        "public_outputs_hide_private_start_packet_data": open_report.get("raw_query_returned") is False
        and open_report.get("raw_text_returned") is False
        and open_report.get("raw_cell_returned") is False
        and open_report.get("raw_notebook_returned") is False
        and open_report.get("notebook_code_returned") is False
        and open_report.get("local_paths_returned") is False
        and open_report.get("values_returned") is False
        and open_report.get("solutions_returned") is False
        and open_report.get("final_interpretations_returned") is False
        and "metadata-only" in boundary
        and "never executes a local action" in boundary
        and "never returns raw queries" in boundary,
        "high_stakes_actions_not_started": open_report.get("automatic_grading_started") is False
        and open_report.get("proctoring_started") is False
        and open_report.get("ai_detection_started") is False
        and open_report.get("exam_clearance_claimed") is False
        and open_report.get("score_returned") is False
        and open_report.get("percentage_returned") is False
        and open_report.get("ranking_returned") is False
        and open_report.get("grade_returned") is False
        and open_report.get("exam_deployment_status") == "not_cleared",
        "not_cleared_receipt_present": open_report.get("exam_deployment_status") == "not_cleared"
        and open_packet.get("exam_deployment_status") == "not_cleared"
        and open_receipt.get("exam_deployment_status") == "not_cleared"
        and open_receipt.get("not_cleared_receipt") is True
        and confirmed_report.get("exam_deployment_status") == "not_cleared",
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "open_status": open_report.get("status"),
        "confirmed_status": confirmed_report.get("status"),
        "selected_skill_tag": open_packet.get("selected_skill_tag"),
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "python-exam-local-cycle-start-packet-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": PYTHON_EXAM_LOCAL_CYCLE_START_PACKET_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "open_packet_status": open_report.get("status"),
        "open_packet_public_safety_status": open_report.get("public_safety_status"),
        "confirmed_packet_status": confirmed_report.get("status"),
        "confirmed_packet_public_safety_status": confirmed_report.get("public_safety_status"),
        "exam_deployment_status": open_report.get("exam_deployment_status"),
        "selected_skill_tag": open_packet.get("selected_skill_tag"),
        "open_start_status": open_summary.get("start_status"),
        "open_blocked_reason": open_summary.get("blocked_reason"),
        "open_confirmation_count": open_summary.get("open_confirmation_count"),
        "confirmed_start_status": confirmed_summary.get("start_status"),
        "confirmed_count": confirmed_summary.get("confirmed_count"),
        "task_hash_present": bool(open_packet.get("task_hash")),
        "checkpoint_hash_present": bool(open_packet.get("checkpoint_hash")),
        "source_card_ids": open_packet.get("source_card_ids", []),
        "source_anchor_count": open_packet.get("source_anchor_count", 0),
        "help_level": open_packet.get("help_level"),
        "gate_receipt_id_present": bool(open_packet.get("gate_receipt_id")),
        "decision_receipt_id_present": bool(open_packet.get("decision_receipt_id")),
        "start_receipt_status": open_receipt.get("status"),
        "start_receipt_hash_present": bool(open_receipt.get("receipt_hash")),
        "not_cleared_receipt": bool(open_receipt.get("not_cleared_receipt", False)),
        "safe_cycle_console_status": open_sources.get("safe_cycle_console_status"),
        "operator_gate_status": open_sources.get("operator_gate_status"),
        "decision_receipt_status": open_sources.get("decision_receipt_status"),
        "dry_run_default": bool(open_report.get("dry_run_default", False)),
        "local_writes_requested": bool(open_report.get("local_writes_requested", True)),
        "local_execution_started": bool(open_report.get("local_execution_started", True)),
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "failed_contract_ids": failed_contract_ids,
        "required_readiness_check_ids": sorted(
            {check_id for section in sections for check_id in section["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({gate for section in sections for gate in section["human_gates"]}),
        "blocked_claims": blocked_claims,
        "public_safety_status": scan["status"],
        "policy": (
            "Python exam local-cycle start packet is a dry-run, metadata-only preparation surface. It may link "
            "safe-cycle, operator-gate, decision-receipt, source-card, task/checkpoint hash, and confirmation "
            "metadata, but it does not start local writes, publish raw notebook/query data, grade, proctor, detect "
            "AI use, claim Eigenleistung percentages, or clear exams."
        ),
    }


def safe_cycle(console: dict[str, Any]) -> dict[str, Any]:
    summary = console.get("safe_cycle_summary", {}) if isinstance(console.get("safe_cycle_summary"), dict) else {}
    view = console.get("current_cycle_view", {}) if isinstance(console.get("current_cycle_view"), dict) else {}
    preview = view.get("preview", {}) if isinstance(view.get("preview"), dict) else {}
    return {
        "status": console.get("status", "missing"),
        "cycle_status": summary.get("cycle_status", "missing"),
        "next_safe_action": safe_action(str(summary.get("next_safe_action") or preview.get("action") or "")),
        "route": str(summary.get("route") or preview.get("route") or "missing"),
        "endpoint": str(summary.get("endpoint") or preview.get("endpoint") or ""),
        "selected_task_hash": str(summary.get("selected_task_hash") or preview.get("selected_task_hash") or ""),
        "checkpoint_hash": str(summary.get("checkpoint_hash") or preview.get("checkpoint_hash") or ""),
        "source_card_ids": [str(item) for item in (preview.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(preview.get("source_anchor_count", 0) or 0),
        "help_level": safe_help_level(str(summary.get("help_level") or preview.get("help_level") or "A2")),
        "ready": bool(summary.get("ready", False)),
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def safe_gate(gate: dict[str, Any]) -> dict[str, Any]:
    summary = gate.get("operator_gate_summary", {}) if isinstance(gate.get("operator_gate_summary"), dict) else {}
    receipt = gate.get("operator_gate_receipt", {}) if isinstance(gate.get("operator_gate_receipt"), dict) else {}
    return {
        "status": gate.get("status", "missing"),
        "gate_status": summary.get("gate_status", "missing"),
        "confirmation_card_count": int(summary.get("confirmation_card_count", 0) or 0),
        "confirmed_count": int(summary.get("confirmed_count", 0) or 0),
        "gate_receipt_id": str(receipt.get("receipt_id", "")),
        "gate_receipt_hash": str(receipt.get("receipt_hash", "")),
        "ready": bool(summary.get("ready", False)),
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def safe_decision(decision: dict[str, Any]) -> dict[str, Any]:
    summary = decision.get("decision_receipt_summary", {}) if isinstance(decision.get("decision_receipt_summary"), dict) else {}
    receipt = decision.get("operator_decision_receipt", {}) if isinstance(decision.get("operator_decision_receipt"), dict) else {}
    next_action = decision.get("next_allowed_local_action", {}) if isinstance(decision.get("next_allowed_local_action"), dict) else {}
    open_items = [
        safe_decision_step(item)
        for item in (decision.get("unconfirmed_steps", []) or [])
        if isinstance(item, dict)
    ]
    confirmed_items = [
        safe_decision_step(item)
        for item in (decision.get("confirmed_step_hash_metadata", []) or [])
        if isinstance(item, dict)
    ]
    return {
        "status": decision.get("status", "missing"),
        "decision_status": summary.get("decision_status", "missing"),
        "confirmed_count": int(summary.get("confirmed_count", 0) or 0),
        "unconfirmed_count": int(summary.get("unconfirmed_count", len(open_items)) or 0),
        "next_confirmable_step_id": str(summary.get("next_confirmable_step_id") or next_action.get("step_id") or ""),
        "next_allowed_action": str(summary.get("next_allowed_local_action") or next_action.get("action") or "review_operator_gate_cards"),
        "decision_receipt_id": str(receipt.get("receipt_id", "")),
        "decision_receipt_hash": str(receipt.get("receipt_hash", "")),
        "open_confirmations": open_items,
        "confirmed_hash_metadata": confirmed_items,
        "ready": bool(summary.get("ready", False)),
        "local_writes_started": False,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def safe_decision_step(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_id": str(item.get("step_id", "")),
        "action": str(item.get("action", "")),
        "card_hash": str(item.get("card_hash", "")),
        "selected_task_hash": str(item.get("selected_task_hash", "")),
        "checkpoint_hash": str(item.get("checkpoint_hash", "")),
        "help_level": safe_help_level(str(item.get("help_level", "A2"))),
        "operator_confirmed": bool(item.get("operator_confirmed", False)),
        "write_started": False,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def start_summary(
    *,
    selected_skill_tag: str,
    cycle: dict[str, Any],
    gate: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    unconfirmed = int(decision.get("unconfirmed_count", 0) or 0)
    all_inputs_ready = cycle["status"] == "python_exam_safe_cycle_console_ready" and gate["status"] == "python_exam_safe_cycle_operator_gate_ready" and decision["status"] == "python_exam_operator_gate_decision_receipt_ready"
    start_status = "blocked_for_confirmation" if unconfirmed > 0 or not all_inputs_ready else "ready_after_human_confirmation"
    blocked_reason = "operator_confirmations_open" if unconfirmed > 0 else ("" if all_inputs_ready else "input_packet_attention")
    return {
        "selected_skill_tag": selected_skill_tag,
        "start_status": start_status,
        "blocked_reason": blocked_reason,
        "next_safe_action": cycle["next_safe_action"],
        "next_safe_user_action": "review_next_operator_confirmation" if start_status == "blocked_for_confirmation" else "review_confirmed_start_packet",
        "next_confirmable_step_id": decision.get("next_confirmable_step_id", ""),
        "selected_task_hash": cycle["selected_task_hash"],
        "checkpoint_hash": cycle["checkpoint_hash"],
        "source_card_count": len(cycle["source_card_ids"]),
        "help_level": cycle["help_level"],
        "gate_receipt_id": gate["gate_receipt_id"],
        "decision_receipt_id": decision["decision_receipt_id"],
        "open_confirmation_count": unconfirmed,
        "confirmed_count": int(decision.get("confirmed_count", 0) or 0),
        "a0_a2_only": True,
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def start_receipt(
    summary: dict[str, Any],
    cycle: dict[str, Any],
    gate: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    receipt_hash = sha256_text(
        json.dumps(
            {"summary": summary, "cycle": cycle, "gate": gate, "decision": decision},
            sort_keys=True,
            ensure_ascii=False,
        )
    )
    return {
        "status": "local_cycle_start_packet_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "score_returned": False,
        "grade_returned": False,
    }


def effective_selected_skill(selected_skill_tag: str, *reports: Any) -> str:
    if selected_skill_tag:
        return str(selected_skill_tag)
    for report in reports:
        if isinstance(report, dict):
            for path in [
                ("selected_skill_tag",),
                ("decision_receipt_summary", "selected_skill_tag"),
                ("operator_gate_summary", "selected_skill_tag"),
                ("safe_cycle_summary", "selected_skill_tag"),
            ]:
                value = nested(report, *path)
                if value:
                    return str(value)
    return "general_python"


def safe_action(action: str) -> str:
    if action in {
        "run_next_microtask",
        "repeat_current_microtask",
        "start_first_microtask",
        "return_to_skill_dashboard",
        "review_skill_readiness",
    }:
        return action
    return "review_skill_readiness"


def safe_help_level(help_level: str) -> str:
    value = str(help_level or "A2").upper()
    return value if value in {"A0", "A1", "A2"} else "A2"


def next_actions(summary: dict[str, Any]) -> list[str]:
    readiness_review_action = "Review the Local Cycle Readiness Review before confirming the next local cycle."
    if summary["start_status"] == "blocked_for_confirmation":
        return [
            readiness_review_action,
            "Review the next open Operator Gate confirmation.",
            "Keep the Local Cycle Start Packet dry-run and do not execute local writes.",
            "Regenerate the Decision Receipt after a human confirmation if needed.",
        ]
    return [
        readiness_review_action,
        "Review the confirmed Start Packet before any local cycle.",
        "Start nothing automatically from this packet.",
        "Keep A0-A2, metadata-only, and not_cleared.",
    ]


def nested(value: Any, *path: str) -> Any:
    current = value
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-local-cycle-start-packet")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]


def synthetic_local_cycle_safe_cycle_console() -> dict[str, Any]:
    task_hash = sha256_text("synthetic python lists local-cycle task")
    checkpoint_hash = sha256_text("synthetic python lists local-cycle checkpoint")
    help_hash = sha256_text("synthetic python lists help ledger preview")
    progress_hash = sha256_text("synthetic python lists progress journal preview")
    return {
        "schema_version": "unibot-python-exam-safe-cycle-console-v1",
        "artifact_type": "python_exam_safe_cycle_console",
        "status": "python_exam_safe_cycle_console_ready",
        "exam_deployment_status": "not_cleared",
        "safe_cycle_summary": {
            "selected_skill_tag": "python_lists",
            "cycle_status": "ready_for_operator_gate",
            "next_safe_action": "run_next_microtask",
            "route": "/api/unibot/course/python-exam/run",
            "endpoint": "/api/unibot/course/python-exam/run",
            "selected_task_hash": task_hash,
            "checkpoint_hash": checkpoint_hash,
            "help_level": "A2",
            "ready": True,
        },
        "current_cycle_view": {
            "preview": {
                "ready": True,
                "selected_skill_tag": "python_lists",
                "action": "run_next_microtask",
                "route": "/api/unibot/course/python-exam/run",
                "endpoint": "/api/unibot/course/python-exam/run",
                "selected_task_hash": task_hash,
                "checkpoint_hash": checkpoint_hash,
                "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
                "source_anchor_count": 2,
                "help_level": "A2",
            },
            "receipts": {
                "help_ledger_event_hash": help_hash,
                "review_loop_receipt_id": sha256_text("synthetic review loop receipt")[:20],
                "progress_entry_hash": progress_hash,
                "control_panel_receipt_id": sha256_text("synthetic control panel receipt")[:20],
                "execution_bridge_receipt_id": sha256_text("synthetic execution bridge receipt")[:20],
            },
            "operator_confirmation_matrix": {
                "status": "all_steps_waiting_for_operator_confirmation",
                "confirmed_count": 0,
                "local_writes_requested": False,
            },
        },
    }
