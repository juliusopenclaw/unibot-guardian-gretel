from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .clearance import validate_clearance_record
from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction_decision import validate_extraction_decision_record
from .external_decision_journal import (
    synthetic_exam_clearance_record,
    synthetic_local_extraction_decision_record,
)
from .materials import sha256_text
from .public_safety import scan_text
from .source_cards import get_source_card


DECISION_STATE_SCHEMA_VERSION = "unibot-external-decision-state-v1"
DECISION_STATE_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-external-decision-state-release-review-board-claim-alignment-v1"
)


def build_external_decision_state_release_claim_alignment(state: dict[str, Any] | None = None) -> dict[str, Any]:
    if state is None:
        state = build_external_decision_state(
            extraction_decision_record=synthetic_local_extraction_decision_record(),
            exam_clearance_record=synthetic_exam_clearance_record(),
            deployment_go_reference="synthetic hash-only deployment go reference",
        )

    sections = [
        {
            "section_id": "decision_state_boundary_trace",
            "summary_claim": "decision state validates records and derives next gates without storing raw decisions or silently switching deployment",
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024"],
            "readiness_check_ids": ["external_decision_state", "external_decision_record_journal", "public_safety"],
            "human_gates": ["human_submission_review_required", "datenschutz_review_required_before_real_pilot"],
        },
        {
            "section_id": "local_extraction_gate_trace",
            "summary_claim": "local extraction can start only from a valid rights/privacy decision and still requires receipts",
            "source_card_ids": ["gdpr-2016-679", "dfg-gwp"],
            "readiness_check_ids": ["external_decision_state", "stakeholder_submission_bundle", "data_protection_screening"],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "exam_authority_gate_trace",
            "summary_claim": "exam authority records stay hash-only and do not clear deployment without an explicit manual switch",
            "source_card_ids": ["hg-nrw-2025", "hg-nrw-64", "uoc-hilfsmittel", "uoc-ki-faq"],
            "readiness_check_ids": ["external_decision_state", "authority_handoff", "exam_boundary"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "decision state keeps high-stakes claims blocked even when records are valid",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq"],
            "readiness_check_ids": ["external_decision_state", "review_board_packet", "release_runbook"],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)

    local = state.get("local_extraction_decision", {})
    exam = state.get("exam_authority_decision", {})
    gate_summary = state.get("gate_summary", {})
    not_authorized = set(state.get("not_authorized_by_this_state", []))
    boundary = state.get("decision_boundary", "")

    contracts = {
        "state_public_safe": state.get("public_safety_status") == "pass",
        "decision_boundary_blocks_raw_send_legal_and_silent_deploy": all(
            phrase in boundary
            for phrase in [
                "does not store raw written decisions",
                "send submissions",
                "provide legal advice",
                "silently switch real exam deployment",
            ]
        ),
        "exam_deployment_not_cleared": state.get("exam_deployment_status") == "not_cleared",
        "local_extraction_valid_hash_only": local.get("status") == "ok_authorizes_local_extraction"
        and local.get("authorized_by_record") is True
        and bool(local.get("decision_reference_hash"))
        and local.get("raw_decision_reference_stored") is False,
        "exam_authority_valid_hash_only_no_deploy": exam.get("status") == "ok_exam_controlled_gateway_clearance_record"
        and exam.get("cleared_scope_by_record") is True
        and bool(exam.get("decision_reference_hash"))
        and exam.get("raw_decision_reference_stored") is False
        and bool(exam.get("deployment_go_reference_hash"))
        and exam.get("deployment_switch_status") == "manual_go_recorded_but_not_deployed",
        "gate_summary_requires_manual_switch": gate_summary.get("local_extraction_can_start") is True
        and gate_summary.get("exam_clearance_record_valid") is True
        and gate_summary.get("manual_deployment_go_recorded") is True
        and gate_summary.get("course_material_extraction_still_requires_receipts") is True
        and gate_summary.get("exam_deployment_requires_manual_switch") is True,
        "high_stakes_claims_blocked": {
            "public release of raw private course text",
            "cloud processing",
            "automatic grading",
            "proctoring",
            "KI detection as evidence",
            "silent exam deployment",
        }.issubset(not_authorized),
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": [
            "raw written decision storage",
            "submission send",
            "legal advice",
            "silent deployment switch",
            "exam deployment",
            "public raw course text release",
            "cloud processing",
            "official grading",
            "proctoring",
            "KI-detection evidence",
        ],
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "external-decision-state-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": DECISION_STATE_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "failed_contract_ids": failed_contract_ids,
        "required_readiness_check_ids": sorted(
            {check_id for section in sections for check_id in section["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({gate for section in sections for gate in section["human_gates"]}),
        "blocked_claims": payload["blocked_claims"],
        "public_safety_status": scan["status"],
        "policy": (
            "External decision state is a derived review state only; it can show validated records and next gates, "
            "but it does not store raw decisions, send submissions, give legal advice, switch deployment, grade, "
            "proctor, detect KI, or clear exam use by itself."
        ),
    }


def build_external_decision_state(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    extraction_decision_record: dict[str, Any] | None = None,
    exam_clearance_record: dict[str, Any] | None = None,
    deployment_go_reference: str | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    extraction_validation = validate_extraction_decision_record(extraction_decision_record or {})
    exam_validation = validate_clearance_record(exam_clearance_record or {})
    extraction_ready = extraction_validation.get("status") == "ok_authorizes_local_extraction"
    exam_record_ready = exam_validation.get("status") == "ok_exam_controlled_gateway_clearance_record"
    deployment_go_hash = sha256_text(str(deployment_go_reference)) if deployment_go_reference else ""

    state = {
        "schema_version": DECISION_STATE_SCHEMA_VERSION,
        "artifact_type": "unibot_external_decision_state",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": decision_state_status(extraction_ready, exam_record_ready),
        "exam_deployment_status": "not_cleared",
        "decision_boundary": (
            "This state validates written decision records and derives next gates. "
            "It does not store raw written decisions, send submissions, provide legal advice, "
            "or silently switch real exam deployment."
        ),
        "local_extraction_decision": {
            "status": extraction_validation.get("status"),
            "authorized_by_record": extraction_ready,
            "issues": extraction_validation.get("issues", []),
            "warnings": extraction_validation.get("warnings", []),
            "decision_reference_hash": extraction_validation.get("rights_decision_reference_hash", ""),
            "raw_decision_reference_stored": False,
            "next_gate_if_valid": "build extraction operator packet, run local private extraction, then validate receipts",
        },
        "exam_authority_decision": {
            "status": exam_validation.get("status"),
            "cleared_scope_by_record": exam_record_ready,
            "issues": exam_validation.get("issues", []),
            "warnings": exam_validation.get("warnings", []),
            "decision_reference_hash": exam_validation.get("decision_reference_hash", ""),
            "raw_decision_reference_stored": False,
            "deployment_go_reference_hash": deployment_go_hash,
            "deployment_switch_status": "manual_go_recorded_but_not_deployed" if exam_record_ready and deployment_go_hash else "not_requested",
            "next_gate_if_valid": "manual institutional deployment review; keep exam_deployment_status not_cleared until intentionally changed",
        },
        "gate_summary": {
            "local_extraction_can_start": extraction_ready,
            "exam_clearance_record_valid": exam_record_ready,
            "manual_deployment_go_recorded": bool(exam_record_ready and deployment_go_hash),
            "course_material_extraction_still_requires_receipts": extraction_ready,
            "exam_deployment_requires_manual_switch": True,
        },
        "not_authorized_by_this_state": [
            "public release of raw private course text",
            "cloud processing",
            "automatic grading",
            "proctoring",
            "KI detection as evidence",
            "silent exam deployment",
        ],
        "next_actions": next_actions(extraction_ready, exam_record_ready, bool(deployment_go_hash)),
    }
    attach_public_scan(state, public_safe=public_safe, source_name="external-decision-state")
    state["release_claim_alignment"] = build_external_decision_state_release_claim_alignment(state)
    return state


def decision_state_status(extraction_ready: bool, exam_record_ready: bool) -> str:
    if extraction_ready and exam_record_ready:
        return "external_decisions_validated_for_next_gates"
    if extraction_ready or exam_record_ready:
        return "partial_external_decisions_validated"
    return "pending_external_decisions"


def next_actions(extraction_ready: bool, exam_record_ready: bool, deployment_go_recorded: bool) -> list[str]:
    actions: list[str] = []
    if extraction_ready:
        actions.append("Use the validated extraction decision to build an operator packet and validate one receipt per OCR/transcription job.")
    else:
        actions.append("Collect and validate the rights/privacy decision record before any local OCR/transcription.")
    if exam_record_ready:
        actions.append("Record the valid exam clearance as a human-review artifact while keeping deployment not_cleared until an explicit manual switch.")
    else:
        actions.append("Collect and validate a written exam-gateway clearance record before any real exam planning.")
    if exam_record_ready and not deployment_go_recorded:
        actions.append("If deployment is ever requested, record a separate manual deployment-go reference and rerun the audit.")
    return actions


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
