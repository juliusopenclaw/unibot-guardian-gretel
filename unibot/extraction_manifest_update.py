from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction_batches import build_all_jobs
from .extraction_decision_context import (
    decision_context_authorizes,
    public_decision_context_view,
    resolve_extraction_decision_context,
)
from .extraction_operator import validate_extraction_receipt
from .extraction_progress import build_extraction_progress_report
from .materials import normalize_material_record, sha256_text, validate_material_record
from .public_safety import scan_text
from .source_cards import get_source_card


EXTRACTION_MANIFEST_UPDATE_SCHEMA_VERSION = "unibot-extraction-manifest-update-plan-v1"
EXTRACTION_MANIFEST_UPDATE_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-extraction-manifest-update-release-review-board-claim-alignment-v1"
)


def build_extraction_manifest_update_plan(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | None = None,
    receipts: list[dict[str, Any]] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    decision_validation = resolve_extraction_decision_context(
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
    )
    authorized = decision_context_authorizes(decision_validation)
    rights_hash = str(decision_validation.get("rights_decision_reference_hash", ""))
    progress = build_extraction_progress_report(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=receipts or [],
        public_safe=public_safe,
    )
    jobs = build_all_jobs(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        authorized=authorized,
        rights_hash=rights_hash if authorized else "",
    )
    job_by_id = {str(job.get("job_id", "")): job for job in jobs if job.get("job_id")}
    receipt_records = [item for item in (receipts or []) if isinstance(item, dict)]
    validations = [
        validate_extraction_receipt(
            receipt,
            decision_record=decision_record or {},
            decision_reference_hash=rights_hash,
        )
        for receipt in receipt_records
    ]
    invalid = [item for item in validations if item.get("status") == "blocked"]
    eligible = [item for item in validations if item.get("eligible_for_private_tutor_index")]
    candidates = [manifest_update_candidate(item, job_by_id.get(str(item.get("job_id", "")))) for item in eligible]
    blocked_candidates = [item for item in candidates if item.get("validation_status") == "blocked"]
    local_cycle_workspace_card = safe_local_cycle_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {},
        candidate_hash=candidate_hash(candidates[0]) if candidates else "",
        candidate_set_hash=candidate_set_hash(candidates),
    )
    plan = {
        "schema_version": EXTRACTION_MANIFEST_UPDATE_SCHEMA_VERSION,
        "artifact_type": "course_extraction_manifest_update_plan",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": manifest_update_status(authorized, invalid, eligible, blocked_candidates),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "This is a private manifest metadata update plan. It does not write manifest files, "
            "does not expose local paths, and does not store raw OCR text or transcripts."
        ),
        "decision_validation": public_decision_context_view(decision_validation),
        "progress_status": progress.get("status"),
        "queue_summary": progress.get("queue_summary", {}),
        "receipt_summary": progress.get("receipt_summary", {}),
        "candidate_summary": {
            "candidate_count": len(candidates),
            "blocked_candidate_count": len(blocked_candidates),
            "source_job_metadata_missing_count": len(
                [item for item in candidates if item.get("source_job_metadata_status") == "missing"]
            ),
            "ready_to_apply_private_count": len([item for item in candidates if item.get("validation_status") == "ok"]),
        },
        "manifest_update_candidates": candidates[:80],
        "candidate_output_truncated": len(candidates) > 80,
        "local_cycle_operator_workspace_card": local_cycle_workspace_card,
        "manifest_update_contract": {
            "required_before_apply": [
                "valid rights/privacy decision",
                "validated extraction receipt",
                "human_review_status reviewed_for_private_tutor",
                "private raw text artifact retained outside public reports",
                "source-card metadata assigned or confirmed",
            ],
            "public_fields_only": [
                "material_id",
                "job_id",
                "job_type",
                "sha256_after_review",
                "extracted_text_char_count",
                "skill_tags",
                "source_card_ids",
                "review_status_after_review",
            ],
            "never_apply_here": [
                "raw OCR text",
                "raw transcript",
                "local source path",
                "exam deployment switch",
                "automatic grade or score",
            ],
        },
        "next_actions": manifest_update_next_actions(authorized, invalid, eligible, blocked_candidates),
    }
    attach_public_scan(plan, public_safe=public_safe, source_name="extraction-manifest-update-plan")
    return plan


def build_extraction_manifest_update_release_claim_alignment(plan: dict[str, Any] | None = None) -> dict[str, Any]:
    if plan is None:
        decision_record = synthetic_manifest_update_decision_record()
        jobs = build_all_jobs(
            DEFAULT_COURSE_ID,
            base_path=None,
            max_files=260,
            review_policy="staged",
            authorized=True,
            rights_hash=sha256_text(str(decision_record["decision_reference"])),
        )
        first_job = jobs[0] if jobs else {"job_id": "synthetic-manifest-job-1", "material_id": "synthetic-material-1", "job_type": "ocr"}
        receipt = {
            "job_id": first_job["job_id"],
            "material_id": first_job["material_id"],
            "job_type": first_job["job_type"],
            "extraction_status": "extracted_private",
            "raw_text_sha256": "e" * 64,
            "extracted_text_char_count": 1440,
            "private_artifact_reference": "synthetic local private manifest artifact reference",
            "human_review_status": "reviewed_for_private_tutor",
            "decision_reference_hash": sha256_text(str(decision_record["decision_reference"])),
        }
        plan = build_extraction_manifest_update_plan(
            decision_record=decision_record,
            receipts=[receipt],
            python_exam_local_cycle_operator_workspace_card=synthetic_manifest_update_workspace_card(),
        )

    sections = [
        {
            "section_id": "private_metadata_plan_trace",
            "summary_claim": "manifest update plans prepare private metadata candidates only and do not write manifest files by themselves",
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024", "dfg-gwp"],
            "readiness_check_ids": [
                "extraction_manifest_update",
                "python_exam_local_cycle_operator_workspace_card",
                "extraction_progress",
                "extraction_receipt_journal",
                "data_protection_screening",
            ],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "candidate_public_boundary_trace",
            "summary_claim": "candidate records expose hashes and metadata only while keeping raw text, local paths, and public release blocked",
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024"],
            "readiness_check_ids": ["extraction_manifest_update", "course_material_policy", "public_safety"],
            "human_gates": ["public_safety_required", "human_submission_review_required"],
        },
        {
            "section_id": "apply_gate_trace",
            "summary_claim": "planning does not apply updates; a separate private manifest apply step and rebuild remain required",
            "source_card_ids": ["dfg-gwp"],
            "readiness_check_ids": ["extraction_manifest_update", "review_board_packet", "release_runbook"],
            "human_gates": ["human_submission_review_required", "datenschutz_review_required_before_real_pilot"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "manifest update plans do not clear public raw text release, cloud processing, grading, proctoring, KI-detection evidence, or exam deployment",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": ["extraction_manifest_update", "external_decision_state", "exam_boundary"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    candidate_summary = plan.get("candidate_summary", {})
    contract = plan.get("manifest_update_contract", {})
    candidates = list(plan.get("manifest_update_candidates", []))
    workspace_card = (
        plan.get("local_cycle_operator_workspace_card", {})
        if isinstance(plan.get("local_cycle_operator_workspace_card"), dict)
        else {}
    )
    execution_boundary = str(plan.get("execution_boundary", ""))
    first_candidate_hash = candidate_hash(candidates[0]) if candidates else ""
    all_candidate_hash = candidate_set_hash(candidates)
    workspace_card_readiness_gate_linked = any(
        "python_exam_local_cycle_operator_workspace_card" in section["readiness_check_ids"] for section in sections
    )
    blocked_claims = [
        "manifest file write by planning",
        "raw OCR text storage",
        "raw transcript storage",
        "local source path exposure",
        "public raw course text release",
        "public release by manifest update plan",
        "cloud processing",
        "exam deployment",
        "official grading",
        "proctoring",
        "KI-detection evidence",
    ]
    contracts = {
        "plan_public_safe": plan.get("public_safety_status") == "pass",
        "exam_deployment_not_cleared": plan.get("exam_deployment_status") == "not_cleared",
        "plan_ready_for_private_manifest_update": plan.get("status") == "ready_for_private_manifest_update",
        "execution_boundary_blocks_file_write_raw_and_paths": "does not write manifest files" in execution_boundary
        and "does not expose local paths" in execution_boundary
        and "does not store raw OCR text or transcripts" in execution_boundary,
        "candidate_summary_ready_private_only": candidate_summary.get("candidate_count", 0) >= 1
        and candidate_summary.get("ready_to_apply_private_count", 0) >= 1
        and candidate_summary.get("blocked_candidate_count", 0) == 0,
        "candidates_private_metadata_only": bool(candidates)
        and all(
            candidate.get("validation_status") == "ok"
            and candidate.get("tutor_usable_after_apply") is True
            and candidate.get("public_release_allowed_after_apply") is False
            and candidate.get("raw_text_stored") is False
            and candidate.get("local_path_stored") is False
            and candidate.get("publish_policy_after_review") == "private_only"
            and candidate.get("permission_status_after_review") == "private_course_use_only"
            and bool(candidate.get("sha256_after_review"))
            for candidate in candidates
        ),
        "contract_requires_reviewed_receipt_and_private_raw_artifact": {
            "valid rights/privacy decision",
            "validated extraction receipt",
            "human_review_status reviewed_for_private_tutor",
            "private raw text artifact retained outside public reports",
            "source-card metadata assigned or confirmed",
        }.issubset(set(contract.get("required_before_apply", []))),
        "contract_public_fields_exclude_raw_and_paths": "raw OCR text" in contract.get("never_apply_here", [])
        and "raw transcript" in contract.get("never_apply_here", [])
        and "local source path" in contract.get("never_apply_here", [])
        and "exam deployment switch" in contract.get("never_apply_here", [])
        and "automatic grade or score" in contract.get("never_apply_here", []),
        "next_actions_keep_private_apply_separate": any(
            "Apply reviewed metadata privately" in str(action) for action in plan.get("next_actions", [])
        ),
        "workspace_card_candidate_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and workspace_card.get("checkpoint_hash") == first_candidate_hash
        and workspace_card.get("task_hash") == all_candidate_hash
        and bool(workspace_card.get("help_ledger_preview_hash"))
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card.get("raw_workspace_card_returned") is False,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "candidate_summary": candidate_summary,
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "extraction-manifest-update-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": EXTRACTION_MANIFEST_UPDATE_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "plan_status": plan.get("status"),
        "plan_public_safety_status": plan.get("public_safety_status"),
        "exam_deployment_status": plan.get("exam_deployment_status"),
        "candidate_summary": candidate_summary,
        "manifest_update_candidate_count": len(candidates),
        "workspace_card_status": workspace_card.get("status"),
        "workspace_card_selected_skill_tag": workspace_card.get("selected_skill_tag"),
        "workspace_card_ready_for_operator_prefill": bool(workspace_card.get("ready_for_operator_prefill", False)),
        "workspace_card_help_ledger_status": workspace_card.get("help_ledger_preview_status"),
        "workspace_card_help_ledger_hash_present": bool(workspace_card.get("help_ledger_preview_hash")),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_candidate_gate_linked": contracts["workspace_card_candidate_gate_linked"],
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
            "Extraction manifest update plans are private metadata planning artifacts only; they can prepare reviewed "
            "hash-backed candidate rows, but they do not write manifest files, expose raw text or local paths, approve "
            "public release, approve cloud processing, grade, proctor, detect KI, or clear exam deployment."
        ),
    }


def synthetic_manifest_update_decision_record() -> dict[str, Any]:
    return {
        "decision_status": "approved_for_local_extraction",
        "scope": "local_private_course_extraction",
        "allowed_job_types": ["ocr", "transcription"],
        "storage_policy": "local_private_only",
        "cloud_processing_allowed": False,
        "raw_text_public_release_allowed": False,
        "human_review_before_tutor_index": True,
        "retention_decision": "delete private extraction artifacts after reviewed metadata is accepted",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic manifest update release alignment decision",
    }


def synthetic_manifest_update_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic manifest update workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "pandas",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic manifest update candidate prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "pandas",
            "next_safe_action": "review_manifest_update_candidate_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_manifest_update_candidates_before_private_apply",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__CANDIDATE_SET_HASH__",
            "checkpoint_hash": "__CANDIDATE_HASH__",
            "source_card_ids": ["dfg-gwp", "dsk-ai-privacy-2024"],
            "source_anchor_count": 2,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": "A2",
            "preview_hash": preview_hash,
        },
    }


def candidate_hash(candidate: dict[str, Any]) -> str:
    if not isinstance(candidate, dict):
        return ""
    return sha256_text(
        json.dumps(
            {
                "material_id": candidate.get("material_id", ""),
                "job_id": candidate.get("job_id", ""),
                "sha256_after_review": candidate.get("sha256_after_review", ""),
                "review_status_after_review": candidate.get("review_status_after_review", ""),
                "publish_policy_after_review": candidate.get("publish_policy_after_review", ""),
                "permission_status_after_review": candidate.get("permission_status_after_review", ""),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def candidate_set_hash(candidates: list[dict[str, Any]]) -> str:
    hashes = [candidate_hash(candidate) for candidate in candidates if isinstance(candidate, dict)]
    return sha256_text(json.dumps(hashes, sort_keys=True, ensure_ascii=False)) if hashes else ""


def safe_local_cycle_workspace_card(
    workspace_card: dict[str, Any],
    *,
    candidate_hash: str = "",
    candidate_set_hash: str = "",
) -> dict[str, Any]:
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
    checkpoint_hash = str(summary.get("checkpoint_hash", ""))
    task_hash = str(summary.get("task_hash", ""))
    if candidate_hash and checkpoint_hash == "__CANDIDATE_HASH__":
        checkpoint_hash = candidate_hash
    if candidate_set_hash and task_hash == "__CANDIDATE_SET_HASH__":
        task_hash = candidate_set_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", review.get("recommendation", "keep_blocked"))),
        "recommendation_reason": str(
            summary.get("recommendation_reason", review.get("recommendation_reason", "missing_manifest_update_candidate"))
        ),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "help_ledger_preview_status": str(summary.get("help_ledger_preview_status", ledger.get("status", "missing"))),
        "next_safe_action": str(summary.get("next_safe_action", review.get("next_safe_action", ""))),
        "next_safe_user_action": str(summary.get("next_safe_user_action", review.get("next_safe_user_action", ""))),
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", handoff.get("operator_run_endpoint", ""))),
        "operator_run_method": str(summary.get("operator_run_method", handoff.get("operator_run_method", "POST"))),
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


def manifest_update_candidate(validation: dict[str, Any], job: dict[str, Any] | None) -> dict[str, Any]:
    job_type = str(validation.get("job_type", ""))
    extraction_status_after_review = "captions_available" if job_type == "transcription" else "text_extracted"
    source_kind = str((job or {}).get("source_kind", "video_file" if job_type == "transcription" else "document"))
    title = str((job or {}).get("title", f"Reviewed private extraction for {validation.get('material_id', '')}"))
    record_preview = {
        "material_id": validation.get("material_id", ""),
        "title": title,
        "source_kind": source_kind,
        "permission_status": "private_course_use_only",
        "publish_policy": "private_only",
        "extraction_status": extraction_status_after_review,
        "review_status": "reviewed_for_private_tutor",
        "skill_tags": list((job or {}).get("skill_tags", []) or [])[:6],
        "source_card_ids": list((job or {}).get("source_card_ids", []) or [])[:6],
        "page_or_timestamp": "",
        "sha256": validation.get("raw_text_sha256", ""),
        "public_excerpt": "",
        "notes": "metadata_only_private_extraction_update",
    }
    material_record = normalize_material_record(record_preview)
    material_validation = validate_material_record(material_record)
    return {
        "material_id": validation.get("material_id", ""),
        "job_id": validation.get("job_id", ""),
        "job_type": job_type,
        "operation": "update_existing_private_material_metadata",
        "source_job_metadata_status": "matched" if job else "missing",
        "source_kind_after_review": source_kind,
        "extraction_status_after_review": extraction_status_after_review,
        "review_status_after_review": "reviewed_for_private_tutor",
        "permission_status_after_review": "private_course_use_only",
        "publish_policy_after_review": "private_only",
        "sha256_after_review": validation.get("raw_text_sha256", ""),
        "extracted_text_char_count": validation.get("extracted_text_char_count", 0),
        "skill_tags": record_preview["skill_tags"],
        "source_card_ids": record_preview["source_card_ids"],
        "validation_status": material_validation.get("status"),
        "validation_issues": material_validation.get("issues", []),
        "validation_warnings": material_validation.get("warnings", []),
        "tutor_usable_after_apply": material_validation.get("tutor_usable", False),
        "public_release_allowed_after_apply": False,
        "raw_text_stored": False,
        "local_path_stored": False,
    }


def manifest_update_status(
    authorized: bool,
    invalid_receipts: list[dict[str, Any]],
    eligible_receipts: list[dict[str, Any]],
    blocked_candidates: list[dict[str, Any]],
) -> str:
    if not authorized:
        return "blocked_until_valid_rights_privacy_decision"
    if invalid_receipts:
        return "blocked_invalid_receipts"
    if blocked_candidates:
        return "blocked_candidate_metadata"
    if eligible_receipts:
        return "ready_for_private_manifest_update"
    return "waiting_for_reviewed_receipts"


def manifest_update_next_actions(
    authorized: bool,
    invalid_receipts: list[dict[str, Any]],
    eligible_receipts: list[dict[str, Any]],
    blocked_candidates: list[dict[str, Any]],
) -> list[str]:
    if not authorized:
        return ["Validate the rights/privacy decision record before planning private manifest updates."]
    if invalid_receipts:
        return ["Fix invalid receipts before preparing manifest metadata updates."]
    if blocked_candidates:
        return ["Fix candidate metadata before applying private material manifest updates."]
    if eligible_receipts:
        return ["Apply reviewed metadata privately, rebuild ExamScopeMap, then rerun course tutor evaluation."]
    return ["Complete human review and mark accepted receipts reviewed_for_private_tutor."]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
