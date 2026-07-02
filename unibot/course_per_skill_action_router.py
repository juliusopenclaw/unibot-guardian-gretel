from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_exam_coverage_dashboard import build_course_exam_coverage_dashboard
from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .materials import sha256_text
from .public_safety import scan_text


COURSE_PER_SKILL_ACTION_ROUTER_SCHEMA_VERSION = "unibot-course-per-skill-action-router-v1"
COURSE_PER_SKILL_ACTION_ROUTER_ENDPOINT = "/api/unibot/course/per-skill-action-router"


def build_course_per_skill_action_router(
    *,
    course_id: str = DEFAULT_COURSE_ID,
    selected_skill_tag: str = "",
    focus_query: str = "",
    dashboard_report: dict[str, Any] | None = None,
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
    console_reports: list[dict[str, Any]] | None = None,
    console_receipts: list[dict[str, Any]] | None = None,
    run_history_report: dict[str, Any] | None = None,
    build_current_console: bool = False,
    public_safe: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    dashboard = dashboard_report if isinstance(dashboard_report, dict) else build_course_exam_coverage_dashboard(
        course_id=safe_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=receipts,
        receipt_journal_path=receipt_journal_path,
        private_manifest_path=private_manifest_path,
        manifest_apply_journal_path=manifest_apply_journal_path,
        tutor_index_path=tutor_index_path,
        tutor_index_journal_path=tutor_index_journal_path,
        focus_query=focus_query,
        selected_skill_tag=selected_skill_tag,
        console_reports=console_reports,
        console_receipts=console_receipts,
        run_history_report=run_history_report,
        build_current_console=build_current_console,
        public_safe=public_safe,
    )
    skill_rows = [item for item in dashboard.get("skill_dashboard", []) if isinstance(item, dict)]
    selected = select_skill_row(skill_rows, selected_skill_tag=selected_skill_tag, focus_query=focus_query)
    all_routes = [skill_action_route(row, selected=False) for row in skill_rows]
    selected_route = skill_action_route(selected, selected=True) if selected else missing_skill_route(selected_skill_tag, focus_query)
    route_summary = summarize_routes(all_routes)
    report = {
        "schema_version": COURSE_PER_SKILL_ACTION_ROUTER_SCHEMA_VERSION,
        "artifact_type": "course_per_skill_action_router",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": "course_per_skill_action_router_ready" if selected else "course_per_skill_action_router_waiting_for_skill",
        "router_title": "Per-Skill Action Router",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Per-Skill Action Router. It turns Course Exam Coverage Dashboard rows into one safe dry-run action "
            "path per Python exam skill. It does not execute local writes by itself and never returns raw queries, "
            "course raw text, notebook code, local paths, values, solutions, final interpretations, proctoring, "
            "AI detection, automatic assessment, or exam clearance."
        ),
        "selected_skill": safe_selected_skill(selected),
        "selected_route": selected_route,
        "skill_action_routes": all_routes,
        "router_summary": route_summary,
        "dashboard_receipt": safe_dashboard_receipt(dashboard),
        "router_receipt": router_receipt(safe_id, selected_route, route_summary),
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "private_manifest_path_returned": False,
        "tutor_index_path_returned": False,
        "ledger_path_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt ausserhalb des Bots; der Router bleibt dry-run und not_cleared."
        ),
        "next_actions": router_next_actions(selected_route),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def select_skill_row(
    rows: list[dict[str, Any]],
    *,
    selected_skill_tag: str,
    focus_query: str,
) -> dict[str, Any] | None:
    selected = str(selected_skill_tag or "").strip().lower()
    focus = str(focus_query or "").strip().lower()
    for row in rows:
        tag = str(row.get("skill_tag", "")).lower()
        if selected and (selected == tag or selected in tag or tag in selected):
            return row
    for row in rows:
        tag = str(row.get("skill_tag", "")).lower()
        title = str(row.get("title", "")).lower()
        if focus and (focus == tag or focus in tag or tag in focus or focus in title):
            return row
    ready = [row for row in rows if row.get("workspace_readiness") == "ready_for_exam_workspace_dry_run"]
    if ready:
        return sorted(ready, key=lambda item: str(item.get("skill_tag", "")))[0]
    return rows[0] if rows else None


def skill_action_route(row: dict[str, Any], *, selected: bool) -> dict[str, Any]:
    tag = str(row.get("skill_tag", ""))
    readiness = str(row.get("workspace_readiness", "unknown"))
    gap = str(row.get("coverage_gap_status", "unknown"))
    checkpoint_count = int(row.get("checkpoint_hash_count", 0) or 0)
    open_count = int(row.get("open_operator_confirmation_count", 0) or 0)
    if open_count > 0:
        route_id = "review_open_operator_confirmations"
        endpoint = "/api/unibot/exam-workspace/run-history-export-review"
        action_label = "Review Run-History and open Operator Confirmations"
        reason = "history exists and local write confirmations are still open"
    elif readiness == "ready_for_exam_workspace_dry_run" and checkpoint_count > 0:
        route_id = "repeat_session_console_or_review_history"
        endpoint = "/api/unibot/exam-workspace/session-console"
        action_label = "Repeat Session Console dry-run"
        reason = "skill is workspace-ready and has checkpoint history"
    elif readiness == "ready_for_exam_workspace_dry_run":
        route_id = "start_session_console_dry_run"
        endpoint = "/api/unibot/exam-workspace/session-console"
        action_label = "Start Session Console dry-run"
        reason = "skill is workspace-ready and has no checkpoint history yet"
    elif gap == "video_transcription_pending" or int(row.get("video_transcription_gap_count", 0) or 0) > 0:
        route_id = "prepare_video_transcription_harness"
        endpoint = "/api/unibot/course/video-transcription/run-batch"
        action_label = "Prepare local video transcription harness"
        reason = "video transcription gaps remain for this skill"
    elif gap == "ocr_pending" or int(row.get("ocr_gap_count", 0) or 0) > 0:
        route_id = "prepare_ocr_harness"
        endpoint = "/api/unibot/course/private-extraction/run-batch"
        action_label = "Prepare local OCR harness"
        reason = "OCR gaps remain for this skill"
    elif readiness == "needs_private_manifest_apply_and_index_rebuild":
        route_id = "apply_manifest_and_rebuild_index_dry_run"
        endpoint = "/api/unibot/course/extraction-manifest/apply-dry-run"
        action_label = "Apply reviewed manifest metadata, then rebuild hash-only index"
        reason = "reviewed course anchors need private manifest/index refresh"
    elif gap == "needs_notebook_anchor_review":
        route_id = "prepare_notebook_anchor_review"
        endpoint = "/api/unibot/course/study-session-plan"
        action_label = "Prepare notebook-anchor practice review"
        reason = "source anchors exist but reviewed notebook anchors are not complete"
    else:
        route_id = "review_source_anchor_mapping"
        endpoint = "/api/unibot/course/material-coverage/run"
        action_label = "Review source-anchor mapping"
        reason = "skill needs approved source anchors before exam workspace use"
    return {
        "skill_tag": tag,
        "selected": selected,
        "route_id": route_id,
        "action_label": action_label,
        "reason": reason,
        "endpoint": endpoint,
        "method": "POST",
        "dry_run_by_default": True,
        "requested_help_level": "A2",
        "allowed_help_levels": ["A0", "A1", "A2"],
        "requires_operator_confirmation_for_local_writes": True,
        "operator_confirmation_status": "open" if open_count else "not_requested",
        "open_operator_confirmation_count": open_count,
        "secondary_endpoints": secondary_endpoints(route_id),
        "payload_template": payload_template_for_route(row, endpoint),
        "safety_contract": safety_contract(),
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def payload_template_for_route(row: dict[str, Any], endpoint: str) -> dict[str, Any]:
    tag = str(row.get("skill_tag", ""))
    template = {
        "selected_skill_tag": tag,
        "focus_query": tag,
        "requested_help_level": "A2",
        "public_safe": True,
        "dry_run": True,
        "operator_confirmations_required": True,
        "source_card_ids": list(row.get("source_card_ids", []) or [])[:8],
        "checkpoint_hashes": list(row.get("latest_checkpoint_hashes", []) or [])[:4],
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }
    if endpoint.endswith("/session-console"):
        template["study_receipt_required"] = True
        template["previous_console_receipts_allowed"] = True
    if endpoint.endswith("/run-history-export-review"):
        template["console_reports_required"] = True
        template["hash_only_receipts_allowed"] = True
    if "video-transcription" in endpoint:
        template["job_types"] = ["transcription"]
        template["rights_privacy_decision_required"] = True
    if "private-extraction" in endpoint:
        template["job_types"] = ["ocr"]
        template["rights_privacy_decision_required"] = True
    if "tutor-index" in endpoint or "manifest" in endpoint:
        template["hash_only_private_metadata"] = True
    return template


def secondary_endpoints(route_id: str) -> list[str]:
    if route_id == "review_open_operator_confirmations":
        return ["/api/unibot/course/exam-coverage-dashboard", "/api/unibot/exam-workspace/session-console"]
    if route_id == "repeat_session_console_or_review_history":
        return ["/api/unibot/exam-workspace/run-history-export-review", "/api/unibot/course/exam-coverage-dashboard"]
    if route_id == "start_session_console_dry_run":
        return ["/api/unibot/course/exam-skill-drilldown", "/api/unibot/course/exam-coverage-dashboard"]
    if route_id == "apply_manifest_and_rebuild_index_dry_run":
        return ["/api/unibot/course/tutor-index/dry-run", "/api/unibot/course/material-coverage/run"]
    return ["/api/unibot/course/exam-coverage-dashboard"]


def safety_contract() -> dict[str, Any]:
    return {
        "a0_a2_only": True,
        "dry_run_by_default": True,
        "no_raw_queries": True,
        "no_course_raw_text": True,
        "no_notebook_code": True,
        "no_local_paths": True,
        "no_values_or_solutions": True,
        "no_final_interpretations": True,
        "no_proctoring": True,
        "no_ai_detection": True,
        "no_automatic_assessment": True,
        "no_exam_clearance_claim": True,
    }


def missing_skill_route(selected_skill_tag: str, focus_query: str) -> dict[str, Any]:
    return {
        "skill_tag": str(selected_skill_tag or focus_query or ""),
        "selected": True,
        "route_id": "waiting_for_skill_selection",
        "action_label": "Select a Python exam skill",
        "reason": "no dashboard row matched the requested skill",
        "endpoint": "/api/unibot/course/exam-coverage-dashboard",
        "method": "POST",
        "dry_run_by_default": True,
        "requested_help_level": "A2",
        "allowed_help_levels": ["A0", "A1", "A2"],
        "requires_operator_confirmation_for_local_writes": True,
        "operator_confirmation_status": "not_requested",
        "open_operator_confirmation_count": 0,
        "secondary_endpoints": [],
        "payload_template": {
            "selected_skill_tag": str(selected_skill_tag or ""),
            "focus_query": str(focus_query or ""),
            "public_safe": True,
            "dry_run": True,
        },
        "safety_contract": safety_contract(),
        "exam_deployment_status": "not_cleared",
    }


def safe_selected_skill(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {"status": "missing", "exam_deployment_status": "not_cleared"}
    return {
        "status": "selected",
        "skill_tag": row.get("skill_tag", ""),
        "title": row.get("title", ""),
        "workspace_readiness": row.get("workspace_readiness", "unknown"),
        "coverage_gap_status": row.get("coverage_gap_status", "unknown"),
        "source_anchor_count": int(row.get("source_anchor_count", 0) or 0),
        "reviewed_notebook_anchor_count": int(row.get("reviewed_notebook_anchor_count", 0) or 0),
        "checkpoint_hash_count": int(row.get("checkpoint_hash_count", 0) or 0),
        "open_operator_confirmation_count": int(row.get("open_operator_confirmation_count", 0) or 0),
        "exam_deployment_status": "not_cleared",
    }


def safe_dashboard_receipt(dashboard: dict[str, Any]) -> dict[str, Any]:
    receipt = dashboard.get("coverage_receipt", {}) if isinstance(dashboard.get("coverage_receipt"), dict) else {}
    summary = dashboard.get("dashboard_summary", {}) if isinstance(dashboard.get("dashboard_summary"), dict) else {}
    return {
        "status": receipt.get("status", "unknown"),
        "receipt_id": receipt.get("receipt_id", ""),
        "skill_count": summary.get("skill_count", 0),
        "workspace_ready_skill_count": summary.get("workspace_ready_skill_count", 0),
        "skills_with_history_count": summary.get("skills_with_history_count", 0),
        "not_cleared_receipt": bool(receipt.get("not_cleared_receipt", True)),
        "raw_text_returned": False,
        "local_paths_returned": False,
    }


def summarize_routes(routes: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(route.get("route_id", "unknown")) for route in routes)
    return {
        "route_count": len(routes),
        "routes_by_id": dict(sorted(counts.items())),
        "ready_session_route_count": counts.get("start_session_console_dry_run", 0)
        + counts.get("repeat_session_console_or_review_history", 0),
        "material_route_count": len(
            [
                route
                for route in routes
                if str(route.get("route_id", "")).startswith(("prepare_", "apply_", "review_source"))
            ]
        ),
        "open_operator_confirmation_route_count": counts.get("review_open_operator_confirmations", 0),
        "exam_deployment_status": "not_cleared",
    }


def router_receipt(course_id: str, selected_route: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    seed = {"course_id": course_id, "selected_route": selected_route, "summary": summary}
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "router_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def router_next_actions(selected_route: dict[str, Any]) -> list[str]:
    route_id = str(selected_route.get("route_id", ""))
    endpoint = str(selected_route.get("endpoint", ""))
    if route_id == "waiting_for_skill_selection":
        return ["Select a Python exam skill from the Course Exam Coverage Dashboard."]
    if route_id == "review_open_operator_confirmations":
        return ["Review Run-History and the listed operator confirmations before any local write."]
    if endpoint:
        return [f"Use {endpoint} as the next dry-run route for {selected_route.get('skill_tag', 'the selected skill')}."]
    return ["Review the Course Exam Coverage Dashboard and choose the next safe route."]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "course-per-skill-action-router")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
