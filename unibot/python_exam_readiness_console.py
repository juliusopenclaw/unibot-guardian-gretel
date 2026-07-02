from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .public_safety import scan_text


PYTHON_EXAM_READINESS_CONSOLE_SCHEMA_VERSION = "unibot-python-exam-readiness-console-v1"
PYTHON_EXAM_READINESS_CONSOLE_ENDPOINT = "/api/unibot/course/python-exam-readiness-console"


def build_python_exam_readiness_console(
    *,
    course_exam_coverage_dashboard: dict[str, Any] | None = None,
    exam_skill_drilldown: dict[str, Any] | None = None,
    review_chain_integrity_check: dict[str, Any] | None = None,
    timeline_export_receipt_journal_summary: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    dashboard = course_exam_coverage_dashboard if isinstance(course_exam_coverage_dashboard, dict) else {}
    drilldown = exam_skill_drilldown if isinstance(exam_skill_drilldown, dict) else {}
    chain = review_chain_integrity_check if isinstance(review_chain_integrity_check, dict) else {}
    journal = timeline_export_receipt_journal_summary if isinstance(timeline_export_receipt_journal_summary, dict) else {}
    selected = selected_skill(dashboard, drilldown, selected_skill_tag)
    console_summary = readiness_summary(
        dashboard=dashboard,
        drilldown=drilldown,
        chain=chain,
        journal=journal,
        selected=selected,
    )
    payload = {
        "schema_version": PYTHON_EXAM_READINESS_CONSOLE_SCHEMA_VERSION,
        "artifact_type": "python_exam_readiness_console",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": console_summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Readiness Console. It combines Course Coverage, Exam-Skill Drilldown, Review Chain "
            "Integrity, and Receipt Journal Summary into a compact per-skill readiness view. It returns only "
            "metadata, hashes, counts, A0-A2 help status, operator-confirmation status, review-chain status, "
            "next safe action, and the real-world clearance reminder. It never returns raw queries, course raw "
            "text, notebook code, local paths, values, solutions, final interpretations, proctoring, AI detection, "
            "automatic assessment, or exam clearance."
        ),
        "readiness_summary": console_summary,
        "selected_skill_readiness": selected,
        "material_tutor_coverage": material_tutor_coverage(selected, dashboard),
        "notebook_checkpoint_status": notebook_checkpoint_status(selected, dashboard),
        "a0_a2_help_status": a0_a2_help_status(selected, chain, journal),
        "operator_confirmation_status": operator_confirmation_status(selected, chain, journal),
        "review_chain_status": review_chain_status(chain),
        "receipt_journal_status": receipt_journal_status(journal),
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; UniBot bleibt technisch nutzbar und not_cleared."
        ),
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "values_returned": False,
        "solutions_returned": False,
        "final_interpretations_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "next_actions": next_actions(console_summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def selected_skill(dashboard: dict[str, Any], drilldown: dict[str, Any], selected_skill_tag: str) -> dict[str, Any]:
    drilldown_skill = drilldown.get("selected_skill", {}) if isinstance(drilldown.get("selected_skill"), dict) else {}
    tag = str(selected_skill_tag or drilldown_skill.get("skill_tag", "")).strip()
    dashboard_rows = [row for row in dashboard.get("skill_dashboard", []) if isinstance(row, dict)]
    dashboard_row = {}
    if tag:
        for row in dashboard_rows:
            if str(row.get("skill_tag", "")) == tag:
                dashboard_row = row
                break
    if not dashboard_row and drilldown_skill.get("skill_tag"):
        for row in dashboard_rows:
            if str(row.get("skill_tag", "")) == str(drilldown_skill.get("skill_tag", "")):
                dashboard_row = row
                break
    merged = {**dashboard_row, **drilldown_skill}
    effective_tag = str(merged.get("skill_tag", tag))
    return {
        "skill_tag": effective_tag,
        "title": str(merged.get("title", effective_tag)),
        "skill_readiness": str(
            merged.get("exam_workspace_readiness", merged.get("workspace_readiness", merged.get("current_readiness", "unknown")))
        ),
        "current_readiness": str(merged.get("current_readiness", "unknown")),
        "projected_readiness": str(merged.get("projected_readiness", "unknown")),
        "start_button_enabled": bool(merged.get("start_button_enabled", False))
        or str(merged.get("workspace_readiness", "")) == "ready_for_exam_workspace_dry_run",
        "recommended_help_level": str(merged.get("recommended_help_level", "A2")),
        "allowed_exam_help": safe_help_levels(merged.get("allowed_exam_help", [])),
        "source_anchor_count": int(merged.get("source_anchor_count", 0) or 0),
        "reviewed_notebook_anchor_count": int(merged.get("reviewed_notebook_anchor_count", 0) or 0),
        "source_card_ids": [str(item) for item in (merged.get("source_card_ids", []) or [])][:8],
        "checkpoint_hashes": [str(item) for item in (merged.get("latest_checkpoint_hashes", []) or [])][:4],
        "open_operator_confirmation_count": int(merged.get("open_operator_confirmation_count", 0) or 0),
        "coverage_gap_status": str(merged.get("coverage_gap_status", "")),
        "next_safe_step": str(merged.get("next_safe_step", merged.get("next_step", "review selected skill readiness"))),
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def readiness_summary(
    *,
    dashboard: dict[str, Any],
    drilldown: dict[str, Any],
    chain: dict[str, Any],
    journal: dict[str, Any],
    selected: dict[str, Any],
) -> dict[str, Any]:
    chain_summary = chain.get("chain_integrity_summary", {}) if isinstance(chain.get("chain_integrity_summary"), dict) else {}
    chain_status = str(chain.get("status", "missing"))
    journal_records = int(journal.get("accepted_record_count", 0) or 0)
    ready_skill = selected.get("skill_readiness") == "ready_for_exam_workspace_dry_run"
    has_anchors = int(selected.get("source_anchor_count", 0) or 0) > 0
    chain_pass = chain_status == "review_chain_integrity_pass" and int(chain_summary.get("issue_count", 0) or 0) == 0
    journal_ready = journal_records >= 1
    if ready_skill and has_anchors and chain_pass and journal_ready:
        status = "python_exam_readiness_console_ready"
        next_safe_action = "Use the selected skill workspace with A0-A2 support, review evidence, and keep not_cleared."
    elif not chain_pass and chain:
        status = "python_exam_readiness_console_chain_attention"
        next_safe_action = str(chain_summary.get("next_safe_action", "Resolve review-chain findings before relying on readiness."))
    elif not ready_skill or not has_anchors:
        status = "python_exam_readiness_console_material_attention"
        next_safe_action = str(selected.get("next_safe_step", "Review material and tutor coverage for the selected skill."))
    else:
        status = "python_exam_readiness_console_waiting_for_evidence"
        next_safe_action = "Build Receipt Journal Summary and Review Chain Integrity before using the console as evidence."
    return {
        "status": status,
        "course_dashboard_status": dashboard.get("status", "missing"),
        "exam_skill_drilldown_status": drilldown.get("status", "missing"),
        "selected_skill_tag": selected.get("skill_tag", ""),
        "skill_ready_for_workspace": bool(ready_skill),
        "source_anchored": bool(has_anchors),
        "review_chain_pass": bool(chain_pass),
        "receipt_journal_ready": bool(journal_ready),
        "latest_notebook_checkpoint_hash": (selected.get("checkpoint_hashes", []) or [""])[0],
        "help_profile": allowed_help_profile(chain_summary, journal),
        "open_operator_confirmation_count": max(
            int(selected.get("open_operator_confirmation_count", 0) or 0),
            int((chain_summary.get("open_operator_confirmation_counts", {}) or {}).get("journal", 0) or 0),
            int(journal.get("open_operator_confirmation_count", 0) or 0),
        ),
        "review_chain_issue_count": int(chain_summary.get("issue_count", 0) or 0),
        "receipt_journal_record_count": int(journal.get("record_count", 0) or 0),
        "accepted_receipt_count": int(journal.get("accepted_record_count", 0) or 0),
        "exam_deployment_status": "not_cleared",
        "next_safe_action": next_safe_action,
    }


def material_tutor_coverage(selected: dict[str, Any], dashboard: dict[str, Any]) -> dict[str, Any]:
    summary = dashboard.get("dashboard_summary", {}) if isinstance(dashboard.get("dashboard_summary"), dict) else {}
    return {
        "skill_tag": selected.get("skill_tag", ""),
        "source_anchor_count": int(selected.get("source_anchor_count", 0) or 0),
        "reviewed_notebook_anchor_count": int(selected.get("reviewed_notebook_anchor_count", 0) or 0),
        "source_card_ids": list(selected.get("source_card_ids", []) or [])[:8],
        "course_source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "course_workspace_ready_skill_count": int(summary.get("workspace_ready_skill_count", 0) or 0),
        "coverage_gap_status": selected.get("coverage_gap_status", ""),
        "raw_source_text_returned": False,
        "local_paths_returned": False,
    }


def notebook_checkpoint_status(selected: dict[str, Any], dashboard: dict[str, Any]) -> dict[str, Any]:
    summary = dashboard.get("dashboard_summary", {}) if isinstance(dashboard.get("dashboard_summary"), dict) else {}
    hashes = list(selected.get("checkpoint_hashes", []) or [])[:4]
    return {
        "skill_tag": selected.get("skill_tag", ""),
        "latest_notebook_checkpoint_hash": hashes[0] if hashes else "",
        "checkpoint_hash_count": len(hashes),
        "course_checkpoint_hash_count": int(summary.get("checkpoint_hash_count", 0) or 0),
        "checkpoint_hashes": hashes,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def a0_a2_help_status(selected: dict[str, Any], chain: dict[str, Any], journal: dict[str, Any]) -> dict[str, Any]:
    chain_summary = chain.get("chain_integrity_summary", {}) if isinstance(chain.get("chain_integrity_summary"), dict) else {}
    profile = allowed_help_profile(chain_summary, journal)
    nonstandard = nonstandard_help_profile(chain_summary, journal)
    return {
        "skill_tag": selected.get("skill_tag", ""),
        "recommended_help_level": selected.get("recommended_help_level", "A2"),
        "allowed_exam_help": safe_help_levels(selected.get("allowed_exam_help", [])),
        "observed_help_profile": profile,
        "nonstandard_help_event_count": sum(nonstandard.values()),
        "nonstandard_help_profile": nonstandard,
        "status": "a0_a2_only" if not nonstandard else "nonstandard_help_attention",
    }


def operator_confirmation_status(selected: dict[str, Any], chain: dict[str, Any], journal: dict[str, Any]) -> dict[str, Any]:
    chain_summary = chain.get("chain_integrity_summary", {}) if isinstance(chain.get("chain_integrity_summary"), dict) else {}
    counts = chain_summary.get("open_operator_confirmation_counts", {}) if isinstance(chain_summary.get("open_operator_confirmation_counts"), dict) else {}
    max_count = max(
        int(selected.get("open_operator_confirmation_count", 0) or 0),
        int(counts.get("packet", 0) or 0),
        int(counts.get("timeline", 0) or 0),
        int(counts.get("review", 0) or 0),
        int(counts.get("journal", 0) or 0),
        int(journal.get("open_operator_confirmation_count", 0) or 0),
    )
    return {
        "open_operator_confirmation_count": max_count,
        "chain_counts": dict(counts),
        "journal_open_operator_confirmation_count": int(journal.get("open_operator_confirmation_count", 0) or 0),
        "status": "operator_confirmations_open" if max_count else "operator_confirmations_reviewed",
        "local_writes_require_confirmation": True,
    }


def review_chain_status(chain: dict[str, Any]) -> dict[str, Any]:
    summary = chain.get("chain_integrity_summary", {}) if isinstance(chain.get("chain_integrity_summary"), dict) else {}
    return {
        "status": chain.get("status", "missing"),
        "issue_count": int(summary.get("issue_count", 0) or 0),
        "missing_count": int(summary.get("missing_count", 0) or 0),
        "contradiction_count": int(summary.get("contradiction_count", 0) or 0),
        "duplicate_count": int(summary.get("duplicate_count", 0) or 0),
        "checked_link_count": int(summary.get("checked_link_count", 0) or 0),
        "next_safe_action": summary.get("next_safe_action", "Build or review the chain integrity check."),
        "exam_deployment_status": "not_cleared",
    }


def receipt_journal_status(journal: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": journal.get("status", "missing"),
        "record_count": int(journal.get("record_count", 0) or 0),
        "accepted_record_count": int(journal.get("accepted_record_count", 0) or 0),
        "blocked_record_count": int(journal.get("blocked_record_count", 0) or 0),
        "skill_tags": [str(item) for item in (journal.get("skill_tags", []) or [])],
        "event_count": int(journal.get("event_count", 0) or 0),
        "checkpoint_hash_count": int(journal.get("checkpoint_hash_count", 0) or 0),
        "reviewer_question_count": int(journal.get("reviewer_question_count", 0) or 0),
        "exam_deployment_status": "not_cleared",
    }


def allowed_help_profile(chain_summary: dict[str, Any], journal: dict[str, Any]) -> dict[str, int]:
    profile: dict[str, int] = {}
    chain_profiles = chain_summary.get("help_level_profiles", {}) if isinstance(chain_summary.get("help_level_profiles"), dict) else {}
    for source in ("packet", "timeline", "review", "journal"):
        source_profile = chain_profiles.get(source, {}) if isinstance(chain_profiles.get(source), dict) else {}
        for level, count in source_profile.items():
            level_text = str(level)
            if level_text in {"A0", "A1", "A2"}:
                profile[level_text] = max(profile.get(level_text, 0), int(count or 0))
    for level, count in dict(journal.get("help_level_profile", {}) or {}).items():
        level_text = str(level)
        if level_text in {"A0", "A1", "A2"}:
            profile[level_text] = max(profile.get(level_text, 0), int(count or 0))
    return profile


def nonstandard_help_profile(chain_summary: dict[str, Any], journal: dict[str, Any]) -> dict[str, int]:
    profile: dict[str, int] = {}
    chain_profiles = chain_summary.get("help_level_profiles", {}) if isinstance(chain_summary.get("help_level_profiles"), dict) else {}
    for source in ("packet", "timeline", "review", "journal"):
        source_profile = chain_profiles.get(source, {}) if isinstance(chain_profiles.get(source), dict) else {}
        for level, count in source_profile.items():
            level_text = str(level)
            if level_text not in {"A0", "A1", "A2"} and int(count or 0) > 0:
                profile[level_text] = max(profile.get(level_text, 0), int(count or 0))
    for level, count in dict(journal.get("help_level_profile", {}) or {}).items():
        level_text = str(level)
        if level_text not in {"A0", "A1", "A2"} and int(count or 0) > 0:
            profile[level_text] = max(profile.get(level_text, 0), int(count or 0))
    return profile


def safe_help_levels(levels: Any) -> list[str]:
    result = [str(item) for item in (levels or []) if str(item).startswith(("A0", "A1", "A2"))]
    return result or ["A0", "A1", "A2"]


def next_actions(summary: dict[str, Any]) -> list[str]:
    return [
        summary.get("next_safe_action", "Review Python exam readiness evidence."),
        "Keep active help inside A0-A2 and keep local writes behind operator confirmation.",
        "Keep real-world exam clearance outside UniBot; console remains not_cleared.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-readiness-console")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
