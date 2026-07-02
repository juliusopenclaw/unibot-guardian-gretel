from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_GUIDED_SESSION_PLAYBACK_JOURNAL_SCHEMA_VERSION = "unibot-python-exam-guided-session-playback-journal-v1"
PYTHON_EXAM_GUIDED_SESSION_PLAYBACK_JOURNAL_ENDPOINT = "/api/unibot/course/python-exam-guided-session-playback-journal"

RESUME_DECISIONS = {
    "continue_current_control_step",
    "review_open_confirmation",
    "refresh_source_checkpoint",
    "continue_a0_a2_drill",
    "repeat_dry_run_rehearsal",
    "handoff_to_human_review",
}


def build_python_exam_guided_session_playback_journal(
    *,
    python_exam_guided_loop_control_surface: dict[str, Any] | None = None,
    previous_control_surfaces: list[dict[str, Any]] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    current = python_exam_guided_loop_control_surface if isinstance(python_exam_guided_loop_control_surface, dict) else {}
    previous = [item for item in (previous_control_surfaces or []) if isinstance(item, dict)]
    surfaces = previous + ([current] if current else [])
    skill_tag = effective_skill_tag(selected_skill_tag, *surfaces)
    entries = [journal_entry(surface, index + 1, skill_tag) for index, surface in enumerate(surfaces)]
    latest = entries[-1] if entries else {}
    decision = resume_decision(latest)
    summary = journal_summary(skill_tag, entries, latest, decision)
    payload = {
        "schema_version": PYTHON_EXAM_GUIDED_SESSION_PLAYBACK_JOURNAL_SCHEMA_VERSION,
        "artifact_type": "python_exam_guided_session_playback_journal",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "python_exam_guided_session_playback_journal_ready"
            if entries
            else "python_exam_guided_session_playback_journal_attention"
        ),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Guided Session Playback Journal. It compacts recent Guided Loop Control Surface cycles "
            "for one Python exam skill into a hash-only playback journal. It records action key, route, endpoint, "
            "prefill hash, Source-Card anchors, notebook checkpoint hashes, open operator confirmations, A0-A2 "
            "help profile, Evidence/Human-Handoff status, next safe click, and surface receipt metadata only. "
            "It writes nothing, executes nothing, and never returns raw queries, course raw text, notebook code, "
            "local paths, values, solutions, final interpretations, scores, rankings, grades, proctoring, AI "
            "detection, automatic grading, or exam clearance claims."
        ),
        "guided_session_playback_journal_endpoint": PYTHON_EXAM_GUIDED_SESSION_PLAYBACK_JOURNAL_ENDPOINT,
        "selected_skill_tag": skill_tag,
        "journal_summary": summary,
        "journal_entries": entries,
        "latest_entry": latest,
        "resume_decision": decision,
        "journal_receipt": journal_receipt(summary, entries, decision),
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "operator_confirmation_required_for_local_write": True,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "values_returned": False,
        "solutions_returned": False,
        "final_interpretations_returned": False,
        "score_returned": False,
        "percentage_returned": False,
        "ranking_returned": False,
        "grade_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; das Session Playback Journal bleibt not_cleared."
        ),
        "next_actions": [
            f"Resume decision: {decision.get('decision', 'continue_current_control_step')}.",
            "Use this journal as hash-only playback context; do not treat it as scoring or exam clearance.",
            "Keep local writes behind explicit operator confirmation and keep exam_deployment_status not_cleared.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def journal_entry(surface: dict[str, Any], sequence_index: int, fallback_skill_tag: str) -> dict[str, Any]:
    summary = safe_dict(surface.get("control_summary"))
    source = safe_dict(surface.get("source_anchor_status"))
    checkpoint = safe_dict(surface.get("notebook_checkpoint_status"))
    confirmations = safe_dict(surface.get("operator_confirmation_status"))
    help_status = safe_dict(surface.get("a0_a2_help_status"))
    evidence = safe_dict(surface.get("evidence_status"))
    receipt = safe_dict(surface.get("surface_receipt"))
    step = safe_dict(surface.get("current_guided_step_card"))
    entry_seed = {
        "sequence_index": sequence_index,
        "surface_receipt_hash": receipt.get("receipt_hash", ""),
        "action_key": summary.get("action_key", ""),
        "route": summary.get("route", ""),
        "prefill_hash": summary.get("prefill_hash") or step.get("prefill_hash", ""),
        "next_safe_click": summary.get("next_safe_click", ""),
        "exam_deployment_status": "not_cleared",
    }
    return {
        "entry_type": "python_exam_guided_session_playback_entry",
        "sequence_index": sequence_index,
        "selected_skill_tag": str(summary.get("selected_skill_tag") or surface.get("selected_skill_tag") or fallback_skill_tag),
        "surface_status": str(surface.get("status", "missing")),
        "action_key": str(summary.get("action_key", "")),
        "route": str(summary.get("route", "")),
        "endpoint": str(summary.get("endpoint", "")),
        "prefill_hash": str(summary.get("prefill_hash") or step.get("prefill_hash", "")),
        "source_card_ids": [str(item) for item in (source.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(source.get("source_anchor_count", 0) or 0),
        "latest_notebook_checkpoint_hash": str(checkpoint.get("latest_notebook_checkpoint_hash", "")),
        "checkpoint_hash_count": int(checkpoint.get("checkpoint_hash_count", 0) or 0),
        "open_operator_confirmation_count": int(confirmations.get("open_operator_confirmation_count", 0) or 0),
        "help_status": str(help_status.get("status", "missing")),
        "help_profile": safe_help_profile(help_status.get("profile")),
        "evidence_preview_status": str(evidence.get("evidence_preview_status", "missing")),
        "evidence_preview_receipt_id": str(evidence.get("evidence_preview_receipt_id", "")),
        "human_handoff_status": str(evidence.get("human_handoff_status", "missing")),
        "human_handoff_markdown_hash": str(evidence.get("human_handoff_markdown_hash", "")),
        "next_safe_click": str(summary.get("next_safe_click", "")),
        "surface_receipt_id": str(receipt.get("receipt_id", "")),
        "surface_receipt_hash": str(receipt.get("receipt_hash", "")),
        "entry_hash": sha256_text(json.dumps(entry_seed, sort_keys=True, ensure_ascii=False)),
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "values_returned": False,
        "solutions_returned": False,
        "final_interpretations_returned": False,
        "score_returned": False,
        "grade_returned": False,
    }


def resume_decision(latest: dict[str, Any]) -> dict[str, Any]:
    action_key = str(latest.get("action_key", ""))
    if not latest:
        decision = "continue_current_control_step"
        reason = "missing_journal_entry"
    elif action_key == "resolve_source_gap" or int(latest.get("source_anchor_count", 0) or 0) <= 0 or int(latest.get("checkpoint_hash_count", 0) or 0) <= 0:
        decision = "refresh_source_checkpoint"
        reason = "source_or_checkpoint_gap"
    elif action_key == "continue_a0_a2_drill" or latest.get("help_status") != "a0_a2_only":
        decision = "continue_a0_a2_drill"
        reason = "a0_a2_drill_or_help_attention"
    elif action_key == "ready_to_rehearse_again":
        decision = "repeat_dry_run_rehearsal"
        reason = "ready_to_rehearse_again"
    elif action_key == "ready_for_human_review_packet":
        decision = "handoff_to_human_review"
        reason = "human_review_packet_ready"
    elif int(latest.get("open_operator_confirmation_count", 0) or 0) > 0 or action_key == "review_operator_confirmation":
        decision = "review_open_confirmation"
        reason = "open_operator_confirmations_present"
    else:
        decision = "continue_current_control_step"
        reason = "current_control_step_prepared"
    return {
        "decision": decision,
        "reason": reason,
        "allowed_decisions": sorted(RESUME_DECISIONS),
        "selected_skill_tag": str(latest.get("selected_skill_tag", "python_lists")),
        "next_safe_click": str(latest.get("next_safe_click", "")),
        "surface_receipt_hash": str(latest.get("surface_receipt_hash", "")),
        "dry_run_default": True,
        "exam_deployment_status": "not_cleared",
        "score_returned": False,
        "grade_returned": False,
    }


def journal_summary(skill_tag: str, entries: list[dict[str, Any]], latest: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "selected_skill_tag": skill_tag,
        "entry_count": len(entries),
        "latest_action_key": str(latest.get("action_key", "")),
        "latest_route": str(latest.get("route", "")),
        "latest_next_safe_click": str(latest.get("next_safe_click", "")),
        "latest_surface_receipt_hash": str(latest.get("surface_receipt_hash", "")),
        "source_anchor_count": int(latest.get("source_anchor_count", 0) or 0),
        "checkpoint_hash_count": int(latest.get("checkpoint_hash_count", 0) or 0),
        "open_operator_confirmation_count": int(latest.get("open_operator_confirmation_count", 0) or 0),
        "help_status": str(latest.get("help_status", "missing")),
        "evidence_preview_status": str(latest.get("evidence_preview_status", "missing")),
        "human_handoff_status": str(latest.get("human_handoff_status", "missing")),
        "resume_decision": decision.get("decision", "continue_current_control_step"),
        "dry_run_default": True,
        "local_writes_requested": False,
        "exam_deployment_status": "not_cleared",
    }


def journal_receipt(summary: dict[str, Any], entries: list[dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "entry_hashes": [entry.get("entry_hash", "") for entry in entries],
        "resume_decision": decision.get("decision", ""),
        "exam_deployment_status": "not_cleared",
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "python_exam_guided_session_playback_journal_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "entry_count": len(entries),
        "not_cleared_receipt": True,
        "dry_run_default": True,
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def effective_skill_tag(selected: str, *artifacts: dict[str, Any]) -> str:
    if str(selected or "").strip():
        return str(selected).strip()
    for artifact in artifacts:
        for path in (
            ("selected_skill_tag",),
            ("control_summary", "selected_skill_tag"),
            ("journal_summary", "selected_skill_tag"),
        ):
            value = nested(artifact, *path)
            if isinstance(value, str) and value:
                return value
    return "python_lists"


def safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_help_profile(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    safe: dict[str, int] = {}
    for key, count in value.items():
        try:
            safe[str(key)] = int(count or 0)
        except (TypeError, ValueError):
            safe[str(key)] = 0
    return safe


def nested(payload: Any, *path: str) -> Any:
    current = payload
    for key in path:
        if not isinstance(current, dict):
            return ""
        current = current.get(key, "")
    return current


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-guided-session-playback-journal")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
