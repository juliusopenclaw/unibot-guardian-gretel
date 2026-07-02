from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction_manifest_apply import build_private_manifest_apply_dry_run
from .ledger import append_ledger_event
from .materials import sha256_text
from .public_safety import scan_text
from .study_session import validate_study_session_receipt
from .tutor_index import build_private_index_tutor_response_dry_run, build_private_tutor_index_dry_run


PRIVATE_TUTOR_USE_FLOW_SCHEMA_VERSION = "unibot-private-tutor-use-flow-v1"


def build_private_tutor_use_flow_dry_run(
    query: str,
    *,
    course_id: str = DEFAULT_COURSE_ID,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | Path | None = None,
    receipts: list[dict[str, Any]] | None = None,
    receipt_journal_path: str | Path | None = None,
    private_manifest_path: str | Path | None = None,
    manifest_apply_journal_path: str | Path | None = None,
    tutor_index_path: str | Path | None = None,
    tutor_index_journal_path: str | Path | None = None,
    ledger_path: str | Path | None = None,
    requested_help_level: str = "A2",
    mode: str = "exam_controlled_gateway",
    exam_status: str = "strict",
    operator_confirmed_manifest_apply: bool = False,
    operator_confirmed_tutor_index_build: bool = False,
    operator_confirmed_help_ledger_append: bool = False,
    study_receipt: dict[str, Any] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    manifest_apply = build_private_manifest_apply_dry_run(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=receipts,
        receipt_journal_path=receipt_journal_path,
        private_manifest_path=private_manifest_path,
        manifest_apply_journal_path=manifest_apply_journal_path,
        operator_confirmed_manifest_apply=operator_confirmed_manifest_apply,
        public_safe=public_safe,
    )
    tutor_index = build_private_tutor_index_dry_run(
        course_id,
        private_manifest_path=private_manifest_path,
        tutor_index_path=tutor_index_path,
        tutor_index_journal_path=tutor_index_journal_path,
        operator_confirmed_tutor_index_build=operator_confirmed_tutor_index_build,
        public_safe=public_safe,
    )
    tutor_response = build_private_index_tutor_response_dry_run(
        query,
        course_id=course_id,
        tutor_index_path=tutor_index_path,
        mode=mode,
        requested_help_level=requested_help_level,
        exam_status=exam_status,
        public_safe=public_safe,
    )
    ledger_append = maybe_append_help_ledger(
        tutor_response,
        operator_confirmed=operator_confirmed_help_ledger_append,
        ledger_path=ledger_path,
    )
    receipt_validation = validate_study_session_receipt(
        flow_study_receipt(tutor_response, study_receipt),
        public_safe=public_safe,
    )
    report = {
        "schema_version": PRIVATE_TUTOR_USE_FLOW_SCHEMA_VERSION,
        "artifact_type": "course_private_tutor_use_flow_dry_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": private_tutor_use_flow_status(
            manifest_apply=manifest_apply,
            tutor_index=tutor_index,
            tutor_response=tutor_response,
            ledger_append=ledger_append,
            receipt_validation=receipt_validation,
        ),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "End-to-end private tutor use flow. Standard is dry-run. It can apply reviewed private manifest "
            "metadata, build a hash-only tutor index, produce A0-A2 index-guided tutor help, append a Help-Ledger "
            "event only with operator confirmation, and validate a hash-only study receipt. It never returns raw "
            "course text, raw queries, local paths, complete code, inserted values, final interpretation, grading, "
            "proctoring, AI detection, or exam clearance."
        ),
        "flow_steps": [
            manifest_step_summary(manifest_apply),
            tutor_index_step_summary(tutor_index),
            tutor_response_step_summary(tutor_response),
            ledger_step_summary(ledger_append),
            study_receipt_step_summary(receipt_validation),
        ],
        "manifest_apply_summary": manifest_step_summary(manifest_apply),
        "tutor_index_summary": tutor_index_step_summary(tutor_index),
        "tutor_response_summary": tutor_response_step_summary(tutor_response),
        "ledger_append_summary": ledger_step_summary(ledger_append),
        "study_receipt_validation": receipt_validation,
        "operator_confirmed_manifest_apply": operator_confirmed_manifest_apply,
        "operator_confirmed_tutor_index_build": operator_confirmed_tutor_index_build,
        "operator_confirmed_help_ledger_append": operator_confirmed_help_ledger_append,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "local_paths_returned": False,
        "private_manifest_path_returned": False,
        "tutor_index_path_returned": False,
        "ledger_path_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "next_actions": private_tutor_use_flow_next_actions(
            manifest_apply=manifest_apply,
            tutor_index=tutor_index,
            tutor_response=tutor_response,
            ledger_append=ledger_append,
            receipt_validation=receipt_validation,
        ),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def maybe_append_help_ledger(
    tutor_response: dict[str, Any],
    *,
    operator_confirmed: bool,
    ledger_path: str | Path | None,
) -> dict[str, Any]:
    event = ledger_event_from_tutor_response(tutor_response)
    if tutor_response.get("status") != "allowed":
        return {
            "status": "not_applicable_tutor_response_not_allowed",
            "ledger_written": False,
            "path_returned": False,
            "event_hash": sha256_text(json.dumps(event, sort_keys=True, ensure_ascii=False)),
        }
    if not operator_confirmed:
        return {
            "status": "dry_run_not_written",
            "ledger_written": False,
            "path_returned": False,
            "event_hash": sha256_text(json.dumps(event, sort_keys=True, ensure_ascii=False)),
        }
    stored = append_ledger_event(event, path=ledger_path)
    return {
        "status": stored.get("status", "stored"),
        "ledger_written": stored.get("status") == "stored",
        "path_returned": False,
        "event_hash": sha256_text(json.dumps(stored.get("record", {}), sort_keys=True, ensure_ascii=False)),
        "record_schema_version": stored.get("record", {}).get("schema_version", ""),
    }


def ledger_event_from_tutor_response(tutor_response: dict[str, Any]) -> dict[str, Any]:
    selected = tutor_response.get("selected_skill", {}) if isinstance(tutor_response.get("selected_skill"), dict) else {}
    ledger = tutor_response.get("help_ledger_preview", {}) if isinstance(tutor_response.get("help_ledger_preview"), dict) else {}
    classification = [] if tutor_response.get("status") == "allowed" else [str(tutor_response.get("status", "blocked"))]
    return {
        "mode": tutor_response.get("mode", "exam_controlled_gateway"),
        "tool": "unibot_private_index_tutor",
        "task_id": f"idx-flow-{str(tutor_response.get('query_hash', ''))[:12]}",
        "skill_tags": [selected.get("skill_tag", "general_python")],
        "raw_output_hash": ledger.get("raw_response_hash", sha256_text(str(tutor_response.get("answer_markdown", "")))),
        "classification": classification,
        "allowed_hint": str(tutor_response.get("answer_markdown", ""))[:500],
        "help_level": tutor_response.get("effective_help_level", "A2"),
        "privacy_flags": [],
        "source_card_ids": list(tutor_response.get("source_card_ids", []) or [])[:8],
        "student_reflection": "",
    }


def flow_study_receipt(tutor_response: dict[str, Any], study_receipt: dict[str, Any] | None) -> dict[str, Any]:
    selected = tutor_response.get("selected_skill", {}) if isinstance(tutor_response.get("selected_skill"), dict) else {}
    anchors = tutor_response.get("source_anchors", []) if isinstance(tutor_response.get("source_anchors"), list) else []
    first_anchor = anchors[0] if anchors and isinstance(anchors[0], dict) else {}
    base = {
        "task_id": f"idx-flow-{str(tutor_response.get('query_hash', ''))[:12]}",
        "skill_tag": selected.get("skill_tag", "general_python"),
        "help_level": tutor_response.get("effective_help_level", "A2"),
        "source_anchor_id": first_anchor.get("anchor_id", ""),
        "retrieval_response_present": tutor_response.get("status") == "allowed",
    }
    if study_receipt:
        base.update({key: value for key, value in study_receipt.items() if key not in {"solution", "final_answer", "raw_private_text"}})
    return base


def private_tutor_use_flow_status(
    *,
    manifest_apply: dict[str, Any],
    tutor_index: dict[str, Any],
    tutor_response: dict[str, Any],
    ledger_append: dict[str, Any],
    receipt_validation: dict[str, Any],
) -> str:
    if manifest_apply.get("status") == "blocked_public_safety" or tutor_index.get("status") == "blocked_public_safety":
        return "blocked_public_safety"
    if manifest_apply.get("status") == "blocked_until_valid_rights_privacy_decision":
        return "waiting_for_manifest_apply_rights_decision"
    if manifest_apply.get("status") in {"blocked_candidate_metadata", "waiting_for_reviewed_receipts"}:
        return str(manifest_apply.get("status"))
    if tutor_index.get("status") in {"waiting_for_private_manifest_apply", "waiting_for_tutor_usable_manifest_records"}:
        return str(tutor_index.get("status"))
    if tutor_response.get("status") != "allowed":
        return f"tutor_response_{tutor_response.get('status', 'blocked')}"
    if receipt_validation.get("status") == "repeat_task_required":
        return "repeat_task_required"
    if receipt_validation.get("status") == "blocked":
        return "study_receipt_needs_evidence"
    if ledger_append.get("ledger_written"):
        return "private_tutor_use_flow_ready_with_ledger"
    return "private_tutor_use_flow_dry_run_ready"


def manifest_step_summary(manifest_apply: dict[str, Any]) -> dict[str, Any]:
    candidates = manifest_apply.get("candidate_summary", {}) if isinstance(manifest_apply.get("candidate_summary"), dict) else {}
    return {
        "step_id": "private_manifest_apply",
        "status": manifest_apply.get("status", "unknown"),
        "candidate_count": candidates.get("candidate_count", 0),
        "records_to_apply_count": candidates.get("records_to_apply_count", 0),
        "manifest_written": bool(manifest_apply.get("manifest_written", False)),
        "path_returned": False,
    }


def tutor_index_step_summary(tutor_index: dict[str, Any]) -> dict[str, Any]:
    preview = tutor_index.get("index_preview", {}) if isinstance(tutor_index.get("index_preview"), dict) else {}
    return {
        "step_id": "private_tutor_index",
        "status": tutor_index.get("status", "unknown"),
        "anchor_count": preview.get("anchor_count", 0),
        "indexed_skill_count": preview.get("indexed_skill_count", 0),
        "tutor_index_built": bool(tutor_index.get("tutor_index_built", False)),
        "path_returned": False,
    }


def tutor_response_step_summary(tutor_response: dict[str, Any]) -> dict[str, Any]:
    selected = tutor_response.get("selected_skill", {}) if isinstance(tutor_response.get("selected_skill"), dict) else {}
    return {
        "step_id": "private_index_tutor_response",
        "status": tutor_response.get("status", "unknown"),
        "skill_tag": selected.get("skill_tag", ""),
        "source_anchor_count": len(tutor_response.get("source_anchors", []) or []),
        "effective_help_level": tutor_response.get("effective_help_level", "A2"),
        "raw_query_returned": False,
    }


def ledger_step_summary(ledger_append: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_id": "help_ledger_append",
        "status": ledger_append.get("status", "unknown"),
        "ledger_written": bool(ledger_append.get("ledger_written", False)),
        "event_hash": ledger_append.get("event_hash", ""),
        "path_returned": False,
    }


def study_receipt_step_summary(receipt_validation: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_id": "study_receipt_validation",
        "status": receipt_validation.get("status", "unknown"),
        "skill_tag": receipt_validation.get("skill_tag", ""),
        "help_level": receipt_validation.get("help_level", "A0"),
        "repeat_task_required": bool(receipt_validation.get("repeat_task_required", False)),
        "raw_text_stored": False,
    }


def private_tutor_use_flow_next_actions(
    *,
    manifest_apply: dict[str, Any],
    tutor_index: dict[str, Any],
    tutor_response: dict[str, Any],
    ledger_append: dict[str, Any],
    receipt_validation: dict[str, Any],
) -> list[str]:
    if manifest_apply.get("status") == "blocked_until_valid_rights_privacy_decision":
        return ["Record or reference a valid local rights/privacy decision before applying private manifest metadata."]
    if tutor_index.get("status") in {"waiting_for_private_manifest_apply", "waiting_for_tutor_usable_manifest_records"}:
        return ["Apply reviewed private manifest metadata, then build the hash-only tutor index."]
    if tutor_response.get("status") != "allowed":
        return ["Use an A0-A2 request with an indexed source anchor; do not ask for code, inserted values, or final interpretation."]
    if receipt_validation.get("status") == "blocked":
        return ["Provide hash-only study evidence: prediction, notebook action, source anchor, and reflection."]
    if not ledger_append.get("ledger_written"):
        return ["Review the dry-run, then set operator_confirmed_help_ledger_append only if this help should be stored locally."]
    return [
        "Use the validated receipt as a human-reviewable learning evidence checkpoint.",
        "Keep expanding course coverage through manifest apply and tutor-index rebuilds.",
        "Reminder: real exam authority clearance remains a real-world follow-up; UniBot stays not_cleared.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "private-tutor-use-flow")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
