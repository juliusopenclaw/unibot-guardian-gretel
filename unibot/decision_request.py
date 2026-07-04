from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .materials import sha256_text
from .public_safety import scan_text
from .source_cards import get_source_card
from .submission import build_stakeholder_submission_bundle


DECISION_REQUEST_SCHEMA_VERSION = "unibot-stakeholder-decision-request-v1"
DECISION_REQUEST_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-stakeholder-decision-request-release-review-board-claim-alignment-v1"
)

ALLOWED_LANE_IDS = {"rights_privacy_local_extraction", "exam_gateway_authority_clearance"}
ALLOWED_RECEIPT_STATUSES = {"draft_not_sent", "sent_for_human_review", "withdrawn", "response_received"}


def build_stakeholder_decision_request_release_claim_alignment(request: dict[str, Any]) -> dict[str, Any]:
    sections = [
        {
            "section_id": "request_boundary_trace",
            "summary_claim": "decision request is a single manual-review draft and not an automatic external send or approval",
            "source_card_ids": ["uoc-ki-lehre", "dfg-gwp"],
            "readiness_check_ids": [
                "stakeholder_decision_request",
                "stakeholder_submission_bundle",
                "review_board_packet",
                "public_safety",
            ],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
        {
            "section_id": "receipt_boundary_trace",
            "summary_claim": "receipt template records only human submission status and hash-safe references, never raw decision text",
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024"],
            "readiness_check_ids": ["stakeholder_decision_request", "data_protection_screening", "public_safety"],
            "human_gates": ["human_submission_review_required", "datenschutz_review_required_before_real_pilot"],
        },
        {
            "section_id": "lane_evidence_trace",
            "summary_claim": "request evidence remains linked to the stakeholder submission bundle and one selected decision lane",
            "source_card_ids": ["dfg-gwp"],
            "readiness_check_ids": [
                "stakeholder_decision_request",
                "stakeholder_submission_bundle",
                "source_card_drift_guard",
            ],
            "human_gates": ["human_submission_review_required"],
        },
        {
            "section_id": "exam_boundary_trace",
            "summary_claim": "exam lane requests remain not cleared and continue to require written university authority review",
            "source_card_ids": ["hg-nrw-2025", "hg-nrw-64", "uoc-hilfsmittel", "uoc-ki-faq"],
            "readiness_check_ids": ["stakeholder_decision_request", "authority_handoff", "exam_boundary"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)

    lane_id = request.get("lane_id", "")
    receipt = request.get("receipt_template", {})
    minimum_record = request.get("minimum_record_template", {})
    evidence_manifest = request.get("evidence_manifest", [])
    evidence_by_artifact = {item.get("artifact"): item for item in evidence_manifest}
    boundary = request.get("request_boundary", "")
    checklist_text = " ".join(request.get("human_review_checklist", []))
    must_not_claim = set(request.get("must_not_claim", []))

    lane_specific_contract = False
    if lane_id == "rights_privacy_local_extraction":
        lane_specific_contract = (
            request.get("validator_endpoint") == "/api/unibot/course/extraction-decision/validate"
            and "Datenschutz" in request.get("target_reviewer_roles", [])
            and minimum_record.get("cloud_processing_allowed") is False
            and minimum_record.get("raw_text_public_release_allowed") is False
            and "cloud processing" in checklist_text
            and "exam deployment is authorized" in must_not_claim
        )
    if lane_id == "exam_gateway_authority_clearance":
        lane_specific_contract = (
            request.get("validator_endpoint") == "/api/unibot/institutional-clearance/validate"
            and "Pruefungsamt" in request.get("target_reviewer_roles", [])
            and minimum_record.get("help_levels_allowed") == ["A0", "A1", "A2"]
            and minimum_record.get("no_proctoring") is True
            and minimum_record.get("no_ai_detection") is True
            and minimum_record.get("no_automatic_grading") is True
            and "exam use is already cleared" in must_not_claim
        )

    contracts = {
        "request_ready_for_manual_review_not_sent": request.get("status") == "ready_for_manual_review_not_sent",
        "supported_single_lane": lane_id in ALLOWED_LANE_IDS,
        "exam_deployment_not_cleared": request.get("exam_deployment_status") == "not_cleared",
        "request_boundary_blocks_send_approval_raw_text_exam": all(
            phrase in boundary
            for phrase in [
                "does not send it",
                "does not claim approval",
                "stores no raw written decision text",
                "does not clear exam deployment",
            ]
        ),
        "human_review_checklist_blocks_private_and_approval_claims": all(
            phrase in checklist_text
            for phrase in [
                "not raw private course text",
                "local absolute paths",
                "private written decision text are absent",
                "does not claim approval",
            ]
        ),
        "receipt_template_is_manual_hash_only": receipt.get("manual_submission_status") == "draft_not_sent"
        and receipt.get("submission_performed_by_human") is True
        and receipt.get("tool_sent_message") is False
        and receipt.get("raw_decision_text_included") is False
        and "hash-only reference" in receipt.get("submission_reference", ""),
        "evidence_manifest_links_submission_bundle_and_lane": evidence_by_artifact.get("stakeholder_submission_bundle", {}).get("status")
        == "ready_for_human_submission_not_sent"
        and evidence_by_artifact.get("stakeholder_submission_bundle", {}).get("public_safety_status") == "pass"
        and evidence_by_artifact.get("stakeholder_submission_bundle", {}).get("exam_deployment_status") == "not_cleared"
        and bool(evidence_by_artifact.get("stakeholder_submission_bundle", {}).get("summary_hash"))
        and evidence_by_artifact.get("decision_lane", {}).get("lane_id") == lane_id
        and bool(evidence_by_artifact.get("decision_lane", {}).get("current_evidence_hash")),
        "lane_specific_contract_matches_boundary": lane_specific_contract,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": [
            "automatic external send",
            "approval claim",
            "exam clearance",
            "official grading",
            "proctoring",
            "KI-detection evidence",
            "raw written decision storage",
            "public raw course text release",
        ],
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "stakeholder-decision-request-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": DECISION_REQUEST_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
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
            "Stakeholder decision request release claims are manual-review drafts only; they do not send "
            "messages, claim approval, store raw written decisions, clear exam use, grade, proctor, detect KI, "
            "or release private course material."
        ),
    }


def build_stakeholder_decision_request(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    lane_id: str = "rights_privacy_local_extraction",
    base_path: str | None = None,
    review_policy: str = "staged",
    public_safe: bool = True,
) -> dict[str, Any]:
    bundle = build_stakeholder_submission_bundle(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    lane = next((item for item in bundle.get("decision_lanes", []) if item.get("lane_id") == lane_id), None)
    if lane is None:
        request = unsupported_lane_request(course_id, lane_id, bundle)
        attach_public_scan(request, public_safe=public_safe, source_name="stakeholder-decision-request")
        return request

    stable_input = {
        "course_id": safe_course_id(course_id),
        "lane_id": lane_id,
        "decision_type": lane.get("decision_type"),
        "validator_endpoint": lane.get("validator_endpoint"),
        "current_evidence": lane.get("current_evidence", {}),
    }
    request_id = sha256_text(json.dumps(stable_input, sort_keys=True, ensure_ascii=False))[:24]
    request = {
        "schema_version": DECISION_REQUEST_SCHEMA_VERSION,
        "artifact_type": "unibot_stakeholder_decision_request",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": "ready_for_manual_review_not_sent",
        "request_id": request_id,
        "lane_id": lane_id,
        "title": lane.get("title", ""),
        "decision_type": lane.get("decision_type", lane_id),
        "exam_deployment_status": "not_cleared",
        "request_boundary": (
            "This packet prepares one manual stakeholder request. UniBot does not send it, "
            "does not claim approval, stores no raw written decision text, and does not clear exam deployment."
        ),
        "target_reviewer_roles": lane.get("reviewer_roles", []),
        "decision_request": lane.get("decision_request", ""),
        "validator_endpoint": lane.get("validator_endpoint"),
        "follow_up_endpoint_if_valid": lane.get("follow_up_endpoint_if_valid"),
        "minimum_record_template": lane.get("minimum_record_template", {}),
        "submission_message_template": lane.get("submission_message_template", ""),
        "must_not_claim": lane.get("must_not_claim", []),
        "human_review_checklist": human_review_checklist(lane_id),
        "evidence_manifest": evidence_manifest(bundle, lane),
        "receipt_template": {
            "request_id": request_id,
            "lane_id": lane_id,
            "manual_submission_status": "draft_not_sent",
            "submission_performed_by_human": True,
            "tool_sent_message": False,
            "channel": "to_be_filled_after_manual_review",
            "submitted_by_role": "project_owner",
            "reviewer_roles": lane.get("reviewer_roles", []),
            "submission_reference": "hash-only reference to manually sent request; do not paste private mail text",
            "raw_decision_text_included": False,
        },
        "next_actions": [
            "Review this packet manually before any external communication.",
            "If a human sends the request, validate a request receipt with the receipt endpoint.",
            "Validate the written decision record itself before changing extraction or exam gates.",
        ],
    }
    request["release_claim_alignment"] = build_stakeholder_decision_request_release_claim_alignment(request)
    attach_public_scan(request, public_safe=public_safe, source_name="stakeholder-decision-request")
    return request


def validate_decision_request_receipt(receipt: dict[str, Any] | None) -> dict[str, Any]:
    record = dict(receipt or {})
    issues: list[str] = []
    warnings: list[str] = []

    request_id = str(record.get("request_id", "")).strip()
    if not request_id:
        issues.append("request_id_required")
    lane_id = str(record.get("lane_id", "")).strip()
    if lane_id not in ALLOWED_LANE_IDS:
        issues.append("unsupported_lane_id")
    status = str(record.get("manual_submission_status", "")).strip()
    if status not in ALLOWED_RECEIPT_STATUSES:
        issues.append("unsupported_manual_submission_status")

    sent_like = status in {"sent_for_human_review", "response_received"}
    if sent_like and not bool(record.get("submission_performed_by_human", False)):
        issues.append("manual_submission_must_be_human_performed")
    if bool(record.get("tool_sent_message", False)):
        issues.append("tool_must_not_send_stakeholder_request")
    if bool(record.get("raw_decision_text_included", False)):
        issues.append("raw_decision_text_must_not_be_included")
    if sent_like and not str(record.get("channel", "")).strip():
        issues.append("channel_required_for_sent_receipt")
    if sent_like and not str(record.get("submitted_by_role", "")).strip():
        issues.append("submitted_by_role_required_for_sent_receipt")
    if sent_like and not str(record.get("submission_reference", "")).strip():
        issues.append("submission_reference_required_for_sent_receipt")

    reviewer_roles = [str(item).strip() for item in record.get("reviewer_roles", []) if str(item).strip()]
    if sent_like and not reviewer_roles:
        issues.append("reviewer_roles_required_for_sent_receipt")
    if status == "draft_not_sent":
        warnings.append("receipt_is_draft_only_no_external_submission")

    reference = str(record.get("submission_reference", "")).strip()
    safe_summary = {
        "schema_version": DECISION_REQUEST_SCHEMA_VERSION,
        "artifact_type": "unibot_stakeholder_decision_request_receipt_validation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ok_manual_request_receipt" if not issues and sent_like else "draft_receipt_not_sent" if not issues else "blocked",
        "request_id": request_id or "missing",
        "lane_id": lane_id or "missing",
        "manual_submission_status": status or "missing",
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
        "submission_performed_by_human": bool(record.get("submission_performed_by_human", False)),
        "tool_sent_message": bool(record.get("tool_sent_message", False)),
        "submission_reference_hash": sha256_text(reference) if reference else "",
        "raw_submission_reference_stored": False,
        "raw_decision_text_included": bool(record.get("raw_decision_text_included", False)),
        "receipt_effect": receipt_effect(status, issues, lane_id),
    }
    attach_public_scan(safe_summary, public_safe=True, source_name="stakeholder-decision-request-receipt")
    return safe_summary


def build_stakeholder_decision_request_markdown(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    lane_id: str = "rights_privacy_local_extraction",
    base_path: str | None = None,
    review_policy: str = "staged",
) -> str:
    packet = build_stakeholder_decision_request(
        course_id,
        lane_id=lane_id,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=True,
    )
    checklist = "\n".join(f"- {item}" for item in packet.get("human_review_checklist", []))
    reviewers = "\n".join(f"- {item}" for item in packet.get("target_reviewer_roles", []))
    must_not = "\n".join(f"- {item}" for item in packet.get("must_not_claim", []))
    evidence = "\n".join(
        (
            f"- {item.get('artifact')}: status={item.get('status')}; "
            f"public_safety={item.get('public_safety_status', 'n/a')}; "
            f"hash={item.get('summary_hash') or item.get('current_evidence_hash')}"
        )
        for item in packet.get("evidence_manifest", [])
    )
    receipt_template = json.dumps(packet.get("receipt_template", {}), indent=2, sort_keys=True)
    minimum_record = json.dumps(packet.get("minimum_record_template", {}), indent=2, sort_keys=True)
    release_alignment = packet.get("release_claim_alignment", {})
    return (
        "# UniBot Stakeholder Decision Request\n\n"
        f"Status: {packet.get('status')}\n\n"
        f"Request ID: `{packet.get('request_id', 'missing')}`\n\n"
        f"Lane: `{packet.get('lane_id', 'missing')}`\n\n"
        f"Exam deployment: `{packet.get('exam_deployment_status', 'not_cleared')}`\n\n"
        f"Boundary: {packet.get('request_boundary')}\n\n"
        "## Release Claim Alignment\n\n"
        f"- Status: {release_alignment.get('status', 'missing')}\n"
        f"- Public Safety: {release_alignment.get('public_safety_status', 'missing')}\n"
        f"- Human Gates: {', '.join(release_alignment.get('required_human_gates', []))}\n"
        f"- Blocked Claims: {', '.join(release_alignment.get('blocked_claims', []))}\n\n"
        "## Decision Request\n\n"
        f"{packet.get('decision_request', '')}\n\n"
        "## Draft Message\n\n"
        f"{packet.get('submission_message_template', '')}\n\n"
        "## Target Reviewer Roles\n\n"
        f"{reviewers or '- to be assigned'}\n\n"
        "## Human Review Checklist\n\n"
        f"{checklist or '- no checklist generated'}\n\n"
        "## Must Not Claim\n\n"
        f"{must_not or '- no claims listed'}\n\n"
        "## Evidence Manifest\n\n"
        f"{evidence or '- no evidence generated'}\n\n"
        "## Minimum Decision Record Template\n\n"
        f"```json\n{minimum_record}\n```\n\n"
        "## Manual Receipt Template\n\n"
        f"```json\n{receipt_template}\n```\n\n"
        "## Next Actions\n\n"
        + "\n".join(f"- {item}" for item in packet.get("next_actions", []))
        + "\n"
    )


def unsupported_lane_request(course_id: str, lane_id: str, bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": DECISION_REQUEST_SCHEMA_VERSION,
        "artifact_type": "unibot_stakeholder_decision_request",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": "blocked_unsupported_decision_lane",
        "lane_id": lane_id,
        "exam_deployment_status": "not_cleared",
        "request_boundary": "Unsupported lane; no request generated and nothing sent.",
        "available_lane_ids": [lane.get("lane_id") for lane in bundle.get("decision_lanes", [])],
        "next_actions": ["Choose a supported decision lane from the stakeholder submission bundle."],
    }


def human_review_checklist(lane_id: str) -> list[str]:
    common = [
        "Confirm the packet contains metadata and summaries only, not raw private course text.",
        "Confirm local absolute paths, names, emails, and private written decision text are absent.",
        "Confirm the request does not claim approval, legal advice, or exam deployment.",
        "Confirm the validator endpoint and minimum record template match the requested lane.",
    ]
    if lane_id == "rights_privacy_local_extraction":
        return common + [
            "Confirm cloud processing remains false for this gate.",
            "Confirm human review is required before any extracted text enters the private tutor index.",
        ]
    if lane_id == "exam_gateway_authority_clearance":
        return common + [
            "Confirm the request says exam_deployment_status remains not_cleared and clearance is a real-world reminder, not a technical blocker.",
            "Confirm A0-A2, no proctoring, no KI detection, and no automatic grading are explicit.",
        ]
    return common


def evidence_manifest(bundle: dict[str, Any], lane: dict[str, Any]) -> list[dict[str, Any]]:
    summary = bundle.get("combined_evidence_summary", {})
    lane_evidence = lane.get("current_evidence", {})
    return [
        {
            "artifact": "stakeholder_submission_bundle",
            "status": bundle.get("status"),
            "public_safety_status": bundle.get("public_safety_status"),
            "exam_deployment_status": bundle.get("exam_deployment_status"),
            "open_gate_count": len(bundle.get("open_external_gates", [])),
            "summary_hash": sha256_text(json.dumps(summary, sort_keys=True, ensure_ascii=False)),
        },
        {
            "artifact": "decision_lane",
            "lane_id": lane.get("lane_id"),
            "status": lane.get("status"),
            "validator_endpoint": lane.get("validator_endpoint"),
            "current_evidence_hash": sha256_text(json.dumps(lane_evidence, sort_keys=True, ensure_ascii=False)),
        },
    ]


def receipt_effect(status: str, issues: list[str], lane_id: str) -> str:
    if issues:
        return "receipt_rejected_no_gate_change"
    if status == "draft_not_sent":
        return "draft_only_no_external_submission_and_no_gate_change"
    if status == "sent_for_human_review":
        return f"manual_request_sent_for_{lane_id}_no_decision_record_yet"
    if status == "response_received":
        return f"response_received_for_{lane_id}_validate_decision_record_next"
    if status == "withdrawn":
        return f"manual_request_withdrawn_for_{lane_id}_no_gate_change"
    return "no_gate_change"


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
