from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction_decision_intake import (
    build_local_extraction_decision_intake_packet,
    record_local_extraction_decision_and_build_intake_packet,
)
from .extraction_receipt_journal import (
    resolve_extraction_receipt_journal_path,
    summarize_extraction_receipt_journal,
)
from .external_decision_journal import (
    resolve_external_decision_journal_path,
    summarize_external_decision_journal,
)
from .materials import sha256_text
from .public_safety import scan_text


LOCAL_EXTRACTION_DECISION_WORKSPACE_SCHEMA_VERSION = "unibot-local-extraction-decision-workspace-v1"
DEFAULT_DECISION_WORKSPACE_DIR = Path.home() / ".unibot_guardian" / "local_extraction_decision_workspace"


def resolve_decision_workspace_dir(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get("UNIBOT_LOCAL_EXTRACTION_DECISION_WORKSPACE_DIR")
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_DECISION_WORKSPACE_DIR


def prepare_local_extraction_decision_workspace(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    workspace_dir: str | Path | None = None,
    decision_record_journal_path: str | Path | None = None,
    receipt_journal_path: str | Path | None = None,
    private_output_dir: str | Path | None = None,
    job_types: list[str] | None = None,
    batch_size: int = 12,
    public_safe: bool = True,
) -> dict[str, Any]:
    workspace_path = resolve_decision_workspace_dir(workspace_dir)
    decision_journal_path = resolve_external_decision_journal_path(decision_record_journal_path)
    receipt_path = resolve_extraction_receipt_journal_path(receipt_journal_path)
    private_output_path = Path(private_output_dir).expanduser() if private_output_dir else Path.home() / ".unibot_guardian" / "private_extractions"
    intake = build_local_extraction_decision_intake_packet(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=str(decision_journal_path),
        receipt_journal_path=str(receipt_path),
        job_types=job_types or ["ocr"],
        batch_size=batch_size,
        public_safe=public_safe,
    )
    workspace_path.mkdir(parents=True, exist_ok=True)
    template = intake.get("decision_record_template", {})
    template_path = workspace_path / "local_extraction_decision.template.json"
    manifest_path = workspace_path / "workspace_manifest.hash_only.json"
    template_path.write_text(json.dumps(template, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = build_workspace_manifest(
        course_id=course_id,
        workspace_path=workspace_path,
        template_path=template_path,
        decision_journal_path=decision_journal_path,
        receipt_journal_path=receipt_path,
        private_output_path=private_output_path,
        intake=intake,
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    workspace = {
        "schema_version": LOCAL_EXTRACTION_DECISION_WORKSPACE_SCHEMA_VERSION,
        "artifact_type": "course_local_extraction_decision_workspace",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": workspace_status(intake),
        "exam_deployment_status": "not_cleared",
        "workspace_policy": (
            "Local private workspace under the UniBot guardian directory. Public responses expose only "
            "template status, hashes, counts, and local-private references; raw written decisions, raw course "
            "text, and local paths are not returned."
        ),
        "workspace_files": {
            "template": workspace_file_view(template_path, "local-private-decision-template"),
            "manifest": workspace_file_view(manifest_path, "local-private-workspace-manifest"),
        },
        "journal_targets": {
            "decision_record_journal": path_target_view(decision_journal_path, "local-private-decision-record-journal"),
            "receipt_journal": path_target_view(receipt_path, "local-private-extraction-receipt-journal"),
            "private_output_dir": path_target_view(private_output_path, "local-private-extraction-output-dir"),
        },
        "decision_validation": intake.get("decision_validation", {}),
        "decision_journal_summary": intake.get("decision_journal_summary", {}),
        "ocr_first_readiness": intake.get("ocr_first_readiness", {}),
        "receipt_journal_summary": intake.get("receipt_journal_summary", {}),
        "post_run_report_summary": intake.get("post_run_report_summary", {}),
        "dry_run_receipt": build_workspace_dry_run_receipt(intake),
        "safe_payload_templates": {
            "record_decision": {
                "endpoint": "/api/unibot/course/extraction-decision/workspace/record",
                "required_payload_fields": ["decision_record"],
                "path_fields_are_local_private": True,
                "raw_decision_record_returned": False,
            },
            "run_ocr_first_batch_1_after_valid_record": {
                "endpoint": "/api/unibot/course/private-extraction/run-batch",
                "fixed_payload": {"job_types": ["ocr"], "max_jobs": 12, "review_policy": review_policy},
                "requires_dry_run_receipt": "ocr_first_batch_1_start_ready",
            },
        },
        "raw_decision_record_stored_by_workspace": False,
        "raw_decision_record_returned": False,
        "raw_text_returned": False,
        "local_paths_returned": False,
        "next_actions": workspace_next_actions(intake),
    }
    attach_public_scan(workspace, public_safe=public_safe, source_name="local-extraction-decision-workspace")
    return workspace


def record_local_extraction_decision_workspace(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    workspace_dir: str | Path | None = None,
    decision_record_journal_path: str | Path | None = None,
    receipt_journal_path: str | Path | None = None,
    private_output_dir: str | Path | None = None,
    job_types: list[str] | None = None,
    batch_size: int = 12,
    public_safe: bool = True,
) -> dict[str, Any]:
    workspace_path = resolve_decision_workspace_dir(workspace_dir)
    decision_journal_path = resolve_external_decision_journal_path(decision_record_journal_path)
    receipt_path = resolve_extraction_receipt_journal_path(receipt_journal_path)
    private_output_path = Path(private_output_dir).expanduser() if private_output_dir else Path.home() / ".unibot_guardian" / "private_extractions"
    record_result = record_local_extraction_decision_and_build_intake_packet(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record or {},
        decision_record_journal_path=str(decision_journal_path),
        receipt_journal_path=str(receipt_path),
        job_types=job_types or ["ocr"],
        batch_size=batch_size,
        public_safe=public_safe,
    )
    workspace = prepare_local_extraction_decision_workspace(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=None if record_result.get("status") == "decision_record_stored_hash_only" else decision_record,
        workspace_dir=workspace_path,
        decision_record_journal_path=decision_journal_path,
        receipt_journal_path=receipt_path,
        private_output_dir=private_output_path,
        job_types=job_types or ["ocr"],
        batch_size=batch_size,
        public_safe=public_safe,
    )
    result = {
        "schema_version": LOCAL_EXTRACTION_DECISION_WORKSPACE_SCHEMA_VERSION,
        "artifact_type": "course_local_extraction_decision_workspace_record_result",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": "workspace_decision_record_stored_hash_only" if record_result.get("status") == "decision_record_stored_hash_only" else "blocked_decision_record_not_stored",
        "exam_deployment_status": "not_cleared",
        "journal_append_status": record_result.get("journal_append_status"),
        "journal_event": record_result.get("journal_event", {}),
        "workspace": workspace,
        "dry_run_receipt": workspace.get("dry_run_receipt", {}),
        "raw_decision_record_stored_by_workspace": False,
        "raw_decision_record_returned": False,
        "raw_text_returned": False,
        "local_paths_returned": False,
    }
    attach_public_scan(result, public_safe=public_safe, source_name="local-extraction-decision-workspace-record")
    return result


def build_workspace_manifest(
    *,
    course_id: str,
    workspace_path: Path,
    template_path: Path,
    decision_journal_path: Path,
    receipt_journal_path: Path,
    private_output_path: Path,
    intake: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": LOCAL_EXTRACTION_DECISION_WORKSPACE_SCHEMA_VERSION,
        "artifact_type": "course_local_extraction_decision_workspace_manifest",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "workspace_hash": sha256_text(str(workspace_path)),
        "template_hash": sha256_text(str(template_path)),
        "decision_record_journal_hash": sha256_text(str(decision_journal_path)),
        "receipt_journal_hash": sha256_text(str(receipt_journal_path)),
        "private_output_dir_hash": sha256_text(str(private_output_path)),
        "intake_status": intake.get("status"),
        "decision_status": intake.get("decision_validation", {}).get("status"),
        "ocr_first_status": intake.get("ocr_first_readiness", {}).get("status"),
        "raw_decision_record_stored": False,
        "raw_text_stored": False,
        "local_paths_stored_in_manifest": False,
    }


def build_workspace_dry_run_receipt(intake: dict[str, Any]) -> dict[str, Any]:
    decision = intake.get("decision_validation", {})
    ocr = intake.get("ocr_first_readiness", {})
    post = intake.get("post_run_report_summary", {})
    receipt = intake.get("receipt_journal_summary", {})
    decision_ready = bool(decision.get("approved_for_local_extraction"))
    ocr_ready = decision_ready and ocr.get("status") in {
        "ready_for_local_private_execution",
        "partially_receipted",
        "all_jobs_receipted",
    }
    reports_reachable = all(
        post.get(key) is not None
        for key in ["progress_status", "manifest_update_status", "tutor_coverage_status"]
    )
    return {
        "artifact_type": "course_local_extraction_decision_workspace_dry_run_receipt",
        "status": "ocr_first_batch_1_start_ready" if ocr_ready else "waiting_for_valid_decision_or_receipts",
        "exam_deployment_status": "not_cleared",
        "decision_valid": decision_ready,
        "decision_record_source": decision.get("decision_record_source", "missing_decision_record"),
        "ocr_first_batch_1_start_ready": ocr_ready,
        "ocr_first_batch_1_job_count": (ocr.get("next_batch", {}) or {}).get("job_count", 0),
        "ocr_first_batch_1_job_type_counts": (ocr.get("next_batch", {}) or {}).get("job_type_counts", {}),
        "expected_receipt_count": ocr.get("expected_receipt_count", 0),
        "missing_receipt_count": ocr.get("missing_receipt_count", 0),
        "receipt_journal_reachable": receipt.get("status") in {"empty", "ok"},
        "progress_report_reachable": post.get("progress_status") is not None,
        "manifest_report_reachable": post.get("manifest_update_status") is not None,
        "tutor_coverage_report_reachable": post.get("tutor_coverage_status") is not None,
        "post_run_reports_reachable": reports_reachable,
        "real_ocr_started": False,
        "raw_decision_record_returned": False,
        "raw_text_returned": False,
        "local_paths_returned": False,
    }


def workspace_status(intake: dict[str, Any]) -> str:
    dry_run = build_workspace_dry_run_receipt(intake)
    if dry_run.get("ocr_first_batch_1_start_ready"):
        return "workspace_ready_for_controlled_ocr_first_batch_1"
    if intake.get("status") == "waiting_for_local_rights_privacy_decision_record":
        return "workspace_waiting_for_local_decision_record"
    return "workspace_prepared_not_ready_for_ocr"


def workspace_file_view(path: Path, reference_prefix: str) -> dict[str, Any]:
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    path_hash = sha256_text(str(path))
    content_hash = sha256_text(path.read_text(encoding="utf-8")) if exists and path.is_file() else ""
    return {
        "status": "written" if exists else "missing",
        "local_private_reference": f"{reference_prefix}:{path_hash[:16]}",
        "path_sha256": path_hash,
        "content_sha256": content_hash,
        "byte_count": size,
        "raw_text_stored": False,
        "local_path_returned": False,
    }


def path_target_view(path: Path, reference_prefix: str) -> dict[str, Any]:
    return {
        "status": "ready" if path.exists() else "not_created_yet",
        "local_private_reference": f"{reference_prefix}:{sha256_text(str(path))[:16]}",
        "path_sha256": sha256_text(str(path)),
        "local_path_returned": False,
    }


def workspace_next_actions(intake: dict[str, Any]) -> list[str]:
    dry_run = build_workspace_dry_run_receipt(intake)
    if dry_run.get("ocr_first_batch_1_start_ready"):
        return [
            "Run OCR-first Batch 1 only if this dry-run receipt is still current and the human operator confirms the local decision record.",
            "After running OCR, use the receipt journal for Progress, Manifest, and Tutor-Coverage reports.",
        ]
    return [
        "Fill the local JSON template with the written rights/privacy decision, then record it through the workspace record endpoint.",
        "Keep raw written decision text out of public reports; the journal append stores validation metadata and hashes only.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
