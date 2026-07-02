from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_EVIDENCE_EXPORT_PREVIEW_SCHEMA_VERSION = "unibot-python-exam-evidence-export-preview-v1"
PYTHON_EXAM_EVIDENCE_EXPORT_PREVIEW_ENDPOINT = "/api/unibot/course/python-exam-evidence-export-preview"


def build_python_exam_evidence_export_preview(
    *,
    python_exam_live_control_surface: dict[str, Any] | None = None,
    python_exam_cockpit_flow: dict[str, Any] | None = None,
    python_exam_readiness_console: dict[str, Any] | None = None,
    exam_skill_drilldown: dict[str, Any] | None = None,
    exam_workspace_operator_run: dict[str, Any] | None = None,
    exam_workspace_session_console: dict[str, Any] | None = None,
    notebook_checkpoint: dict[str, Any] | None = None,
    review_chain_integrity_check: dict[str, Any] | None = None,
    timeline_export_review_packet: dict[str, Any] | None = None,
    timeline_export_receipt_journal_summary: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    live_control = python_exam_live_control_surface if isinstance(python_exam_live_control_surface, dict) else {}
    cockpit = python_exam_cockpit_flow if isinstance(python_exam_cockpit_flow, dict) else {}
    readiness = python_exam_readiness_console if isinstance(python_exam_readiness_console, dict) else {}
    drilldown = exam_skill_drilldown if isinstance(exam_skill_drilldown, dict) else {}
    operator = exam_workspace_operator_run if isinstance(exam_workspace_operator_run, dict) else {}
    session = exam_workspace_session_console if isinstance(exam_workspace_session_console, dict) else {}
    checkpoint = notebook_checkpoint if isinstance(notebook_checkpoint, dict) else {}
    chain = review_chain_integrity_check if isinstance(review_chain_integrity_check, dict) else {}
    review = timeline_export_review_packet if isinstance(timeline_export_review_packet, dict) else {}
    journal = timeline_export_receipt_journal_summary if isinstance(timeline_export_receipt_journal_summary, dict) else {}
    skill_tag = effective_skill_tag(selected_skill_tag, live_control, cockpit, readiness, drilldown, session, chain, journal)
    manifest = preview_manifest(
        skill_tag=skill_tag,
        live_control=live_control,
        cockpit=cockpit,
        readiness=readiness,
        drilldown=drilldown,
        operator=operator,
        session=session,
        checkpoint=checkpoint,
        chain=chain,
        review=review,
        journal=journal,
    )
    reviewer_packet = human_review_packet(manifest, review, chain)
    summary = preview_summary(manifest, reviewer_packet)
    payload = {
        "schema_version": PYTHON_EXAM_EVIDENCE_EXPORT_PREVIEW_SCHEMA_VERSION,
        "artifact_type": "python_exam_evidence_export_preview",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Evidence Export Preview. It bundles the selected Python skill's readiness, cockpit "
            "steps, Live Control actions, evidence receipts, A0-A2 help-level profile, open operator confirmations, "
            "review-chain status, notebook checkpoint hash, and receipt-journal summary into a human-reviewable "
            "preview manifest. It is preview/dry-run by default and writes no local export package. Future export "
            "writes require explicit operator confirmation in a separate step. It never returns raw queries, course "
            "raw text, notebook code, local paths, values, solutions, final interpretations, proctoring, AI "
            "detection, automatic assessment, or exam clearance."
        ),
        "selected_skill_tag": skill_tag,
        "preview_summary": summary,
        "preview_manifest": manifest,
        "human_review_packet": reviewer_packet,
        "preview_receipt": preview_receipt(manifest, reviewer_packet),
        "dry_run_default": True,
        "export_preview_only": True,
        "local_export_package_written": False,
        "operator_confirmation_required_for_export_write": True,
        "operator_confirmed_export_write": False,
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; das Evidence Export Preview bleibt not_cleared."
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
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def preview_manifest(
    *,
    skill_tag: str,
    live_control: dict[str, Any],
    cockpit: dict[str, Any],
    readiness: dict[str, Any],
    drilldown: dict[str, Any],
    operator: dict[str, Any],
    session: dict[str, Any],
    checkpoint: dict[str, Any],
    chain: dict[str, Any],
    review: dict[str, Any],
    journal: dict[str, Any],
) -> dict[str, Any]:
    return {
        "manifest_type": "python_exam_evidence_export_preview_manifest",
        "selected_skill_tag": skill_tag,
        "readiness_snapshot": readiness_snapshot(readiness, drilldown),
        "cockpit_steps": cockpit_steps(cockpit),
        "live_control_actions": live_control_actions(live_control),
        "evidence_receipts": evidence_receipts(live_control, cockpit, readiness, operator, session, checkpoint, chain, review, journal),
        "help_level_profile": help_level_profile(live_control, readiness, chain, journal),
        "operator_confirmation_profile": operator_confirmation_profile(live_control, cockpit, readiness, operator, journal),
        "review_chain_status": review_chain_status(chain),
        "notebook_checkpoint": notebook_checkpoint_status(live_control, cockpit, readiness, session, checkpoint),
        "receipt_journal_summary": receipt_journal_summary(journal),
        "timeline_export_review_summary": timeline_export_review_summary(review),
        "dry_run_default": True,
        "export_preview_only": True,
        "local_export_package_written": False,
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
    }


def readiness_snapshot(readiness: dict[str, Any], drilldown: dict[str, Any]) -> dict[str, Any]:
    summary = readiness.get("readiness_summary", {}) if isinstance(readiness.get("readiness_summary"), dict) else {}
    selected = readiness.get("selected_skill_readiness", {}) if isinstance(readiness.get("selected_skill_readiness"), dict) else {}
    drilldown_skill = drilldown.get("selected_skill", {}) if isinstance(drilldown.get("selected_skill"), dict) else {}
    return {
        "status": readiness.get("status", "missing"),
        "selected_skill_tag": first_text(summary.get("selected_skill_tag"), selected.get("skill_tag"), drilldown_skill.get("skill_tag")),
        "skill_ready_for_workspace": bool(summary.get("skill_ready_for_workspace", False)),
        "source_anchored": bool(summary.get("source_anchored", False)),
        "review_chain_pass": bool(summary.get("review_chain_pass", False)),
        "receipt_journal_ready": bool(summary.get("receipt_journal_ready", False)),
        "source_anchor_count": int(selected.get("source_anchor_count", 0) or 0),
        "reviewed_notebook_anchor_count": int(selected.get("reviewed_notebook_anchor_count", 0) or 0),
        "source_card_ids": [str(item) for item in (selected.get("source_card_ids", []) or [])][:8],
        "next_safe_action": summary.get("next_safe_action", selected.get("next_safe_step", "")),
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def cockpit_steps(cockpit: dict[str, Any]) -> list[dict[str, Any]]:
    steps = []
    for item in [step for step in cockpit.get("step_bar", []) if isinstance(step, dict)]:
        steps.append(
            {
                "step_id": str(item.get("step_id", "")),
                "label": str(item.get("label", "")),
                "status": str(item.get("status", "unknown")),
                "source": str(item.get("source", "")),
                "requires_operator_confirmation_for_local_writes": bool(
                    item.get("requires_operator_confirmation_for_local_writes", False)
                ),
                "next_safe_action": str(item.get("next_safe_action", "")),
                "exam_deployment_status": "not_cleared",
                "raw_text_returned": False,
                "notebook_code_returned": False,
                "local_paths_returned": False,
            }
        )
    return steps


def live_control_actions(live_control: dict[str, Any]) -> list[dict[str, Any]]:
    actions = []
    for item in [action for action in live_control.get("control_actions", []) if isinstance(action, dict)]:
        actions.append(
            {
                "safe_action_id": str(item.get("safe_action_id", "")),
                "step_id": str(item.get("step_id", "")),
                "label": str(item.get("label", "")),
                "endpoint": str(item.get("endpoint", "")),
                "status": str(item.get("status", "unknown")),
                "light": str(item.get("light", "grey")),
                "enabled": bool(item.get("enabled", False)),
                "requires_operator_confirmation_for_local_writes": bool(
                    item.get("requires_operator_confirmation_for_local_writes", False)
                ),
                "local_write_confirmation_keys": [str(key) for key in (item.get("local_write_confirmation_keys", []) or [])],
                "dry_run_default": True,
                "exam_deployment_status": "not_cleared",
                "raw_text_returned": False,
                "notebook_code_returned": False,
                "local_paths_returned": False,
            }
        )
    return actions


def evidence_receipts(
    live_control: dict[str, Any],
    cockpit: dict[str, Any],
    readiness: dict[str, Any],
    operator: dict[str, Any],
    session: dict[str, Any],
    checkpoint: dict[str, Any],
    chain: dict[str, Any],
    review: dict[str, Any],
    journal: dict[str, Any],
) -> dict[str, Any]:
    live_receipts = live_control.get("evidence_receipts", {}) if isinstance(live_control.get("evidence_receipts"), dict) else {}
    cockpit_receipts = cockpit.get("evidence_receipts", {}) if isinstance(cockpit.get("evidence_receipts"), dict) else {}
    return {
        "readiness_status": first_text(live_receipts.get("readiness_status"), cockpit_receipts.get("readiness_status"), readiness.get("status"), "missing"),
        "operator_receipt_id": first_text(live_receipts.get("operator_receipt_id"), cockpit_receipts.get("operator_receipt_id"), nested(operator, "dry_run_receipt", "receipt_id")),
        "session_receipt_id": first_text(live_receipts.get("session_receipt_id"), cockpit_receipts.get("session_receipt_id"), nested(session, "session_console_receipt", "receipt_id")),
        "notebook_checkpoint_hash": notebook_checkpoint_hash(live_control, cockpit, readiness, session, checkpoint),
        "review_chain_status": first_text(live_receipts.get("review_chain_status"), cockpit_receipts.get("review_chain_status"), chain.get("status"), "missing"),
        "review_receipt_id": first_text(live_receipts.get("review_receipt_id"), cockpit_receipts.get("review_receipt_id"), nested(review, "local_export_receipt", "receipt_id")),
        "review_receipt_hash": nested(review, "local_export_receipt", "receipt_hash"),
        "receipt_journal_record_count": int(first_number(live_receipts.get("receipt_journal_record_count"), cockpit_receipts.get("receipt_journal_record_count"), journal.get("record_count"), 0)),
        "receipt_journal_accepted_record_count": int(first_number(live_receipts.get("receipt_journal_accepted_record_count"), cockpit_receipts.get("receipt_journal_accepted_record_count"), journal.get("accepted_record_count"), 0)),
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def help_level_profile(
    live_control: dict[str, Any],
    readiness: dict[str, Any],
    chain: dict[str, Any],
    journal: dict[str, Any],
) -> dict[str, Any]:
    live_help = live_control.get("a0_a2_help_status", {}) if isinstance(live_control.get("a0_a2_help_status"), dict) else {}
    readiness_help = readiness.get("a0_a2_help_status", {}) if isinstance(readiness.get("a0_a2_help_status"), dict) else {}
    profile = merge_profiles(
        live_help.get("observed_help_profile", {}),
        readiness_help.get("observed_help_profile", {}),
        journal.get("help_level_profile", {}),
        nested(chain, "chain_integrity_summary", "help_level_profiles", "journal"),
    )
    nonstandard_count = sum(count for level, count in profile.items() if level not in {"A0", "A1", "A2"})
    return {
        "status": "a0_a2_only" if nonstandard_count == 0 else "nonstandard_help_attention",
        "profile": profile,
        "allowed_help_boundary": "A0-A2",
        "effective_help_level": first_text(live_help.get("effective_help_level"), readiness_help.get("recommended_help_level"), "A2"),
        "nonstandard_help_event_count": nonstandard_count,
        "exam_deployment_status": "not_cleared",
    }


def operator_confirmation_profile(
    live_control: dict[str, Any],
    cockpit: dict[str, Any],
    readiness: dict[str, Any],
    operator: dict[str, Any],
    journal: dict[str, Any],
) -> dict[str, Any]:
    live_confirmations = live_control.get("operator_confirmation_status", {}) if isinstance(live_control.get("operator_confirmation_status"), dict) else {}
    cockpit_confirmations = cockpit.get("operator_confirmation_status", {}) if isinstance(cockpit.get("operator_confirmation_status"), dict) else {}
    readiness_confirmations = readiness.get("operator_confirmation_status", {}) if isinstance(readiness.get("operator_confirmation_status"), dict) else {}
    matrix = operator.get("operator_confirmation_matrix", {}) if isinstance(operator.get("operator_confirmation_matrix"), dict) else {}
    open_count = max(
        int(live_confirmations.get("open_operator_confirmation_count", 0) or 0),
        int(cockpit_confirmations.get("open_operator_confirmation_count", 0) or 0),
        int(readiness_confirmations.get("open_operator_confirmation_count", 0) or 0),
        int(journal.get("open_operator_confirmation_count", 0) or 0),
    )
    return {
        "status": "operator_confirmations_open" if open_count else "operator_confirmations_reviewed",
        "open_operator_confirmation_count": open_count,
        "confirmed_local_write_step_count": int(first_number(live_confirmations.get("confirmed_local_write_step_count"), cockpit_confirmations.get("confirmed_local_write_step_count"), matrix.get("confirmed_count"), 0)),
        "open_operator_confirmation_steps": [str(item) for item in (live_confirmations.get("open_operator_confirmation_steps", []) or cockpit_confirmations.get("open_operator_confirmation_steps", []) or [])],
        "local_writes_require_confirmation": True,
        "export_write_requires_future_confirmation": True,
        "dry_run_default": True,
        "exam_deployment_status": "not_cleared",
    }


def review_chain_status(chain: dict[str, Any]) -> dict[str, Any]:
    summary = chain.get("chain_integrity_summary", {}) if isinstance(chain.get("chain_integrity_summary"), dict) else {}
    return {
        "status": chain.get("status", "missing"),
        "issue_count": int(summary.get("issue_count", 0) or 0),
        "checked_link_count": int(summary.get("checked_link_count", 0) or 0),
        "next_safe_action": summary.get("next_safe_action", "Review chain integrity before export preview."),
        "exam_deployment_status": "not_cleared",
    }


def notebook_checkpoint_status(
    live_control: dict[str, Any],
    cockpit: dict[str, Any],
    readiness: dict[str, Any],
    session: dict[str, Any],
    checkpoint: dict[str, Any],
) -> dict[str, Any]:
    checkpoint_hash = notebook_checkpoint_hash(live_control, cockpit, readiness, session, checkpoint)
    return {
        "status": "checkpoint_hash_present" if checkpoint_hash else "checkpoint_hash_missing",
        "notebook_checkpoint_hash": checkpoint_hash,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "exam_deployment_status": "not_cleared",
    }


def receipt_journal_summary(journal: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": journal.get("status", "missing"),
        "record_count": int(journal.get("record_count", 0) or 0),
        "accepted_record_count": int(journal.get("accepted_record_count", 0) or 0),
        "blocked_record_count": int(journal.get("blocked_record_count", 0) or 0),
        "skill_tags": [str(item) for item in (journal.get("skill_tags", []) or [])],
        "event_count": int(journal.get("event_count", 0) or 0),
        "checkpoint_hash_count": int(journal.get("checkpoint_hash_count", 0) or 0),
        "reviewer_question_count": int(journal.get("reviewer_question_count", 0) or 0),
        "help_level_profile": dict(journal.get("help_level_profile", {}) or {}),
        "reflection_statuses": [str(item) for item in (journal.get("reflection_statuses", []) or [])],
        "exam_deployment_status": "not_cleared",
    }


def timeline_export_review_summary(review: dict[str, Any]) -> dict[str, Any]:
    summary = review.get("export_review_summary", {}) if isinstance(review.get("export_review_summary"), dict) else {}
    receipt = review.get("local_export_receipt", {}) if isinstance(review.get("local_export_receipt"), dict) else {}
    return {
        "status": review.get("status", "missing"),
        "event_count": int(summary.get("event_count", 0) or 0),
        "skill_count": int(summary.get("skill_count", 0) or 0),
        "checkpoint_hash_count": int(summary.get("checkpoint_hash_count", 0) or 0),
        "open_operator_confirmation_count": int(summary.get("open_operator_confirmation_count", 0) or 0),
        "review_receipt_id": receipt.get("receipt_id", ""),
        "review_receipt_hash_present": bool(receipt.get("receipt_hash")),
        "exam_deployment_status": "not_cleared",
    }


def human_review_packet(manifest: dict[str, Any], review: dict[str, Any], chain: dict[str, Any]) -> dict[str, Any]:
    review_questions = review.get("human_reviewer_questions", []) if isinstance(review.get("human_reviewer_questions"), list) else []
    questions = [str(item) for item in review_questions][:8]
    if not questions:
        questions = [
            "Do readiness, cockpit, Live Control, review-chain, and receipt-journal evidence agree for this skill?",
            "Does the help-level profile remain within A0-A2?",
            "Are all open operator confirmations visible before any write-capable export step?",
            "Does the notebook checkpoint hash match the human-reviewed notebook checkpoint?",
            "Does every visible status preserve exam_deployment_status not_cleared?",
        ]
    evidence = manifest.get("evidence_receipts", {}) if isinstance(manifest.get("evidence_receipts"), dict) else {}
    return {
        "packet_type": "python_exam_evidence_export_human_review_packet",
        "status": "ready_for_human_review" if preview_manifest_ready(manifest) else "needs_attention_before_human_review",
        "review_questions": questions,
        "review_chain_status": manifest.get("review_chain_status", {}),
        "receipt_ids": {
            "operator_receipt_id": evidence.get("operator_receipt_id", ""),
            "session_receipt_id": evidence.get("session_receipt_id", ""),
            "review_receipt_id": evidence.get("review_receipt_id", ""),
        },
        "chain_issue_count": int(nested(chain, "chain_integrity_summary", "issue_count") or 0),
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def preview_summary(manifest: dict[str, Any], reviewer_packet: dict[str, Any]) -> dict[str, Any]:
    readiness = manifest.get("readiness_snapshot", {}) if isinstance(manifest.get("readiness_snapshot"), dict) else {}
    checkpoint = manifest.get("notebook_checkpoint", {}) if isinstance(manifest.get("notebook_checkpoint"), dict) else {}
    receipts = manifest.get("evidence_receipts", {}) if isinstance(manifest.get("evidence_receipts"), dict) else {}
    confirmations = manifest.get("operator_confirmation_profile", {}) if isinstance(manifest.get("operator_confirmation_profile"), dict) else {}
    help_profile = manifest.get("help_level_profile", {}) if isinstance(manifest.get("help_level_profile"), dict) else {}
    review_chain = manifest.get("review_chain_status", {}) if isinstance(manifest.get("review_chain_status"), dict) else {}
    ready = preview_manifest_ready(manifest)
    return {
        "status": "python_exam_evidence_export_preview_ready" if ready else "python_exam_evidence_export_preview_attention",
        "selected_skill_tag": manifest.get("selected_skill_tag", ""),
        "readiness_status": readiness.get("status", "missing"),
        "skill_ready_for_workspace": bool(readiness.get("skill_ready_for_workspace", False)),
        "cockpit_step_count": len(manifest.get("cockpit_steps", []) or []),
        "live_control_action_count": len(manifest.get("live_control_actions", []) or []),
        "evidence_receipt_count": len([value for value in receipts.values() if isinstance(value, str) and value]),
        "help_status": help_profile.get("status", "missing"),
        "open_operator_confirmation_count": int(confirmations.get("open_operator_confirmation_count", 0) or 0),
        "review_chain_status": review_chain.get("status", "missing"),
        "review_chain_issue_count": int(review_chain.get("issue_count", 0) or 0),
        "notebook_checkpoint_hash_present": bool(checkpoint.get("notebook_checkpoint_hash")),
        "receipt_journal_accepted_record_count": int(nested(manifest, "receipt_journal_summary", "accepted_record_count") or 0),
        "human_review_status": reviewer_packet.get("status", "missing"),
        "dry_run_default": True,
        "export_preview_only": True,
        "local_export_package_written": False,
        "exam_deployment_status": "not_cleared",
        "next_safe_action": (
            "Hand the preview manifest to human review; write no export package until a future explicit confirmation."
            if ready
            else "Resolve preview attention items before relying on the export preview."
        ),
    }


def preview_manifest_ready(manifest: dict[str, Any]) -> bool:
    readiness = manifest.get("readiness_snapshot", {}) if isinstance(manifest.get("readiness_snapshot"), dict) else {}
    checkpoint = manifest.get("notebook_checkpoint", {}) if isinstance(manifest.get("notebook_checkpoint"), dict) else {}
    review_chain = manifest.get("review_chain_status", {}) if isinstance(manifest.get("review_chain_status"), dict) else {}
    journal = manifest.get("receipt_journal_summary", {}) if isinstance(manifest.get("receipt_journal_summary"), dict) else {}
    help_profile = manifest.get("help_level_profile", {}) if isinstance(manifest.get("help_level_profile"), dict) else {}
    return (
        bool(readiness.get("skill_ready_for_workspace", False))
        and bool(checkpoint.get("notebook_checkpoint_hash"))
        and review_chain.get("status") == "review_chain_integrity_pass"
        and int(review_chain.get("issue_count", 0) or 0) == 0
        and int(journal.get("accepted_record_count", 0) or 0) >= 1
        and help_profile.get("status") == "a0_a2_only"
    )


def preview_receipt(manifest: dict[str, Any], reviewer_packet: dict[str, Any]) -> dict[str, Any]:
    seed = {
        "schema_version": PYTHON_EXAM_EVIDENCE_EXPORT_PREVIEW_SCHEMA_VERSION,
        "manifest": manifest,
        "human_review_status": reviewer_packet.get("status", ""),
        "export_preview_only": True,
        "exam_deployment_status": "not_cleared",
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "python_exam_evidence_export_preview_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "export_preview_only": True,
        "local_export_package_written": False,
        "operator_confirmation_required_for_export_write": True,
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def notebook_checkpoint_hash(
    live_control: dict[str, Any],
    cockpit: dict[str, Any],
    readiness: dict[str, Any],
    session: dict[str, Any],
    checkpoint: dict[str, Any],
) -> str:
    return first_text(
        nested(live_control, "evidence_receipts", "notebook_checkpoint_hash"),
        nested(cockpit, "evidence_receipts", "notebook_checkpoint_hash"),
        nested(readiness, "readiness_summary", "latest_notebook_checkpoint_hash"),
        nested(session, "session_console", "notebook_checkpoint", "notebook_work_sha256"),
        checkpoint.get("notebook_work_sha256", ""),
        nested(checkpoint, "notebook_checkpoint", "notebook_work_sha256"),
    )


def next_actions(summary: dict[str, Any]) -> list[str]:
    return [
        summary.get("next_safe_action", "Review the Evidence Export Preview."),
        "Use this preview for human review only; do not claim exam clearance.",
        "Keep export writes for a later slice with explicit operator confirmation.",
        "Keep A0-A2 help, hash-only notebook checkpoints, and not_cleared.",
    ]


def merge_profiles(*profiles: Any) -> dict[str, int]:
    merged: dict[str, int] = {}
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        for level, count in profile.items():
            text = str(level)
            if not text:
                continue
            merged[text] = max(merged.get(text, 0), int(count or 0))
    if not merged:
        merged["A2"] = 1
    return merged


def effective_skill_tag(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            for path in [
                ("selected_skill_tag",),
                ("preview_summary", "selected_skill_tag"),
                ("control_summary", "selected_skill_tag"),
                ("readiness_summary", "selected_skill_tag"),
                ("selected_skill_readiness", "skill_tag"),
                ("selected_skill", "skill_tag"),
                ("session_console", "selected_skill", "skill_tag"),
                ("chain_integrity_summary", "skill_tags"),
                ("skill_tags",),
            ]:
                found = nested(value, *path)
                if isinstance(found, list) and found:
                    return str(found[0])
                if isinstance(found, str) and found:
                    return found
    return "python_skill"


def first_text(*values: Any) -> str:
    for value in values:
        text = str(value or "")
        if text:
            return text
    return ""


def first_number(*values: Any) -> int:
    for value in values:
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def nested(payload: dict[str, Any], *path: str) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return ""
        current = current.get(key, "")
    return current


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-evidence-export-preview")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
