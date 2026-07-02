from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction_batches import build_extraction_batch_plan
from .extraction_decision_workspace import prepare_local_extraction_decision_workspace
from .extraction_manifest_update import build_extraction_manifest_update_plan
from .extraction_progress import build_extraction_progress_report
from .extraction_receipt_journal import (
    extraction_receipts_for_progress,
    resolve_extraction_receipt_journal_path,
    summarize_extraction_receipt_journal,
)
from .external_decision_journal import resolve_external_decision_journal_path
from .private_extraction_runner import run_private_extraction_batch
from .public_safety import scan_text
from .tutor_coverage import build_course_tutor_coverage_plan


OCR_FIRST_OPERATOR_SCHEMA_VERSION = "unibot-ocr-first-operator-v1"


def run_controlled_ocr_first_batch_1(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    workspace_dir: str | Path | None = None,
    decision_record_journal_path: str | Path | None = None,
    receipt_journal_path: str | Path | None = None,
    private_output_dir: str | Path | None = None,
    batch_size: int = 12,
    operator_confirmed_dry_run: bool = False,
    public_safe: bool = True,
) -> dict[str, Any]:
    decision_journal_path = resolve_external_decision_journal_path(decision_record_journal_path)
    receipt_path = resolve_extraction_receipt_journal_path(receipt_journal_path)
    workspace = prepare_local_extraction_decision_workspace(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        workspace_dir=workspace_dir,
        decision_record_journal_path=decision_journal_path,
        receipt_journal_path=receipt_path,
        private_output_dir=private_output_dir,
        job_types=["ocr"],
        batch_size=batch_size,
        public_safe=public_safe,
    )
    dry_run = workspace.get("dry_run_receipt", {})
    if dry_run.get("status") != "ocr_first_batch_1_start_ready":
        report = base_operator_report(
            course_id,
            workspace=workspace,
            status="blocked_until_workspace_dry_run_ready",
            operator_confirmed_dry_run=operator_confirmed_dry_run,
        )
        attach_public_scan(report, public_safe=public_safe)
        return report
    if not operator_confirmed_dry_run:
        report = base_operator_report(
            course_id,
            workspace=workspace,
            status="waiting_for_operator_confirmation_after_dry_run",
            operator_confirmed_dry_run=False,
        )
        attach_public_scan(report, public_safe=public_safe)
        return report

    batch_plan = build_extraction_batch_plan(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record_journal_path=str(decision_journal_path),
        receipts=extraction_receipts_for_progress(path=receipt_path),
        batch_size=batch_size,
        job_types=["ocr"],
        public_safe=public_safe,
    )
    batch = selected_ocr_batch_1(batch_plan)
    batch_job_ids = [str(item) for item in batch.get("job_ids", []) if str(item)]
    private_run = run_private_extraction_batch(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record_journal_path=str(decision_journal_path),
        receipt_journal_path=str(receipt_path),
        private_output_dir=private_output_dir,
        max_jobs=int(batch.get("job_count", 0) or batch_size),
        job_types=["ocr"],
        job_ids=batch_job_ids,
        human_review_status="pending_review",
        public_safe=public_safe,
    )
    receipts = extraction_receipts_for_progress(path=receipt_path)
    progress = build_extraction_progress_report(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record_journal_path=str(decision_journal_path),
        receipts=receipts,
        public_safe=public_safe,
    )
    manifest = build_extraction_manifest_update_plan(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record_journal_path=str(decision_journal_path),
        receipts=receipts,
        public_safe=public_safe,
    )
    coverage = build_course_tutor_coverage_plan(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record_journal_path=str(decision_journal_path),
        receipts=receipts,
        public_safe=public_safe,
    )
    receipt_summary = summarize_extraction_receipt_journal(path=receipt_path)
    report = {
        "schema_version": OCR_FIRST_OPERATOR_SCHEMA_VERSION,
        "artifact_type": "course_ocr_first_batch_1_operator_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": operator_run_status(private_run, progress, manifest, coverage),
        "exam_deployment_status": "not_cleared",
        "operator_boundary": (
            "Controlled OCR-first Batch 1 operator. It checks the local Decision-Record workspace dry-run, "
            "runs only when the local decision journal authorizes extraction and the operator confirms, then "
            "returns public-safe receipt and report summaries only."
        ),
        "workspace_dry_run_receipt": public_dry_run_view(dry_run),
        "operator_confirmed_dry_run": True,
        "selected_batch": {
            "batch_index": batch.get("batch_index", 0),
            "batch_id": batch.get("batch_id", ""),
            "job_count": batch.get("job_count", 0),
            "job_type_counts": batch.get("job_type_counts", {}),
            "job_id_count": len(batch_job_ids),
        },
        "private_run_summary": private_run_summary(private_run),
        "receipt_journal_summary": public_receipt_summary(receipt_summary),
        "post_run_reports": {
            "progress": progress_summary(progress),
            "manifest_update": manifest_summary(manifest),
            "tutor_coverage": coverage_summary(coverage),
        },
        "private_ocr_started": True,
        "real_ocr_started": True,
        "raw_decision_record_returned": False,
        "raw_text_returned": False,
        "local_paths_returned": False,
        "next_actions": operator_next_actions(private_run, progress, manifest, coverage),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def base_operator_report(
    course_id: str,
    *,
    workspace: dict[str, Any],
    status: str,
    operator_confirmed_dry_run: bool,
) -> dict[str, Any]:
    return {
        "schema_version": OCR_FIRST_OPERATOR_SCHEMA_VERSION,
        "artifact_type": "course_ocr_first_batch_1_operator_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": status,
        "exam_deployment_status": "not_cleared",
        "operator_boundary": (
            "No private OCR is run unless the current workspace dry-run receipt is start-ready "
            "and operator_confirmed_dry_run is true."
        ),
        "workspace_dry_run_receipt": public_dry_run_view(workspace.get("dry_run_receipt", {})),
        "operator_confirmed_dry_run": operator_confirmed_dry_run,
        "selected_batch": {
            "batch_index": (workspace.get("ocr_first_readiness", {}).get("next_batch", {}) or {}).get("batch_index", 0),
            "job_count": (workspace.get("ocr_first_readiness", {}).get("next_batch", {}) or {}).get("job_count", 0),
            "job_type_counts": (workspace.get("ocr_first_readiness", {}).get("next_batch", {}) or {}).get("job_type_counts", {}),
        },
        "private_run_summary": {
            "status": "not_started",
            "selected_job_count": 0,
            "stored_receipt_count": 0,
        },
        "post_run_reports": workspace.get("post_run_report_summary", {}),
        "private_ocr_started": False,
        "real_ocr_started": False,
        "raw_decision_record_returned": False,
        "raw_text_returned": False,
        "local_paths_returned": False,
        "next_actions": blocked_next_actions(status),
    }


def selected_ocr_batch_1(batch_plan: dict[str, Any]) -> dict[str, Any]:
    batches = [item for item in batch_plan.get("batches", []) if isinstance(item, dict)]
    if not batches:
        return {}
    for batch in batches:
        if int(batch.get("batch_index", 0) or 0) == 1:
            return batch
    return batches[0]


def public_dry_run_view(dry_run: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": dry_run.get("status", "missing"),
        "decision_valid": bool(dry_run.get("decision_valid", False)),
        "decision_record_source": dry_run.get("decision_record_source", "missing_decision_record"),
        "ocr_first_batch_1_start_ready": bool(dry_run.get("ocr_first_batch_1_start_ready", False)),
        "ocr_first_batch_1_job_count": int(dry_run.get("ocr_first_batch_1_job_count", 0) or 0),
        "ocr_first_batch_1_job_type_counts": dry_run.get("ocr_first_batch_1_job_type_counts", {}),
        "receipt_journal_reachable": bool(dry_run.get("receipt_journal_reachable", False)),
        "post_run_reports_reachable": bool(dry_run.get("post_run_reports_reachable", False)),
        "real_ocr_started": False,
        "raw_decision_record_returned": False,
        "raw_text_returned": False,
        "local_paths_returned": False,
    }


def private_run_summary(private_run: dict[str, Any]) -> dict[str, Any]:
    counts = private_run.get("counts", {})
    return {
        "status": private_run.get("status", "unknown"),
        "decision_record_source": private_run.get("decision_record_source", "missing_decision_record"),
        "selected_job_count": counts.get("selected_job_count", 0),
        "extracted_private_count": counts.get("extracted_private_count", 0),
        "failed_extraction_count": counts.get("failed_extraction_count", 0),
        "stored_receipt_count": counts.get("stored_receipt_count", 0),
        "job_id_filter_count": counts.get("job_id_filter_count", 0),
        "raw_text_returned": private_run.get("raw_text_returned", False),
        "local_paths_returned": private_run.get("local_paths_returned", False),
    }


def public_receipt_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": summary.get("status", "empty"),
        "record_count": summary.get("record_count", 0),
        "accepted_record_count": summary.get("accepted_record_count", 0),
        "ready_for_human_review_count": summary.get("ready_for_human_review_count", 0),
        "eligible_for_private_tutor_index_count": summary.get("eligible_for_private_tutor_index_count", 0),
        "progress_receipt_count": summary.get("progress_receipt_count", 0),
        "raw_text_returned": False,
        "local_paths_returned": False,
    }


def progress_summary(progress: dict[str, Any]) -> dict[str, Any]:
    receipt = progress.get("receipt_summary", {})
    return {
        "status": progress.get("status", "unknown"),
        "valid_receipt_count": receipt.get("valid_receipt_count", 0),
        "ready_for_human_review_count": receipt.get("ready_for_human_review_count", 0),
        "eligible_for_private_tutor_index_count": receipt.get("eligible_for_private_tutor_index_count", 0),
        "public_safety_status": progress.get("public_safety_status", "unknown"),
    }


def manifest_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    candidates = manifest.get("candidate_summary", {})
    return {
        "status": manifest.get("status", "unknown"),
        "candidate_count": candidates.get("candidate_count", 0),
        "ready_to_apply_private_count": candidates.get("ready_to_apply_private_count", 0),
        "public_safety_status": manifest.get("public_safety_status", "unknown"),
    }


def coverage_summary(coverage: dict[str, Any]) -> dict[str, Any]:
    projected = coverage.get("projected_scope_summary", {})
    return {
        "status": coverage.get("status", "unknown"),
        "candidate_material_count": projected.get("candidate_material_count", 0),
        "ready_skill_uplift": projected.get("ready_skill_uplift", 0),
        "public_safety_status": coverage.get("public_safety_status", "unknown"),
    }


def operator_run_status(
    private_run: dict[str, Any],
    progress: dict[str, Any],
    manifest: dict[str, Any],
    coverage: dict[str, Any],
) -> str:
    private_status = str(private_run.get("status", ""))
    if private_status.startswith("blocked"):
        return private_status
    if private_status == "partial_private_extraction_run":
        return "ocr_first_batch_1_partial_receipts_recorded"
    if progress.get("status") == "receipts_ready_for_human_review":
        return "ocr_first_batch_1_receipts_ready_for_human_review"
    if manifest.get("status") == "ready_for_private_manifest_update":
        return "ocr_first_batch_1_ready_for_private_manifest_update"
    if coverage.get("status") == "coverage_uplift_ready_after_private_manifest_update":
        return "ocr_first_batch_1_coverage_uplift_ready"
    return "ocr_first_batch_1_run_recorded"


def blocked_next_actions(status: str) -> list[str]:
    if status == "waiting_for_operator_confirmation_after_dry_run":
        return ["Review the dry-run receipt, then rerun with operator_confirmed_dry_run true if local extraction should start."]
    return ["Prepare or record a valid local rights/privacy decision before running OCR-first Batch 1."]


def operator_next_actions(
    private_run: dict[str, Any],
    progress: dict[str, Any],
    manifest: dict[str, Any],
    coverage: dict[str, Any],
) -> list[str]:
    if progress.get("status") == "receipts_ready_for_human_review":
        return ["Human-review the private OCR artifacts referenced by hash-only receipts before tutor indexing."]
    if manifest.get("status") == "ready_for_private_manifest_update":
        return ["Apply reviewed private manifest metadata, rebuild ExamScopeMap, and rerun tutor coverage."]
    if coverage.get("status") == "coverage_uplift_ready_after_private_manifest_update":
        return ["Rebuild course tutor retrieval and run the course tutor eval."]
    if private_run.get("status") == "partial_private_extraction_run":
        return ["Inspect failed hash-only receipts locally, then decide whether to rerun the failed jobs."]
    return ["Inspect the receipt journal and rerun Progress, Manifest, and Tutor-Coverage reports."]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "ocr-first-operator")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
