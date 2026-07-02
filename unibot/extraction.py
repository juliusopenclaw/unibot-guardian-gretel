from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id, scan_course_intake
from .materials import sha256_text
from .public_safety import scan_text


EXTRACTION_SCHEMA_VERSION = "unibot-course-extraction-v1"


def build_course_extraction_queue(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    rights_decision_reference: str | None = None,
    rights_decision_reference_hash: str | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    scan = scan_course_intake(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        public_safe=True,
    )
    records = list(scan.get("records", []))
    rights_hash = (
        sha256_text(str(rights_decision_reference or ""))
        if rights_decision_reference
        else str(rights_decision_reference_hash or "")
    )
    authorized = bool(rights_decision_reference or rights_hash)
    jobs = []
    quarantine_count = 0
    skipped_review_ready = 0

    for record in records:
        notes = str(record.get("notes", ""))
        if record.get("review_status") == "blocked" or "quarantined_solution_or_exam" in notes:
            quarantine_count += 1
            continue
        if record.get("extraction_status") in {"text_extracted", "captions_available"}:
            skipped_review_ready += 1
            continue
        job_type = job_type_for_record(record)
        if not job_type:
            continue
        jobs.append(extraction_job(record, job_type=job_type, authorized=authorized, rights_hash=rights_hash))

    ocr_jobs = [job for job in jobs if job["job_type"] == "ocr"]
    transcription_jobs = [job for job in jobs if job["job_type"] == "transcription"]
    queue = {
        "schema_version": EXTRACTION_SCHEMA_VERSION,
        "artifact_type": "course_extraction_queue",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": "ready_to_run_when_authorized" if jobs and not authorized else "authorized_manifest_ready" if jobs else "empty",
        "exam_deployment_status": "not_cleared",
        "execution_mode": "plan_only_no_extraction_performed",
        "rights_gate": {
            "required_before_processing": True,
            "authorized": authorized,
            "decision_reference_hash": rights_hash,
            "policy": "OCR/transcription may run only locally after rights/privacy decision; queue itself stores metadata only.",
        },
        "counts": {
            "total_record_count": scan.get("record_count", 0),
            "job_count": len(jobs),
            "ocr_job_count": len(ocr_jobs),
            "transcription_job_count": len(transcription_jobs),
            "blocked_until_rights_decision_count": 0 if authorized else len(jobs),
            "quarantine_count": quarantine_count,
            "already_text_or_caption_count": skipped_review_ready,
        },
        "jobs": jobs[:80],
        "job_policy": {
            "source_files": "local private course files are not copied into this queue",
            "public_fields": ["material_id", "title", "source_kind", "job_type", "status", "sha256", "skill_tags"],
            "raw_output_storage": "raw OCR/transcript output must remain local private until review",
            "review_after_extraction": "new text must be reviewed_for_private_tutor before tutor retrieval",
        },
        "next_actions": next_actions(len(ocr_jobs), len(transcription_jobs), authorized),
        "intake_status": scan.get("status", "unknown"),
        "root_policy": scan.get("root_policy", "local private course-material root is not returned"),
    }
    attach_public_scan(queue, public_safe=public_safe, source_name="course-extraction-queue")
    return queue


def build_extraction_run_manifest(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    rights_decision_reference: str | None = None,
    dry_run: bool = True,
    public_safe: bool = True,
) -> dict[str, Any]:
    queue = build_course_extraction_queue(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        rights_decision_reference=rights_decision_reference,
        public_safe=public_safe,
    )
    authorized = bool(rights_decision_reference)
    runnable = authorized and dry_run
    manifest = {
        "schema_version": EXTRACTION_SCHEMA_VERSION,
        "artifact_type": "course_extraction_run_manifest",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": "dry_run_ready" if runnable else "blocked_until_rights_decision" if queue["counts"]["job_count"] else "empty",
        "dry_run": dry_run,
        "exam_deployment_status": "not_cleared",
        "rights_gate": queue["rights_gate"],
        "job_count": queue["counts"]["job_count"],
        "steps": [
            "resolve local source path from private manifest outside public output",
            "extract OCR or transcript locally",
            "hash extracted text",
            "run public-safety and solution-marker scan on metadata only for public reports",
            "human-review extracted text before marking reviewed_for_private_tutor",
            "rebuild ExamScopeMap and tutor retrieval index",
        ],
        "expected_outputs": [
            "private local text artifact",
            "metadata-only source card candidate",
            "review queue item",
            "updated material manifest after human review",
        ],
        "source_policy": "manifest is metadata-only; it does not contain local paths or raw extracted course text",
        "queue_summary": queue["counts"],
    }
    attach_public_scan(manifest, public_safe=public_safe, source_name="course-extraction-run-manifest")
    return manifest


def job_type_for_record(record: dict[str, Any]) -> str:
    source_kind = str(record.get("source_kind", ""))
    extraction_status = str(record.get("extraction_status", ""))
    if extraction_status == "ocr_needed" and source_kind in {"slide_pdf", "slide_deck", "document"}:
        return "ocr"
    if extraction_status == "staged" and source_kind == "video_file":
        return "transcription"
    return ""


def extraction_job(record: dict[str, Any], *, job_type: str, authorized: bool, rights_hash: str) -> dict[str, Any]:
    material_id = str(record.get("material_id", ""))
    return {
        "job_id": sha256_text(f"{material_id}:{job_type}")[:20],
        "material_id": material_id,
        "title": str(record.get("title", "")),
        "source_kind": str(record.get("source_kind", "")),
        "job_type": job_type,
        "status": "queued" if authorized else "blocked_until_rights_decision",
        "priority": priority_for_job(record, job_type),
        "sha256": str(record.get("sha256", "")),
        "skill_tags": list(record.get("skill_tags", []) or [])[:6],
        "source_card_ids": list(record.get("source_card_ids", []) or [])[:6],
        "review_after_extraction": "human_review_required_before_private_tutor_use",
        "rights_decision_reference_hash": rights_hash,
        "raw_output_policy": "do_not_emit_raw_text_in_public_reports",
    }


def priority_for_job(record: dict[str, Any], job_type: str) -> str:
    skill_tags = set(record.get("skill_tags", []) or [])
    if skill_tags.intersection({"pandas", "boxplots", "statistics_pingouin", "debugging"}):
        return "high"
    if job_type == "ocr":
        return "medium"
    return "normal"


def next_actions(ocr_count: int, transcription_count: int, authorized: bool) -> list[str]:
    if not ocr_count and not transcription_count:
        return ["No extraction jobs found; rebuild the ExamScopeMap from reviewed text/caption materials."]
    if not authorized:
        return [
            "record rights/privacy decision before processing any course media",
            f"prepare local OCR batch for {ocr_count} slide/document files",
            f"prepare local transcription batch for {transcription_count} video files",
            "review extracted text before adding it to tutor retrieval",
        ]
    return [
        f"run local dry-run harness for {ocr_count} OCR jobs and {transcription_count} transcription jobs",
        "store extracted raw text only in private local workspace",
        "human-review extracted text before private tutor indexing",
        "rerun completion audit and pipeline smoke",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["public_safety_findings"] = scan["findings"]
