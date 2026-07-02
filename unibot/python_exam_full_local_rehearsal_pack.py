from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .exam_packet_timeline import build_exam_packet_timeline
from .exam_run_packet_builder import build_exam_run_packet
from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_cockpit_flow import build_python_exam_cockpit_flow
from .python_exam_confirmed_local_export_draft import build_python_exam_confirmed_local_export_draft
from .python_exam_draft_package_review_console import build_python_exam_draft_package_review_console
from .python_exam_evidence_export_preview import build_python_exam_evidence_export_preview
from .python_exam_human_handoff_packet import build_python_exam_human_handoff_packet
from .python_exam_live_control_surface import build_python_exam_live_control_surface
from .python_exam_local_cycle_chain_snapshot import build_python_exam_local_cycle_chain_snapshot


PYTHON_EXAM_FULL_LOCAL_REHEARSAL_PACK_SCHEMA_VERSION = "unibot-python-exam-full-local-rehearsal-pack-v1"
PYTHON_EXAM_FULL_LOCAL_REHEARSAL_PACK_ENDPOINT = "/api/unibot/course/python-exam-full-local-rehearsal-pack"


def build_python_exam_full_local_rehearsal_pack(
    *,
    exam_skill_drilldown: dict[str, Any] | None = None,
    python_exam_local_cycle_readiness_review: dict[str, Any] | None = None,
    python_exam_local_cycle_readiness_handoff: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    python_exam_local_cycle_chain_snapshot: dict[str, Any] | None = None,
    exam_workspace_operator_run: dict[str, Any] | None = None,
    exam_workspace_session_console: dict[str, Any] | None = None,
    exam_workspace_run_history_export_review: dict[str, Any] | None = None,
    course_exam_coverage_dashboard: dict[str, Any] | None = None,
    course_per_skill_action_router: dict[str, Any] | None = None,
    routed_action_executor: dict[str, Any] | None = None,
    exam_run_packet: dict[str, Any] | None = None,
    exam_packet_timeline: dict[str, Any] | None = None,
    timeline_export_review_packet: dict[str, Any] | None = None,
    timeline_export_receipt_journal_summary: dict[str, Any] | None = None,
    review_chain_integrity_check: dict[str, Any] | None = None,
    python_exam_readiness_console: dict[str, Any] | None = None,
    python_exam_cockpit_flow: dict[str, Any] | None = None,
    python_exam_live_control_surface: dict[str, Any] | None = None,
    python_exam_evidence_export_preview: dict[str, Any] | None = None,
    python_exam_confirmed_local_export_draft: dict[str, Any] | None = None,
    python_exam_draft_package_review_console: dict[str, Any] | None = None,
    python_exam_human_handoff_packet: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    drilldown = safe_dict(exam_skill_drilldown)
    local_review = safe_dict(python_exam_local_cycle_readiness_review)
    local_handoff = safe_dict(python_exam_local_cycle_readiness_handoff)
    workspace_card = safe_dict(python_exam_local_cycle_operator_workspace_card)
    local_chain = selected_local_cycle_chain(
        provided=python_exam_local_cycle_chain_snapshot,
        review=local_review,
        handoff=local_handoff,
        workspace_card=workspace_card,
    )
    operator = safe_dict(exam_workspace_operator_run)
    session = safe_dict(exam_workspace_session_console)
    history = safe_dict(exam_workspace_run_history_export_review)
    dashboard = safe_dict(course_exam_coverage_dashboard)
    router = safe_dict(course_per_skill_action_router)
    executor = safe_dict(routed_action_executor)
    packet = selected_exam_run_packet(
        provided=exam_run_packet,
        dashboard=dashboard,
        router=router,
        executor=executor,
        history=history,
        session=session,
        local_review=local_review,
        local_handoff=local_handoff,
        workspace_card=workspace_card,
        local_chain=local_chain,
        selected_skill_tag=selected_skill_tag,
    )
    timeline = selected_exam_packet_timeline(
        provided=exam_packet_timeline,
        packet=packet,
        local_review=local_review,
        local_handoff=local_handoff,
        workspace_card=workspace_card,
        local_chain=local_chain,
        selected_skill_tag=selected_skill_tag,
    )
    review_packet = safe_dict(timeline_export_review_packet)
    receipt_summary = safe_dict(timeline_export_receipt_journal_summary)
    chain_integrity = safe_dict(review_chain_integrity_check)
    readiness = safe_dict(python_exam_readiness_console)
    skill_tag = effective_skill_tag(
        selected_skill_tag,
        drilldown,
        local_chain,
        operator,
        session,
        packet,
        timeline,
        readiness,
    )
    cockpit = selected_cockpit(
        provided=python_exam_cockpit_flow,
        readiness=readiness,
        drilldown=drilldown,
        operator=operator,
        session=session,
        chain_integrity=chain_integrity,
        review_packet=review_packet,
        receipt_summary=receipt_summary,
        selected_skill_tag=skill_tag,
    )
    live_control = selected_live_control(
        provided=python_exam_live_control_surface,
        cockpit=cockpit,
        readiness=readiness,
        drilldown=drilldown,
        workspace_card=workspace_card,
        operator=operator,
        session=session,
        chain_integrity=chain_integrity,
        review_packet=review_packet,
        receipt_summary=receipt_summary,
        selected_skill_tag=skill_tag,
    )
    evidence = selected_evidence_preview(
        provided=python_exam_evidence_export_preview,
        live_control=live_control,
        cockpit=cockpit,
        readiness=readiness,
        drilldown=drilldown,
        operator=operator,
        session=session,
        chain_integrity=chain_integrity,
        review_packet=review_packet,
        receipt_summary=receipt_summary,
        selected_skill_tag=skill_tag,
    )
    draft = selected_local_export_draft(
        provided=python_exam_confirmed_local_export_draft,
        evidence=evidence,
    )
    draft_console = selected_draft_console(
        provided=python_exam_draft_package_review_console,
        draft=draft,
        evidence=evidence,
    )
    human_handoff = selected_human_handoff(
        provided=python_exam_human_handoff_packet,
        draft_console=draft_console,
        evidence=evidence,
        draft=draft,
    )
    steps = rehearsal_steps(
        skill_tag=skill_tag,
        drilldown=drilldown,
        local_review=local_review,
        local_handoff=local_handoff,
        workspace_card=workspace_card,
        local_chain=local_chain,
        operator=operator,
        session=session,
        history=history,
        packet=packet,
        timeline=timeline,
        evidence=evidence,
        human_handoff=human_handoff,
    )
    summary = rehearsal_summary(
        skill_tag=skill_tag,
        steps=steps,
        local_chain=local_chain,
        operator=operator,
        session=session,
        packet=packet,
        timeline=timeline,
        evidence=evidence,
        human_handoff=human_handoff,
        live_control=live_control,
    )
    payload = {
        "schema_version": PYTHON_EXAM_FULL_LOCAL_REHEARSAL_PACK_SCHEMA_VERSION,
        "artifact_type": "python_exam_full_local_rehearsal_pack",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Full Local Rehearsal Pack. It compacts one selected Python exam skill into a full "
            "metadata-only local rehearsal: skill selection, course/source anchors, local-cycle readiness, handoff, "
            "operator workspace card, chain snapshot, operator dry-run, session console, run history, exam run "
            "packet, timeline, evidence export preview, and human handoff packet. It remains dry-run by default, "
            "performs no local writes by itself, and keeps every local write behind explicit operator confirmation. "
            "It never returns raw queries, course raw text, notebook code, local paths, values, solutions, final "
            "interpretations, scores, rankings, grades, proctoring, AI detection, automatic grading, or exam "
            "clearance claims."
        ),
        "selected_skill_tag": skill_tag,
        "rehearsal_summary": summary,
        "rehearsal_steps": steps,
        "source_anchor_metadata": source_anchor_metadata(drilldown, local_chain, packet, evidence),
        "operator_confirmation_status": operator_confirmation_status(live_control, operator, evidence, human_handoff),
        "a0_a2_help_status": a0_a2_help_status(evidence, live_control, readiness),
        "evidence_chain": evidence_chain(local_chain, packet, timeline, evidence, human_handoff),
        "notebook_checkpoint_metadata": notebook_checkpoint_metadata(local_review, workspace_card, local_chain, session, evidence),
        "artifact_statuses": artifact_statuses(
            drilldown=drilldown,
            local_chain=local_chain,
            operator=operator,
            session=session,
            history=history,
            packet=packet,
            timeline=timeline,
            evidence=evidence,
            human_handoff=human_handoff,
        ),
        "dry_run_default": True,
        "local_writes_executed_by_rehearsal_pack": False,
        "operator_confirmation_required_for_local_write": True,
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Full Local Rehearsal Pack bleibt not_cleared."
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
        "score_returned": False,
        "percentage_returned": False,
        "ranking_returned": False,
        "grade_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def selected_local_cycle_chain(
    *,
    provided: dict[str, Any] | None,
    review: dict[str, Any],
    handoff: dict[str, Any],
    workspace_card: dict[str, Any],
) -> dict[str, Any]:
    if isinstance(provided, dict):
        return provided
    if not review and not handoff and not workspace_card:
        return {}
    return build_python_exam_local_cycle_chain_snapshot(
        python_exam_local_cycle_readiness_review=review,
        python_exam_local_cycle_readiness_handoff=handoff,
        python_exam_local_cycle_operator_workspace_card=workspace_card,
        public_safe=True,
    )


def selected_exam_run_packet(
    *,
    provided: dict[str, Any] | None,
    dashboard: dict[str, Any],
    router: dict[str, Any],
    executor: dict[str, Any],
    history: dict[str, Any],
    session: dict[str, Any],
    local_review: dict[str, Any],
    local_handoff: dict[str, Any],
    workspace_card: dict[str, Any],
    local_chain: dict[str, Any],
    selected_skill_tag: str,
) -> dict[str, Any]:
    if isinstance(provided, dict):
        return provided
    if not (dashboard or router or executor or history or session):
        return {}
    console_receipt = session.get("session_console_receipt") if isinstance(session.get("session_console_receipt"), dict) else None
    return build_exam_run_packet(
        dashboard_report=dashboard or None,
        router_report=router or None,
        executor_report=executor or None,
        run_history_report=history or None,
        console_reports=[session] if session else None,
        console_receipts=[console_receipt] if console_receipt else None,
        python_exam_local_cycle_readiness_review=local_review or None,
        python_exam_local_cycle_readiness_handoff=local_handoff or None,
        python_exam_local_cycle_operator_workspace_card=workspace_card or None,
        python_exam_local_cycle_chain_snapshot=local_chain or None,
        selected_skill_tag=selected_skill_tag,
        public_safe=True,
    )


def selected_exam_packet_timeline(
    *,
    provided: dict[str, Any] | None,
    packet: dict[str, Any],
    local_review: dict[str, Any],
    local_handoff: dict[str, Any],
    workspace_card: dict[str, Any],
    local_chain: dict[str, Any],
    selected_skill_tag: str,
) -> dict[str, Any]:
    if isinstance(provided, dict):
        return provided
    if not packet:
        return {}
    return build_exam_packet_timeline(
        exam_run_packets=[packet],
        python_exam_local_cycle_readiness_review=local_review or None,
        python_exam_local_cycle_readiness_handoff=local_handoff or None,
        python_exam_local_cycle_operator_workspace_card=workspace_card or None,
        python_exam_local_cycle_chain_snapshot=local_chain or None,
        selected_skill_tag=selected_skill_tag,
        public_safe=True,
    )


def selected_cockpit(
    *,
    provided: dict[str, Any] | None,
    readiness: dict[str, Any],
    drilldown: dict[str, Any],
    operator: dict[str, Any],
    session: dict[str, Any],
    chain_integrity: dict[str, Any],
    review_packet: dict[str, Any],
    receipt_summary: dict[str, Any],
    selected_skill_tag: str,
) -> dict[str, Any]:
    if isinstance(provided, dict):
        return provided
    if not (readiness or drilldown or operator or session or chain_integrity or review_packet or receipt_summary):
        return {}
    return build_python_exam_cockpit_flow(
        python_exam_readiness_console=readiness or None,
        exam_skill_drilldown=drilldown or None,
        exam_workspace_operator_run=operator or None,
        exam_workspace_session_console=session or None,
        review_chain_integrity_check=chain_integrity or None,
        timeline_export_review_packet=review_packet or None,
        timeline_export_receipt_journal_summary=receipt_summary or None,
        selected_skill_tag=selected_skill_tag,
        public_safe=True,
    )


def selected_live_control(
    *,
    provided: dict[str, Any] | None,
    cockpit: dict[str, Any],
    readiness: dict[str, Any],
    drilldown: dict[str, Any],
    workspace_card: dict[str, Any],
    operator: dict[str, Any],
    session: dict[str, Any],
    chain_integrity: dict[str, Any],
    review_packet: dict[str, Any],
    receipt_summary: dict[str, Any],
    selected_skill_tag: str,
) -> dict[str, Any]:
    if isinstance(provided, dict):
        return provided
    if not cockpit:
        return {}
    return build_python_exam_live_control_surface(
        python_exam_cockpit_flow=cockpit,
        python_exam_readiness_console=readiness or None,
        exam_skill_drilldown=drilldown or None,
        python_exam_local_cycle_operator_workspace_card=workspace_card or None,
        exam_workspace_operator_run=operator or None,
        exam_workspace_session_console=session or None,
        review_chain_integrity_check=chain_integrity or None,
        timeline_export_review_packet=review_packet or None,
        timeline_export_receipt_journal_summary=receipt_summary or None,
        selected_skill_tag=selected_skill_tag,
        public_safe=True,
    )


def selected_evidence_preview(
    *,
    provided: dict[str, Any] | None,
    live_control: dict[str, Any],
    cockpit: dict[str, Any],
    readiness: dict[str, Any],
    drilldown: dict[str, Any],
    operator: dict[str, Any],
    session: dict[str, Any],
    chain_integrity: dict[str, Any],
    review_packet: dict[str, Any],
    receipt_summary: dict[str, Any],
    selected_skill_tag: str,
) -> dict[str, Any]:
    if isinstance(provided, dict):
        return provided
    if not (live_control or cockpit):
        return {}
    return build_python_exam_evidence_export_preview(
        python_exam_live_control_surface=live_control or None,
        python_exam_cockpit_flow=cockpit or None,
        python_exam_readiness_console=readiness or None,
        exam_skill_drilldown=drilldown or None,
        exam_workspace_operator_run=operator or None,
        exam_workspace_session_console=session or None,
        review_chain_integrity_check=chain_integrity or None,
        timeline_export_review_packet=review_packet or None,
        timeline_export_receipt_journal_summary=receipt_summary or None,
        selected_skill_tag=selected_skill_tag,
        public_safe=True,
    )


def selected_local_export_draft(*, provided: dict[str, Any] | None, evidence: dict[str, Any]) -> dict[str, Any]:
    if isinstance(provided, dict):
        return provided
    if not evidence:
        return {}
    return build_python_exam_confirmed_local_export_draft(
        python_exam_evidence_export_preview=evidence,
        operator_confirmed_local_export_draft_write=False,
        public_safe=True,
    )


def selected_draft_console(
    *,
    provided: dict[str, Any] | None,
    draft: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    if isinstance(provided, dict):
        return provided
    if not (draft or evidence):
        return {}
    return build_python_exam_draft_package_review_console(
        python_exam_confirmed_local_export_draft=draft or None,
        python_exam_evidence_export_preview=evidence or None,
        public_safe=True,
    )


def selected_human_handoff(
    *,
    provided: dict[str, Any] | None,
    draft_console: dict[str, Any],
    evidence: dict[str, Any],
    draft: dict[str, Any],
) -> dict[str, Any]:
    if isinstance(provided, dict):
        return provided
    if not (draft_console or evidence or draft):
        return {}
    return build_python_exam_human_handoff_packet(
        python_exam_draft_package_review_console=draft_console or None,
        python_exam_evidence_export_preview=evidence or None,
        python_exam_confirmed_local_export_draft=draft or None,
        public_safe=True,
    )


def rehearsal_steps(
    *,
    skill_tag: str,
    drilldown: dict[str, Any],
    local_review: dict[str, Any],
    local_handoff: dict[str, Any],
    workspace_card: dict[str, Any],
    local_chain: dict[str, Any],
    operator: dict[str, Any],
    session: dict[str, Any],
    history: dict[str, Any],
    packet: dict[str, Any],
    timeline: dict[str, Any],
    evidence: dict[str, Any],
    human_handoff: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        rehearsal_step("skill_selection", "exam_skill_drilldown", drilldown, ready_statuses={"exam_skill_drilldown_ready_for_workspace"}, skill_tag=skill_tag),
        rehearsal_step("local_cycle_readiness_review", "python_exam_local_cycle_readiness_review", local_review, ready_statuses={"python_exam_local_cycle_readiness_review_ready"}, skill_tag=skill_tag),
        rehearsal_step("local_cycle_readiness_handoff", "python_exam_local_cycle_readiness_handoff", local_handoff, ready_statuses={"python_exam_local_cycle_readiness_handoff_ready"}, skill_tag=skill_tag),
        rehearsal_step("local_cycle_operator_workspace_card", "python_exam_local_cycle_operator_workspace_card", workspace_card, ready_statuses={"python_exam_local_cycle_operator_workspace_card_ready"}, skill_tag=skill_tag),
        rehearsal_step("local_cycle_chain_snapshot", "python_exam_local_cycle_chain_snapshot", local_chain, ready_statuses={"python_exam_local_cycle_chain_snapshot_ready"}, skill_tag=skill_tag),
        rehearsal_step("exam_workspace_operator_dry_run", "exam_workspace_operator_run_dry_run", operator, ready_statuses={"exam_workspace_operator_dry_run_ready", "exam_workspace_operator_ready_with_confirmed_local_writes"}, skill_tag=skill_tag),
        rehearsal_step("session_console", "exam_workspace_session_console", session, ready_status_prefixes=("exam_workspace_session_console_",), skill_tag=skill_tag),
        rehearsal_step("run_history", "exam_workspace_run_history_export_review", history, ready_statuses={"exam_workspace_run_history_export_review_ready"}, skill_tag=skill_tag),
        rehearsal_step("exam_run_packet", "exam_run_packet", packet, ready_statuses={"exam_run_packet_ready"}, skill_tag=skill_tag),
        rehearsal_step("exam_packet_timeline", "exam_packet_timeline", timeline, ready_statuses={"exam_packet_timeline_ready"}, skill_tag=skill_tag),
        rehearsal_step("evidence_export_preview", "python_exam_evidence_export_preview", evidence, ready_statuses={"python_exam_evidence_export_preview_ready"}, skill_tag=skill_tag),
        rehearsal_step("human_handoff_packet", "python_exam_human_handoff_packet", human_handoff, ready_statuses={"python_exam_human_handoff_packet_ready"}, skill_tag=skill_tag),
    ]


def rehearsal_step(
    step_id: str,
    expected_artifact_type: str,
    artifact: dict[str, Any],
    *,
    ready_statuses: set[str] | None = None,
    ready_status_prefixes: tuple[str, ...] = (),
    skill_tag: str,
) -> dict[str, Any]:
    artifact_type = str(artifact.get("artifact_type", "missing")) if artifact else "missing"
    status = str(artifact.get("status", "missing")) if artifact else "missing"
    ready = artifact_type == expected_artifact_type and (
        status in (ready_statuses or set()) or any(status.startswith(prefix) and "ready" in status for prefix in ready_status_prefixes)
    )
    if not artifact:
        step_status = "missing"
    elif ready:
        step_status = "ready"
    else:
        step_status = "attention"
    return {
        "step_id": step_id,
        "artifact_type": artifact_type,
        "status": status,
        "step_status": step_status,
        "selected_skill_tag": skill_tag,
        "artifact_hash": artifact_hash(artifact),
        "next_safe_action": next_safe_action_from_artifact(artifact),
        "dry_run_default": True,
        "operator_confirmation_required_for_local_write": step_id in {
            "exam_workspace_operator_dry_run",
            "evidence_export_preview",
            "human_handoff_packet",
        },
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def rehearsal_summary(
    *,
    skill_tag: str,
    steps: list[dict[str, Any]],
    local_chain: dict[str, Any],
    operator: dict[str, Any],
    session: dict[str, Any],
    packet: dict[str, Any],
    timeline: dict[str, Any],
    evidence: dict[str, Any],
    human_handoff: dict[str, Any],
    live_control: dict[str, Any],
) -> dict[str, Any]:
    ready_steps = len([step for step in steps if step.get("step_status") == "ready"])
    missing_steps = len([step for step in steps if step.get("step_status") == "missing"])
    attention_steps = len([step for step in steps if step.get("step_status") == "attention"])
    open_confirmations = operator_confirmation_status(live_control, operator, evidence, human_handoff)
    status = (
        "python_exam_full_local_rehearsal_pack_ready"
        if ready_steps == len(steps) and attention_steps == 0 and missing_steps == 0
        else "python_exam_full_local_rehearsal_pack_attention"
    )
    return {
        "status": status,
        "selected_skill_tag": skill_tag,
        "step_count": len(steps),
        "ready_step_count": ready_steps,
        "missing_step_count": missing_steps,
        "attention_step_count": attention_steps,
        "local_cycle_chain_snapshot_status": local_chain.get("status", "missing"),
        "local_cycle_chain_snapshot_hash": local_chain.get("snapshot_hash", ""),
        "operator_run_status": operator.get("status", "missing"),
        "session_console_status": session.get("status", "missing"),
        "exam_run_packet_status": packet.get("status", "missing"),
        "exam_packet_timeline_status": timeline.get("status", "missing"),
        "evidence_preview_status": evidence.get("status", "missing"),
        "human_handoff_status": human_handoff.get("status", "missing"),
        "open_operator_confirmation_count": open_confirmations.get("open_operator_confirmation_count", 0),
        "dry_run_default": True,
        "local_writes_executed_by_rehearsal_pack": False,
        "exam_deployment_status": "not_cleared",
        "next_safe_action": (
            "Use this rehearsal pack for human review; keep all real exam clearance outside UniBot."
            if status == "python_exam_full_local_rehearsal_pack_ready"
            else "Complete the missing or attention rehearsal steps before relying on the full local rehearsal pack."
        ),
    }


def source_anchor_metadata(
    drilldown: dict[str, Any],
    local_chain: dict[str, Any],
    packet: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    selected = drilldown.get("selected_skill", {}) if isinstance(drilldown.get("selected_skill"), dict) else {}
    chain_summary = local_chain.get("chain_snapshot_summary", {}) if isinstance(local_chain.get("chain_snapshot_summary"), dict) else {}
    manifest = evidence.get("preview_manifest", {}) if isinstance(evidence.get("preview_manifest"), dict) else {}
    readiness = manifest.get("readiness_snapshot", {}) if isinstance(manifest.get("readiness_snapshot"), dict) else {}
    packet_skill = packet.get("selected_skill_packet", {}) if isinstance(packet.get("selected_skill_packet"), dict) else {}
    source_ids = first_list(
        selected.get("source_card_ids", []),
        chain_summary.get("source_card_ids", []),
        readiness.get("source_card_ids", []),
        packet_skill.get("source_card_ids", []),
    )
    return {
        "source_card_ids": source_ids[:8],
        "source_anchor_count": first_int(
            selected.get("source_anchor_count"),
            chain_summary.get("source_anchor_count"),
            readiness.get("source_anchor_count"),
            packet_skill.get("source_anchor_count"),
            0,
        ),
        "source_anchored": bool(source_ids),
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "local_paths_returned": False,
    }


def operator_confirmation_status(
    live_control: dict[str, Any],
    operator: dict[str, Any],
    evidence: dict[str, Any],
    human_handoff: dict[str, Any],
) -> dict[str, Any]:
    live_status = live_control.get("operator_confirmation_status", {}) if isinstance(live_control.get("operator_confirmation_status"), dict) else {}
    operator_matrix = operator.get("operator_confirmation_matrix", {}) if isinstance(operator.get("operator_confirmation_matrix"), dict) else {}
    evidence_profile = nested(evidence, "preview_manifest", "operator_confirmation_profile")
    evidence_profile = evidence_profile if isinstance(evidence_profile, dict) else {}
    handoff_confirmations = nested(human_handoff, "handoff_packet", "operator_confirmations")
    handoff_confirmations = handoff_confirmations if isinstance(handoff_confirmations, dict) else {}
    return {
        "status": first_text(
            live_status.get("status"),
            evidence_profile.get("status"),
            handoff_confirmations.get("status"),
            "metadata_only_confirmations",
        ),
        "open_operator_confirmation_count": first_int(
            live_status.get("open_operator_confirmation_count"),
            operator_matrix.get("open_operator_confirmation_count"),
            evidence_profile.get("open_operator_confirmation_count"),
            handoff_confirmations.get("open_operator_confirmation_count"),
            0,
        ),
        "confirmed_count": first_int(live_status.get("confirmed_count"), operator_matrix.get("confirmed_count"), 0),
        "write_step_count": first_int(live_status.get("write_step_count"), operator_matrix.get("write_step_count"), 0),
        "local_writes_require_confirmation": True,
        "dry_run_default": True,
        "exam_deployment_status": "not_cleared",
    }


def a0_a2_help_status(evidence: dict[str, Any], live_control: dict[str, Any], readiness: dict[str, Any]) -> dict[str, Any]:
    evidence_help = nested(evidence, "preview_manifest", "help_level_profile")
    evidence_help = evidence_help if isinstance(evidence_help, dict) else {}
    live_help = live_control.get("a0_a2_help_status", {}) if isinstance(live_control.get("a0_a2_help_status"), dict) else {}
    readiness_help = readiness.get("a0_a2_help_status", {}) if isinstance(readiness.get("a0_a2_help_status"), dict) else {}
    profile = first_dict(evidence_help.get("profile"), live_help.get("observed_help_profile"), readiness_help.get("observed_help_profile"))
    nonstandard = sum(int(count or 0) for level, count in profile.items() if str(level) not in {"A0", "A1", "A2"})
    return {
        "status": "a0_a2_only" if nonstandard == 0 else "nonstandard_help_attention",
        "profile": profile,
        "allowed_help_boundary": "A0-A2",
        "nonstandard_help_event_count": nonstandard,
        "exam_deployment_status": "not_cleared",
    }


def evidence_chain(
    local_chain: dict[str, Any],
    packet: dict[str, Any],
    timeline: dict[str, Any],
    evidence: dict[str, Any],
    human_handoff: dict[str, Any],
) -> dict[str, Any]:
    return {
        "local_cycle_chain_snapshot_hash": local_chain.get("snapshot_hash", ""),
        "exam_run_packet_receipt_id": nested(packet, "packet_receipt", "receipt_id"),
        "exam_run_packet_receipt_hash": nested(packet, "packet_receipt", "receipt_hash"),
        "exam_packet_timeline_receipt_id": nested(timeline, "timeline_receipt", "receipt_id"),
        "exam_packet_timeline_receipt_hash": nested(timeline, "timeline_receipt", "receipt_hash"),
        "evidence_preview_receipt_id": nested(evidence, "preview_receipt", "receipt_id"),
        "evidence_preview_receipt_hash": nested(evidence, "preview_receipt", "receipt_hash"),
        "human_handoff_markdown_hash": nested(human_handoff, "copy_export_view", "markdown_hash"),
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def notebook_checkpoint_metadata(
    local_review: dict[str, Any],
    workspace_card: dict[str, Any],
    local_chain: dict[str, Any],
    session: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    hashes = unique_values(
        nested(local_review, "readiness_review_summary", "checkpoint_hash"),
        nested(local_review, "local_cycle_start_packet", "checkpoint_hash"),
        nested(workspace_card, "workspace_card_summary", "checkpoint_hash"),
        nested(local_chain, "chain_snapshot_summary", "checkpoint_hash"),
        nested(session, "session_console", "notebook_checkpoint", "notebook_work_sha256"),
        nested(evidence, "preview_manifest", "notebook_checkpoint", "notebook_checkpoint_hash"),
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


def artifact_statuses(**artifacts: dict[str, Any]) -> dict[str, str]:
    return {
        name: str(artifact.get("status", "missing")) if isinstance(artifact, dict) and artifact else "missing"
        for name, artifact in artifacts.items()
    }


def next_actions(summary: dict[str, Any]) -> list[str]:
    return [
        summary.get("next_safe_action", "Review the full local rehearsal pack."),
        "Use the pack as a human-reviewable rehearsal record only; keep dry-run and A0-A2.",
        "Keep exam_deployment_status not_cleared and handle real exam clearance outside UniBot.",
    ]


def effective_skill_tag(selected: str, *artifacts: dict[str, Any]) -> str:
    if str(selected or "").strip():
        return str(selected).strip()
    for artifact in artifacts:
        for path in (
            ("selected_skill_tag",),
            ("rehearsal_summary", "selected_skill_tag"),
            ("selected_skill", "skill_tag"),
            ("chain_snapshot_summary", "selected_skill_tag"),
            ("packet_summary", "selected_skill_tag"),
            ("timeline_summary", "skill_tags"),
            ("readiness_summary", "selected_skill_tag"),
        ):
            value = nested(artifact, *path)
            if isinstance(value, list) and value:
                return str(value[0])
            if isinstance(value, str) and value:
                return value
    return "python_lists"


def next_safe_action_from_artifact(artifact: dict[str, Any]) -> str:
    for path in (
        ("next_safe_action",),
        ("rehearsal_summary", "next_safe_action"),
        ("chain_snapshot_summary", "next_safe_action"),
        ("packet_summary", "next_safe_action"),
        ("preview_summary", "next_safe_action"),
        ("handoff_summary", "next_safe_action"),
    ):
        value = nested(artifact, *path)
        if isinstance(value, str) and value:
            return value
    actions = artifact.get("next_actions", []) if isinstance(artifact.get("next_actions"), list) else []
    return str(actions[0]) if actions else ""


def artifact_hash(artifact: dict[str, Any]) -> str:
    if not artifact:
        return ""
    return sha256_text(json.dumps(artifact, sort_keys=True, ensure_ascii=False))


def safe_dict(value: dict[str, Any] | None) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def first_text(*values: Any) -> str:
    for value in values:
        text = str(value or "")
        if text:
            return text
    return ""


def first_int(*values: Any) -> int:
    for value in values:
        try:
            if value is not None and str(value) != "":
                return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def first_list(*values: Any) -> list[str]:
    for value in values:
        if isinstance(value, list) and value:
            return [str(item) for item in value]
    return []


def unique_values(*values: Any) -> list[str]:
    result: list[str] = []
    for value in values:
        candidates = value if isinstance(value, list) else [value]
        for candidate in candidates:
            text = str(candidate or "").strip()
            if text and text not in result:
                result.append(text)
    return result


def first_dict(*values: Any) -> dict[str, int]:
    for value in values:
        if isinstance(value, dict) and value:
            return {str(key): int(count or 0) for key, count in value.items()}
    return {}


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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-full-local-rehearsal-pack")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
