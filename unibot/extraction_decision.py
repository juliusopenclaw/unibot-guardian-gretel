from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction import build_course_extraction_queue
from .public_safety import scan_text
from .source_cards import get_source_card
from .materials import sha256_text


EXTRACTION_DECISION_SCHEMA_VERSION = "unibot-extraction-decision-v1"

REQUIRED_REVIEWER_ROLES = [
    "Datenschutz",
    "Lehreinheit / Modulverantwortliche",
    "IT / SZI",
]
ALLOWED_JOB_TYPES = {"ocr", "transcription"}
ALLOWED_DECISION_STATUSES = {"needs_review", "approved_for_local_extraction", "rejected"}


def build_extraction_decision_packet(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    review_policy: str = "staged",
    public_safe: bool = True,
) -> dict[str, Any]:
    queue = build_course_extraction_queue(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    source_cards = [
        card
        for source_id in ["gdpr-2016-679", "dsk-ai-privacy-2024", "uoc-ki-lehre", "dfg-gwp"]
        if (card := get_source_card(source_id))
    ]
    packet = {
        "schema_version": EXTRACTION_DECISION_SCHEMA_VERSION,
        "artifact_type": "course_extraction_rights_privacy_decision_packet",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": "draft_ready_for_rights_privacy_review",
        "exam_deployment_status": "not_cleared",
        "decision_boundary": "This packet prepares a local OCR/transcription decision; it is not approval, legal advice, or exam clearance.",
        "queue_summary": queue["counts"],
        "required_decisions": [
            "Whether local OCR of slide/document files is permitted for private tutor indexing.",
            "Whether local transcription of course videos is permitted for private tutor indexing.",
            "Which local storage location, retention period, and access roles are permitted.",
            "Whether extracted text must be reviewed before source-card or tutor use.",
            "Whether any cloud processing is prohibited or separately reviewable.",
            "How deletion/withdrawal/revocation is documented.",
        ],
        "required_reviewer_roles": REQUIRED_REVIEWER_ROLES,
        "minimum_decision_record": {
            "decision_status": "needs_review",
            "scope": "local_private_course_extraction",
            "allowed_job_types": ["ocr", "transcription"],
            "storage_policy": "local_private_only",
            "cloud_processing_allowed": False,
            "raw_text_public_release_allowed": False,
            "human_review_before_tutor_index": True,
            "retention_decision": "to_be_filled_by_review",
            "access_roles": ["project_owner", "approved_reviewer"],
            "reviewer_roles": REQUIRED_REVIEWER_ROLES,
            "decision_reference": "hash-only reference; do not include names, emails, or private text in public packets",
        },
        "approval_effect_if_valid": {
            "authorizes": "metadata-selected local OCR/transcription dry-run and private extraction workspace only",
            "does_not_authorize": [
                "public release of raw extracted text",
                "exam deployment",
                "automatic grading",
                "cloud processing",
                "tutor indexing before human review",
            ],
        },
        "source_cards": source_cards,
        "queue_policy": queue["job_policy"],
        "next_actions": [
            "collect a written role-based decision record using the minimum schema",
            "validate the decision record before passing a rights_decision_reference to extraction manifests",
            "keep raw extracted text local-private and review it before private tutor indexing",
        ],
    }
    attach_public_scan(packet, public_safe=public_safe, source_name="extraction-decision-packet")
    return packet


def validate_extraction_decision_record(decision: dict[str, Any] | None) -> dict[str, Any]:
    record = dict(decision or {})
    issues: list[str] = []
    warnings: list[str] = []

    status = str(record.get("decision_status", "")).strip()
    if status not in ALLOWED_DECISION_STATUSES:
        issues.append("unsupported_decision_status")
    if str(record.get("scope", "")).strip() != "local_private_course_extraction":
        issues.append("scope_must_be_local_private_course_extraction")

    allowed_job_types = [str(item).strip() for item in record.get("allowed_job_types", []) if str(item).strip()]
    if not allowed_job_types:
        issues.append("allowed_job_types_required")
    unsupported = [item for item in allowed_job_types if item not in ALLOWED_JOB_TYPES]
    if unsupported:
        issues.append("unsupported_job_type")

    if str(record.get("storage_policy", "")).strip() != "local_private_only":
        issues.append("storage_policy_must_be_local_private_only")
    if bool(record.get("cloud_processing_allowed", False)):
        issues.append("cloud_processing_must_remain_false_for_this_gate")
    if bool(record.get("raw_text_public_release_allowed", False)):
        issues.append("raw_text_public_release_must_remain_false")
    if not bool(record.get("human_review_before_tutor_index", False)):
        issues.append("human_review_before_tutor_index_required")
    if not str(record.get("retention_decision", "")).strip():
        issues.append("retention_decision_required")
    if not str(record.get("decision_reference", "")).strip():
        issues.append("decision_reference_required")

    reviewer_roles = [str(item).strip() for item in record.get("reviewer_roles", []) if str(item).strip()]
    missing_roles = [role for role in REQUIRED_REVIEWER_ROLES if role not in reviewer_roles]
    if missing_roles:
        issues.append("missing_required_reviewer_roles")
    access_roles = [str(item).strip() for item in record.get("access_roles", []) if str(item).strip()]
    if not access_roles:
        issues.append("access_roles_required")
    if status == "approved_for_local_extraction" and "approved_reviewer" not in access_roles:
        warnings.append("approved_reviewer_access_role_recommended")

    decision_reference_hash = sha256_text(str(record.get("decision_reference", ""))) if record.get("decision_reference") else ""
    safe_summary = {
        "schema_version": EXTRACTION_DECISION_SCHEMA_VERSION,
        "artifact_type": "course_extraction_decision_validation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ok_authorizes_local_extraction" if not issues and status == "approved_for_local_extraction" else "needs_review" if not issues else "blocked",
        "decision_status": status or "missing",
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
        "approved_for_local_extraction": not issues and status == "approved_for_local_extraction",
        "rights_decision_reference_hash": decision_reference_hash,
        "allowed_job_types": allowed_job_types,
        "reviewer_roles": reviewer_roles,
        "access_roles": access_roles,
        "authorization_scope": "local private OCR/transcription only; no exam clearance and no public raw text release",
        "raw_decision_reference_stored": False,
    }
    scan = scan_text(json.dumps(safe_summary, ensure_ascii=False), "extraction-decision-validation")
    safe_summary["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        safe_summary["status"] = "blocked"
        safe_summary["public_safety_findings"] = scan["findings"]
    return safe_summary


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["public_safety_findings"] = scan["findings"]
