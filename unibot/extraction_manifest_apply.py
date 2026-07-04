from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import (
    DEFAULT_COURSE_ID,
    build_course_exam_scope,
    safe_course_id,
    scan_course_intake,
)
from .extraction_decision_context import (
    decision_context_authorizes,
    public_decision_context_view,
    resolve_extraction_decision_context,
)
from .extraction_manifest_update import (
    build_extraction_manifest_update_plan,
    synthetic_manifest_update_decision_record,
)
from .extraction_receipt_journal import extraction_receipts_for_progress
from .materials import build_material_manifest, normalize_material_record, sha256_text
from .public_safety import scan_text
from .source_cards import get_source_card
from .tutor_coverage import build_course_tutor_coverage_plan, scope_summary


EXTRACTION_MANIFEST_APPLY_SCHEMA_VERSION = "unibot-private-manifest-apply-v1"
EXTRACTION_MANIFEST_APPLY_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-extraction-manifest-apply-release-review-board-claim-alignment-v1"
)
DEFAULT_PRIVATE_MANIFEST_PATH = Path.home() / ".unibot_guardian" / "private_course_material_manifest.json"
DEFAULT_MANIFEST_APPLY_JOURNAL_PATH = Path.home() / ".unibot_guardian" / "private_manifest_apply_journal.jsonl"


def resolve_private_manifest_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get("UNIBOT_PRIVATE_MATERIAL_MANIFEST_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_PRIVATE_MANIFEST_PATH


def resolve_manifest_apply_journal_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get("UNIBOT_PRIVATE_MANIFEST_APPLY_JOURNAL_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_MANIFEST_APPLY_JOURNAL_PATH


def build_private_manifest_apply_dry_run(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | Path | None = None,
    receipts: list[dict[str, Any]] | None = None,
    receipt_journal_path: str | Path | None = None,
    private_manifest_path: str | Path | None = None,
    manifest_apply_journal_path: str | Path | None = None,
    operator_confirmed_manifest_apply: bool = False,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    workspace_card_source = (
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {}
    )
    decision_context = resolve_extraction_decision_context(
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
    )
    authorized = decision_context_authorizes(decision_context)
    all_receipts = [item for item in (receipts or []) if isinstance(item, dict)]
    if receipt_journal_path:
        all_receipts.extend(extraction_receipts_for_progress(path=receipt_journal_path))
    latest_receipts = latest_receipts_by_job(all_receipts)
    manifest_plan = build_extraction_manifest_update_plan(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=latest_receipts,
        public_safe=public_safe,
    )
    candidates = ready_manifest_candidates(manifest_plan)
    private_manifest = resolve_private_manifest_path(private_manifest_path)
    apply_journal = resolve_manifest_apply_journal_path(manifest_apply_journal_path)
    existing_payload = read_private_manifest(private_manifest)
    existing_records = existing_payload.get("records", [])
    intake = scan_course_intake(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    intake_records = [item for item in intake.get("records", []) if isinstance(item, dict)]
    candidate_records = [candidate_to_material_record(candidate) for candidate in candidates]
    current_records = merge_material_records([*intake_records, *existing_records])
    projected_records = merge_material_records([*current_records, *candidate_records])
    current_scope = build_course_exam_scope(
        course_id,
        records=current_records,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    projected_scope = build_course_exam_scope(
        course_id,
        records=projected_records,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    coverage = build_course_tutor_coverage_plan(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=latest_receipts,
        public_safe=public_safe,
    )
    delta = build_manifest_delta(current_records, candidate_records)
    invalid_candidates = [
        candidate for candidate in manifest_plan.get("manifest_update_candidates", [])
        if isinstance(candidate, dict) and candidate.get("validation_status") == "blocked"
    ]
    apply_result = {"status": "not_requested", "applied_count": 0, "manifest_written": False, "journal_written": False}
    can_apply = authorized and not invalid_candidates and bool(delta["records_to_apply"])
    if operator_confirmed_manifest_apply and can_apply:
        apply_result = write_private_manifest_apply(
            projected_records,
            delta=delta,
            private_manifest_path=private_manifest,
            journal_path=apply_journal,
            existing_payload=existing_payload,
            public_safe=public_safe,
        )
    local_cycle_workspace_card = safe_local_cycle_workspace_card(
        workspace_card_source,
        manifest_hash=str(apply_result.get("new_manifest_hash", "")),
        delta_hash=str(apply_result.get("delta_hash", delta["delta_hash"])),
    )

    report = {
        "schema_version": EXTRACTION_MANIFEST_APPLY_SCHEMA_VERSION,
        "artifact_type": "course_private_manifest_apply_dry_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": manifest_apply_status(
            authorized=authorized,
            invalid_candidate_count=len(invalid_candidates),
            candidate_count=len(candidates),
            delta_count=len(delta["records_to_apply"]),
            confirmed=operator_confirmed_manifest_apply,
            apply_result=apply_result,
        ),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Controlled private manifest apply harness. Dry-run is metadata-only. It writes a local private "
            "manifest only when operator_confirmed_manifest_apply is true, never writes raw extracted text, "
            "never exposes local paths, never starts tutor indexing, and never clears exam deployment."
        ),
        "decision_validation": public_decision_context_view(decision_context),
        "source_manifest_update_status": manifest_plan.get("status", "unknown"),
        "candidate_summary": {
            "candidate_count": len(candidates),
            "invalid_candidate_count": len(invalid_candidates),
            "records_to_apply_count": len(delta["records_to_apply"]),
            "unchanged_existing_count": len(delta["unchanged_existing"]),
            "blocked_candidate_count": len(invalid_candidates),
        },
        "private_manifest_summary": {
            "existing_status": existing_payload.get("status", "missing"),
            "existing_record_count": len(existing_records),
            "projected_record_count": len(projected_records),
            "existing_manifest_hash": existing_payload.get("manifest_hash", ""),
            "projected_manifest_hash": manifest_hash_for_records(projected_records),
            "private_manifest_path_returned": False,
        },
        "delta_preview": {
            "records_to_apply": delta["records_to_apply"][:30],
            "records_to_apply_truncated": len(delta["records_to_apply"]) > 30,
            "unchanged_existing_count": len(delta["unchanged_existing"]),
            "delta_hash": delta["delta_hash"],
        },
        "exam_scope_preview": {
            "current_scope_summary": scope_summary(current_scope),
            "projected_scope_summary": projected_scope_summary(current_scope, projected_scope, delta),
            "projected_scope_status": projected_scope.get("status", "unknown"),
        },
        "tutor_coverage_preview": {
            "status": coverage.get("status", "unknown"),
            "candidate_material_count": coverage.get("projected_scope_summary", {}).get("candidate_material_count", 0),
            "ready_skill_uplift": coverage.get("projected_scope_summary", {}).get("ready_skill_uplift", 0),
            "priority_skill_gaps": coverage.get("priority_skill_gaps", [])[:6],
        },
        "apply_result": public_apply_result(apply_result),
        "local_cycle_operator_workspace_card": local_cycle_workspace_card,
        "operator_confirmed_manifest_apply": operator_confirmed_manifest_apply,
        "manifest_written": bool(apply_result.get("manifest_written", False)),
        "manifest_apply_journal_written": bool(apply_result.get("journal_written", False)),
        "tutor_indexing_started": False,
        "raw_text_returned": False,
        "local_paths_returned": False,
        "private_manifest_path_returned": False,
        "next_actions": manifest_apply_next_actions(
            authorized=authorized,
            invalid_candidate_count=len(invalid_candidates),
            candidate_count=len(candidates),
            delta_count=len(delta["records_to_apply"]),
            confirmed=operator_confirmed_manifest_apply,
            apply_result=apply_result,
        ),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def build_private_manifest_apply_release_claim_alignment(
    dry_run_report: dict[str, Any] | None = None,
    confirmed_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if dry_run_report is None or confirmed_report is None:
        decision_record = synthetic_manifest_update_decision_record()
        receipt = synthetic_apply_receipt(decision_record)
        with tempfile.TemporaryDirectory(prefix="unibot_manifest_apply_alignment_") as temp_dir:
            private_manifest_path = Path(temp_dir) / "private_manifest.json"
            journal_path = Path(temp_dir) / "apply_journal.jsonl"
            if dry_run_report is None:
                dry_run_report = build_private_manifest_apply_dry_run(
                    decision_record=decision_record,
                    receipts=[receipt],
                    private_manifest_path=private_manifest_path,
                    manifest_apply_journal_path=journal_path,
                )
            if confirmed_report is None:
                confirmed_report = build_private_manifest_apply_dry_run(
                    decision_record=decision_record,
                    receipts=[receipt],
                    private_manifest_path=private_manifest_path,
                    manifest_apply_journal_path=journal_path,
                    operator_confirmed_manifest_apply=True,
                    python_exam_local_cycle_operator_workspace_card=synthetic_manifest_apply_workspace_card(),
                )

    sections = [
        {
            "section_id": "dry_run_trace",
            "summary_claim": "private manifest apply dry-runs preview metadata deltas without writing files, returning raw text, returning local paths, or starting tutor indexing",
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024", "dfg-gwp"],
            "readiness_check_ids": ["extraction_manifest_apply", "extraction_manifest_update", "extraction_progress"],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "confirmed_private_write_trace",
            "summary_claim": "confirmed apply writes only local-private metadata and hash-only journal records when the operator explicitly confirms",
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024", "dfg-gwp"],
            "readiness_check_ids": [
                "extraction_manifest_apply",
                "python_exam_local_cycle_operator_workspace_card",
                "extraction_manifest_update",
                "extraction_receipt_journal",
                "data_protection_screening",
            ],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "tutor_index_boundary_trace",
            "summary_claim": "manifest apply may improve projected coverage but still does not start tutor indexing or retrieval",
            "source_card_ids": ["dfg-gwp"],
            "readiness_check_ids": ["extraction_manifest_apply", "course_material_policy", "review_board_packet"],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "manifest apply does not clear public release, cloud processing, official grading, proctoring, KI-detection evidence, or exam deployment",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": ["extraction_manifest_apply", "external_decision_state", "exam_boundary"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    blocked_claims = [
        "raw extracted text returned",
        "local path returned",
        "private manifest path returned",
        "private artifact reference exposure",
        "tutor indexing started by apply",
        "public raw course text release",
        "cloud processing",
        "exam deployment",
        "official grading",
        "proctoring",
        "KI-detection evidence",
    ]
    dry_apply_result = dry_run_report.get("apply_result", {})
    confirmed_apply_result = confirmed_report.get("apply_result", {})
    workspace_card = (
        confirmed_report.get("local_cycle_operator_workspace_card", {})
        if isinstance(confirmed_report.get("local_cycle_operator_workspace_card"), dict)
        else {}
    )
    workspace_card_readiness_gate_linked = any(
        "python_exam_local_cycle_operator_workspace_card" in section["readiness_check_ids"] for section in sections
    )
    contracts = {
        "dry_run_public_safe": dry_run_report.get("public_safety_status") == "pass",
        "confirmed_public_safe": confirmed_report.get("public_safety_status") == "pass",
        "dry_run_does_not_write": dry_run_report.get("status") == "manifest_apply_dry_run_ready"
        and dry_run_report.get("operator_confirmed_manifest_apply") is False
        and dry_run_report.get("manifest_written") is False
        and dry_run_report.get("manifest_apply_journal_written") is False
        and dry_apply_result.get("manifest_written") is False
        and dry_apply_result.get("journal_written") is False,
        "confirmed_write_requires_operator_confirmation": confirmed_report.get("operator_confirmed_manifest_apply") is True
        and confirmed_report.get("status") == "private_manifest_applied"
        and confirmed_report.get("manifest_written") is True
        and confirmed_report.get("manifest_apply_journal_written") is True
        and confirmed_apply_result.get("manifest_written") is True
        and confirmed_apply_result.get("journal_written") is True,
        "public_outputs_hide_paths_and_raw_text": all(
            report.get("raw_text_returned") is False
            and report.get("local_paths_returned") is False
            and report.get("private_manifest_path_returned") is False
            and report.get("apply_result", {}).get("private_manifest_path_returned") is False
            and report.get("apply_result", {}).get("journal_path_returned") is False
            for report in [dry_run_report, confirmed_report]
        ),
        "tutor_indexing_never_started": dry_run_report.get("tutor_indexing_started") is False
        and confirmed_report.get("tutor_indexing_started") is False,
        "exam_deployment_not_cleared": dry_run_report.get("exam_deployment_status") == "not_cleared"
        and confirmed_report.get("exam_deployment_status") == "not_cleared",
        "candidate_delta_and_hashes_linked": dry_run_report.get("candidate_summary", {}).get("records_to_apply_count", 0) >= 1
        and bool(dry_run_report.get("delta_preview", {}).get("delta_hash"))
        and bool(confirmed_apply_result.get("new_manifest_hash"))
        and bool(confirmed_apply_result.get("delta_hash")),
        "workspace_card_manifest_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and workspace_card.get("checkpoint_hash") == confirmed_apply_result.get("new_manifest_hash")
        and workspace_card.get("task_hash") == confirmed_apply_result.get("delta_hash")
        and bool(workspace_card.get("help_ledger_preview_hash"))
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card.get("raw_workspace_card_returned") is False,
        "projected_scope_preview_metadata_only": "projected_scope_summary" in dry_run_report.get("exam_scope_preview", {})
        and "priority_skill_gaps" in dry_run_report.get("tutor_coverage_preview", {}),
        "execution_boundary_blocks_raw_paths_indexing_exam": "never writes raw extracted text"
        in dry_run_report.get("execution_boundary", "")
        and "never exposes local paths" in dry_run_report.get("execution_boundary", "")
        and "never starts tutor indexing" in dry_run_report.get("execution_boundary", "")
        and "never clears exam deployment" in dry_run_report.get("execution_boundary", ""),
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "dry_run_status": dry_run_report.get("status"),
        "confirmed_status": confirmed_report.get("status"),
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "extraction-manifest-apply-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": EXTRACTION_MANIFEST_APPLY_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "dry_run_status": dry_run_report.get("status"),
        "confirmed_status": confirmed_report.get("status"),
        "dry_run_public_safety_status": dry_run_report.get("public_safety_status"),
        "confirmed_public_safety_status": confirmed_report.get("public_safety_status"),
        "dry_run_records_to_apply_count": dry_run_report.get("candidate_summary", {}).get("records_to_apply_count", 0),
        "confirmed_applied_count": confirmed_apply_result.get("applied_count", 0),
        "workspace_card_status": workspace_card.get("status"),
        "workspace_card_selected_skill_tag": workspace_card.get("selected_skill_tag"),
        "workspace_card_ready_for_operator_prefill": bool(workspace_card.get("ready_for_operator_prefill", False)),
        "workspace_card_help_ledger_status": workspace_card.get("help_ledger_preview_status"),
        "workspace_card_help_ledger_hash_present": bool(workspace_card.get("help_ledger_preview_hash")),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_manifest_gate_linked": contracts["workspace_card_manifest_gate_linked"],
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
            "Private manifest apply is a controlled local metadata harness: dry-runs do not write, confirmed applies "
            "require operator confirmation, public responses hide paths and raw text, tutor indexing remains off, and "
            "exam deployment, grading, proctoring, KI detection, cloud processing, and public release remain blocked."
        ),
    }


def synthetic_apply_receipt(decision_record: dict[str, Any]) -> dict[str, Any]:
    jobs = build_extraction_manifest_update_plan(decision_record=decision_record).get("manifest_update_candidates", [])
    job_id = "synthetic-apply-job-1"
    material_id = "synthetic-apply-material-1"
    job_type = "ocr"
    if jobs:
        job_id = str(jobs[0].get("job_id", job_id))
        material_id = str(jobs[0].get("material_id", material_id))
        job_type = str(jobs[0].get("job_type", job_type))
    return {
        "job_id": job_id,
        "material_id": material_id,
        "job_type": job_type,
        "extraction_status": "extracted_private",
        "raw_text_sha256": "f" * 64,
        "extracted_text_char_count": 1500,
        "private_artifact_reference": "synthetic local private manifest apply artifact reference",
        "human_review_status": "reviewed_for_private_tutor",
        "decision_reference_hash": sha256_text(str(decision_record["decision_reference"])),
    }


def synthetic_manifest_apply_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic manifest apply workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "pandas",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic manifest apply metadata prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "pandas",
            "next_safe_action": "review_private_manifest_apply_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_manifest_apply_receipt_before_any_tutor_indexing",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__DELTA_HASH__",
            "checkpoint_hash": "__MANIFEST_HASH__",
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


def safe_local_cycle_workspace_card(
    workspace_card: dict[str, Any],
    *,
    manifest_hash: str = "",
    delta_hash: str = "",
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
    if manifest_hash and checkpoint_hash == "__MANIFEST_HASH__":
        checkpoint_hash = manifest_hash
    if delta_hash and task_hash == "__DELTA_HASH__":
        task_hash = delta_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", review.get("recommendation", "keep_blocked"))),
        "recommendation_reason": str(
            summary.get("recommendation_reason", review.get("recommendation_reason", "missing_manifest_apply_receipt"))
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


def read_private_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "missing",
            "record_count": 0,
            "records": [],
            "manifest_hash": "",
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "status": "blocked_unreadable_manifest",
            "record_count": 0,
            "records": [],
            "manifest_hash": "",
        }
    records = payload.get("records", []) if isinstance(payload, dict) else []
    safe_records = [public_manifest_record_view(record) for record in records if isinstance(record, dict)]
    return {
        "status": "ok",
        "record_count": len(safe_records),
        "records": safe_records,
        "manifest_hash": sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=False)),
    }


def write_private_manifest_apply(
    records: list[dict[str, Any]],
    *,
    delta: dict[str, Any],
    private_manifest_path: Path,
    journal_path: Path,
    existing_payload: dict[str, Any],
    public_safe: bool,
) -> dict[str, Any]:
    manifest = build_material_manifest(records)
    manifest["schema_version"] = EXTRACTION_MANIFEST_APPLY_SCHEMA_VERSION
    manifest["artifact_type"] = "course_private_material_manifest"
    manifest["exam_deployment_status"] = "not_cleared"
    manifest["storage_policy"] = (
        "local-private metadata manifest; no raw OCR text, raw transcripts, private artifact references, "
        "student data, or local source paths"
    )
    scan = scan_text(json.dumps(manifest, ensure_ascii=False), "private-material-manifest")
    if public_safe and scan["status"] != "pass":
        return {
            "status": "blocked_public_safety",
            "applied_count": 0,
            "manifest_written": False,
            "journal_written": False,
            "public_safety_findings": scan["findings"],
        }

    private_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    private_manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    manifest_hash = sha256_text(json.dumps(manifest, sort_keys=True, ensure_ascii=False))
    journal_record = {
        "schema_version": EXTRACTION_MANIFEST_APPLY_SCHEMA_VERSION,
        "artifact_type": "course_private_manifest_apply_journal_record",
        "stored_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "accepted",
        "event": {
            "event_type": "private_manifest_metadata_applied",
            "applied_count": len(delta["records_to_apply"]),
            "unchanged_existing_count": len(delta["unchanged_existing"]),
            "previous_manifest_hash": existing_payload.get("manifest_hash", ""),
            "new_manifest_hash": manifest_hash,
            "delta_hash": delta["delta_hash"],
            "exam_deployment_status": "not_cleared",
            "manifest_path_stored": False,
            "raw_text_stored": False,
            "local_path_stored": False,
            "tutor_indexing_started": False,
        },
        "storage_policy": "hash-only apply journal; no local paths, raw text, or private artifact references",
    }
    journal_record["event"]["validation_hash"] = sha256_text(
        json.dumps(journal_record["event"], sort_keys=True, ensure_ascii=False)
    )
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    with journal_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(journal_record, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "status": "private_manifest_applied",
        "applied_count": len(delta["records_to_apply"]),
        "manifest_written": True,
        "journal_written": True,
        "new_manifest_hash": manifest_hash,
        "delta_hash": delta["delta_hash"],
        "private_manifest_path_returned": False,
        "journal_path_returned": False,
    }


def ready_manifest_candidates(manifest_plan: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = [
        item for item in manifest_plan.get("manifest_update_candidates", [])
        if isinstance(item, dict) and item.get("validation_status") == "ok"
    ]
    return dedupe_candidates(candidates)


def dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate in candidates:
        key = (str(candidate.get("material_id", "")), str(candidate.get("job_id", "")))
        by_key[key] = candidate
    return list(by_key.values())


def candidate_to_material_record(candidate: dict[str, Any]) -> dict[str, Any]:
    material_id = str(candidate.get("material_id", ""))
    title = str(candidate.get("title_after_review", "") or f"Reviewed private extraction {material_id}")
    return public_manifest_record_view(
        {
            "material_id": material_id,
            "title": title,
            "source_kind": candidate.get("source_kind_after_review", "document"),
            "permission_status": candidate.get("permission_status_after_review", "private_course_use_only"),
            "publish_policy": candidate.get("publish_policy_after_review", "private_only"),
            "extraction_status": candidate.get("extraction_status_after_review", "text_extracted"),
            "review_status": candidate.get("review_status_after_review", "reviewed_for_private_tutor"),
            "skill_tags": list(candidate.get("skill_tags", []) or [])[:6],
            "source_card_ids": list(candidate.get("source_card_ids", []) or [])[:8],
            "page_or_timestamp": candidate.get("page_or_timestamp_after_review", ""),
            "sha256": candidate.get("sha256_after_review", ""),
            "public_excerpt": "",
            "notes": "metadata_only_private_manifest_apply",
            "source_job_id": candidate.get("job_id", ""),
            "raw_text_stored": False,
            "local_path_stored": False,
        }
    )


def public_manifest_record_view(record: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_material_record(record)
    return {
        "material_id": normalized.material_id,
        "title": normalized.title,
        "source_kind": normalized.source_kind,
        "permission_status": normalized.permission_status,
        "publish_policy": normalized.publish_policy,
        "extraction_status": normalized.extraction_status,
        "review_status": normalized.review_status,
        "skill_tags": list(normalized.skill_tags),
        "source_card_ids": list(normalized.source_card_ids),
        "page_or_timestamp": normalized.page_or_timestamp,
        "sha256": normalized.sha256,
        "public_excerpt": normalized.public_excerpt if normalized.public_excerpt else "",
        "notes": normalized.notes,
    }


def merge_material_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    anonymous: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        safe_record = public_manifest_record_view(record)
        material_id = str(safe_record.get("material_id", ""))
        if not material_id:
            anonymous.append(safe_record)
            continue
        by_id[material_id] = safe_record
    return [*by_id.values(), *anonymous]


def build_manifest_delta(current_records: list[dict[str, Any]], candidate_records: list[dict[str, Any]]) -> dict[str, Any]:
    current_by_id = {str(record.get("material_id", "")): record for record in current_records if record.get("material_id")}
    records_to_apply = []
    unchanged = []
    for candidate in candidate_records:
        material_id = str(candidate.get("material_id", ""))
        if not material_id:
            continue
        current = current_by_id.get(material_id)
        if current and comparable_record(current) == comparable_record(candidate):
            unchanged.append(delta_record_view(candidate, operation="unchanged_existing_private_metadata"))
        else:
            operation = "update_existing_private_material_metadata" if current else "add_private_material_metadata"
            records_to_apply.append(delta_record_view(candidate, operation=operation))
    delta_payload = {
        "records_to_apply": records_to_apply,
        "unchanged_existing": unchanged,
    }
    delta_payload["delta_hash"] = sha256_text(json.dumps(delta_payload, sort_keys=True, ensure_ascii=False))
    return delta_payload


def comparable_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "material_id": record.get("material_id", ""),
        "source_kind": record.get("source_kind", ""),
        "permission_status": record.get("permission_status", ""),
        "publish_policy": record.get("publish_policy", ""),
        "extraction_status": record.get("extraction_status", ""),
        "review_status": record.get("review_status", ""),
        "skill_tags": list(record.get("skill_tags", []) or []),
        "source_card_ids": list(record.get("source_card_ids", []) or []),
        "sha256": record.get("sha256", ""),
    }


def delta_record_view(record: dict[str, Any], *, operation: str) -> dict[str, Any]:
    return {
        "operation": operation,
        "material_id": record.get("material_id", ""),
        "title": record.get("title", ""),
        "source_kind": record.get("source_kind", ""),
        "extraction_status": record.get("extraction_status", ""),
        "review_status": record.get("review_status", ""),
        "sha256": record.get("sha256", ""),
        "skill_tags": list(record.get("skill_tags", []) or [])[:6],
        "source_card_ids": list(record.get("source_card_ids", []) or [])[:8],
        "raw_text_stored": False,
        "local_path_stored": False,
        "public_release_allowed": False,
    }


def latest_receipts_by_job(receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    anonymous: list[dict[str, Any]] = []
    for receipt in receipts:
        if not isinstance(receipt, dict):
            continue
        job_id = str(receipt.get("job_id", ""))
        if not job_id:
            anonymous.append(receipt)
            continue
        by_id[job_id] = receipt
    return [*by_id.values(), *anonymous]


def manifest_hash_for_records(records: list[dict[str, Any]]) -> str:
    return sha256_text(json.dumps(records, sort_keys=True, ensure_ascii=False)) if records else ""


def projected_scope_summary(
    current_scope: dict[str, Any],
    projected_scope: dict[str, Any],
    delta: dict[str, Any],
) -> dict[str, Any]:
    current = scope_summary(current_scope)
    projected = scope_summary(projected_scope)
    return {
        **projected,
        "ready_skill_uplift": max(0, int(projected["ready_skill_count"]) - int(current["ready_skill_count"])),
        "needs_review_reduction": max(
            0,
            int(current["needs_review_skill_count"]) - int(projected["needs_review_skill_count"]),
        ),
        "records_to_apply_count": len(delta["records_to_apply"]),
    }


def manifest_apply_status(
    *,
    authorized: bool,
    invalid_candidate_count: int,
    candidate_count: int,
    delta_count: int,
    confirmed: bool,
    apply_result: dict[str, Any],
) -> str:
    if not authorized:
        return "blocked_until_valid_rights_privacy_decision"
    if invalid_candidate_count:
        return "blocked_candidate_metadata"
    if not candidate_count:
        return "waiting_for_reviewed_receipts"
    if not delta_count:
        return "private_manifest_already_current"
    if confirmed:
        return str(apply_result.get("status", "blocked_apply_failed"))
    return "manifest_apply_dry_run_ready"


def manifest_apply_next_actions(
    *,
    authorized: bool,
    invalid_candidate_count: int,
    candidate_count: int,
    delta_count: int,
    confirmed: bool,
    apply_result: dict[str, Any],
) -> list[str]:
    if not authorized:
        return ["Record a valid local rights/privacy decision before private manifest apply."]
    if invalid_candidate_count:
        return ["Fix blocked candidate metadata before any private manifest apply."]
    if not candidate_count:
        return ["Complete human review until receipts are reviewed_for_private_tutor."]
    if not delta_count:
        return ["Private manifest is current; rebuild ExamScopeMap preview and inspect tutor gaps."]
    if confirmed and apply_result.get("status") == "private_manifest_applied":
        return ["Rebuild ExamScopeMap from the private manifest snapshot, then run tutor eval before any retrieval indexing."]
    return ["Review the dry-run delta, then rerun with operator_confirmed_manifest_apply true if the private manifest should be updated."]


def public_apply_result(apply_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": apply_result.get("status", "not_requested"),
        "applied_count": apply_result.get("applied_count", 0),
        "manifest_written": bool(apply_result.get("manifest_written", False)),
        "journal_written": bool(apply_result.get("journal_written", False)),
        "new_manifest_hash": apply_result.get("new_manifest_hash", ""),
        "delta_hash": apply_result.get("delta_hash", ""),
        "private_manifest_path_returned": False,
        "journal_path_returned": False,
    }


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "private-manifest-apply-dry-run")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
