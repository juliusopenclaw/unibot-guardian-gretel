from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .python_exam_local_cycle_readiness_review import build_python_exam_local_cycle_readiness_review
from .python_exam_local_cycle_start_packet import (
    build_python_exam_local_cycle_start_packet,
    synthetic_local_cycle_safe_cycle_console,
)
from .python_exam_operator_gate_decision_receipt import build_python_exam_operator_gate_decision_receipt
from .python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate
from .public_safety import scan_text
from .source_cards import get_source_card


PYTHON_EXAM_LOCAL_CYCLE_READINESS_HANDOFF_SCHEMA_VERSION = "unibot-python-exam-local-cycle-readiness-handoff-v1"
PYTHON_EXAM_LOCAL_CYCLE_READINESS_HANDOFF_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-python-exam-local-cycle-readiness-handoff-release-review-board-claim-alignment-v1"
)
PYTHON_EXAM_LOCAL_CYCLE_READINESS_HANDOFF_ENDPOINT = "/api/unibot/course/python-exam-local-cycle-readiness-handoff"
OPERATOR_RUN_ENDPOINT = "/api/unibot/exam-workspace/operator-run"


def build_python_exam_local_cycle_readiness_handoff(
    *,
    python_exam_local_cycle_readiness_review: dict[str, Any] | None = None,
    python_exam_local_cycle_start_packet: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    review = python_exam_local_cycle_readiness_review if isinstance(python_exam_local_cycle_readiness_review, dict) else {}
    packet = python_exam_local_cycle_start_packet if isinstance(python_exam_local_cycle_start_packet, dict) else {}
    review_view = safe_review_view(review)
    packet_view = safe_packet_view(packet, review_view)
    selected = str(selected_skill_tag or review_view.get("selected_skill_tag", "") or packet_view.get("selected_skill_tag", "")).strip()
    if not selected:
        selected = "general_python"
    ready_for_operator_prefill = review_view["recommendation"] in {
        "request_missing_confirmation_review",
        "ready_for_manual_local_cycle_review",
    } and review_view["hash_metadata_complete"]
    summary = handoff_summary(
        selected_skill_tag=selected,
        review_view=review_view,
        packet_view=packet_view,
        ready_for_operator_prefill=ready_for_operator_prefill,
    )
    operator_prefill = build_operator_run_prefill(review_view, packet_view, ready_for_operator_prefill)
    manual_handoff = build_manual_local_cycle_handoff(review_view, packet_view, operator_prefill, ready_for_operator_prefill)
    payload = {
        "schema_version": PYTHON_EXAM_LOCAL_CYCLE_READINESS_HANDOFF_SCHEMA_VERSION,
        "artifact_type": "python_exam_local_cycle_readiness_handoff",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Local Cycle Readiness Handoff. It turns the Readiness Review into a safe operator "
            "prefill and a manual handoff packet for the next local cycle without executing anything. It consumes "
            "only metadata, hashes, Source-Card anchors, task/checkpoint hashes, the Readiness Review "
            "recommendation, and the Start Packet, then prepares an operator-run dry-run prefill. It never returns "
            "raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, "
            "scores, rankings, grades, proctoring, AI detection, automatic grading, or exam clearance claims."
        ),
        "local_cycle_readiness_handoff_endpoint": PYTHON_EXAM_LOCAL_CYCLE_READINESS_HANDOFF_ENDPOINT,
        "selected_skill_tag": selected,
        "readiness_review_status": review_view["status"],
        "local_cycle_start_packet_status": packet_view["status"],
        "handoff_summary": summary,
        "operator_run_prefill": operator_prefill,
        "manual_local_cycle_handoff": manual_handoff,
        "handoff_receipt": handoff_receipt(summary, operator_prefill, manual_handoff),
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Local Cycle Handoff bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def build_python_exam_local_cycle_readiness_handoff_release_claim_alignment(
    ready_handoff: dict[str, Any] | None = None,
    attention_handoff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if ready_handoff is None or attention_handoff is None:
        console = synthetic_local_cycle_safe_cycle_console()
        gate = build_python_exam_safe_cycle_operator_gate(
            python_exam_safe_cycle_console=console,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        decision = build_python_exam_operator_gate_decision_receipt(
            python_exam_safe_cycle_operator_gate=gate,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        start_packet = build_python_exam_local_cycle_start_packet(
            python_exam_safe_cycle_console=console,
            python_exam_safe_cycle_operator_gate=gate,
            python_exam_operator_gate_decision_receipt=decision,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        review = build_python_exam_local_cycle_readiness_review(
            python_exam_local_cycle_start_packet=start_packet,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        ready_handoff = ready_handoff or build_python_exam_local_cycle_readiness_handoff(
            python_exam_local_cycle_readiness_review=review,
            python_exam_local_cycle_start_packet=start_packet,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        attention_handoff = attention_handoff or build_python_exam_local_cycle_readiness_handoff(
            selected_skill_tag="python_lists",
            public_safe=True,
        )

    sections = [
        {
            "section_id": "readiness_review_handoff_trace",
            "summary_claim": "handoff derives operator-run prefill and manual packet from readiness-review and start-packet metadata",
            "source_card_ids": ["dfg-gwp", "vanlehn-2011", "dsk-ai-privacy-2024"],
            "readiness_check_ids": [
                "python_exam_local_cycle_readiness_handoff",
                "python_exam_local_cycle_readiness_review",
                "python_exam_local_cycle_start_packet",
                "review_board_packet",
            ],
            "human_gates": ["human_submission_review_required", "datenschutz_review_required_before_real_pilot"],
        },
        {
            "section_id": "operator_prefill_boundary_trace",
            "summary_claim": "handoff may prepare an operator-run prefill but keeps every local write dry-run and confirmation-bound",
            "source_card_ids": ["dfg-gwp", "uoc-hilfsmittel"],
            "readiness_check_ids": [
                "python_exam_local_cycle_readiness_handoff",
                "exam_workspace_operator_run",
                "exam_boundary",
            ],
            "human_gates": ["human_submission_review_required", "written_university_clearance_required_before_exam_use"],
        },
        {
            "section_id": "attention_state_trace",
            "summary_claim": "missing readiness-review/start-packet evidence keeps handoff attention rather than inventing prefill readiness",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679"],
            "readiness_check_ids": ["python_exam_local_cycle_readiness_handoff", "external_decision_state"],
            "human_gates": ["public_safety_required", "datenschutz_review_required_before_real_pilot"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "handoff does not publish notebooks, write locally, grade, proctor, detect AI use, or clear exam deployment",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": [
                "python_exam_local_cycle_readiness_handoff",
                "evaluation_packet",
                "exam_boundary",
            ],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    ready_summary = (
        ready_handoff.get("handoff_summary", {}) if isinstance(ready_handoff.get("handoff_summary"), dict) else {}
    )
    ready_prefill = (
        ready_handoff.get("operator_run_prefill", {})
        if isinstance(ready_handoff.get("operator_run_prefill"), dict)
        else {}
    )
    ready_manual = (
        ready_handoff.get("manual_local_cycle_handoff", {})
        if isinstance(ready_handoff.get("manual_local_cycle_handoff"), dict)
        else {}
    )
    ready_receipt = (
        ready_handoff.get("handoff_receipt", {}) if isinstance(ready_handoff.get("handoff_receipt"), dict) else {}
    )
    attention_summary = (
        attention_handoff.get("handoff_summary", {})
        if isinstance(attention_handoff.get("handoff_summary"), dict)
        else {}
    )
    attention_prefill = (
        attention_handoff.get("operator_run_prefill", {})
        if isinstance(attention_handoff.get("operator_run_prefill"), dict)
        else {}
    )
    attention_manual = (
        attention_handoff.get("manual_local_cycle_handoff", {})
        if isinstance(attention_handoff.get("manual_local_cycle_handoff"), dict)
        else {}
    )
    blocked_claims = [
        "raw query returned",
        "raw source text returned",
        "raw notebook code returned",
        "raw cell text returned",
        "raw notebook returned",
        "local path returned",
        "local write requested",
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
    boundary = str(ready_handoff.get("execution_boundary", ""))
    contracts = {
        "ready_handoff_public_safe": ready_handoff.get("public_safety_status") == "pass",
        "attention_handoff_public_safe": attention_handoff.get("public_safety_status") == "pass",
        "operator_prefill_ready_metadata_only": ready_handoff.get("status")
        == "python_exam_local_cycle_readiness_handoff_ready"
        and ready_summary.get("ready_for_operator_prefill") is True
        and ready_prefill.get("status") == "prefill_ready"
        and ready_prefill.get("endpoint") == OPERATOR_RUN_ENDPOINT
        and ready_prefill.get("method") == "POST"
        and ready_prefill.get("selected_skill_tag") == "python_lists"
        and ready_prefill.get("requested_help_level") == "A2"
        and ready_prefill.get("operator_confirmations_default") == "all_false_dry_run"
        and bool(ready_prefill.get("prefill_hash"))
        and ready_prefill.get("raw_query_included") is False
        and ready_prefill.get("raw_cell_included") is False
        and ready_prefill.get("raw_source_text_included") is False
        and ready_prefill.get("notebook_code_included") is False
        and ready_prefill.get("local_paths_returned") is False,
        "manual_handoff_ready_not_execution": ready_manual.get("status") == "manual_local_cycle_handoff_ready"
        and ready_manual.get("next_operator_action") == "open_operator_run_prefill"
        and ready_manual.get("operator_run_endpoint") == OPERATOR_RUN_ENDPOINT
        and bool(ready_manual.get("operator_run_prefill_hash"))
        and ready_manual.get("not_cleared_receipt") is True
        and ready_handoff.get("local_writes_requested") is False
        and ready_handoff.get("local_execution_started") is False
        and ready_handoff.get("dry_run_default") is True,
        "attention_handoff_stays_blocked": attention_handoff.get("status")
        == "python_exam_local_cycle_readiness_handoff_attention"
        and attention_summary.get("ready_for_operator_prefill") is False
        and attention_prefill.get("status") == "prefill_attention"
        and attention_manual.get("status") == "manual_local_cycle_handoff_attention",
        "hash_metadata_and_source_cards_preserved": bool(ready_summary.get("task_hash"))
        and bool(ready_summary.get("checkpoint_hash"))
        and bool(ready_prefill.get("task_hash"))
        and bool(ready_prefill.get("checkpoint_hash"))
        and ready_summary.get("source_card_ids") == ["dfg-gwp", "vanlehn-2011"]
        and ready_prefill.get("source_card_ids") == ["dfg-gwp", "vanlehn-2011"]
        and int(ready_prefill.get("source_anchor_count", 0) or 0) == 2
        and ready_manual.get("help_level") == "A2"
        and ready_receipt.get("status") == "local_cycle_readiness_handoff_receipt_ready_not_exam_clearance"
        and bool(ready_receipt.get("receipt_hash")),
        "public_outputs_hide_private_handoff_data": ready_handoff.get("raw_query_returned") is False
        and ready_handoff.get("raw_text_returned") is False
        and ready_handoff.get("raw_cell_returned") is False
        and ready_handoff.get("raw_notebook_returned") is False
        and ready_handoff.get("notebook_code_returned") is False
        and ready_handoff.get("local_paths_returned") is False
        and ready_handoff.get("values_returned") is False
        and ready_handoff.get("solutions_returned") is False
        and ready_handoff.get("final_interpretations_returned") is False
        and "without executing anything" in boundary
        and "only metadata" in boundary
        and "operator-run dry-run prefill" in boundary,
        "high_stakes_actions_not_started": ready_handoff.get("automatic_grading_started") is False
        and ready_handoff.get("proctoring_started") is False
        and ready_handoff.get("ai_detection_started") is False
        and ready_handoff.get("exam_clearance_claimed") is False
        and ready_handoff.get("score_returned") is False
        and ready_handoff.get("percentage_returned") is False
        and ready_handoff.get("ranking_returned") is False
        and ready_handoff.get("grade_returned") is False
        and ready_handoff.get("exam_deployment_status") == "not_cleared",
        "not_cleared_receipt_present": ready_handoff.get("exam_deployment_status") == "not_cleared"
        and ready_prefill.get("exam_deployment_status") == "not_cleared"
        and ready_manual.get("exam_deployment_status") == "not_cleared"
        and ready_receipt.get("exam_deployment_status") == "not_cleared"
        and ready_receipt.get("not_cleared_receipt") is True,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "ready_status": ready_handoff.get("status"),
        "attention_status": attention_handoff.get("status"),
        "selected_skill_tag": ready_summary.get("selected_skill_tag"),
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "python-exam-local-cycle-readiness-handoff-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": PYTHON_EXAM_LOCAL_CYCLE_READINESS_HANDOFF_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "ready_handoff_status": ready_handoff.get("status"),
        "ready_handoff_public_safety_status": ready_handoff.get("public_safety_status"),
        "attention_handoff_status": attention_handoff.get("status"),
        "attention_handoff_public_safety_status": attention_handoff.get("public_safety_status"),
        "exam_deployment_status": ready_handoff.get("exam_deployment_status"),
        "selected_skill_tag": ready_summary.get("selected_skill_tag"),
        "recommendation": ready_summary.get("recommendation"),
        "recommendation_reason": ready_summary.get("recommendation_reason"),
        "ready_for_operator_prefill": bool(ready_summary.get("ready_for_operator_prefill", False)),
        "operator_run_endpoint": ready_summary.get("operator_run_endpoint"),
        "operator_run_method": ready_summary.get("operator_run_method"),
        "operator_prefill_status": ready_prefill.get("status"),
        "operator_prefill_hash_present": bool(ready_prefill.get("prefill_hash")),
        "manual_handoff_status": ready_manual.get("status"),
        "manual_next_operator_action": ready_manual.get("next_operator_action"),
        "attention_prefill_status": attention_prefill.get("status"),
        "attention_manual_handoff_status": attention_manual.get("status"),
        "task_hash_present": bool(ready_summary.get("task_hash")),
        "checkpoint_hash_present": bool(ready_summary.get("checkpoint_hash")),
        "source_card_ids": ready_summary.get("source_card_ids", []),
        "source_anchor_count": ready_summary.get("source_anchor_count", 0),
        "help_level": ready_manual.get("help_level"),
        "handoff_receipt_status": ready_receipt.get("status"),
        "handoff_receipt_hash_present": bool(ready_receipt.get("receipt_hash")),
        "not_cleared_receipt": bool(ready_receipt.get("not_cleared_receipt", False)),
        "dry_run_default": bool(ready_handoff.get("dry_run_default", False)),
        "local_writes_requested": bool(ready_handoff.get("local_writes_requested", True)),
        "local_execution_started": bool(ready_handoff.get("local_execution_started", True)),
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
            "Python exam local-cycle readiness handoff is a metadata-only handoff surface. It may prepare an "
            "operator-run dry-run prefill and manual handoff packet, but it does not start local writes, publish "
            "raw notebook/query data, grade, proctor, detect AI use, claim Eigenleistung percentages, or clear exams."
        ),
    }


def safe_review_view(review: dict[str, Any]) -> dict[str, Any]:
    summary = review.get("readiness_review_summary", {}) if isinstance(review.get("readiness_review_summary"), dict) else {}
    checks = review.get("readiness_review_checks", {}) if isinstance(review.get("readiness_review_checks"), dict) else {}
    return {
        "status": review.get("status", "missing"),
        "selected_skill_tag": str(review.get("selected_skill_tag", summary.get("selected_skill_tag", ""))),
        "recommendation": str(review.get("readiness_review_recommendation", summary.get("recommendation", "keep_blocked"))),
        "recommendation_reason": str(review.get("readiness_review_reason", summary.get("recommendation_reason", "missing_start_packet"))),
        "packet_present": bool(summary.get("packet_present", False)),
        "hash_metadata_complete": bool(summary.get("hash_metadata_complete", False)),
        "blocked_for_confirmation": bool(summary.get("blocked_for_confirmation", False)),
        "request_missing_confirmation_review": bool(
            checks.get("request_missing_confirmation_review", summary.get("recommendation") == "request_missing_confirmation_review")
        ),
        "ready_for_manual_local_cycle_review": bool(
            checks.get("ready_for_manual_local_cycle_review", summary.get("recommendation") == "ready_for_manual_local_cycle_review")
        ),
        "keep_blocked": bool(checks.get("keep_blocked", summary.get("recommendation") == "keep_blocked")),
        "open_confirmation_count": int(summary.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(summary.get("confirmed_count", 0) or 0),
        "task_hash": str(summary.get("task_hash", "")),
        "checkpoint_hash": str(summary.get("checkpoint_hash", "")),
        "gate_receipt_hash": str(summary.get("gate_receipt_hash", "")),
        "decision_receipt_hash": str(summary.get("decision_receipt_hash", "")),
        "start_receipt_hash": str(summary.get("start_receipt_hash", "")),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "help_level": str(summary.get("help_level", "A2")),
        "next_safe_action": str(summary.get("next_safe_action", "")),
        "next_safe_user_action": str(summary.get("next_safe_user_action", "")),
        "exam_deployment_status": "not_cleared",
    }


def safe_packet_view(packet: dict[str, Any], review_view: dict[str, Any]) -> dict[str, Any]:
    start = packet.get("local_cycle_start_packet", {}) if isinstance(packet.get("local_cycle_start_packet"), dict) else {}
    packet_summary = packet.get("local_cycle_start_summary", {}) if isinstance(packet.get("local_cycle_start_summary"), dict) else {}
    if not start:
        start = packet.get("start_packet", {}) if isinstance(packet.get("start_packet"), dict) else {}
    selected_skill_tag = str(
        packet.get("selected_skill_tag")
        or start.get("selected_skill_tag")
        or packet_summary.get("selected_skill_tag")
        or review_view.get("selected_skill_tag", "")
    )
    return {
        "status": packet.get("status", "missing"),
        "selected_skill_tag": selected_skill_tag,
        "start_status": str(packet_summary.get("start_status") or start.get("start_status") or "missing"),
        "task_hash": str(packet_summary.get("selected_task_hash") or start.get("task_hash") or ""),
        "checkpoint_hash": str(packet_summary.get("checkpoint_hash") or start.get("checkpoint_hash") or ""),
        "source_card_ids": [str(item) for item in (start.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(start.get("source_anchor_count", 0) or 0),
        "help_level": str(packet_summary.get("help_level") or start.get("help_level") or "A2"),
        "gate_receipt_id": str(packet_summary.get("gate_receipt_id") or start.get("gate_receipt_id") or ""),
        "gate_receipt_hash": str(packet_summary.get("gate_receipt_hash") or start.get("gate_receipt_hash") or ""),
        "decision_receipt_id": str(packet_summary.get("decision_receipt_id") or start.get("decision_receipt_id") or ""),
        "decision_receipt_hash": str(packet_summary.get("decision_receipt_hash") or start.get("decision_receipt_hash") or ""),
        "start_receipt_id": str(packet_summary.get("start_receipt_id") or start.get("start_receipt_id") or ""),
        "start_receipt_hash": str(packet_summary.get("start_receipt_hash") or start.get("start_receipt_hash") or ""),
        "open_confirmation_count": int(packet_summary.get("open_confirmation_count") or start.get("open_confirmation_count") or 0),
        "confirmed_count": int(packet_summary.get("confirmed_count") or start.get("confirmed_count") or 0),
        "open_confirmations": list(packet_summary.get("open_confirmations", start.get("open_confirmations", [])) or [])[:8],
        "confirmed_hash_metadata": list(packet_summary.get("confirmed_hash_metadata", start.get("confirmed_hash_metadata", [])) or [])[:8],
        "exam_deployment_status": "not_cleared",
    }


def build_operator_run_prefill(review_view: dict[str, Any], packet_view: dict[str, Any], ready: bool) -> dict[str, Any]:
    prefill_seed = {
        "endpoint": OPERATOR_RUN_ENDPOINT,
        "selected_skill_tag": packet_view.get("selected_skill_tag", review_view.get("selected_skill_tag", "")),
        "task_hash": packet_view.get("task_hash", ""),
        "checkpoint_hash": packet_view.get("checkpoint_hash", ""),
        "source_card_ids": packet_view.get("source_card_ids", []),
        "source_anchor_count": packet_view.get("source_anchor_count", 0),
        "help_level": packet_view.get("help_level", review_view.get("help_level", "A2")),
        "recommendation": review_view.get("recommendation", "keep_blocked"),
        "start_status": packet_view.get("start_status", "missing"),
    }
    return {
        "status": "prefill_ready" if ready else "prefill_attention",
        "endpoint": OPERATOR_RUN_ENDPOINT,
        "method": "POST",
        "selected_skill_tag": prefill_seed["selected_skill_tag"],
        "task_hash": prefill_seed["task_hash"],
        "checkpoint_hash": prefill_seed["checkpoint_hash"],
        "source_card_ids": list(prefill_seed.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": int(prefill_seed.get("source_anchor_count", 0) or 0),
        "requested_help_level": "A2",
        "operator_confirmations_default": "all_false_dry_run",
        "ready_for_manual_local_cycle_review": ready,
        "dry_run_default": True,
        "local_writes_requested": False,
        "prefill_hash": sha256_text(json.dumps(prefill_seed, sort_keys=True, ensure_ascii=False)),
        "raw_query_included": False,
        "raw_cell_included": False,
        "raw_source_text_included": False,
        "notebook_code_included": False,
        "local_paths_returned": False,
        "exam_deployment_status": "not_cleared",
    }


def build_manual_local_cycle_handoff(
    review_view: dict[str, Any],
    packet_view: dict[str, Any],
    operator_prefill: dict[str, Any],
    ready: bool,
) -> dict[str, Any]:
    return {
        "status": "manual_local_cycle_handoff_ready" if ready else "manual_local_cycle_handoff_attention",
        "selected_skill_tag": packet_view.get("selected_skill_tag", review_view.get("selected_skill_tag", "")),
        "recommendation": review_view.get("recommendation", "keep_blocked"),
        "recommendation_reason": review_view.get("recommendation_reason", "missing_start_packet"),
        "next_operator_action": (
            "open_operator_run_prefill" if ready else "resolve_readiness_review_attention"
        ),
        "operator_run_endpoint": OPERATOR_RUN_ENDPOINT,
        "operator_run_prefill_hash": operator_prefill.get("prefill_hash", ""),
        "open_confirmation_count": int(review_view.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(review_view.get("confirmed_count", 0) or 0),
        "help_level": packet_view.get("help_level", review_view.get("help_level", "A2")),
        "task_hash": packet_view.get("task_hash", ""),
        "checkpoint_hash": packet_view.get("checkpoint_hash", ""),
        "source_card_ids": list(packet_view.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": int(packet_view.get("source_anchor_count", 0) or 0),
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def handoff_summary(
    *,
    selected_skill_tag: str,
    review_view: dict[str, Any],
    packet_view: dict[str, Any],
    ready_for_operator_prefill: bool,
) -> dict[str, Any]:
    packet_present = bool(review_view.get("packet_present", False))
    hash_complete = bool(review_view.get("hash_metadata_complete", False))
    if not packet_present:
        status = "python_exam_local_cycle_readiness_handoff_attention"
        reason = "missing_start_packet"
    elif not hash_complete:
        status = "python_exam_local_cycle_readiness_handoff_attention"
        reason = "missing_hash_metadata"
    elif ready_for_operator_prefill:
        status = "python_exam_local_cycle_readiness_handoff_ready"
        reason = review_view.get("recommendation_reason", "open_confirmations_present")
    else:
        status = "python_exam_local_cycle_readiness_handoff_attention"
        reason = "review_not_ready_for_prefill"
    return {
        "status": status,
        "selected_skill_tag": selected_skill_tag,
        "readiness_review_status": review_view.get("status", "missing"),
        "start_packet_status": packet_view.get("status", "missing"),
        "recommendation": review_view.get("recommendation", "keep_blocked"),
        "recommendation_reason": reason,
        "ready_for_operator_prefill": ready_for_operator_prefill,
        "operator_run_endpoint": OPERATOR_RUN_ENDPOINT,
        "operator_run_method": "POST",
        "task_hash": packet_view.get("task_hash", ""),
        "checkpoint_hash": packet_view.get("checkpoint_hash", ""),
        "open_confirmation_count": int(review_view.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(review_view.get("confirmed_count", 0) or 0),
        "help_level": packet_view.get("help_level", review_view.get("help_level", "A2")),
        "source_card_ids": list(packet_view.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": int(packet_view.get("source_anchor_count", 0) or 0),
        "manual_handoff_ready": ready_for_operator_prefill,
        "operator_prefill_ready": ready_for_operator_prefill,
        "next_safe_action": (
            "Open the operator-run prefill and review the confirmed or missing confirmations."
            if ready_for_operator_prefill
            else "Resolve readiness review attention items before prefilling operator-run."
        ),
        "exam_deployment_status": "not_cleared",
    }


def handoff_receipt(summary: dict[str, Any], operator_prefill: dict[str, Any], manual_handoff: dict[str, Any]) -> dict[str, Any]:
    receipt_hash = sha256_text(
        json.dumps({"summary": summary, "operator_prefill": operator_prefill, "manual_handoff": manual_handoff}, sort_keys=True, ensure_ascii=False)
    )
    return {
        "status": "local_cycle_readiness_handoff_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "score_returned": False,
        "grade_returned": False,
    }


def next_actions(summary: dict[str, Any]) -> list[str]:
    if summary.get("status") == "python_exam_local_cycle_readiness_handoff_ready":
        return [
            "Open the operator-run prefill and keep confirmations explicit.",
            "Review the manual handoff packet before any local write.",
            "Keep the operator-run dry-run by default and stay not_cleared.",
        ]
    return [
        "Resolve readiness review attention items before using the handoff.",
        "Keep the handoff metadata-only and do not start local writes.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-local-cycle-readiness-handoff")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["public_safety_findings"] = scan["findings"]
