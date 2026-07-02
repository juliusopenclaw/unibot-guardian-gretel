from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .clearance import validate_clearance_record
from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction_decision import validate_extraction_decision_record
from .materials import sha256_text
from .public_safety import scan_text


DECISION_STATE_SCHEMA_VERSION = "unibot-external-decision-state-v1"


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
