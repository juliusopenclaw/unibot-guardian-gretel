from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_REHEARSAL_PLAYBACK_GAP_COACH_SCHEMA_VERSION = "unibot-python-exam-rehearsal-playback-gap-coach-v1"
PYTHON_EXAM_REHEARSAL_PLAYBACK_GAP_COACH_ENDPOINT = "/api/unibot/course/python-exam-rehearsal-playback-gap-coach"

NEXT_SAFE_ACTIONS = {
    "ready_to_rehearse_again",
    "resolve_missing_artifact",
    "resolve_source_gap",
    "review_operator_confirmation",
    "continue_a0_a2_drill",
    "ready_for_human_review_packet",
}


def build_python_exam_rehearsal_playback_gap_coach(
    *,
    python_exam_full_local_rehearsal_pack: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    pack = python_exam_full_local_rehearsal_pack if isinstance(python_exam_full_local_rehearsal_pack, dict) else {}
    skill_tag = effective_skill_tag(selected_skill_tag, pack)
    steps = safe_steps(pack)
    source = safe_dict(pack.get("source_anchor_metadata"))
    confirmations = safe_dict(pack.get("operator_confirmation_status"))
    help_status = safe_dict(pack.get("a0_a2_help_status"))
    chain = safe_dict(pack.get("evidence_chain"))
    summary = safe_dict(pack.get("rehearsal_summary"))
    notebook = notebook_checkpoint_metadata(pack, summary, chain)
    gaps = gap_profile(
        pack=pack,
        steps=steps,
        source=source,
        confirmations=confirmations,
        help_status=help_status,
        notebook=notebook,
        chain=chain,
        summary=summary,
    )
    action = next_safe_action(gaps)
    payload = {
        "schema_version": PYTHON_EXAM_REHEARSAL_PLAYBACK_GAP_COACH_SCHEMA_VERSION,
        "artifact_type": "python_exam_rehearsal_playback_gap_coach",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_rehearsal_playback_gap_coach_ready" if pack else "python_exam_rehearsal_playback_gap_coach_attention",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Rehearsal Playback + Gap Coach. It replays the latest Full Local Rehearsal Pack for one "
            "Python exam skill and derives exactly one safe next learning or review action from metadata only. It "
            "summarizes rehearsal step status, missing artifacts, Source-Card anchor coverage, open operator "
            "confirmations, A0-A2 help profile, notebook checkpoint hashes, Evidence Preview status, and Human "
            "Handoff status. It never executes, writes, scores, ranks, grades, proctors, detects AI use, returns "
            "raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, "
            "or claims exam clearance."
        ),
        "selected_skill_tag": skill_tag,
        "playback_summary": playback_summary(pack, summary, steps, source, confirmations, help_status, notebook, action),
        "gap_profile": gaps,
        "next_safe_action_key": action,
        "next_safe_action": next_safe_action_text(action),
        "playback_steps": playback_steps(steps),
        "source_anchor_metadata": {
            "source_card_ids": [str(item) for item in (source.get("source_card_ids", []) or [])][:8],
            "source_anchor_count": int(source.get("source_anchor_count", 0) or 0),
            "source_anchored": bool(source.get("source_anchored", False)),
            "exam_deployment_status": "not_cleared",
            "raw_text_returned": False,
            "local_paths_returned": False,
        },
        "operator_confirmation_status": {
            "open_operator_confirmation_count": int(confirmations.get("open_operator_confirmation_count", 0) or 0),
            "confirmed_count": int(confirmations.get("confirmed_count", 0) or 0),
            "write_step_count": int(confirmations.get("write_step_count", 0) or 0),
            "local_writes_require_confirmation": True,
            "dry_run_default": True,
            "exam_deployment_status": "not_cleared",
        },
        "a0_a2_help_status": {
            "status": str(help_status.get("status", "missing")),
            "profile": safe_help_profile(help_status.get("profile")),
            "allowed_help_boundary": "A0-A2",
            "nonstandard_help_event_count": int(help_status.get("nonstandard_help_event_count", 0) or 0),
            "exam_deployment_status": "not_cleared",
        },
        "notebook_checkpoint_metadata": notebook,
        "evidence_playback": {
            "exam_run_packet_receipt_id": str(chain.get("exam_run_packet_receipt_id", "")),
            "exam_packet_timeline_receipt_id": str(chain.get("exam_packet_timeline_receipt_id", "")),
            "evidence_preview_receipt_id": str(chain.get("evidence_preview_receipt_id", "")),
            "human_handoff_markdown_hash": str(chain.get("human_handoff_markdown_hash", "")),
            "evidence_preview_status": str(summary.get("evidence_preview_status", "missing")),
            "human_handoff_status": str(summary.get("human_handoff_status", "missing")),
            "exam_deployment_status": "not_cleared",
            "raw_text_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
        },
        "playback_receipt": playback_receipt(skill_tag, gaps, action, notebook, chain),
        "dry_run_default": True,
        "local_writes_executed_by_gap_coach": False,
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
        "next_actions": [
            next_safe_action_text(action),
            "Use the playback as a metadata-only learning/review compass; keep A0-A2 and dry-run.",
            "Keep exam_deployment_status not_cleared and real exam clearance outside UniBot.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_steps(pack: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in pack.get("rehearsal_steps", []) if isinstance(item, dict)]


def playback_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    safe = []
    for item in steps:
        safe.append(
            {
                "step_id": str(item.get("step_id", "")),
                "artifact_type": str(item.get("artifact_type", "")),
                "status": str(item.get("status", "missing")),
                "step_status": str(item.get("step_status", "missing")),
                "artifact_hash": str(item.get("artifact_hash", "")),
                "next_safe_action": str(item.get("next_safe_action", "")),
                "operator_confirmation_required_for_local_write": bool(
                    item.get("operator_confirmation_required_for_local_write", False)
                ),
                "exam_deployment_status": "not_cleared",
                "raw_text_returned": False,
                "notebook_code_returned": False,
                "local_paths_returned": False,
            }
        )
    return safe


def gap_profile(
    *,
    pack: dict[str, Any],
    steps: list[dict[str, Any]],
    source: dict[str, Any],
    confirmations: dict[str, Any],
    help_status: dict[str, Any],
    notebook: dict[str, Any],
    chain: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, Any]:
    missing = [str(item.get("step_id", "")) for item in steps if item.get("step_status") == "missing"]
    attention = [str(item.get("step_id", "")) for item in steps if item.get("step_status") == "attention"]
    source_gap = not source.get("source_anchored") or int(source.get("source_anchor_count", 0) or 0) <= 0
    open_confirmations = int(confirmations.get("open_operator_confirmation_count", 0) or 0)
    nonstandard_help = int(help_status.get("nonstandard_help_event_count", 0) or 0)
    help_missing = help_status.get("status") != "a0_a2_only"
    checkpoint_missing = int(notebook.get("checkpoint_hash_count", 0) or 0) <= 0
    evidence_missing = not chain.get("evidence_preview_receipt_id") or summary.get("evidence_preview_status") != "python_exam_evidence_export_preview_ready"
    handoff_missing = not chain.get("human_handoff_markdown_hash") or summary.get("human_handoff_status") != "python_exam_human_handoff_packet_ready"
    pack_missing = not bool(pack)
    return {
        "pack_missing": pack_missing,
        "missing_artifact_step_ids": missing,
        "attention_step_ids": attention,
        "missing_or_attention_count": len(missing) + len(attention) + (1 if pack_missing else 0),
        "source_gap": bool(source_gap),
        "source_anchor_count": int(source.get("source_anchor_count", 0) or 0),
        "source_card_count": len(source.get("source_card_ids", []) or []),
        "open_operator_confirmation_count": open_confirmations,
        "operator_confirmation_gap": open_confirmations > 0,
        "a0_a2_profile_gap": bool(nonstandard_help or help_missing),
        "nonstandard_help_event_count": nonstandard_help,
        "notebook_checkpoint_gap": checkpoint_missing,
        "evidence_preview_gap": bool(evidence_missing),
        "human_handoff_gap": bool(handoff_missing),
        "ready_for_human_review_packet": not any(
            [
                pack_missing,
                missing,
                attention,
                source_gap,
                open_confirmations > 0,
                nonstandard_help,
                help_missing,
                checkpoint_missing,
                evidence_missing,
                handoff_missing,
            ]
        ),
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def next_safe_action(gaps: dict[str, Any]) -> str:
    if gaps.get("pack_missing") or gaps.get("missing_artifact_step_ids") or gaps.get("attention_step_ids"):
        return "resolve_missing_artifact"
    if gaps.get("source_gap") or gaps.get("notebook_checkpoint_gap"):
        return "resolve_source_gap"
    if gaps.get("operator_confirmation_gap"):
        return "review_operator_confirmation"
    if gaps.get("a0_a2_profile_gap"):
        return "continue_a0_a2_drill"
    if gaps.get("ready_for_human_review_packet"):
        return "ready_for_human_review_packet"
    return "ready_to_rehearse_again"


def next_safe_action_text(action: str) -> str:
    return {
        "ready_to_rehearse_again": "Run the next dry-run rehearsal for this skill after human review of the current metadata.",
        "resolve_missing_artifact": "Resolve missing or attention rehearsal artifacts before using this playback.",
        "resolve_source_gap": "Review Source-Card anchors and notebook checkpoint hashes before continuing.",
        "review_operator_confirmation": "Review open operator confirmations before any local write-capable step.",
        "continue_a0_a2_drill": "Continue an A0-A2-only drill for this skill; do not request solutions or final interpretations.",
        "ready_for_human_review_packet": "Hand the metadata-only packet to a human reviewer; do not claim exam clearance.",
    }.get(action, "Review the playback gaps before continuing.")


def playback_summary(
    pack: dict[str, Any],
    summary: dict[str, Any],
    steps: list[dict[str, Any]],
    source: dict[str, Any],
    confirmations: dict[str, Any],
    help_status: dict[str, Any],
    notebook: dict[str, Any],
    action: str,
) -> dict[str, Any]:
    return {
        "status": "playback_ready" if pack else "playback_attention",
        "selected_skill_tag": effective_skill_tag("", pack),
        "last_rehearsal_status": str(pack.get("status", "missing")),
        "step_count": int(summary.get("step_count", len(steps)) or len(steps)),
        "ready_step_count": int(summary.get("ready_step_count", 0) or 0),
        "missing_step_count": int(summary.get("missing_step_count", 0) or 0),
        "attention_step_count": int(summary.get("attention_step_count", 0) or 0),
        "source_anchor_count": int(source.get("source_anchor_count", 0) or 0),
        "open_operator_confirmation_count": int(confirmations.get("open_operator_confirmation_count", 0) or 0),
        "help_status": str(help_status.get("status", "missing")),
        "checkpoint_hash_count": int(notebook.get("checkpoint_hash_count", 0) or 0),
        "evidence_preview_status": str(summary.get("evidence_preview_status", "missing")),
        "human_handoff_status": str(summary.get("human_handoff_status", "missing")),
        "next_safe_action_key": action,
        "next_safe_action": next_safe_action_text(action),
        "dry_run_default": True,
        "exam_deployment_status": "not_cleared",
    }


def notebook_checkpoint_metadata(pack: dict[str, Any], summary: dict[str, Any], chain: dict[str, Any]) -> dict[str, Any]:
    hashes = unique_hashes(
        nested(pack, "notebook_checkpoint_metadata", "checkpoint_hashes"),
        nested(pack, "notebook_checkpoint_metadata", "latest_notebook_checkpoint_hash"),
        nested(pack, "source_anchor_metadata", "notebook_checkpoint_hash"),
        nested(pack, "a0_a2_help_status", "latest_notebook_checkpoint_hash"),
        nested(chain, "notebook_checkpoint_hash"),
        nested(summary, "latest_notebook_checkpoint_hash"),
    )
    return {
        "status": "checkpoint_hash_present" if hashes else "checkpoint_hash_missing",
        "latest_notebook_checkpoint_hash": hashes[0] if hashes else "",
        "checkpoint_hashes": hashes[:4],
        "checkpoint_hash_count": len(hashes[:4]),
        "exam_deployment_status": "not_cleared",
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def playback_receipt(skill_tag: str, gaps: dict[str, Any], action: str, notebook: dict[str, Any], chain: dict[str, Any]) -> dict[str, Any]:
    seed = {
        "schema_version": PYTHON_EXAM_REHEARSAL_PLAYBACK_GAP_COACH_SCHEMA_VERSION,
        "selected_skill_tag": skill_tag,
        "gap_profile": gaps,
        "next_safe_action_key": action,
        "checkpoint_hashes": notebook.get("checkpoint_hashes", []),
        "evidence_preview_receipt_id": chain.get("evidence_preview_receipt_id", ""),
        "human_handoff_markdown_hash": chain.get("human_handoff_markdown_hash", ""),
        "exam_deployment_status": "not_cleared",
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "python_exam_rehearsal_playback_gap_coach_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "not_cleared_receipt": True,
        "dry_run_default": True,
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def effective_skill_tag(selected: str, pack: dict[str, Any]) -> str:
    if str(selected or "").strip():
        return str(selected).strip()
    for path in (
        ("selected_skill_tag",),
        ("rehearsal_summary", "selected_skill_tag"),
        ("playback_summary", "selected_skill_tag"),
    ):
        value = nested(pack, *path)
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


def unique_hashes(*values: Any) -> list[str]:
    result: list[str] = []
    for value in values:
        candidates = value if isinstance(value, list) else [value]
        for candidate in candidates:
            text = str(candidate or "").strip()
            if text and text not in result:
                result.append(text)
    return result


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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-rehearsal-playback-gap-coach")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
