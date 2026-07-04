from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .python_exam_local_cycle_readiness_handoff import build_python_exam_local_cycle_readiness_handoff
from .python_exam_local_cycle_readiness_review import build_python_exam_local_cycle_readiness_review
from .python_exam_local_cycle_start_packet import (
    build_python_exam_local_cycle_start_packet,
    synthetic_local_cycle_safe_cycle_console,
)
from .python_exam_operator_gate_decision_receipt import build_python_exam_operator_gate_decision_receipt
from .python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate
from .public_safety import scan_text
from .source_cards import get_source_card


PYTHON_EXAM_LOCAL_CYCLE_OPERATOR_WORKSPACE_CARD_SCHEMA_VERSION = "unibot-python-exam-local-cycle-operator-workspace-card-v1"
PYTHON_EXAM_LOCAL_CYCLE_OPERATOR_WORKSPACE_CARD_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-python-exam-local-cycle-operator-workspace-card-release-review-board-claim-alignment-v1"
)
PYTHON_EXAM_LOCAL_CYCLE_OPERATOR_WORKSPACE_CARD_ENDPOINT = "/api/unibot/course/python-exam-local-cycle-operator-workspace-card"


def build_python_exam_local_cycle_operator_workspace_card(
    *,
    python_exam_local_cycle_readiness_review: dict[str, Any] | None = None,
    python_exam_local_cycle_readiness_handoff: dict[str, Any] | None = None,
    python_exam_local_cycle_start_packet: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    review = python_exam_local_cycle_readiness_review if isinstance(python_exam_local_cycle_readiness_review, dict) else {}
    handoff = python_exam_local_cycle_readiness_handoff if isinstance(python_exam_local_cycle_readiness_handoff, dict) else {}
    packet = python_exam_local_cycle_start_packet if isinstance(python_exam_local_cycle_start_packet, dict) else {}
    review_view = safe_review_view(review)
    handoff_view = safe_handoff_view(handoff)
    packet_view = safe_packet_view(packet, review_view, handoff_view)
    selected = str(
        selected_skill_tag or review_view.get("selected_skill_tag", "") or handoff_view.get("selected_skill_tag", "") or packet_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    help_ledger_preview = safe_help_ledger_preview(review_view, handoff_view, packet_view)
    summary = workspace_card_summary(
        selected_skill_tag=selected,
        review_view=review_view,
        handoff_view=handoff_view,
        packet_view=packet_view,
        help_ledger_preview=help_ledger_preview,
    )
    payload = {
        "schema_version": PYTHON_EXAM_LOCAL_CYCLE_OPERATOR_WORKSPACE_CARD_SCHEMA_VERSION,
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Local Cycle Operator Workspace Card. It combines the Local Cycle Readiness Review, "
            "Readiness Handoff, and a compact Help-Ledger Preview into one notebook-first sidepanel card. It "
            "presents only metadata and hashes, marks the next safe action clearly, stays dry-run by default, "
            "and never returns raw queries, course raw text, notebook code, local paths, values, solutions, final "
            "interpretations, scores, rankings, grades, proctoring, AI detection, automatic grading, or exam "
            "clearance claims."
        ),
        "local_cycle_operator_workspace_card_endpoint": PYTHON_EXAM_LOCAL_CYCLE_OPERATOR_WORKSPACE_CARD_ENDPOINT,
        "selected_skill_tag": selected,
        "workspace_card_summary": summary,
        "readiness_review_status": review_view["status"],
        "readiness_handoff_status": handoff_view["status"],
        "local_cycle_start_packet_status": packet_view["status"],
        "readiness_review": review_view,
        "readiness_handoff": handoff_view,
        "help_ledger_preview": help_ledger_preview,
        "operator_run_prefill": dict(handoff.get("operator_run_prefill", {}) if isinstance(handoff.get("operator_run_prefill"), dict) else {}),
        "manual_local_cycle_handoff": dict(handoff.get("manual_local_cycle_handoff", {}) if isinstance(handoff.get("manual_local_cycle_handoff"), dict) else {}),
        "source_card_ids": list(packet_view.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": int(packet_view.get("source_anchor_count", 0) or 0),
        "task_hash": str(packet_view.get("task_hash", "")),
        "checkpoint_hash": str(packet_view.get("checkpoint_hash", "")),
        "help_level": str(packet_view.get("help_level", "A2")),
        "next_safe_action": summary["next_safe_action"],
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "operator_confirmation_required_for_local_write": True,
        "not_cleared_receipt": True,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; die Local Cycle Operator Workspace Card bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def build_python_exam_local_cycle_operator_workspace_card_release_claim_alignment(
    ready_card: dict[str, Any] | None = None,
    attention_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if ready_card is None or attention_card is None:
        console = synthetic_local_cycle_safe_cycle_console()
        gate = build_python_exam_safe_cycle_operator_gate(
            python_exam_safe_cycle_console=console,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        confirmed_decision = build_python_exam_operator_gate_decision_receipt(
            python_exam_safe_cycle_operator_gate=gate,
            confirmed_step_ids=[card["step_id"] for card in gate.get("confirmation_cards", [])],
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        start_packet = build_python_exam_local_cycle_start_packet(
            python_exam_safe_cycle_console=console,
            python_exam_safe_cycle_operator_gate=gate,
            python_exam_operator_gate_decision_receipt=confirmed_decision,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        review = build_python_exam_local_cycle_readiness_review(
            python_exam_local_cycle_start_packet=start_packet,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        handoff = build_python_exam_local_cycle_readiness_handoff(
            python_exam_local_cycle_readiness_review=review,
            python_exam_local_cycle_start_packet=start_packet,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        ready_card = ready_card or build_python_exam_local_cycle_operator_workspace_card(
            python_exam_local_cycle_readiness_review=review,
            python_exam_local_cycle_readiness_handoff=handoff,
            python_exam_local_cycle_start_packet=start_packet,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        attention_card = attention_card or build_python_exam_local_cycle_operator_workspace_card(
            selected_skill_tag="python_lists",
            public_safe=True,
        )

    sections = [
        {
            "section_id": "workspace_card_evidence_trace",
            "summary_claim": "workspace card combines readiness review, readiness handoff, start-packet metadata, and help-ledger preview",
            "source_card_ids": ["dfg-gwp", "vanlehn-2011", "dsk-ai-privacy-2024"],
            "readiness_check_ids": [
                "python_exam_local_cycle_operator_workspace_card",
                "python_exam_local_cycle_readiness_handoff",
                "python_exam_local_cycle_readiness_review",
                "python_exam_local_cycle_start_packet",
            ],
            "human_gates": ["human_submission_review_required", "datenschutz_review_required_before_real_pilot"],
        },
        {
            "section_id": "operator_workspace_boundary_trace",
            "summary_claim": "workspace card may point to operator-run prefill but remains notebook-first, dry-run, and confirmation-bound",
            "source_card_ids": ["dfg-gwp", "uoc-hilfsmittel"],
            "readiness_check_ids": [
                "python_exam_local_cycle_operator_workspace_card",
                "exam_workspace_operator_run",
                "exam_boundary",
            ],
            "human_gates": ["human_submission_review_required", "written_university_clearance_required_before_exam_use"],
        },
        {
            "section_id": "attention_state_trace",
            "summary_claim": "missing review/handoff evidence keeps the workspace card attention instead of inventing readiness",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679"],
            "readiness_check_ids": ["python_exam_local_cycle_operator_workspace_card", "external_decision_state"],
            "human_gates": ["public_safety_required", "datenschutz_review_required_before_real_pilot"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "workspace card does not publish notebooks, write locally, grade, proctor, detect AI use, or clear exam deployment",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": [
                "python_exam_local_cycle_operator_workspace_card",
                "evaluation_packet",
                "exam_boundary",
            ],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    ready_summary = (
        ready_card.get("workspace_card_summary", {})
        if isinstance(ready_card.get("workspace_card_summary"), dict)
        else {}
    )
    ready_review = (
        ready_card.get("readiness_review", {}) if isinstance(ready_card.get("readiness_review"), dict) else {}
    )
    ready_handoff = (
        ready_card.get("readiness_handoff", {}) if isinstance(ready_card.get("readiness_handoff"), dict) else {}
    )
    ready_preview = (
        ready_card.get("help_ledger_preview", {}) if isinstance(ready_card.get("help_ledger_preview"), dict) else {}
    )
    ready_prefill = (
        ready_card.get("operator_run_prefill", {}) if isinstance(ready_card.get("operator_run_prefill"), dict) else {}
    )
    ready_manual = (
        ready_card.get("manual_local_cycle_handoff", {})
        if isinstance(ready_card.get("manual_local_cycle_handoff"), dict)
        else {}
    )
    attention_summary = (
        attention_card.get("workspace_card_summary", {})
        if isinstance(attention_card.get("workspace_card_summary"), dict)
        else {}
    )
    attention_preview = (
        attention_card.get("help_ledger_preview", {})
        if isinstance(attention_card.get("help_ledger_preview"), dict)
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
    boundary = str(ready_card.get("execution_boundary", ""))
    contracts = {
        "ready_card_public_safe": ready_card.get("public_safety_status") == "pass",
        "attention_card_public_safe": attention_card.get("public_safety_status") == "pass",
        "workspace_card_ready_metadata_only": ready_card.get("status")
        == "python_exam_local_cycle_operator_workspace_card_ready"
        and ready_summary.get("ready_for_operator_prefill") is True
        and ready_summary.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and ready_preview.get("status") == "help_ledger_preview_ready"
        and bool(ready_preview.get("preview_hash"))
        and ready_review.get("recommendation") == "ready_for_manual_local_cycle_review"
        and ready_handoff.get("ready_for_operator_prefill") is True
        and ready_card.get("selected_skill_tag") == "python_lists",
        "operator_prefill_and_manual_handoff_linked": ready_prefill.get("status") == "prefill_ready"
        and ready_prefill.get("endpoint") == "/api/unibot/exam-workspace/operator-run"
        and ready_prefill.get("operator_confirmations_default") == "all_false_dry_run"
        and bool(ready_prefill.get("prefill_hash"))
        and ready_manual.get("status") == "manual_local_cycle_handoff_ready"
        and ready_manual.get("next_operator_action") == "open_operator_run_prefill"
        and ready_card.get("operator_confirmation_required_for_local_write") is True,
        "attention_card_stays_blocked": attention_card.get("status")
        == "python_exam_local_cycle_operator_workspace_card_attention"
        and attention_summary.get("ready_for_operator_prefill") is False
        and attention_summary.get("help_ledger_preview_status") == "help_ledger_preview_attention"
        and attention_preview.get("status") == "help_ledger_preview_attention",
        "hash_metadata_and_source_cards_preserved": bool(ready_card.get("task_hash"))
        and bool(ready_card.get("checkpoint_hash"))
        and bool(ready_summary.get("help_ledger_preview_hash"))
        and ready_card.get("source_card_ids") == ["dfg-gwp", "vanlehn-2011"]
        and ready_summary.get("source_card_ids") == ["dfg-gwp", "vanlehn-2011"]
        and int(ready_card.get("source_anchor_count", 0) or 0) == 2
        and ready_card.get("help_level") == "A2",
        "public_outputs_hide_private_workspace_card_data": ready_card.get("raw_query_returned") is False
        and ready_card.get("raw_text_returned") is False
        and ready_card.get("raw_cell_returned") is False
        and ready_card.get("raw_notebook_returned") is False
        and ready_card.get("notebook_code_returned") is False
        and ready_card.get("local_paths_returned") is False
        and ready_card.get("values_returned") is False
        and ready_card.get("solutions_returned") is False
        and ready_card.get("final_interpretations_returned") is False
        and ready_preview.get("raw_query_returned") is False
        and ready_preview.get("raw_text_returned") is False
        and ready_preview.get("local_paths_returned") is False
        and "presents only metadata and hashes" in boundary
        and "stays dry-run by default" in boundary,
        "high_stakes_actions_not_started": ready_card.get("automatic_grading_started") is False
        and ready_card.get("proctoring_started") is False
        and ready_card.get("ai_detection_started") is False
        and ready_card.get("exam_clearance_claimed") is False
        and ready_card.get("score_returned") is False
        and ready_card.get("percentage_returned") is False
        and ready_card.get("ranking_returned") is False
        and ready_card.get("grade_returned") is False
        and ready_card.get("exam_deployment_status") == "not_cleared",
        "not_cleared_receipt_present": ready_card.get("exam_deployment_status") == "not_cleared"
        and ready_card.get("not_cleared_receipt") is True
        and ready_summary.get("not_cleared_receipt") is True
        and ready_preview.get("not_cleared_receipt") is True
        and ready_manual.get("not_cleared_receipt") is True,
        "no_local_execution_or_write": ready_card.get("local_writes_requested") is False
        and ready_card.get("local_execution_started") is False
        and ready_preview.get("write_requested") is False
        and ready_preview.get("dry_run_default") is True,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "ready_status": ready_card.get("status"),
        "attention_status": attention_card.get("status"),
        "selected_skill_tag": ready_card.get("selected_skill_tag"),
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "python-exam-local-cycle-operator-workspace-card-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": PYTHON_EXAM_LOCAL_CYCLE_OPERATOR_WORKSPACE_CARD_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "ready_card_status": ready_card.get("status"),
        "ready_card_public_safety_status": ready_card.get("public_safety_status"),
        "attention_card_status": attention_card.get("status"),
        "attention_card_public_safety_status": attention_card.get("public_safety_status"),
        "exam_deployment_status": ready_card.get("exam_deployment_status"),
        "selected_skill_tag": ready_card.get("selected_skill_tag"),
        "recommendation": ready_summary.get("recommendation"),
        "recommendation_reason": ready_summary.get("recommendation_reason"),
        "ready_for_operator_prefill": ready_summary.get("ready_for_operator_prefill"),
        "help_ledger_preview_status": ready_preview.get("status"),
        "help_ledger_preview_hash_present": bool(ready_preview.get("preview_hash")),
        "operator_prefill_status": ready_prefill.get("status"),
        "operator_prefill_hash_present": bool(ready_prefill.get("prefill_hash")),
        "manual_handoff_status": ready_manual.get("status"),
        "manual_next_operator_action": ready_manual.get("next_operator_action"),
        "attention_help_ledger_preview_status": attention_preview.get("status"),
        "task_hash_present": bool(ready_card.get("task_hash")),
        "checkpoint_hash_present": bool(ready_card.get("checkpoint_hash")),
        "source_card_ids": ready_card.get("source_card_ids", []),
        "source_anchor_count": ready_card.get("source_anchor_count", 0),
        "help_level": ready_card.get("help_level"),
        "dry_run_default": bool(ready_card.get("dry_run_default", False)),
        "local_writes_requested": bool(ready_card.get("local_writes_requested", True)),
        "local_execution_started": bool(ready_card.get("local_execution_started", True)),
        "not_cleared_receipt": bool(ready_card.get("not_cleared_receipt", False)),
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
            "Python exam local-cycle operator workspace card is a notebook-first status card. It may display "
            "review, handoff, operator-prefill, help-ledger preview, source-card, and hash metadata, but it does "
            "not start local writes, publish raw notebook/query data, grade, proctor, detect AI use, claim "
            "Eigenleistung percentages, or clear exams."
        ),
    }


def safe_review_view(review: dict[str, Any]) -> dict[str, Any]:
    summary = review.get("readiness_review_summary", {}) if isinstance(review.get("readiness_review_summary"), dict) else {}
    return {
        "status": review.get("status", "missing"),
        "selected_skill_tag": str(review.get("selected_skill_tag", summary.get("selected_skill_tag", ""))),
        "recommendation": str(review.get("readiness_review_recommendation", summary.get("recommendation", "keep_blocked"))),
        "recommendation_reason": str(review.get("readiness_review_reason", summary.get("recommendation_reason", "missing_start_packet"))),
        "blocked_for_confirmation": bool(summary.get("blocked_for_confirmation", False)),
        "request_missing_confirmation_review": bool(summary.get("request_missing_confirmation_review", False)),
        "ready_for_manual_local_cycle_review": bool(summary.get("ready_for_manual_local_cycle_review", False)),
        "keep_blocked": bool(summary.get("keep_blocked", True)),
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


def safe_handoff_view(handoff: dict[str, Any]) -> dict[str, Any]:
    summary = handoff.get("handoff_summary", {}) if isinstance(handoff.get("handoff_summary"), dict) else {}
    prefill = handoff.get("operator_run_prefill", {}) if isinstance(handoff.get("operator_run_prefill"), dict) else {}
    manual = handoff.get("manual_local_cycle_handoff", {}) if isinstance(handoff.get("manual_local_cycle_handoff"), dict) else {}
    preview = handoff.get("help_ledger_preview", {}) if isinstance(handoff.get("help_ledger_preview"), dict) else {}
    return {
        "status": handoff.get("status", "missing"),
        "selected_skill_tag": str(handoff.get("selected_skill_tag", summary.get("selected_skill_tag", ""))),
        "recommendation": str(handoff.get("recommendation", summary.get("recommendation", "keep_blocked"))),
        "recommendation_reason": str(handoff.get("recommendation_reason", summary.get("recommendation_reason", "missing_start_packet"))),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", prefill.get("endpoint", ""))),
        "operator_run_method": str(summary.get("operator_run_method", prefill.get("method", "POST"))),
        "task_hash": str(summary.get("task_hash", prefill.get("task_hash", manual.get("task_hash", "")))),
        "checkpoint_hash": str(summary.get("checkpoint_hash", prefill.get("checkpoint_hash", manual.get("checkpoint_hash", "")))),
        "open_confirmation_count": int(summary.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(summary.get("confirmed_count", 0) or 0),
        "help_level": str(summary.get("help_level", prefill.get("requested_help_level", manual.get("help_level", "A2")))),
        "source_card_ids": [str(item) for item in (prefill.get("source_card_ids", manual.get("source_card_ids", [])) or [])][:8],
        "source_anchor_count": int(prefill.get("source_anchor_count", manual.get("source_anchor_count", 0)) or 0),
        "prefill_hash": str(prefill.get("prefill_hash", "")),
        "manual_next_operator_action": str(manual.get("next_operator_action", "")),
        "help_ledger_preview": preview,
        "exam_deployment_status": "not_cleared",
    }


def safe_packet_view(
    packet: dict[str, Any],
    review_view: dict[str, Any],
    handoff_view: dict[str, Any],
) -> dict[str, Any]:
    start = packet.get("local_cycle_start_packet", {}) if isinstance(packet.get("local_cycle_start_packet"), dict) else {}
    packet_summary = packet.get("local_cycle_start_summary", {}) if isinstance(packet.get("local_cycle_start_summary"), dict) else {}
    if not start:
        start = packet.get("start_packet", {}) if isinstance(packet.get("start_packet"), dict) else {}
    selected_skill_tag = str(
        packet.get("selected_skill_tag")
        or start.get("selected_skill_tag")
        or packet_summary.get("selected_skill_tag")
        or review_view.get("selected_skill_tag", "")
        or handoff_view.get("selected_skill_tag", "")
    )
    return {
        "status": packet.get("status", "missing"),
        "selected_skill_tag": selected_skill_tag,
        "task_hash": str(packet_summary.get("selected_task_hash") or start.get("task_hash") or ""),
        "checkpoint_hash": str(packet_summary.get("checkpoint_hash") or start.get("checkpoint_hash") or ""),
        "source_card_ids": [str(item) for item in (start.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(start.get("source_anchor_count", 0) or 0),
        "help_level": str(packet_summary.get("help_level") or start.get("help_level") or handoff_view.get("help_level", "A2")),
        "open_confirmation_count": int(packet_summary.get("open_confirmation_count") or start.get("open_confirmation_count") or review_view.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(packet_summary.get("confirmed_count") or start.get("confirmed_count") or review_view.get("confirmed_count", 0) or 0),
        "start_status": str(packet_summary.get("start_status") or start.get("start_status") or "missing"),
        "gate_receipt_hash": str(packet_summary.get("gate_receipt_hash") or start.get("gate_receipt_hash") or review_view.get("gate_receipt_hash", "")),
        "decision_receipt_hash": str(packet_summary.get("decision_receipt_hash") or start.get("decision_receipt_hash") or review_view.get("decision_receipt_hash", "")),
        "start_receipt_hash": str(packet_summary.get("start_receipt_hash") or start.get("start_receipt_hash") or review_view.get("start_receipt_hash", "")),
        "exam_deployment_status": "not_cleared",
    }


def safe_help_ledger_preview(
    review_view: dict[str, Any],
    handoff_view: dict[str, Any],
    packet_view: dict[str, Any],
) -> dict[str, Any]:
    seed = {
        "selected_skill_tag": packet_view.get("selected_skill_tag", review_view.get("selected_skill_tag", handoff_view.get("selected_skill_tag", ""))),
        "task_hash": packet_view.get("task_hash", ""),
        "checkpoint_hash": packet_view.get("checkpoint_hash", ""),
        "source_card_ids": packet_view.get("source_card_ids", []),
        "source_anchor_count": packet_view.get("source_anchor_count", 0),
        "help_level": packet_view.get("help_level", handoff_view.get("help_level", review_view.get("help_level", "A2"))),
        "open_confirmation_count": packet_view.get("open_confirmation_count", review_view.get("open_confirmation_count", 0)),
        "confirmed_count": packet_view.get("confirmed_count", review_view.get("confirmed_count", 0)),
        "next_safe_action": review_view.get("next_safe_action", ""),
        "next_safe_user_action": review_view.get("next_safe_user_action", ""),
        "operator_run_prefill_hash": handoff_view.get("prefill_hash", ""),
    }
    preview_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "help_ledger_preview_ready" if handoff_view.get("ready_for_operator_prefill") else "help_ledger_preview_attention",
        "selected_skill_tag": seed["selected_skill_tag"],
        "help_level": seed["help_level"],
        "task_hash": seed["task_hash"],
        "checkpoint_hash": seed["checkpoint_hash"],
        "source_card_ids": list(seed.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": int(seed.get("source_anchor_count", 0) or 0),
        "open_confirmation_count": int(seed.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(seed.get("confirmed_count", 0) or 0),
        "next_safe_action": seed["next_safe_action"],
        "next_safe_user_action": seed["next_safe_user_action"],
        "operator_run_prefill_hash": seed["operator_run_prefill_hash"],
        "preview_hash": preview_hash,
        "dry_run_default": True,
        "write_requested": False,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "local_paths_returned": False,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def workspace_card_summary(
    *,
    selected_skill_tag: str,
    review_view: dict[str, Any],
    handoff_view: dict[str, Any],
    packet_view: dict[str, Any],
    help_ledger_preview: dict[str, Any],
) -> dict[str, Any]:
    ready = bool(handoff_view.get("ready_for_operator_prefill", False)) and help_ledger_preview.get("status") == "help_ledger_preview_ready"
    if not review_view.get("status") or review_view.get("status") == "missing":
        status = "python_exam_local_cycle_operator_workspace_card_attention"
        reason = "missing_readiness_review"
    elif not handoff_view.get("status") or handoff_view.get("status") == "missing":
        status = "python_exam_local_cycle_operator_workspace_card_attention"
        reason = "missing_readiness_handoff"
    elif ready:
        status = "python_exam_local_cycle_operator_workspace_card_ready"
        reason = "operator_prefill_and_help_ledger_ready"
    else:
        status = "python_exam_local_cycle_operator_workspace_card_attention"
        reason = "operator_prefill_not_ready"
    return {
        "status": status,
        "selected_skill_tag": selected_skill_tag,
        "recommendation": review_view.get("recommendation", "keep_blocked"),
        "recommendation_reason": review_view.get("recommendation_reason", reason),
        "readiness_review_status": review_view.get("status", "missing"),
        "readiness_handoff_status": handoff_view.get("status", "missing"),
        "help_ledger_preview_status": help_ledger_preview.get("status", "missing"),
        "next_safe_action": review_view.get("next_safe_action", handoff_view.get("manual_next_operator_action", "review_skill_readiness")),
        "next_safe_user_action": review_view.get("next_safe_user_action", "review_confirmed_start_packet"),
        "operator_run_endpoint": handoff_view.get("operator_run_endpoint", ""),
        "operator_run_method": handoff_view.get("operator_run_method", "POST"),
        "ready_for_operator_prefill": bool(handoff_view.get("ready_for_operator_prefill", False)),
        "help_level": packet_view.get("help_level", handoff_view.get("help_level", "A2")),
        "open_confirmation_count": int(review_view.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(review_view.get("confirmed_count", 0) or 0),
        "source_card_ids": list(packet_view.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": int(packet_view.get("source_anchor_count", 0) or 0),
        "task_hash": packet_view.get("task_hash", ""),
        "checkpoint_hash": packet_view.get("checkpoint_hash", ""),
        "help_ledger_preview_hash": help_ledger_preview.get("preview_hash", ""),
        "dry_run_default": True,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def safe_local_cycle_workspace_card(workspace_card: dict[str, Any]) -> dict[str, Any]:
    summary = workspace_card.get("workspace_card_summary", {}) if isinstance(workspace_card.get("workspace_card_summary"), dict) else {}
    review = workspace_card.get("readiness_review", {}) if isinstance(workspace_card.get("readiness_review"), dict) else {}
    handoff = workspace_card.get("readiness_handoff", {}) if isinstance(workspace_card.get("readiness_handoff"), dict) else {}
    ledger = workspace_card.get("help_ledger_preview", {}) if isinstance(workspace_card.get("help_ledger_preview"), dict) else {}
    if not summary and (
        workspace_card.get("help_ledger_preview_hash") is not None
        or workspace_card.get("ready_for_operator_prefill") is not None
        or workspace_card.get("help_ledger_preview_status") is not None
    ):
        summary = workspace_card
    return {
        "status": workspace_card.get("status", "missing"),
        "recommendation": str(summary.get("recommendation", review.get("recommendation", "keep_blocked"))),
        "recommendation_reason": str(summary.get("recommendation_reason", review.get("recommendation_reason", "missing_start_packet"))),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "help_ledger_preview_status": str(summary.get("help_ledger_preview_status", ledger.get("status", "missing"))),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "next_safe_action": str(summary.get("next_safe_action", review.get("next_safe_action", ""))),
        "next_safe_user_action": str(summary.get("next_safe_user_action", review.get("next_safe_user_action", ""))),
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", handoff.get("operator_run_endpoint", ""))),
        "operator_run_method": str(summary.get("operator_run_method", handoff.get("operator_run_method", "POST"))),
        "help_level": str(summary.get("help_level", ledger.get("help_level", "A2"))),
        "task_hash": str(summary.get("task_hash", "")),
        "checkpoint_hash": str(summary.get("checkpoint_hash", "")),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "help_ledger_preview_hash": str(summary.get("help_ledger_preview_hash", ledger.get("preview_hash", ""))),
        "not_cleared_receipt": bool(workspace_card.get("not_cleared_receipt", True)),
        "exam_deployment_status": "not_cleared",
    }


def next_actions(summary: dict[str, Any]) -> list[str]:
    return [
        f"Recommendation: {summary['recommendation']}.",
        "Open the operator-run prefill and review the help-ledger preview before any local write.",
        "Keep the card notebook-first, A0-A2 only, dry-run by default, and not_cleared.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-local-cycle-operator-workspace-card")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
