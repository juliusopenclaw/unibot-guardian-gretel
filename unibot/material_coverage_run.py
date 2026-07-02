from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, SKILL_PROFILES, build_course_exam_scope, safe_course_id, scan_course_intake
from .extraction import build_course_extraction_queue
from .extraction_decision_context import decision_context_authorizes, resolve_extraction_decision_context
from .extraction_manifest_apply import read_private_manifest, resolve_private_manifest_path
from .extraction_receipt_journal import extraction_receipts_for_progress, summarize_extraction_receipt_records
from .materials import sha256_text
from .public_safety import scan_text
from .study_session import build_course_study_session_plan
from .tutor_coverage import build_course_tutor_coverage_plan
from .tutor_index import read_private_tutor_index, resolve_private_tutor_index_path


MATERIAL_COVERAGE_RUN_SCHEMA_VERSION = "unibot-course-material-coverage-run-v1"


def build_course_material_coverage_run(
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
    tutor_index_path: str | Path | None = None,
    tutor_index_journal_path: str | Path | None = None,
    focus_query: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    decision_context = resolve_extraction_decision_context(
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
    )
    authorized = decision_context_authorizes(decision_context)
    all_receipts = [item for item in (receipts or []) if isinstance(item, dict)]
    if receipt_journal_path:
        all_receipts.extend(extraction_receipts_for_progress(path=receipt_journal_path))

    intake = scan_course_intake(
        safe_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    queue = build_course_extraction_queue(
        safe_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        rights_decision_reference_hash=str(decision_context.get("rights_decision_reference_hash", "")) if authorized else None,
        public_safe=public_safe,
    )
    progress_summary = summarize_extraction_receipt_records(
        safe_receipt_records_for_summary(all_receipts),
        status="ok" if all_receipts else "empty",
    )
    manifest_path = resolve_private_manifest_path(private_manifest_path)
    manifest = read_private_manifest(manifest_path)
    index_path = resolve_private_tutor_index_path(tutor_index_path)
    index = read_private_tutor_index(index_path)
    coverage = build_course_tutor_coverage_plan(
        safe_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=all_receipts,
        public_safe=public_safe,
    )
    scope = build_course_exam_scope(
        safe_id,
        records=[item for item in intake.get("records", []) if isinstance(item, dict)],
        review_policy=review_policy,
        public_safe=public_safe,
    )
    study = build_course_study_session_plan(
        safe_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        receipts=all_receipts,
        focus_query=focus_query,
        max_items=len(SKILL_PROFILES),
        public_safe=public_safe,
    )
    skill_rows = build_skill_rows(
        scope=scope,
        coverage=coverage,
        index=index,
        queue=queue,
        study=study,
    )
    start_point = select_exam_workspace_start_point(skill_rows, focus_query=focus_query)
    report = {
        "schema_version": MATERIAL_COVERAGE_RUN_SCHEMA_VERSION,
        "artifact_type": "course_material_coverage_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": material_coverage_status(
            intake=intake,
            manifest=manifest,
            index=index,
            coverage=coverage,
            skill_rows=skill_rows,
            start_point=start_point,
        ),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Course material coverage run. It condenses local material metadata, private manifest status, "
            "extraction receipt evidence, hash-only tutor-index anchors, and notebook practice coverage into "
            "a per-exam-skill control report. It does not run OCR/transcription, does not build an index, "
            "does not open an exam workspace, and never returns raw course text, raw queries, notebook code, "
            "local paths, grading, proctoring, AI detection, or exam clearance."
        ),
        "decision_summary": {
            "status": decision_context.get("status", "missing"),
            "authorized_for_local_extraction": authorized,
            "decision_reference_hash": decision_context.get("rights_decision_reference_hash", ""),
            "raw_decision_returned": False,
        },
        "material_summary": {
            "intake_status": intake.get("status", "unknown"),
            "record_count": intake.get("record_count", 0),
            "total_file_count": intake.get("total_file_count", 0),
            "counts_by_kind": intake.get("counts_by_kind", {}),
            "counts_by_extraction_status": intake.get("counts_by_extraction_status", {}),
            "review_summary": intake.get("review_summary", {}),
            "raw_text_returned": False,
            "local_paths_returned": False,
        },
        "extraction_gap_summary": {
            **queue.get("counts", {}),
            "queue_status": queue.get("status", "unknown"),
            "receipt_summary": safe_receipt_summary(progress_summary),
        },
        "private_manifest_summary": {
            "status": manifest.get("status", "missing"),
            "record_count": manifest.get("record_count", 0),
            "manifest_hash": manifest.get("manifest_hash", ""),
            "journal": journal_summary(manifest_apply_journal_path, "private_manifest_apply_journal"),
            "private_manifest_path_returned": False,
        },
        "private_tutor_index_summary": {
            "status": index.get("status", "missing"),
            "index_hash": index.get("index_hash", ""),
            "manifest_hash": index.get("manifest_hash", ""),
            "anchor_count": index.get("coverage_summary", {}).get("anchor_count", 0),
            "indexed_skill_count": index.get("coverage_summary", {}).get("indexed_skill_count", 0),
            "missing_skill_count": index.get("coverage_summary", {}).get("missing_skill_count", 0),
            "journal": journal_summary(tutor_index_journal_path, "private_tutor_index_journal"),
            "tutor_index_path_returned": False,
        },
        "coverage_summary": {
            "coverage_status": coverage.get("status", "unknown"),
            "current_ready_skill_count": coverage.get("current_scope_summary", {}).get("ready_skill_count", 0),
            "projected_ready_skill_count": coverage.get("projected_scope_summary", {}).get("ready_skill_count", 0),
            "indexed_skill_count": index.get("coverage_summary", {}).get("indexed_skill_count", 0),
            "skill_count": len(skill_rows),
            "exam_workspace_ready_skill_count": len(
                [item for item in skill_rows if item.get("exam_workspace_readiness") == "ready_for_exam_workspace_dry_run"]
            ),
            "ocr_gap_count": queue.get("counts", {}).get("ocr_job_count", 0),
            "video_gap_count": queue.get("counts", {}).get("transcription_job_count", 0),
        },
        "skill_coverage": skill_rows,
        "next_exam_workspace_start_point": start_point,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "private_manifest_path_returned": False,
        "tutor_index_path_returned": False,
        "receipt_journal_path_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "real_world_clearance_reminder": (
            "Real exam authority clearance remains outside the bot. This report chooses technical next steps only."
        ),
        "next_actions": material_coverage_next_actions(start_point, manifest=manifest, index=index, queue=queue, coverage=coverage),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def safe_receipt_records_for_summary(receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for receipt in receipts:
        if not isinstance(receipt, dict):
            continue
        event = {
            "job_id": str(receipt.get("job_id", "")),
            "material_id": str(receipt.get("material_id", "")),
            "job_type": str(receipt.get("job_type", "")),
            "extraction_status": str(receipt.get("extraction_status", "")),
            "human_review_status": str(receipt.get("human_review_status", "")),
            "raw_text_sha256": str(receipt.get("raw_text_sha256", "")),
            "extracted_text_char_count": int(receipt.get("extracted_text_char_count", 0) or 0),
            "ready_for_human_review_queue": str(receipt.get("human_review_status", "")) != "reviewed_for_private_tutor",
            "eligible_for_private_tutor_index": str(receipt.get("human_review_status", "")) == "reviewed_for_private_tutor",
        }
        records.append({"status": "accepted", "event": event})
    return records


def safe_receipt_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": summary.get("status", "empty"),
        "record_count": summary.get("record_count", 0),
        "accepted_record_count": summary.get("accepted_record_count", 0),
        "ready_for_human_review_count": summary.get("ready_for_human_review_count", 0),
        "eligible_for_private_tutor_index_count": summary.get("eligible_for_private_tutor_index_count", 0),
        "failed_or_skipped_count": summary.get("failed_or_skipped_count", 0),
        "by_job_type": summary.get("by_job_type", {}),
        "by_human_review_status": summary.get("by_human_review_status", {}),
        "raw_text_returned": False,
        "local_paths_returned": False,
    }


def journal_summary(path: str | Path | None, journal_kind: str) -> dict[str, Any]:
    if not path:
        return {"status": "not_configured", "journal_kind": journal_kind, "record_count": 0, "path_returned": False}
    journal_path = Path(path).expanduser()
    if not journal_path.exists():
        return {"status": "empty", "journal_kind": journal_kind, "record_count": 0, "path_returned": False}
    rows = []
    try:
        with journal_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
    except (OSError, json.JSONDecodeError):
        return {"status": "blocked_unreadable_journal", "journal_kind": journal_kind, "record_count": 0, "path_returned": False}
    accepted = [row for row in rows if isinstance(row, dict) and row.get("status") == "accepted"]
    latest = accepted[-1] if accepted else rows[-1] if rows else {}
    return {
        "status": "ok" if rows else "empty",
        "journal_kind": journal_kind,
        "record_count": len(rows),
        "accepted_record_count": len(accepted),
        "latest_record_hash": sha256_text(json.dumps(latest, sort_keys=True, ensure_ascii=False)) if latest else "",
        "path_returned": False,
    }


def build_skill_rows(
    *,
    scope: dict[str, Any],
    coverage: dict[str, Any],
    index: dict[str, Any],
    queue: dict[str, Any],
    study: dict[str, Any],
) -> list[dict[str, Any]]:
    scope_by_tag = {item.get("skill_tag"): item for item in scope.get("skills", []) if isinstance(item, dict)}
    coverage_by_tag = {item.get("skill_tag"): item for item in coverage.get("skill_coverage", []) if isinstance(item, dict)}
    index_by_tag = {item.get("skill_tag"): item for item in index.get("skill_index", []) if isinstance(item, dict)}
    study_by_tag = {item.get("skill_tag"): item for item in study.get("tasks", []) if isinstance(item, dict)}
    queue_jobs_by_tag: dict[str, list[dict[str, Any]]] = {}
    for job in queue.get("jobs", []) or []:
        if not isinstance(job, dict):
            continue
        for tag in job.get("skill_tags", []) or []:
            queue_jobs_by_tag.setdefault(str(tag), []).append(job)

    rows = []
    for profile in SKILL_PROFILES:
        tag = profile.skill_tag
        scope_skill = scope_by_tag.get(tag, {})
        coverage_skill = coverage_by_tag.get(tag, {})
        index_skill = index_by_tag.get(tag, {})
        study_task = study_by_tag.get(tag, {})
        jobs = queue_jobs_by_tag.get(tag, [])
        ocr_jobs = [job for job in jobs if job.get("job_type") == "ocr"]
        video_jobs = [job for job in jobs if job.get("job_type") == "transcription"]
        anchor_count = int(index_skill.get("anchor_count", 0) or 0)
        notebook_anchor_count = count_index_notebook_anchors(index, tag)
        exercise_ready = (bool(study_task) and str(study_task.get("readiness", "")) == "ready_for_private_tutor") or anchor_count > 0
        exercise_status = (
            "ready"
            if bool(study_task) and str(study_task.get("readiness", "")) == "ready_for_private_tutor"
            else "ready_from_private_index_anchor"
            if anchor_count > 0
            else "waiting_for_course_anchor"
        )
        microtask_seed = str(study_task.get("notebook_microtask", "")) or f"{profile.skill_tag}:{profile.exam_task_type}"
        readiness = skill_exam_workspace_readiness(
            anchor_count=anchor_count,
            exercise_ready=exercise_ready,
            projected_readiness=str(coverage_skill.get("projected_readiness", "")),
            ocr_gap_count=len(ocr_jobs),
            video_gap_count=len(video_jobs),
        )
        rows.append(
            {
                "skill_tag": tag,
                "title": profile.title,
                "exam_task_type": profile.exam_task_type,
                "current_readiness": scope_skill.get("readiness", coverage_skill.get("current_readiness", "no_course_anchor")),
                "projected_readiness": coverage_skill.get("projected_readiness", "no_course_anchor"),
                "private_index_readiness": index_skill.get("readiness", "no_private_index_anchor"),
                "source_anchor_count": anchor_count,
                "source_anchor_ids_returned": False,
                "source_card_ids": list(index_skill.get("source_card_ids", profile.source_card_ids))[:8],
                "material_count": scope_skill.get("material_count", coverage_skill.get("current_material_count", 0)),
                "tutor_usable_count": scope_skill.get("tutor_usable_count", coverage_skill.get("current_tutor_usable_count", 0)),
                "reviewed_notebook_anchor_count": notebook_anchor_count,
                "ocr_gap_count": len(ocr_jobs),
                "video_transcription_gap_count": len(video_jobs),
                "queued_job_count": len(jobs),
                "notebook_exercise": {
                    "status": exercise_status,
                    "task_id": study_task.get("task_id", sha256_text(f"{profile.skill_tag}:index-anchor-notebook-task")[:16]),
                    "notebook_microtask_hash": sha256_text(microtask_seed),
                    "expected_artifact_count": len(study_task.get("expected_artifacts", []) or []),
                    "raw_task_text_returned": False,
                },
                "allowed_exam_help": list(profile.allowed_exam_help),
                "blocked_help": ["A6 final solution", "complete code", "inserted values", "final interpretation"],
                "exam_workspace_readiness": readiness,
                "next_step": skill_next_step(readiness, len(ocr_jobs), len(video_jobs), anchor_count),
            }
        )
    return rows


def count_index_notebook_anchors(index: dict[str, Any], skill_tag: str) -> int:
    count = 0
    for anchor in index.get("source_anchors", []) or []:
        if not isinstance(anchor, dict):
            continue
        if skill_tag in {str(tag) for tag in anchor.get("skill_tags", []) or []} and anchor.get("source_kind") == "notebook":
            count += 1
    return count


def skill_exam_workspace_readiness(
    *,
    anchor_count: int,
    exercise_ready: bool,
    projected_readiness: str,
    ocr_gap_count: int,
    video_gap_count: int,
) -> str:
    if anchor_count > 0 and exercise_ready:
        return "ready_for_exam_workspace_dry_run"
    if anchor_count > 0:
        return "ready_for_tutor_anchor_needs_notebook_exercise"
    if projected_readiness == "ready_for_private_tutor":
        return "needs_private_manifest_apply_and_index_rebuild"
    if ocr_gap_count or video_gap_count:
        return "needs_extraction_or_transcription"
    return "needs_course_anchor_review"


def skill_next_step(readiness: str, ocr_gap_count: int, video_gap_count: int, anchor_count: int) -> str:
    if readiness == "ready_for_exam_workspace_dry_run":
        return "start exam workspace dry-run with A2 source-grounded sidecar"
    if readiness == "ready_for_tutor_anchor_needs_notebook_exercise":
        return "generate or select the smallest notebook microtask before exam workspace use"
    if readiness == "needs_private_manifest_apply_and_index_rebuild":
        return "apply reviewed private manifest metadata, then rebuild the hash-only tutor index"
    if video_gap_count:
        return "run local video transcription harness after rights/privacy decision and human review"
    if ocr_gap_count:
        return "run local OCR harness after rights/privacy decision and human review"
    if anchor_count == 0:
        return "map or review one approved course anchor for this skill"
    return "review coverage state"


def select_exam_workspace_start_point(skill_rows: list[dict[str, Any]], *, focus_query: str) -> dict[str, Any]:
    focus = str(focus_query or "").lower()
    ready = [row for row in skill_rows if row.get("exam_workspace_readiness") == "ready_for_exam_workspace_dry_run"]
    if focus and ready:
        focused = [
            row
            for row in ready
            if str(row.get("skill_tag", "")).lower() in focus or any(part in focus for part in str(row.get("title", "")).lower().split()[:4])
        ]
        if focused:
            ready = focused
    if ready:
        chosen = sorted(ready, key=lambda row: (-int(row.get("source_anchor_count", 0) or 0), str(row.get("skill_tag", ""))))[0]
        return {
            "status": "ready",
            "skill_tag": chosen.get("skill_tag", ""),
            "title": chosen.get("title", ""),
            "recommended_endpoint": "/api/unibot/exam-workspace/run-dry-run",
            "recommended_help_level": "A2",
            "query_template": f"Welche Quelle und welche eigene Vorhersage pruefe ich zuerst fuer {chosen.get('title', 'diesen Skill')}?",
            "requires_operator_confirmation_for_writes": True,
            "source_anchor_count": chosen.get("source_anchor_count", 0),
            "notebook_exercise_task_id": chosen.get("notebook_exercise", {}).get("task_id", ""),
            "exam_deployment_status": "not_cleared",
        }
    gaps = [row for row in skill_rows if row.get("exam_workspace_readiness") != "ready_for_exam_workspace_dry_run"]
    gaps.sort(key=lambda row: (0 if row.get("skill_tag") in {"python_lists", "control_flow", "pandas", "debugging"} else 1, row.get("queued_job_count", 0)))
    chosen_gap = gaps[0] if gaps else {}
    return {
        "status": "not_ready",
        "skill_tag": chosen_gap.get("skill_tag", ""),
        "title": chosen_gap.get("title", ""),
        "blocking_readiness": chosen_gap.get("exam_workspace_readiness", "unknown"),
        "next_step": chosen_gap.get("next_step", "build course coverage"),
        "recommended_endpoint": "",
        "recommended_help_level": "A2",
        "exam_deployment_status": "not_cleared",
    }


def material_coverage_status(
    *,
    intake: dict[str, Any],
    manifest: dict[str, Any],
    index: dict[str, Any],
    coverage: dict[str, Any],
    skill_rows: list[dict[str, Any]],
    start_point: dict[str, Any],
) -> str:
    if intake.get("status") == "missing":
        return "course_material_coverage_needs_materials"
    if manifest.get("status") == "missing" and coverage.get("projected_scope_summary", {}).get("candidate_material_count", 0):
        return "course_material_coverage_needs_private_manifest_apply"
    if index.get("status") == "missing" and manifest.get("record_count", 0):
        return "course_material_coverage_needs_tutor_index_build"
    if start_point.get("status") == "ready":
        return "course_material_coverage_ready_for_exam_workspace"
    if any(row.get("exam_workspace_readiness") == "needs_extraction_or_transcription" for row in skill_rows):
        return "course_material_coverage_needs_extraction_or_transcription"
    return "course_material_coverage_needs_anchor_review"


def material_coverage_next_actions(
    start_point: dict[str, Any],
    *,
    manifest: dict[str, Any],
    index: dict[str, Any],
    queue: dict[str, Any],
    coverage: dict[str, Any],
) -> list[str]:
    if start_point.get("status") == "ready":
        return [
            f"Start the Exam-Workspace dry-run for {start_point.get('skill_tag', 'the selected skill')} with A2 help.",
            "Keep local writes behind operator confirmations and keep exam_deployment_status not_cleared.",
        ]
    if manifest.get("status") == "missing" and coverage.get("projected_scope_summary", {}).get("candidate_material_count", 0):
        return ["Apply reviewed private manifest metadata, then rebuild the hash-only tutor index."]
    if index.get("status") == "missing" and manifest.get("record_count", 0):
        return ["Build the hash-only tutor index from the private manifest, then rerun this coverage report."]
    if queue.get("counts", {}).get("transcription_job_count", 0):
        return ["Run the local video transcription harness for queued video jobs after rights/privacy decision."]
    if queue.get("counts", {}).get("ocr_job_count", 0):
        return ["Run the local OCR harness for queued OCR jobs after rights/privacy decision."]
    return ["Review or map at least one approved course anchor for the next high-priority Python exam skill."]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "course-material-coverage-run")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
