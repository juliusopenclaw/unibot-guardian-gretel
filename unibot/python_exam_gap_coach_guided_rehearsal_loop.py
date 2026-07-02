from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_rehearsal_playback_gap_coach import NEXT_SAFE_ACTIONS


PYTHON_EXAM_GAP_COACH_GUIDED_REHEARSAL_LOOP_SCHEMA_VERSION = "unibot-python-exam-gap-coach-guided-rehearsal-loop-v1"
PYTHON_EXAM_GAP_COACH_GUIDED_REHEARSAL_LOOP_ENDPOINT = "/api/unibot/course/python-exam-gap-coach-guided-rehearsal-loop"

ENDPOINTS = {
    "resolve_missing_artifact": "/api/unibot/course/python-exam-rehearsal-playback-gap-coach",
    "resolve_source_gap": "/api/unibot/course/python-exam-evidence-export-preview",
    "review_operator_confirmation": "/api/unibot/course/python-exam-local-cycle-operator-workspace-card",
    "continue_a0_a2_drill": "/api/unibot/course/python-exam-source-grounded-tutor-drill-pack",
    "ready_to_rehearse_again": "/api/unibot/course/python-exam-full-local-rehearsal-pack",
    "ready_for_human_review_packet": "/api/unibot/course/python-exam-human-handoff-packet",
}


def build_python_exam_gap_coach_guided_rehearsal_loop(
    *,
    python_exam_rehearsal_playback_gap_coach: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    requested_action_key: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    coach = python_exam_rehearsal_playback_gap_coach if isinstance(python_exam_rehearsal_playback_gap_coach, dict) else {}
    skill_tag = effective_skill_tag(selected_skill_tag, coach)
    action_key = safe_action_key(requested_action_key or str(coach.get("next_safe_action_key", "")))
    source = safe_dict(coach.get("source_anchor_metadata"))
    gaps = safe_dict(coach.get("gap_profile"))
    confirmations = safe_dict(coach.get("operator_confirmation_status"))
    help_status = safe_dict(coach.get("a0_a2_help_status"))
    checkpoint = safe_dict(coach.get("notebook_checkpoint_metadata"))
    evidence = safe_dict(coach.get("evidence_playback"))
    steps = [item for item in (coach.get("playback_steps", []) or []) if isinstance(item, dict)]
    guided_step = build_guided_step(
        action_key=action_key,
        skill_tag=skill_tag,
        source=source,
        gaps=gaps,
        confirmations=confirmations,
        help_status=help_status,
        checkpoint=checkpoint,
        evidence=evidence,
        steps=steps,
    )
    summary = guided_loop_summary(coach, guided_step, action_key, skill_tag, gaps, source, confirmations, help_status, checkpoint)
    payload = {
        "schema_version": PYTHON_EXAM_GAP_COACH_GUIDED_REHEARSAL_LOOP_SCHEMA_VERSION,
        "artifact_type": "python_exam_gap_coach_guided_rehearsal_loop",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_gap_coach_guided_rehearsal_loop_ready" if coach else "python_exam_gap_coach_guided_rehearsal_loop_attention",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Gap-Coach Guided Rehearsal Loop. It consumes the Rehearsal Playback + Gap Coach and "
            "prepares exactly one dry-run next-step card for the current next_safe_action_key. It can request a "
            "missing metadata artifact, review Source-Card/checkpoint coverage, show open operator confirmation "
            "review cards, prepare an A0-A2-only drill, prepare another full dry-run rehearsal, or surface the "
            "Human Review Packet metadata. It performs no local writes, starts no local execution, and never "
            "returns raw queries, course raw text, notebook code, local paths, values, solutions, final "
            "interpretations, scores, rankings, grades, proctoring, AI detection, automatic grading, or exam "
            "clearance claims."
        ),
        "guided_loop_endpoint": PYTHON_EXAM_GAP_COACH_GUIDED_REHEARSAL_LOOP_ENDPOINT,
        "selected_skill_tag": skill_tag,
        "requested_action_key": action_key,
        "guided_loop_summary": summary,
        "guided_step": guided_step,
        "safe_prefill": guided_step.get("safe_prefill", {}),
        "operator_confirmation_review_cards": guided_step.get("operator_confirmation_review_cards", []),
        "source_checkpoint_review_cards": guided_step.get("source_checkpoint_review_cards", []),
        "missing_artifact_request_cards": guided_step.get("missing_artifact_request_cards", []),
        "a0_a2_drill_card": guided_step.get("a0_a2_drill_card", {}),
        "human_review_packet_card": guided_step.get("human_review_packet_card", {}),
        "guided_loop_receipt": guided_loop_receipt(summary, guided_step),
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "operator_confirmation_required_for_local_write": True,
        "operator_confirmations": {
            "checkpoint_store": False,
            "progress_journal_append": False,
            "workspace_local_write": False,
            "export_write": False,
            "human_handoff_write": False,
        },
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Guided Rehearsal Loop bleibt not_cleared."
        ),
        "next_actions": [
            next_safe_action_text(action_key),
            f"Use {guided_step.get('route', 'metadata_review')} as dry-run preparation only.",
            "Keep local writes behind explicit operator confirmation and keep exam_deployment_status not_cleared.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def build_guided_step(
    *,
    action_key: str,
    skill_tag: str,
    source: dict[str, Any],
    gaps: dict[str, Any],
    confirmations: dict[str, Any],
    help_status: dict[str, Any],
    checkpoint: dict[str, Any],
    evidence: dict[str, Any],
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    if action_key == "resolve_missing_artifact":
        return missing_artifact_step(skill_tag, gaps, steps)
    if action_key == "resolve_source_gap":
        return source_gap_step(skill_tag, source, checkpoint)
    if action_key == "review_operator_confirmation":
        return operator_confirmation_step(skill_tag, confirmations, steps, source, checkpoint)
    if action_key == "continue_a0_a2_drill":
        return a0_a2_drill_step(skill_tag, source, checkpoint, help_status)
    if action_key == "ready_for_human_review_packet":
        return human_review_packet_step(skill_tag, evidence, source, checkpoint)
    return rehearse_again_step(skill_tag, source, checkpoint, evidence)


def missing_artifact_step(skill_tag: str, gaps: dict[str, Any], steps: list[dict[str, Any]]) -> dict[str, Any]:
    requested = [str(item) for item in (gaps.get("missing_artifact_step_ids", []) or [])]
    requested += [str(item) for item in (gaps.get("attention_step_ids", []) or [])]
    if gaps.get("pack_missing"):
        requested.insert(0, "full_local_rehearsal_pack")
    cards = []
    for step_id in unique_values(requested or ["full_local_rehearsal_pack"]):
        step = first_step(steps, step_id)
        cards.append(
            safe_card(
                {
                    "card_id": f"request_{safe_id(step_id)}",
                    "step_id": step_id,
                    "artifact_type": str(step.get("artifact_type", "missing")),
                    "current_status": str(step.get("status", "missing")),
                    "artifact_hash": str(step.get("artifact_hash", "")),
                    "endpoint": endpoint_for_step(step_id),
                    "instruction": "Rebuild or review this metadata artifact before continuing.",
                }
            )
        )
    return base_step("resolve_missing_artifact", "metadata_artifact_repair", ENDPOINTS["resolve_missing_artifact"], skill_tag, True, {"requested_artifact_step_ids": [card["step_id"] for card in cards]}, missing_artifact_request_cards=cards)


def source_gap_step(skill_tag: str, source: dict[str, Any], checkpoint: dict[str, Any]) -> dict[str, Any]:
    cards = [
        safe_card(
            {
                "card_id": "review_source_cards",
                "status": "source_anchor_present" if int(source.get("source_anchor_count", 0) or 0) > 0 else "source_anchor_missing",
                "source_card_ids": [str(item) for item in (source.get("source_card_ids", []) or [])][:8],
                "source_anchor_count": int(source.get("source_anchor_count", 0) or 0),
                "instruction": "Review Source-Card anchors for this skill before continuing.",
            }
        ),
        safe_card(
            {
                "card_id": "review_checkpoint_hash",
                "status": str(checkpoint.get("status", "checkpoint_hash_missing")),
                "latest_notebook_checkpoint_hash": str(checkpoint.get("latest_notebook_checkpoint_hash", "")),
                "checkpoint_hash_count": int(checkpoint.get("checkpoint_hash_count", 0) or 0),
                "instruction": "Review notebook checkpoint hashes only; do not expose notebook code.",
            }
        ),
    ]
    return base_step("resolve_source_gap", "source_checkpoint_review", ENDPOINTS["resolve_source_gap"], skill_tag, True, {"source_card_ids": cards[0]["source_card_ids"], "checkpoint_hash_count": cards[1]["checkpoint_hash_count"]}, source_checkpoint_review_cards=cards)


def operator_confirmation_step(skill_tag: str, confirmations: dict[str, Any], steps: list[dict[str, Any]], source: dict[str, Any], checkpoint: dict[str, Any]) -> dict[str, Any]:
    open_count = int(confirmations.get("open_operator_confirmation_count", 0) or 0)
    candidates = [item for item in steps if item.get("operator_confirmation_required_for_local_write") is True]
    cards = []
    for index, step in enumerate((candidates or [{"step_id": "operator_confirmation_review"}])[: max(open_count, 1)]):
        cards.append(
            safe_card(
                {
                    "card_id": f"operator_confirmation_{index + 1}",
                    "step_id": str(step.get("step_id", f"confirmation_{index + 1}")),
                    "current_status": str(step.get("status", "open_confirmation")),
                    "artifact_hash": str(step.get("artifact_hash", "")),
                    "operator_confirmed": False,
                    "instruction": "Human operator reviews this confirmation before local write-capable steps.",
                }
            )
        )
    return base_step(
        "review_operator_confirmation",
        "operator_confirmation_review",
        ENDPOINTS["review_operator_confirmation"],
        skill_tag,
        True,
        {
            "open_operator_confirmation_count": open_count,
            "source_anchor_count": int(source.get("source_anchor_count", 0) or 0),
            "checkpoint_hash_count": int(checkpoint.get("checkpoint_hash_count", 0) or 0),
            "operator_confirmations_default": "all_false_dry_run",
        },
        operator_confirmation_review_cards=cards,
    )


def a0_a2_drill_step(skill_tag: str, source: dict[str, Any], checkpoint: dict[str, Any], help_status: dict[str, Any]) -> dict[str, Any]:
    card = safe_card(
        {
            "card_id": "continue_a0_a2_drill",
            "selected_skill_tag": skill_tag,
            "allowed_help_levels": ["A0", "A1", "A2"],
            "requested_help_level": "A2",
            "source_card_ids": [str(item) for item in (source.get("source_card_ids", []) or [])][:8],
            "source_anchor_count": int(source.get("source_anchor_count", 0) or 0),
            "latest_notebook_checkpoint_hash": str(checkpoint.get("latest_notebook_checkpoint_hash", "")),
            "current_help_profile": safe_help_profile(help_status.get("profile")),
            "instruction": "Prepare an A0-A2-only drill; no solutions, values, full code, or final interpretation.",
        }
    )
    return base_step("continue_a0_a2_drill", "a0_a2_drill", ENDPOINTS["continue_a0_a2_drill"], skill_tag, True, {"requested_help_level": "A2", "source_card_ids": card["source_card_ids"], "checkpoint_hash": card["latest_notebook_checkpoint_hash"]}, a0_a2_drill_card=card)


def rehearse_again_step(skill_tag: str, source: dict[str, Any], checkpoint: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    return base_step("ready_to_rehearse_again", "full_rehearsal_dry_run", ENDPOINTS["ready_to_rehearse_again"], skill_tag, True, {"source_card_ids": [str(item) for item in (source.get("source_card_ids", []) or [])][:8], "checkpoint_hash": str(checkpoint.get("latest_notebook_checkpoint_hash", "")), "evidence_preview_receipt_id": str(evidence.get("evidence_preview_receipt_id", ""))})


def human_review_packet_step(skill_tag: str, evidence: dict[str, Any], source: dict[str, Any], checkpoint: dict[str, Any]) -> dict[str, Any]:
    card = safe_card(
        {
            "card_id": "human_review_packet",
            "selected_skill_tag": skill_tag,
            "endpoint": ENDPOINTS["ready_for_human_review_packet"],
            "human_handoff_status": str(evidence.get("human_handoff_status", "missing")),
            "human_handoff_markdown_hash": str(evidence.get("human_handoff_markdown_hash", "")),
            "evidence_preview_receipt_id": str(evidence.get("evidence_preview_receipt_id", "")),
            "source_anchor_count": int(source.get("source_anchor_count", 0) or 0),
            "checkpoint_hash_count": int(checkpoint.get("checkpoint_hash_count", 0) or 0),
            "instruction": "Surface metadata-only Human Review Packet state; do not claim exam clearance.",
        }
    )
    return base_step("ready_for_human_review_packet", "human_review_packet", ENDPOINTS["ready_for_human_review_packet"], skill_tag, bool(card["human_handoff_markdown_hash"]), {"human_handoff_markdown_hash": card["human_handoff_markdown_hash"], "evidence_preview_receipt_id": card["evidence_preview_receipt_id"]}, human_review_packet_card=card)


def base_step(action_key: str, route: str, endpoint: str, skill_tag: str, ready: bool, safe_prefill: dict[str, Any], **extra: Any) -> dict[str, Any]:
    prefill = {
        "status": "guided_rehearsal_prefill_ready" if ready else "guided_rehearsal_prefill_attention",
        "endpoint": endpoint,
        "method": "POST",
        "selected_skill_tag": skill_tag,
        "action_key": action_key,
        "route": route,
        "dry_run_default": True,
        "operator_confirmations_default": "all_false_dry_run",
        "raw_query_included": False,
        "raw_cell_included": False,
        "raw_source_text_included": False,
        "notebook_code_included": False,
        "local_paths_returned": False,
        "exam_deployment_status": "not_cleared",
    }
    prefill.update(safe_prefill)
    prefill["prefill_hash"] = sha256_text(json.dumps(prefill, sort_keys=True, ensure_ascii=False))
    step = {
        "status": "guided_rehearsal_step_ready" if ready else "guided_rehearsal_step_attention",
        "action_key": action_key,
        "route": route,
        "endpoint": endpoint,
        "method": "POST",
        "selected_skill_tag": skill_tag,
        "ready": ready,
        "safe_prefill": prefill,
        "dry_run_default": True,
        "local_writes_requested": False,
        "operator_confirmation_required_for_local_write": True,
        "exam_deployment_status": "not_cleared",
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
        "grade_returned": False,
    }
    step.update(extra)
    return step


def safe_card(card: dict[str, Any]) -> dict[str, Any]:
    card.update(
        {
            "method": card.get("method", "POST"),
            "dry_run_default": True,
            "exam_deployment_status": "not_cleared",
            "raw_query_returned": False,
            "raw_text_returned": False,
            "raw_cell_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
            "solutions_returned": False,
            "final_interpretations_returned": False,
        }
    )
    return card


def guided_loop_summary(coach: dict[str, Any], guided_step: dict[str, Any], action_key: str, skill_tag: str, gaps: dict[str, Any], source: dict[str, Any], confirmations: dict[str, Any], help_status: dict[str, Any], checkpoint: dict[str, Any]) -> dict[str, Any]:
    return {
        "selected_skill_tag": skill_tag,
        "coach_status": str(coach.get("status", "missing")),
        "next_safe_action_key": action_key,
        "route": guided_step.get("route", ""),
        "endpoint": guided_step.get("endpoint", ""),
        "guided_step_status": guided_step.get("status", "missing"),
        "ready": bool(guided_step.get("ready", False)),
        "missing_or_attention_count": int(gaps.get("missing_or_attention_count", 0) or 0),
        "source_anchor_count": int(source.get("source_anchor_count", 0) or 0),
        "open_operator_confirmation_count": int(confirmations.get("open_operator_confirmation_count", 0) or 0),
        "help_status": str(help_status.get("status", "missing")),
        "checkpoint_hash_count": int(checkpoint.get("checkpoint_hash_count", 0) or 0),
        "a0_a2_only": True,
        "dry_run_default": True,
        "local_writes_requested": False,
        "exam_deployment_status": "not_cleared",
        "next_safe_action": next_safe_action_text(action_key),
    }


def guided_loop_receipt(summary: dict[str, Any], step: dict[str, Any]) -> dict[str, Any]:
    receipt_hash = sha256_text(json.dumps({"summary": summary, "step": step}, sort_keys=True, ensure_ascii=False))
    return {
        "status": "python_exam_gap_coach_guided_rehearsal_loop_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "not_cleared_receipt": True,
        "dry_run_default": True,
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def next_safe_action_text(action_key: str) -> str:
    return {
        "resolve_missing_artifact": "Rebuild or review the missing metadata artifact, then rerun the Gap Coach.",
        "resolve_source_gap": "Review Source-Card anchors and notebook checkpoint hashes before continuing.",
        "review_operator_confirmation": "Review open operator confirmation cards before local write-capable steps.",
        "continue_a0_a2_drill": "Prepare the next A0-A2-only drill for this skill.",
        "ready_to_rehearse_again": "Prepare another full dry-run rehearsal for this skill.",
        "ready_for_human_review_packet": "Surface the Human Review Packet metadata for human review; do not claim exam clearance.",
    }.get(action_key, "Review the Gap Coach output before continuing.")


def endpoint_for_step(step_id: str) -> str:
    return {
        "full_local_rehearsal_pack": ENDPOINTS["ready_to_rehearse_again"],
        "skill_selection": "/api/unibot/course/exam-skill-drilldown",
        "local_cycle_readiness_review": "/api/unibot/course/python-exam-local-cycle-readiness-review",
        "local_cycle_readiness_handoff": "/api/unibot/course/python-exam-local-cycle-readiness-handoff",
        "local_cycle_operator_workspace_card": ENDPOINTS["review_operator_confirmation"],
        "local_cycle_chain_snapshot": "/api/unibot/course/python-exam-local-cycle-chain-snapshot",
        "exam_workspace_operator_dry_run": "/api/unibot/exam-workspace/operator-run",
        "session_console": "/api/unibot/exam-workspace/session-console",
        "run_history": "/api/unibot/exam-workspace/run-history-export-review",
        "exam_run_packet": "/api/unibot/course/exam-run-packet",
        "exam_packet_timeline": "/api/unibot/course/exam-packet-timeline",
        "evidence_export_preview": ENDPOINTS["resolve_source_gap"],
        "human_handoff_packet": ENDPOINTS["ready_for_human_review_packet"],
    }.get(step_id, ENDPOINTS["resolve_missing_artifact"])


def effective_skill_tag(selected: str, coach: dict[str, Any]) -> str:
    if str(selected or "").strip():
        return str(selected).strip()
    for path in (("selected_skill_tag",), ("playback_summary", "selected_skill_tag")):
        value = nested(coach, *path)
        if isinstance(value, str) and value:
            return value
    return "python_lists"


def safe_action_key(action_key: str) -> str:
    value = str(action_key or "").strip()
    return value if value in NEXT_SAFE_ACTIONS else "resolve_missing_artifact"


def first_step(steps: list[dict[str, Any]], step_id: str) -> dict[str, Any]:
    for step in steps:
        if step.get("step_id") == step_id:
            return step
    return {}


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


def unique_values(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return result


def safe_id(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in str(value or ""))
    return safe or "artifact"


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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-gap-coach-guided-rehearsal-loop")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
