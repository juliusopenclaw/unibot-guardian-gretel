from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .exam_workspace_run_history import build_exam_workspace_run_history_export_review
from .exam_workspace_session_console import (
    operator_summary,
    session_console_markdown,
    session_console_receipt,
    session_console_status,
    session_console_view,
)
from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_cockpit_flow import build_python_exam_cockpit_flow
from .python_exam_confirmed_local_export_draft import build_python_exam_confirmed_local_export_draft
from .python_exam_draft_package_review_console import build_python_exam_draft_package_review_console
from .python_exam_evidence_export_preview import build_python_exam_evidence_export_preview
from .python_exam_human_handoff_packet import build_python_exam_human_handoff_packet
from .python_exam_live_control_surface import build_python_exam_live_control_surface
from .skill_to_workspace_live_flow import build_skill_to_workspace_live_flow


SKILL_TO_WORKSPACE_SESSION_CARRYOVER_SCHEMA_VERSION = "unibot-skill-to-workspace-session-carryover-v1"
SKILL_TO_WORKSPACE_SESSION_CARRYOVER_ENDPOINT = "/api/unibot/course/skill-to-workspace-session-carryover"


def build_skill_to_workspace_session_carryover(
    *,
    skill_to_workspace_live_flow: dict[str, Any] | None = None,
    review_chain_integrity_check: dict[str, Any] | None = None,
    timeline_export_review_packet: dict[str, Any] | None = None,
    timeline_export_receipt_journal_summary: dict[str, Any] | None = None,
    course_id: str = DEFAULT_COURSE_ID,
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
    ledger_path: str | Path | None = None,
    checkpoint_journal_path: str | Path | None = None,
    focus_query: str = "",
    selected_skill_tag: str = "",
    requested_help_level: str = "A2",
    exam_status: str = "strict",
    student_reflection: str = "",
    study_receipt: dict[str, Any] | None = None,
    notebook_checkpoint: dict[str, Any] | None = None,
    cell_source: str = "",
    cell_index: int = 0,
    cell_id: str = "",
    cell_type: str = "code",
    repeat_run_index: int = 1,
    previous_console_receipts: list[dict[str, Any]] | None = None,
    operator_confirmed_checkpoint_store: bool = False,
    operator_confirmed_exam_workspace_run: bool = False,
    operator_confirmed_manifest_apply: bool = False,
    operator_confirmed_tutor_index_build: bool = False,
    operator_confirmed_help_ledger_append: bool = False,
    operator_confirmed_exam_ledger_append: bool = False,
    public_safe: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    live_flow = skill_to_workspace_live_flow if isinstance(skill_to_workspace_live_flow, dict) else {}
    if not live_flow:
        live_flow = build_skill_to_workspace_live_flow(
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
            ledger_path=ledger_path,
            checkpoint_journal_path=checkpoint_journal_path,
            focus_query=focus_query,
            selected_skill_tag=selected_skill_tag,
            requested_help_level=requested_help_level,
            exam_status=exam_status,
            student_reflection=student_reflection,
            study_receipt=study_receipt,
            notebook_checkpoint=notebook_checkpoint,
            cell_source=cell_source,
            cell_index=cell_index,
            cell_id=cell_id,
            cell_type=cell_type,
            operator_confirmed_checkpoint_store=operator_confirmed_checkpoint_store,
            operator_confirmed_exam_workspace_run=operator_confirmed_exam_workspace_run,
            operator_confirmed_manifest_apply=operator_confirmed_manifest_apply,
            operator_confirmed_tutor_index_build=operator_confirmed_tutor_index_build,
            operator_confirmed_help_ledger_append=operator_confirmed_help_ledger_append,
            operator_confirmed_exam_ledger_append=operator_confirmed_exam_ledger_append,
            public_safe=public_safe,
        )
    operator = live_flow.get("operator_dry_run", {}) if isinstance(live_flow.get("operator_dry_run"), dict) else {}
    session = build_session_from_operator(
        course_id=safe_id,
        operator=operator,
        repeat_run_index=repeat_run_index,
        previous_console_receipts=previous_console_receipts or [],
        public_safe=public_safe,
    )
    run_history = build_exam_workspace_run_history_export_review(
        course_id=safe_id,
        console_reports=[session],
        console_receipts=[session.get("session_console_receipt", {})],
        build_current_console=False,
        public_safe=public_safe,
    )
    chain = review_chain_integrity_check if isinstance(review_chain_integrity_check, dict) else default_review_chain(live_flow, session)
    review = timeline_export_review_packet if isinstance(timeline_export_review_packet, dict) else default_timeline_export_review(run_history)
    journal = (
        timeline_export_receipt_journal_summary
        if isinstance(timeline_export_receipt_journal_summary, dict)
        else default_receipt_journal_summary(run_history)
    )
    readiness = carryover_readiness(live_flow, session, chain, journal)
    cockpit = build_python_exam_cockpit_flow(
        python_exam_readiness_console=readiness,
        exam_skill_drilldown=live_flow.get("exam_skill_drilldown", {}),
        exam_workspace_operator_run=operator,
        exam_workspace_session_console=session,
        review_chain_integrity_check=chain,
        timeline_export_review_packet=review,
        timeline_export_receipt_journal_summary=journal,
        selected_skill_tag=effective_skill_tag(live_flow, session),
        public_safe=public_safe,
    )
    live_control = build_python_exam_live_control_surface(
        python_exam_cockpit_flow=cockpit,
        python_exam_readiness_console=readiness,
        exam_skill_drilldown=live_flow.get("exam_skill_drilldown", {}),
        exam_workspace_operator_run=operator,
        exam_workspace_session_console=session,
        review_chain_integrity_check=chain,
        timeline_export_review_packet=review,
        timeline_export_receipt_journal_summary=journal,
        selected_skill_tag=effective_skill_tag(live_flow, session),
        public_safe=public_safe,
    )
    evidence_preview = build_python_exam_evidence_export_preview(
        python_exam_live_control_surface=live_control,
        python_exam_cockpit_flow=cockpit,
        python_exam_readiness_console=readiness,
        exam_skill_drilldown=live_flow.get("exam_skill_drilldown", {}),
        exam_workspace_operator_run=operator,
        exam_workspace_session_console=session,
        review_chain_integrity_check=chain,
        timeline_export_review_packet=review,
        timeline_export_receipt_journal_summary=journal,
        selected_skill_tag=effective_skill_tag(live_flow, session),
        public_safe=public_safe,
    )
    export_draft = build_python_exam_confirmed_local_export_draft(
        python_exam_evidence_export_preview=evidence_preview,
        operator_confirmed_local_export_draft_write=False,
        public_safe=public_safe,
    )
    draft_review = build_python_exam_draft_package_review_console(
        python_exam_confirmed_local_export_draft=export_draft,
        python_exam_evidence_export_preview=evidence_preview,
        public_safe=public_safe,
    )
    human_handoff = build_python_exam_human_handoff_packet(
        python_exam_draft_package_review_console=draft_review,
        python_exam_evidence_export_preview=evidence_preview,
        python_exam_confirmed_local_export_draft=export_draft,
        public_safe=public_safe,
    )
    summary = carryover_summary(
        live_flow=live_flow,
        session=session,
        run_history=run_history,
        evidence_preview=evidence_preview,
        human_handoff=human_handoff,
    )
    payload = {
        "schema_version": SKILL_TO_WORKSPACE_SESSION_CARRYOVER_SCHEMA_VERSION,
        "artifact_type": "skill_to_workspace_session_carryover",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Skill-to-Workspace Session Carryover. It carries a Skill-to-Workspace Operator dry-run receipt into "
            "Session Console, Run History, Evidence Export Preview, and Human Handoff Packet using metadata only. "
            "Dry-run remains the default; local writes stay behind individual operator confirmations. It returns "
            "receipt ids, skill tag, checkpoint hash, A0-A2 profile, source-card/anchor metadata, confirmation "
            "status, and not_cleared state, but never raw queries, course raw text, notebook code, local paths, "
            "values, solutions, final interpretations, proctoring, AI detection, automatic grading, or exam "
            "clearance."
        ),
        "carryover_summary": summary,
        "carryover_packet": carryover_packet(live_flow, session, run_history, evidence_preview, human_handoff),
        "carryover_artifacts": {
            "session_console": session,
            "run_history_export_review": run_history,
            "python_exam_evidence_export_preview": evidence_preview,
            "python_exam_human_handoff_packet": human_handoff,
        },
        "dry_run_default": True,
        "local_writes_requested": bool(summary.get("local_writes_requested", False)),
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
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Session Carryover bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def build_session_from_operator(
    *,
    course_id: str,
    operator: dict[str, Any],
    repeat_run_index: int,
    previous_console_receipts: list[dict[str, Any]],
    public_safe: bool,
) -> dict[str, Any]:
    console = session_console_view(operator=operator, repeat_run_index=repeat_run_index)
    receipt = session_console_receipt(
        course_id=course_id,
        operator=operator,
        console=console,
        repeat_run_index=repeat_run_index,
        previous_console_receipts=previous_console_receipts,
    )
    report = {
        "schema_version": "unibot-exam-workspace-session-console-v1",
        "artifact_type": "exam_workspace_session_console",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": course_id,
        "status": session_console_status(operator),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": "Session Console built from a Skill-to-Workspace dry-run receipt; metadata only.",
        "session_console": console,
        "session_console_markdown": session_console_markdown(console),
        "session_console_receipt": receipt,
        "operator_summary": operator_summary(operator),
        "operator_confirmation_matrix": operator.get("operator_confirmation_matrix", {}),
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
    }
    attach_session_public_scan(report, public_safe=public_safe)
    return report


def carryover_readiness(
    live_flow: dict[str, Any],
    session: dict[str, Any],
    chain: dict[str, Any],
    journal: dict[str, Any],
) -> dict[str, Any]:
    selected = live_flow.get("selected_skill", {}) if isinstance(live_flow.get("selected_skill"), dict) else {}
    source = live_flow.get("source_anchor_metadata", {}) if isinstance(live_flow.get("source_anchor_metadata"), dict) else {}
    checkpoint_hash = nested(session, "session_console", "notebook_checkpoint", "notebook_work_sha256")
    chain_pass = chain.get("status") == "review_chain_integrity_pass"
    journal_ready = int(journal.get("accepted_record_count", 0) or 0) >= 1
    return {
        "artifact_type": "python_exam_readiness_console",
        "status": "python_exam_readiness_console_ready" if chain_pass and journal_ready else "python_exam_readiness_console_attention",
        "exam_deployment_status": "not_cleared",
        "readiness_summary": {
            "selected_skill_tag": effective_skill_tag(live_flow, session),
            "skill_ready_for_workspace": live_flow.get("status") == "skill_to_workspace_live_flow_ready",
            "source_anchored": int(source.get("source_anchor_count", 0) or 0) >= 1,
            "review_chain_pass": chain_pass,
            "receipt_journal_ready": journal_ready,
            "latest_notebook_checkpoint_hash": checkpoint_hash,
            "next_safe_action": "Carry the dry-run receipt through session, evidence preview, and human handoff; keep not_cleared.",
        },
        "selected_skill_readiness": {
            "skill_tag": effective_skill_tag(live_flow, session),
            "source_anchor_count": int(source.get("source_anchor_count", selected.get("source_anchor_count", 0)) or 0),
            "reviewed_notebook_anchor_count": int(
                source.get("reviewed_notebook_anchor_count", selected.get("reviewed_notebook_anchor_count", 0)) or 0
            ),
            "source_card_ids": list(source.get("source_card_ids", selected.get("source_card_ids", [])) or [])[:8],
        },
        "a0_a2_help_status": {
            "recommended_help_level": first_text(
                nested(session, "session_console", "tutor_state", "effective_help_level"),
                nested(live_flow, "live_flow_summary", "requested_help_level"),
                "A2",
            ),
            "status": "a0_a2_only" if live_flow.get("a0_a2_only", True) else "nonstandard_help_attention",
            "observed_help_profile": {first_text(nested(session, "session_console", "tutor_state", "effective_help_level"), "A2"): 1},
            "nonstandard_help_event_count": 0 if live_flow.get("a0_a2_only", True) else 1,
        },
        "operator_confirmation_status": {
            "open_operator_confirmation_count": open_operator_confirmation_count(live_flow),
            "confirmed_local_write_step_count": int(nested(live_flow, "operator_confirmation_matrix", "confirmed_count") or 0),
            "open_operator_confirmation_steps": open_operator_confirmation_steps(live_flow),
        },
        "raw_query_returned": False,
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def default_review_chain(live_flow: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    ready = live_flow.get("status") == "skill_to_workspace_live_flow_ready" and bool(
        nested(session, "session_console", "notebook_checkpoint", "notebook_work_sha256")
    )
    return {
        "artifact_type": "review_chain_integrity_check",
        "status": "review_chain_integrity_pass" if ready else "review_chain_integrity_attention_required",
        "exam_deployment_status": "not_cleared",
        "chain_integrity_summary": {
            "issue_count": 0 if ready else 1,
            "checked_link_count": 4 if ready else 1,
            "help_level_profiles": {"journal": {"A2": 1}},
            "next_safe_action": "Review metadata-only carryover links; keep exam_deployment_status not_cleared.",
        },
    }


def default_timeline_export_review(run_history: dict[str, Any]) -> dict[str, Any]:
    summary = run_history.get("history_summary", {}) if isinstance(run_history.get("history_summary"), dict) else {}
    receipt_hash = sha256_text(json.dumps(summary, sort_keys=True, ensure_ascii=False))
    return {
        "artifact_type": "timeline_export_review_packet",
        "status": "timeline_export_review_packet_ready" if summary.get("run_count") else "timeline_export_review_packet_attention",
        "exam_deployment_status": "not_cleared",
        "export_review_summary": {
            "event_count": int(summary.get("run_count", 0) or 0),
            "skill_tags": list(summary.get("skill_tags", []) or []),
            "checkpoint_hash_count": int(summary.get("checkpoint_hash_count", 0) or 0),
            "help_level_profile": summary.get("help_level_profile", {}),
            "open_operator_confirmation_count": int(summary.get("open_operator_confirmation_count", 0) or 0),
            "reviewer_question_count": 6,
        },
        "local_export_receipt": {
            "receipt_id": receipt_hash[:20],
            "receipt_hash": receipt_hash,
            "status": "timeline_export_review_packet_receipt_ready_not_exam_clearance",
            "not_cleared_receipt": True,
        },
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
    }


def default_receipt_journal_summary(run_history: dict[str, Any]) -> dict[str, Any]:
    summary = run_history.get("history_summary", {}) if isinstance(run_history.get("history_summary"), dict) else {}
    ready = int(summary.get("run_count", 0) or 0) >= 1
    return {
        "artifact_type": "timeline_export_receipt_journal_summary",
        "status": "ok" if ready else "empty",
        "record_count": 1 if ready else 0,
        "accepted_record_count": 1 if ready else 0,
        "blocked_record_count": 0,
        "skill_tags": list(summary.get("skill_tags", []) or []),
        "event_count": int(summary.get("run_count", 0) or 0),
        "checkpoint_hash_count": int(summary.get("checkpoint_hash_count", 0) or 0),
        "reviewer_question_count": 6 if ready else 0,
        "help_level_profile": summary.get("help_level_profile", {"A2": 1}),
        "open_operator_confirmation_count": int(summary.get("open_operator_confirmation_count", 0) or 0),
        "reflection_statuses": ["reflection_evidence_present"] if ready else [],
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
    }


def carryover_summary(
    *,
    live_flow: dict[str, Any],
    session: dict[str, Any],
    run_history: dict[str, Any],
    evidence_preview: dict[str, Any],
    human_handoff: dict[str, Any],
) -> dict[str, Any]:
    ready = (
        live_flow.get("status") == "skill_to_workspace_live_flow_ready"
        and session.get("status") == "exam_workspace_session_console_ready"
        and run_history.get("status") == "exam_workspace_run_history_export_review_ready"
        and evidence_preview.get("status") == "python_exam_evidence_export_preview_ready"
        and human_handoff.get("status") == "python_exam_human_handoff_packet_ready"
    )
    return {
        "status": "skill_to_workspace_session_carryover_ready" if ready else "skill_to_workspace_session_carryover_attention",
        "selected_skill_tag": effective_skill_tag(live_flow, session),
        "operator_receipt_id": nested(live_flow, "dry_run_receipt", "receipt_id"),
        "session_receipt_id": nested(session, "session_console_receipt", "receipt_id"),
        "checkpoint_hash": nested(session, "session_console", "notebook_checkpoint", "notebook_work_sha256"),
        "checkpoint_hash_present": bool(nested(session, "session_console", "notebook_checkpoint", "notebook_work_sha256")),
        "help_status": nested(evidence_preview, "preview_summary", "help_status"),
        "source_card_count": len(nested(live_flow, "source_anchor_metadata", "source_card_ids") or []),
        "source_anchor_count": int(nested(live_flow, "source_anchor_metadata", "source_anchor_count") or 0),
        "open_operator_confirmation_count": open_operator_confirmation_count(live_flow),
        "local_writes_requested": bool(nested(live_flow, "operator_confirmation_matrix", "local_writes_requested")),
        "session_status": session.get("status", "missing"),
        "run_history_status": run_history.get("status", "missing"),
        "evidence_preview_status": evidence_preview.get("status", "missing"),
        "human_handoff_status": human_handoff.get("status", "missing"),
        "not_cleared_receipt": True,
        "dry_run_default": True,
        "exam_deployment_status": "not_cleared",
    }


def carryover_packet(
    live_flow: dict[str, Any],
    session: dict[str, Any],
    run_history: dict[str, Any],
    evidence_preview: dict[str, Any],
    human_handoff: dict[str, Any],
) -> dict[str, Any]:
    return {
        "packet_type": "skill_to_workspace_session_carryover",
        "selected_skill_tag": effective_skill_tag(live_flow, session),
        "operator_receipt": {
            "receipt_id": nested(live_flow, "dry_run_receipt", "receipt_id"),
            "status": nested(live_flow, "dry_run_receipt", "status"),
            "help_level": nested(live_flow, "dry_run_receipt", "effective_help_level"),
            "not_cleared_receipt": bool(nested(live_flow, "dry_run_receipt", "not_cleared_receipt") or True),
        },
        "session_receipt": {
            "receipt_id": nested(session, "session_console_receipt", "receipt_id"),
            "receipt_hash": nested(session, "session_console_receipt", "receipt_hash"),
            "checkpoint_hash": nested(session, "session_console_receipt", "notebook_work_sha256"),
        },
        "run_history": {
            "status": run_history.get("status", "missing"),
            "run_count": int(nested(run_history, "history_summary", "run_count") or 0),
            "checkpoint_hash_count": int(nested(run_history, "history_summary", "checkpoint_hash_count") or 0),
        },
        "evidence_preview": {
            "status": evidence_preview.get("status", "missing"),
            "preview_receipt_id": nested(evidence_preview, "preview_receipt", "receipt_id"),
            "help_status": nested(evidence_preview, "preview_summary", "help_status"),
        },
        "human_handoff": {
            "status": human_handoff.get("status", "missing"),
            "markdown_hash": nested(human_handoff, "copy_export_view", "markdown_hash"),
            "copy_export_ready": bool(nested(human_handoff, "handoff_summary", "copy_export_ready")),
        },
        "source_anchor_metadata": live_flow.get("source_anchor_metadata", {}),
        "operator_confirmation_status": {
            "status": nested(live_flow, "operator_confirmation_matrix", "status"),
            "confirmed_count": int(nested(live_flow, "operator_confirmation_matrix", "confirmed_count") or 0),
            "write_step_count": int(nested(live_flow, "operator_confirmation_matrix", "write_step_count") or 0),
            "open_operator_confirmation_count": open_operator_confirmation_count(live_flow),
            "local_writes_requested": bool(nested(live_flow, "operator_confirmation_matrix", "local_writes_requested")),
        },
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


def next_actions(summary: dict[str, Any]) -> list[str]:
    if summary.get("status") == "skill_to_workspace_session_carryover_ready":
        return [
            "Review the carryover packet and human handoff markdown hash before any local export write.",
            "Repeat the dry-run after the next notebook checkpoint if the selected skill changes.",
            "Keep exam_deployment_status not_cleared; real-world exam clearance stays outside UniBot.",
        ]
    return [
        "Resolve carryover attention items before treating the handoff packet as ready.",
        "Keep using dry-run previews and A0-A2 only.",
    ]


def effective_skill_tag(*values: Any) -> str:
    for value in values:
        if isinstance(value, dict):
            for path in [
                ("live_flow_summary", "selected_skill_tag"),
                ("selected_skill", "skill_tag"),
                ("session_console", "selected_skill", "skill_tag"),
                ("dry_run_receipt", "selected_skill_tag"),
            ]:
                found = nested(value, *path)
                if found:
                    return str(found)
    return "python_skill"


def open_operator_confirmation_count(live_flow: dict[str, Any]) -> int:
    matrix = live_flow.get("operator_confirmation_matrix", {}) if isinstance(live_flow.get("operator_confirmation_matrix"), dict) else {}
    steps = matrix.get("steps", {}) if isinstance(matrix.get("steps"), dict) else {}
    if steps:
        return len([step for step in steps.values() if isinstance(step, dict) and not step.get("confirmed")])
    return max(int(matrix.get("write_step_count", 0) or 0) - int(matrix.get("confirmed_count", 0) or 0), 0)


def open_operator_confirmation_steps(live_flow: dict[str, Any]) -> list[str]:
    matrix = live_flow.get("operator_confirmation_matrix", {}) if isinstance(live_flow.get("operator_confirmation_matrix"), dict) else {}
    steps = matrix.get("steps", {}) if isinstance(matrix.get("steps"), dict) else {}
    return [str(key) for key, step in steps.items() if isinstance(step, dict) and not step.get("confirmed")][:8]


def first_text(*values: Any) -> str:
    for value in values:
        text = str(value or "")
        if text:
            return text
    return ""


def nested(value: Any, *path: str) -> Any:
    current = value
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def attach_session_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "skill-to-workspace-session-console")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "skill-to-workspace-session-carryover")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
