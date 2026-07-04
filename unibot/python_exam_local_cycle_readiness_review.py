from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .python_exam_local_cycle_start_packet import (
    build_python_exam_local_cycle_start_packet,
    synthetic_local_cycle_safe_cycle_console,
)
from .python_exam_operator_gate_decision_receipt import build_python_exam_operator_gate_decision_receipt
from .python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate
from .public_safety import scan_text
from .source_cards import get_source_card


PYTHON_EXAM_LOCAL_CYCLE_READINESS_REVIEW_SCHEMA_VERSION = "unibot-python-exam-local-cycle-readiness-review-v1"
PYTHON_EXAM_LOCAL_CYCLE_READINESS_REVIEW_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-python-exam-local-cycle-readiness-review-release-review-board-claim-alignment-v1"
)
PYTHON_EXAM_LOCAL_CYCLE_READINESS_REVIEW_ENDPOINT = "/api/unibot/course/python-exam-local-cycle-readiness-review"


def build_python_exam_local_cycle_readiness_review(
    *,
    python_exam_local_cycle_start_packet: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    packet = python_exam_local_cycle_start_packet if isinstance(python_exam_local_cycle_start_packet, dict) else {}
    start_view = safe_start_packet(packet)
    selected = str(selected_skill_tag or start_view.get("selected_skill_tag", "") or "").strip()
    if not selected:
        selected = "general_python"
    summary = readiness_review_summary(selected_skill_tag=selected, start_view=start_view, packet=packet)
    packet_view = {
        "status": packet.get("status", "missing"),
        "selected_skill_tag": start_view.get("selected_skill_tag", selected),
        "start_status": start_view.get("start_status", "missing"),
        "blocked_reason": start_view.get("blocked_reason", ""),
        "next_safe_action": start_view.get("next_safe_action", "review_skill_readiness"),
        "next_safe_user_action": start_view.get("next_safe_user_action", "review_confirmed_start_packet"),
        "task_hash": start_view.get("task_hash", ""),
        "checkpoint_hash": start_view.get("checkpoint_hash", ""),
        "source_card_ids": list(start_view.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": int(start_view.get("source_anchor_count", 0) or 0),
        "help_level": start_view.get("help_level", "A2"),
        "gate_receipt_id": start_view.get("gate_receipt_id", ""),
        "gate_receipt_hash": start_view.get("gate_receipt_hash", ""),
        "decision_receipt_id": start_view.get("decision_receipt_id", ""),
        "decision_receipt_hash": start_view.get("decision_receipt_hash", ""),
        "start_receipt_id": start_view.get("start_receipt_id", ""),
        "start_receipt_hash": start_view.get("start_receipt_hash", ""),
        "open_confirmation_count": int(start_view.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(start_view.get("confirmed_count", 0) or 0),
        "blocked_for_confirmation": bool(start_view.get("blocked_for_confirmation", False)),
        "ready_for_manual_local_cycle_review": bool(start_view.get("ready_for_manual_local_cycle_review", False)),
        "open_confirmations": list(start_view.get("open_confirmations", []) or [])[:8],
        "confirmed_hash_metadata": list(start_view.get("confirmed_hash_metadata", []) or [])[:8],
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }
    report = {
        "schema_version": PYTHON_EXAM_LOCAL_CYCLE_READINESS_REVIEW_SCHEMA_VERSION,
        "artifact_type": "python_exam_local_cycle_readiness_review",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Local Cycle Readiness Review. It consumes the Local Cycle Start Packet and produces a "
            "human-reviewable recommendation about whether the local cycle stays blocked_for_confirmation, needs "
            "missing confirmation review, or is ready for manual local cycle review after full human confirmation. "
            "It only uses metadata, hashes, Source-Card anchors, task and checkpoint hashes, gate/decision/start "
            "receipt hashes, A0-A2 help level, and confirmation counts. It never executes a local action, writes "
            "anything, or returns raw queries, course raw text, notebook code, local paths, values, solutions, "
            "final interpretations, scores, rankings, grades, proctoring, AI detection, automatic grading, or "
            "exam clearance claims."
        ),
        "local_cycle_readiness_review_endpoint": PYTHON_EXAM_LOCAL_CYCLE_READINESS_REVIEW_ENDPOINT,
        "selected_skill_tag": selected,
        "local_cycle_start_packet_status": start_view.get("status", "missing"),
        "local_cycle_start_packet": packet_view,
        "readiness_review_summary": summary,
        "readiness_review_recommendation": summary["recommendation"],
        "readiness_review_reason": summary["recommendation_reason"],
        "readiness_review_checks": {
            "packet_present": summary["packet_present"],
            "hash_metadata_complete": summary["hash_metadata_complete"],
            "blocked_for_confirmation": summary["blocked_for_confirmation"],
            "request_missing_confirmation_review": summary["request_missing_confirmation_review"],
            "ready_for_manual_local_cycle_review": summary["ready_for_manual_local_cycle_review"],
            "keep_blocked": summary["keep_blocked"],
        },
        "readiness_review_receipt": readiness_review_receipt(summary, packet_view),
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Readiness Review bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def build_python_exam_local_cycle_readiness_review_release_claim_alignment(
    open_review: dict[str, Any] | None = None,
    confirmed_review: dict[str, Any] | None = None,
    missing_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if open_review is None or confirmed_review is None or missing_review is None:
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
        open_packet = build_python_exam_local_cycle_start_packet(
            python_exam_safe_cycle_console=console,
            python_exam_safe_cycle_operator_gate=gate,
            python_exam_operator_gate_decision_receipt=open_decision,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        confirmed_packet = build_python_exam_local_cycle_start_packet(
            python_exam_safe_cycle_console=console,
            python_exam_safe_cycle_operator_gate=gate,
            python_exam_operator_gate_decision_receipt=confirmed_decision,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        open_review = open_review or build_python_exam_local_cycle_readiness_review(
            python_exam_local_cycle_start_packet=open_packet,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        confirmed_review = confirmed_review or build_python_exam_local_cycle_readiness_review(
            python_exam_local_cycle_start_packet=confirmed_packet,
            selected_skill_tag="python_lists",
            public_safe=True,
        )
        missing_review = missing_review or build_python_exam_local_cycle_readiness_review(
            selected_skill_tag="python_lists",
            public_safe=True,
        )

    sections = [
        {
            "section_id": "start_packet_review_trace",
            "summary_claim": "readiness review consumes start-packet metadata, receipts, source cards, and confirmation counts",
            "source_card_ids": ["dfg-gwp", "vanlehn-2011", "dsk-ai-privacy-2024"],
            "readiness_check_ids": [
                "python_exam_local_cycle_readiness_review",
                "python_exam_local_cycle_start_packet",
                "exam_workspace_session_console",
                "review_board_packet",
            ],
            "human_gates": ["human_submission_review_required", "datenschutz_review_required_before_real_pilot"],
        },
        {
            "section_id": "recommendation_boundary_trace",
            "summary_claim": "open confirmations request human review while complete confirmations allow only manual local-cycle review",
            "source_card_ids": ["dfg-gwp", "uoc-hilfsmittel"],
            "readiness_check_ids": [
                "python_exam_local_cycle_readiness_review",
                "python_exam_local_cycle_start_packet",
                "study_session",
                "exam_boundary",
            ],
            "human_gates": ["human_submission_review_required", "written_university_clearance_required_before_exam_use"],
        },
        {
            "section_id": "missing_packet_block_trace",
            "summary_claim": "missing start-packet evidence keeps the review blocked rather than inventing readiness",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679"],
            "readiness_check_ids": ["python_exam_local_cycle_readiness_review", "external_decision_state"],
            "human_gates": ["public_safety_required", "datenschutz_review_required_before_real_pilot"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "readiness review does not publish notebooks, write locally, grade, proctor, detect AI use, or clear exam deployment",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": [
                "python_exam_local_cycle_readiness_review",
                "evaluation_packet",
                "exam_boundary",
            ],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    open_summary = (
        open_review.get("readiness_review_summary", {})
        if isinstance(open_review.get("readiness_review_summary"), dict)
        else {}
    )
    open_packet = (
        open_review.get("local_cycle_start_packet", {})
        if isinstance(open_review.get("local_cycle_start_packet"), dict)
        else {}
    )
    open_receipt = (
        open_review.get("readiness_review_receipt", {})
        if isinstance(open_review.get("readiness_review_receipt"), dict)
        else {}
    )
    confirmed_summary = (
        confirmed_review.get("readiness_review_summary", {})
        if isinstance(confirmed_review.get("readiness_review_summary"), dict)
        else {}
    )
    confirmed_packet = (
        confirmed_review.get("local_cycle_start_packet", {})
        if isinstance(confirmed_review.get("local_cycle_start_packet"), dict)
        else {}
    )
    missing_summary = (
        missing_review.get("readiness_review_summary", {})
        if isinstance(missing_review.get("readiness_review_summary"), dict)
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
    boundary = str(open_review.get("execution_boundary", ""))
    contracts = {
        "open_review_public_safe": open_review.get("public_safety_status") == "pass",
        "confirmed_review_public_safe": confirmed_review.get("public_safety_status") == "pass",
        "missing_review_public_safe": missing_review.get("public_safety_status") == "pass",
        "open_confirmation_review_recommendation_ready": open_review.get("status")
        == "python_exam_local_cycle_readiness_review_ready"
        and open_summary.get("recommendation") == "request_missing_confirmation_review"
        and open_summary.get("recommendation_reason") == "open_confirmations_present"
        and open_summary.get("start_status") == "blocked_for_confirmation"
        and int(open_summary.get("open_confirmation_count", -1) or 0) == 5
        and int(open_summary.get("confirmed_count", -1) or 0) == 0
        and open_summary.get("hash_metadata_complete") is True
        and open_summary.get("packet_present") is True
        and open_review.get("readiness_review_checks", {}).get("request_missing_confirmation_review") is True,
        "confirmed_review_manual_only_ready": confirmed_review.get("status")
        == "python_exam_local_cycle_readiness_review_ready"
        and confirmed_summary.get("recommendation") == "ready_for_manual_local_cycle_review"
        and confirmed_summary.get("recommendation_reason") == "full_human_confirmation_present"
        and int(confirmed_summary.get("open_confirmation_count", -1) or 0) == 0
        and int(confirmed_summary.get("confirmed_count", -1) or 0) == 5
        and confirmed_review.get("local_writes_requested") is False
        and confirmed_review.get("local_execution_started") is False
        and confirmed_packet.get("ready_for_manual_local_cycle_review") is True,
        "missing_start_packet_keeps_blocked": missing_review.get("status")
        == "python_exam_local_cycle_readiness_review_attention"
        and missing_summary.get("recommendation") == "keep_blocked"
        and missing_summary.get("recommendation_reason") == "missing_start_packet"
        and missing_summary.get("packet_present") is False
        and missing_review.get("readiness_review_checks", {}).get("keep_blocked") is True,
        "hash_metadata_and_source_cards_preserved": bool(open_summary.get("task_hash"))
        and bool(open_summary.get("checkpoint_hash"))
        and bool(open_summary.get("gate_receipt_hash"))
        and bool(open_summary.get("decision_receipt_hash"))
        and bool(open_summary.get("start_receipt_hash"))
        and bool(open_receipt.get("receipt_hash"))
        and open_packet.get("source_card_ids") == ["dfg-gwp", "vanlehn-2011"]
        and int(open_packet.get("source_anchor_count", 0) or 0) == 2
        and open_packet.get("help_level") == "A2"
        and open_receipt.get("status") == "local_cycle_readiness_review_receipt_ready_not_exam_clearance",
        "public_outputs_hide_private_review_data": open_review.get("raw_query_returned") is False
        and open_review.get("raw_text_returned") is False
        and open_review.get("raw_cell_returned") is False
        and open_review.get("raw_notebook_returned") is False
        and open_review.get("notebook_code_returned") is False
        and open_review.get("local_paths_returned") is False
        and open_review.get("values_returned") is False
        and open_review.get("solutions_returned") is False
        and open_review.get("final_interpretations_returned") is False
        and "only uses metadata" in boundary
        and "never executes a local action" in boundary
        and "writes anything" in boundary,
        "high_stakes_actions_not_started": open_review.get("automatic_grading_started") is False
        and open_review.get("proctoring_started") is False
        and open_review.get("ai_detection_started") is False
        and open_review.get("exam_clearance_claimed") is False
        and open_review.get("score_returned") is False
        and open_review.get("percentage_returned") is False
        and open_review.get("ranking_returned") is False
        and open_review.get("grade_returned") is False
        and open_review.get("exam_deployment_status") == "not_cleared",
        "not_cleared_receipt_present": open_review.get("exam_deployment_status") == "not_cleared"
        and open_packet.get("exam_deployment_status") == "not_cleared"
        and open_receipt.get("exam_deployment_status") == "not_cleared"
        and open_receipt.get("not_cleared_receipt") is True
        and confirmed_review.get("exam_deployment_status") == "not_cleared",
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "open_status": open_review.get("status"),
        "confirmed_status": confirmed_review.get("status"),
        "missing_status": missing_review.get("status"),
        "selected_skill_tag": open_summary.get("selected_skill_tag"),
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "python-exam-local-cycle-readiness-review-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": PYTHON_EXAM_LOCAL_CYCLE_READINESS_REVIEW_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "open_review_status": open_review.get("status"),
        "open_review_public_safety_status": open_review.get("public_safety_status"),
        "confirmed_review_status": confirmed_review.get("status"),
        "confirmed_review_public_safety_status": confirmed_review.get("public_safety_status"),
        "missing_review_status": missing_review.get("status"),
        "missing_review_public_safety_status": missing_review.get("public_safety_status"),
        "exam_deployment_status": open_review.get("exam_deployment_status"),
        "selected_skill_tag": open_summary.get("selected_skill_tag"),
        "open_recommendation": open_summary.get("recommendation"),
        "open_recommendation_reason": open_summary.get("recommendation_reason"),
        "open_start_status": open_summary.get("start_status"),
        "open_confirmation_count": open_summary.get("open_confirmation_count"),
        "confirmed_recommendation": confirmed_summary.get("recommendation"),
        "confirmed_count": confirmed_summary.get("confirmed_count"),
        "missing_recommendation": missing_summary.get("recommendation"),
        "missing_recommendation_reason": missing_summary.get("recommendation_reason"),
        "packet_present": bool(open_summary.get("packet_present", False)),
        "hash_metadata_complete": bool(open_summary.get("hash_metadata_complete", False)),
        "task_hash_present": bool(open_summary.get("task_hash")),
        "checkpoint_hash_present": bool(open_summary.get("checkpoint_hash")),
        "gate_receipt_hash_present": bool(open_summary.get("gate_receipt_hash")),
        "decision_receipt_hash_present": bool(open_summary.get("decision_receipt_hash")),
        "start_receipt_hash_present": bool(open_summary.get("start_receipt_hash")),
        "review_receipt_hash_present": bool(open_receipt.get("receipt_hash")),
        "source_card_ids": open_packet.get("source_card_ids", []),
        "source_anchor_count": open_packet.get("source_anchor_count", 0),
        "help_level": open_packet.get("help_level"),
        "dry_run_default": bool(open_review.get("dry_run_default", False)),
        "local_writes_requested": bool(open_review.get("local_writes_requested", True)),
        "local_execution_started": bool(open_review.get("local_execution_started", True)),
        "not_cleared_receipt": bool(open_receipt.get("not_cleared_receipt", False)),
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
            "Python exam local-cycle readiness review is a read-only review surface. It may recommend missing "
            "confirmation review or manual local-cycle review based on hash/source-card metadata, but it does not "
            "start local writes, publish raw notebook/query data, grade, proctor, detect AI use, claim "
            "Eigenleistung percentages, or clear exams."
        ),
    }


def safe_start_packet(packet: dict[str, Any]) -> dict[str, Any]:
    summary = packet.get("local_cycle_start_summary", {}) if isinstance(packet.get("local_cycle_start_summary"), dict) else {}
    start = packet.get("start_packet", {}) if isinstance(packet.get("start_packet"), dict) else {}
    receipt = packet.get("local_cycle_start_receipt", {}) if isinstance(packet.get("local_cycle_start_receipt"), dict) else {}
    open_confirmations = safe_confirmation_items(start.get("open_confirmations", []) if isinstance(start.get("open_confirmations"), list) else [])
    confirmed_hash_metadata = safe_confirmation_items(
        start.get("confirmed_hash_metadata", []) if isinstance(start.get("confirmed_hash_metadata"), list) else []
    )
    start_status = str(summary.get("start_status") or start.get("start_status") or "missing")
    selected = str(summary.get("selected_skill_tag") or start.get("selected_skill_tag") or packet.get("selected_skill_tag", "")).strip()
    return {
        "status": packet.get("status", "missing"),
        "selected_skill_tag": selected,
        "start_status": start_status,
        "blocked_reason": str(summary.get("blocked_reason") or start.get("blocked_reason") or ""),
        "next_safe_action": safe_action(str(summary.get("next_safe_action") or start.get("next_safe_action") or "")),
        "next_safe_user_action": str(summary.get("next_safe_user_action") or start.get("next_safe_user_action") or ""),
        "task_hash": str(summary.get("selected_task_hash") or start.get("task_hash") or ""),
        "checkpoint_hash": str(summary.get("checkpoint_hash") or start.get("checkpoint_hash") or ""),
        "source_card_ids": [str(item) for item in (start.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(start.get("source_anchor_count", 0) or 0),
        "help_level": safe_help_level(str(summary.get("help_level") or start.get("help_level") or "A2")),
        "gate_receipt_id": str(summary.get("gate_receipt_id") or start.get("gate_receipt_id") or ""),
        "gate_receipt_hash": str(start.get("gate_receipt_hash") or ""),
        "decision_receipt_id": str(summary.get("decision_receipt_id") or start.get("decision_receipt_id") or ""),
        "decision_receipt_hash": str(start.get("decision_receipt_hash") or ""),
        "start_receipt_id": str(receipt.get("receipt_id", "")),
        "start_receipt_hash": str(receipt.get("receipt_hash", "")),
        "open_confirmation_count": len(open_confirmations),
        "confirmed_count": len(confirmed_hash_metadata),
        "open_confirmations": open_confirmations,
        "confirmed_hash_metadata": confirmed_hash_metadata,
        "blocked_for_confirmation": start_status == "blocked_for_confirmation",
        "ready_for_manual_local_cycle_review": start_status == "ready_after_human_confirmation",
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def safe_confirmation_items(items: list[Any]) -> list[dict[str, Any]]:
    safe = []
    for item in items:
        if not isinstance(item, dict):
            continue
        safe.append(
            {
                "step_id": str(item.get("step_id", "")),
                "action": str(item.get("action", "")),
                "card_hash": str(item.get("card_hash", "")),
                "selected_task_hash": str(item.get("selected_task_hash", "")),
                "checkpoint_hash": str(item.get("checkpoint_hash", "")),
                "help_level": safe_help_level(str(item.get("help_level", "A2"))),
                "operator_confirmed": bool(item.get("operator_confirmed", False)),
                "not_cleared_receipt": True,
                "exam_deployment_status": "not_cleared",
            }
        )
    return safe


def readiness_review_summary(*, selected_skill_tag: str, start_view: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    packet_present = start_view.get("status") != "missing"
    required_hashes = [
        str(start_view.get("task_hash", "")),
        str(start_view.get("checkpoint_hash", "")),
        str(start_view.get("gate_receipt_hash", "")),
        str(start_view.get("decision_receipt_hash", "")),
        str(start_view.get("start_receipt_hash", "")),
    ]
    has_required_hashes = all(required_hashes) and bool(start_view.get("selected_skill_tag"))
    has_anchor_metadata = int(start_view.get("source_anchor_count", 0) or 0) > 0 and bool(start_view.get("source_card_ids", []))
    help_level = str(start_view.get("help_level", "A2"))
    help_level_safe = help_level in {"A0", "A1", "A2"}
    start_status = str(start_view.get("start_status", "missing"))
    open_confirmation_count = int(start_view.get("open_confirmation_count", 0) or 0)
    confirmed_count = int(start_view.get("confirmed_count", 0) or 0)
    blocked_for_confirmation = bool(start_view.get("blocked_for_confirmation", False))
    request_missing_confirmation_review = open_confirmation_count > 0
    ready_for_manual_local_cycle_review = (
        start_status == "ready_after_human_confirmation"
        and confirmed_count > 0
        and open_confirmation_count == 0
        and has_required_hashes
        and has_anchor_metadata
        and help_level_safe
    )
    keep_blocked = not packet_present or not has_required_hashes or not has_anchor_metadata or not help_level_safe or (
        not request_missing_confirmation_review and not ready_for_manual_local_cycle_review
    )
    if not packet_present:
        recommendation = "keep_blocked"
        recommendation_reason = "missing_start_packet"
    elif not has_required_hashes:
        recommendation = "keep_blocked"
        recommendation_reason = "missing_hash_metadata"
    elif not has_anchor_metadata:
        recommendation = "keep_blocked"
        recommendation_reason = "missing_source_anchor_metadata"
    elif not help_level_safe:
        recommendation = "keep_blocked"
        recommendation_reason = "unsupported_help_level"
    elif request_missing_confirmation_review:
        recommendation = "request_missing_confirmation_review"
        recommendation_reason = "open_confirmations_present"
    elif ready_for_manual_local_cycle_review:
        recommendation = "ready_for_manual_local_cycle_review"
        recommendation_reason = "full_human_confirmation_present"
    else:
        recommendation = "keep_blocked"
        recommendation_reason = "start_packet_not_ready"
    return {
        "status": "python_exam_local_cycle_readiness_review_ready" if packet_present else "python_exam_local_cycle_readiness_review_attention",
        "selected_skill_tag": selected_skill_tag,
        "packet_status": start_view.get("status", "missing"),
        "start_status": start_status,
        "blocked_reason": str(start_view.get("blocked_reason", "")),
        "blocked_for_confirmation": blocked_for_confirmation,
        "request_missing_confirmation_review": recommendation == "request_missing_confirmation_review",
        "ready_for_manual_local_cycle_review": recommendation == "ready_for_manual_local_cycle_review",
        "keep_blocked": recommendation == "keep_blocked",
        "recommendation": recommendation,
        "recommendation_reason": recommendation_reason,
        "open_confirmation_count": open_confirmation_count,
        "confirmed_count": confirmed_count,
        "task_hash": str(start_view.get("task_hash", "")),
        "checkpoint_hash": str(start_view.get("checkpoint_hash", "")),
        "gate_receipt_id": str(start_view.get("gate_receipt_id", "")),
        "gate_receipt_hash": str(start_view.get("gate_receipt_hash", "")),
        "decision_receipt_id": str(start_view.get("decision_receipt_id", "")),
        "decision_receipt_hash": str(start_view.get("decision_receipt_hash", "")),
        "start_receipt_id": str(start_view.get("start_receipt_id", "")),
        "start_receipt_hash": str(start_view.get("start_receipt_hash", "")),
        "source_card_ids": list(start_view.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": int(start_view.get("source_anchor_count", 0) or 0),
        "help_level": help_level,
        "next_safe_action": str(start_view.get("next_safe_action", "")),
        "next_safe_user_action": str(start_view.get("next_safe_user_action", "")),
        "hash_metadata_complete": has_required_hashes and has_anchor_metadata and help_level_safe,
        "packet_present": packet_present,
        "exam_deployment_status": "not_cleared",
    }


def readiness_review_receipt(summary: dict[str, Any], packet_view: dict[str, Any]) -> dict[str, Any]:
    receipt_hash = sha256_text(
        json.dumps({"summary": summary, "packet_view": packet_view}, sort_keys=True, ensure_ascii=False)
    )
    return {
        "status": "local_cycle_readiness_review_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "score_returned": False,
        "grade_returned": False,
    }


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
    return [
        f"Recommendation: {summary['recommendation']}.",
        "Keep the review read-only; do not start any local write from this packet.",
        "Use the result as the human-checkpoint before the next local exam work cycle.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-local-cycle-readiness-review")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["public_safety_findings"] = scan["findings"]
