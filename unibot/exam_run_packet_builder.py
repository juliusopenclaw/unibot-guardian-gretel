from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_exam_coverage_dashboard import build_course_exam_coverage_dashboard
from .course_per_skill_action_router import build_course_per_skill_action_router
from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .exam_workspace_run_history import build_exam_workspace_run_history_export_review
from .materials import sha256_text
from .public_safety import scan_text
from .routed_action_executor import build_routed_action_executor
from .python_exam_local_cycle_chain_snapshot import build_python_exam_local_cycle_chain_snapshot


EXAM_RUN_PACKET_SCHEMA_VERSION = "unibot-exam-run-packet-v1"
EXAM_RUN_PACKET_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-exam-run-packet-workspace-card-packet-alignment-v1"
)
EXAM_RUN_PACKET_ENDPOINT = "/api/unibot/course/exam-run-packet"


def build_exam_run_packet(
    *,
    course_id: str = DEFAULT_COURSE_ID,
    selected_skill_tag: str = "",
    focus_query: str = "",
    dashboard_report: dict[str, Any] | None = None,
    router_report: dict[str, Any] | None = None,
    executor_report: dict[str, Any] | None = None,
    run_history_report: dict[str, Any] | None = None,
    console_reports: list[dict[str, Any]] | None = None,
    console_receipts: list[dict[str, Any]] | None = None,
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
    query: str = "",
    requested_help_level: str = "A2",
    exam_status: str = "strict",
    student_reflection: str = "",
    study_receipt: dict[str, Any] | None = None,
    notebook_checkpoint: dict[str, Any] | None = None,
    cell_source: str = "",
    cell_index: int = 0,
    cell_id: str = "",
    cell_type: str = "code",
    python_exam_local_cycle_readiness_review: dict[str, Any] | None = None,
    python_exam_local_cycle_readiness_handoff: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    python_exam_local_cycle_chain_snapshot: dict[str, Any] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    safe_console_reports = [item for item in (console_reports or []) if isinstance(item, dict)]
    safe_console_receipts = [item for item in (console_receipts or []) if isinstance(item, dict)]
    history = run_history_report if isinstance(run_history_report, dict) else build_exam_workspace_run_history_export_review(
        course_id=safe_id,
        console_reports=safe_console_reports,
        console_receipts=safe_console_receipts,
        build_current_console=False,
        public_safe=public_safe,
    )
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
        focus_query=focus_query or query,
        selected_skill_tag=selected_skill_tag,
        console_reports=safe_console_reports,
        console_receipts=safe_console_receipts,
        run_history_report=history,
        public_safe=public_safe,
    )
    router = router_report if isinstance(router_report, dict) else build_course_per_skill_action_router(
        course_id=safe_id,
        selected_skill_tag=selected_skill_tag,
        focus_query=focus_query or query,
        dashboard_report=dashboard,
        console_reports=safe_console_reports,
        console_receipts=safe_console_receipts,
        run_history_report=history,
        public_safe=public_safe,
    )
    executor = executor_report if isinstance(executor_report, dict) else build_routed_action_executor(
        course_id=safe_id,
        selected_skill_tag=selected_skill_tag,
        focus_query=focus_query or query,
        router_report=router,
        selected_route=router.get("selected_route", {}) if isinstance(router.get("selected_route"), dict) else {},
        dashboard_report=dashboard,
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
        console_reports=safe_console_reports,
        console_receipts=safe_console_receipts,
        run_history_report=history,
        query=query,
        requested_help_level=requested_help_level,
        exam_status=exam_status,
        student_reflection=student_reflection,
        study_receipt=study_receipt,
        notebook_checkpoint=notebook_checkpoint,
        cell_source=cell_source,
        cell_index=cell_index,
        cell_id=cell_id,
        cell_type=cell_type,
        public_safe=public_safe,
    )
    selected_tag = selected_skill_tag_from_inputs(selected_skill_tag, router, executor)
    dashboard_row = selected_dashboard_row(dashboard, selected_tag, focus_query or query)
    history_entries = selected_history_entries(history, selected_tag)
    local_cycle_chain_snapshot = selected_local_cycle_chain_snapshot(
        provided_snapshot=python_exam_local_cycle_chain_snapshot,
        python_exam_local_cycle_readiness_review=python_exam_local_cycle_readiness_review,
        python_exam_local_cycle_readiness_handoff=python_exam_local_cycle_readiness_handoff,
        python_exam_local_cycle_operator_workspace_card=python_exam_local_cycle_operator_workspace_card,
    )
    packet = {
        "schema_version": EXAM_RUN_PACKET_SCHEMA_VERSION,
        "artifact_type": "exam_run_packet",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": "exam_run_packet_ready",
        "packet_title": "Exam Run Packet",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Exam Run Packet. It condenses Course Coverage Dashboard, Per-Skill Action Router, Routed Action "
            "Executor, Session Console receipts, and Run-History Export Review into one human-reviewable "
            "work packet. It contains metadata, hashes, receipts, help-level profile, open confirmations, and "
            "next safe action only. It never returns raw queries, course raw text, notebook code, local paths, "
            "values, solutions, final interpretations, proctoring, AI detection, automatic assessment, or exam "
            "clearance."
        ),
        "selected_skill_packet": selected_skill_packet(
            dashboard_row=dashboard_row,
            router=router,
            executor=executor,
            history=history,
            history_entries=history_entries,
        ),
        "packet_summary": packet_summary(dashboard, router, executor, history, history_entries, local_cycle_chain_snapshot),
        "local_cycle_chain_snapshot": local_cycle_chain_snapshot,
        "human_reviewable_independence_trace": independence_trace(
            dashboard_row=dashboard_row,
            router=router,
            executor=executor,
            history=history,
            history_entries=history_entries,
        ),
        "packet_receipt": packet_receipt(safe_id, dashboard_row, router, executor, history),
        "source_receipts": source_receipts(dashboard, router, executor, history),
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
            "Reale Pruefungsfreigabe bleibt ausserhalb des Bots; das Exam Run Packet bleibt not_cleared."
        ),
        "next_actions": packet_next_actions(router, executor, dashboard_row),
    }
    attach_public_scan(packet, public_safe=public_safe)
    packet["workspace_card_packet_alignment"] = build_exam_run_packet_workspace_card_alignment(packet)
    attach_public_scan(packet, public_safe=public_safe)
    return packet


def exam_run_packet_hash(packet: dict[str, Any] | None = None) -> str:
    packet = packet if isinstance(packet, dict) else {}
    return sha256_text(
        json.dumps(
            {
                "schema_version": packet.get("schema_version", ""),
                "artifact_type": packet.get("artifact_type", ""),
                "status": packet.get("status", ""),
                "course_id": packet.get("course_id", ""),
                "exam_deployment_status": packet.get("exam_deployment_status", ""),
                "selected_skill_packet": packet.get("selected_skill_packet", {}),
                "packet_summary": packet.get("packet_summary", {}),
                "local_cycle_chain_snapshot": packet.get("local_cycle_chain_snapshot", {}),
                "human_reviewable_independence_trace": packet.get("human_reviewable_independence_trace", {}),
                "source_receipts": packet.get("source_receipts", {}),
                "public_safety_status": packet.get("public_safety_status", ""),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def exam_run_packet_receipt_hash(packet: dict[str, Any] | None = None) -> str:
    packet = packet if isinstance(packet, dict) else {}
    receipt = packet.get("packet_receipt", {}) if isinstance(packet.get("packet_receipt"), dict) else {}
    return sha256_text(
        json.dumps(
            {
                "receipt_status": receipt.get("status", ""),
                "receipt_id": receipt.get("receipt_id", ""),
                "receipt_hash": receipt.get("receipt_hash", ""),
                "exam_deployment_status": receipt.get("exam_deployment_status", ""),
                "not_cleared_receipt": receipt.get("not_cleared_receipt", None),
                "selected_skill_packet_hash": sha256_text(
                    json.dumps(packet.get("selected_skill_packet", {}), sort_keys=True, ensure_ascii=False)
                ),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def synthetic_exam_run_packet_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic exam run packet workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "python_lists",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic exam run packet prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "python_lists",
            "next_safe_action": "review_exam_run_packet_hashes_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_packet_before_exam_like_use_or_public_claim",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__EXAM_RUN_PACKET_RECEIPT_HASH__",
            "checkpoint_hash": "__EXAM_RUN_PACKET_HASH__",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "zai-glm-52"],
            "source_anchor_count": 3,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": "A2",
            "preview_hash": preview_hash,
        },
    }


def safe_exam_run_packet_workspace_card(
    workspace_card: dict[str, Any],
    *,
    packet_hash: str = "",
    receipt_hash: str = "",
) -> dict[str, Any]:
    summary = workspace_card.get("workspace_card_summary", {}) if isinstance(workspace_card.get("workspace_card_summary"), dict) else {}
    ledger = workspace_card.get("help_ledger_preview", {}) if isinstance(workspace_card.get("help_ledger_preview"), dict) else {}
    if not summary and (
        workspace_card.get("help_ledger_preview_hash") is not None
        or workspace_card.get("ready_for_operator_prefill") is not None
        or workspace_card.get("help_ledger_preview_status") is not None
    ):
        summary = workspace_card
    checkpoint_hash = str(summary.get("checkpoint_hash", ""))
    task_hash = str(summary.get("task_hash", ""))
    if packet_hash and checkpoint_hash == "__EXAM_RUN_PACKET_HASH__":
        checkpoint_hash = packet_hash
    if receipt_hash and task_hash == "__EXAM_RUN_PACKET_RECEIPT_HASH__":
        task_hash = receipt_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", "keep_blocked")),
        "recommendation_reason": str(summary.get("recommendation_reason", "missing_exam_run_packet_gate")),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "help_ledger_preview_status": str(summary.get("help_ledger_preview_status", ledger.get("status", "missing"))),
        "next_safe_action": str(summary.get("next_safe_action", "")),
        "next_safe_user_action": str(summary.get("next_safe_user_action", "")),
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", "")),
        "operator_run_method": str(summary.get("operator_run_method", "POST")),
        "help_level": str(summary.get("help_level", ledger.get("help_level", "A2"))),
        "task_hash": task_hash,
        "checkpoint_hash": checkpoint_hash,
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "help_ledger_preview_hash": str(summary.get("help_ledger_preview_hash", ledger.get("preview_hash", ""))),
        "not_cleared_receipt": bool(workspace_card.get("not_cleared_receipt", True)),
        "exam_deployment_status": "not_cleared",
        "raw_workspace_card_returned": False,
    }


def build_exam_run_packet_workspace_card_alignment(
    exam_run_packet: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    packet = exam_run_packet if isinstance(exam_run_packet, dict) else {}
    skill = packet.get("selected_skill_packet", {}) if isinstance(packet.get("selected_skill_packet"), dict) else {}
    route = skill.get("selected_route", {}) if isinstance(skill.get("selected_route"), dict) else {}
    executed = skill.get("executed_dry_run", {}) if isinstance(skill.get("executed_dry_run"), dict) else {}
    receipt = packet.get("packet_receipt", {}) if isinstance(packet.get("packet_receipt"), dict) else {}
    chain_snapshot = (
        packet.get("local_cycle_chain_snapshot", {})
        if isinstance(packet.get("local_cycle_chain_snapshot"), dict)
        else {}
    )
    packet_hash = exam_run_packet_hash(packet)
    receipt_hash = exam_run_packet_receipt_hash(packet)
    workspace_card = safe_exam_run_packet_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else synthetic_exam_run_packet_workspace_card(),
        packet_hash=packet_hash,
        receipt_hash=receipt_hash,
    )
    workspace_card_readiness_gate_linked = (
        workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and workspace_card.get("help_ledger_preview_hash") != ""
        and workspace_card.get("exam_deployment_status") == "not_cleared"
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card.get("raw_workspace_card_returned") is False
    )
    raw_flag_names = [
        "raw_query_returned",
        "raw_text_returned",
        "raw_cell_returned",
        "raw_notebook_returned",
        "notebook_code_returned",
        "local_paths_returned",
    ]
    high_stakes_flag_names = [
        "automatic_grading_started",
        "proctoring_started",
        "ai_detection_started",
        "exam_clearance_claimed",
    ]
    contracts = {
        "packet_public_safe": packet.get("public_safety_status") == "pass",
        "packet_ready": packet.get("status") == "exam_run_packet_ready" and bool(skill),
        "receipt_ready_not_clearance": receipt.get("status") == "exam_run_packet_receipt_ready_not_exam_clearance"
        and bool(receipt.get("receipt_id"))
        and bool(receipt.get("receipt_hash"))
        and receipt.get("not_cleared_receipt") is True,
        "route_execution_metadata_present": bool(route.get("route_id"))
        and bool(executed.get("artifact_type"))
        and bool(executed.get("status"))
        and bool(executed.get("result_hash")),
        "local_cycle_chain_snapshot_preserved": chain_snapshot.get("status") == "python_exam_local_cycle_chain_snapshot_ready"
        and bool(chain_snapshot.get("snapshot_hash")),
        "local_write_boundary_preserved": executed.get("local_write_started") is False,
        "no_clearance_or_deployment_claim": packet.get("exam_deployment_status") == "not_cleared"
        and receipt.get("exam_deployment_status") == "not_cleared"
        and skill.get("exam_deployment_status") == "not_cleared",
        "metadata_only_safety_flags_false": all(packet.get(flag) is False for flag in raw_flag_names)
        and all(receipt.get(flag, False) is False for flag in raw_flag_names)
        and all(skill.get(flag, False) is False for flag in raw_flag_names),
        "high_stakes_boundaries_blocked": all(packet.get(flag) is False for flag in high_stakes_flag_names),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_exam_run_packet_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("checkpoint_hash") == packet_hash
        and workspace_card.get("task_hash") == receipt_hash,
        "workspace_card_public_metadata_only": workspace_card.get("raw_workspace_card_returned") is False,
    }
    required_readiness_check_ids = [
        "exam_run_packet",
        "exam_packet_timeline",
        "timeline_export_review_packet",
        "python_exam_local_cycle_operator_workspace_card",
    ]
    alignment = {
        "schema_version": EXAM_RUN_PACKET_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION,
        "status": "ready",
        "exam_run_packet_hash": packet_hash,
        "exam_run_packet_receipt_hash": receipt_hash,
        "packet_status": packet.get("status", "missing"),
        "receipt_status": receipt.get("status", "missing"),
        "skill_tag": skill.get("skill_tag", ""),
        "route_id": route.get("route_id", "missing"),
        "executed_artifact_type": executed.get("artifact_type", "missing"),
        "executed_status": executed.get("status", "missing"),
        "executed_result_hash_present": bool(executed.get("result_hash")),
        "local_write_started": bool(executed.get("local_write_started", True)),
        "local_cycle_chain_snapshot_status": chain_snapshot.get("status", "missing"),
        "local_cycle_chain_snapshot_hash_present": bool(chain_snapshot.get("snapshot_hash")),
        "exam_deployment_status": packet.get("exam_deployment_status", "missing"),
        "required_readiness_check_ids": required_readiness_check_ids,
        "required_human_gates": [
            "human_review_required",
            "public_safety_required",
            "operator_confirmation_required_for_local_write",
            "exam_clearance_requires_written_authority_clearance",
        ],
        "blocked_claims": [
            "raw private course text publication",
            "contact data publication",
            "local path publication",
            "provider call",
            "autonomous publication",
            "approval claim",
            "exam clearance claim",
            "grading",
            "proctoring",
            "KI-detection evidence",
            "exam deployment",
        ],
        "contracts": contracts,
        "failed_contract_ids": sorted(contract_id for contract_id, passed in contracts.items() if not passed),
        "workspace_card_status": workspace_card["status"],
        "workspace_card_selected_skill_tag": workspace_card["selected_skill_tag"],
        "workspace_card_ready_for_operator_prefill": workspace_card["ready_for_operator_prefill"],
        "workspace_card_help_ledger_status": workspace_card["help_ledger_preview_status"],
        "workspace_card_help_ledger_hash_present": workspace_card["help_ledger_preview_hash"] != "",
        "workspace_card_operator_prefill_hash_present": workspace_card["task_hash"] != ""
        and workspace_card["checkpoint_hash"] != "",
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_exam_run_packet_gate_linked": contracts["workspace_card_exam_run_packet_gate_linked"],
        "workspace_card_readiness_gate_claim_linked": "python_exam_local_cycle_operator_workspace_card"
        in required_readiness_check_ids,
        "raw_workspace_card_returned": workspace_card["raw_workspace_card_returned"],
        "public_language": (
            "Exam run packet claims are hash-only review aids for selected skill packet, route execution "
            "metadata, packet receipt, local-cycle chain snapshot, and local-write boundaries; they do not "
            "authorize publication, provider calls, grading, proctoring, KI detection, or exam use."
        ),
    }
    if alignment["failed_contract_ids"]:
        alignment["status"] = "blocked"
    scan = scan_text(
        json.dumps(alignment, ensure_ascii=False, sort_keys=True),
        "exam-run-packet-workspace-card-alignment",
    )
    alignment["alignment_public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked"
        alignment["public_safety_findings"] = scan["findings"]
    return alignment


def synthetic_exam_run_packet_inputs() -> dict[str, Any]:
    snapshot_hash = sha256_text("synthetic exam run packet local cycle chain snapshot")
    packet = build_exam_run_packet(
        selected_skill_tag="python_lists",
        focus_query="Python Listen",
        python_exam_local_cycle_chain_snapshot={
            "schema_version": "unibot-python-exam-local-cycle-chain-snapshot-v1",
            "artifact_type": "python_exam_local_cycle_chain_snapshot",
            "status": "python_exam_local_cycle_chain_snapshot_ready",
            "selected_skill_tag": "python_lists",
            "snapshot_hash": snapshot_hash,
            "chain_step_count": 4,
            "exam_deployment_status": "not_cleared",
            "raw_query_returned": False,
            "raw_text_returned": False,
            "raw_cell_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
        },
        public_safe=True,
    )
    return {"exam_run_packet": packet}


def selected_skill_tag_from_inputs(selected_skill_tag: str, router: dict[str, Any], executor: dict[str, Any]) -> str:
    if selected_skill_tag:
        return str(selected_skill_tag)
    for source in (executor.get("selected_skill", {}), router.get("selected_skill", {}), router.get("selected_route", {})):
        if isinstance(source, dict) and source.get("skill_tag"):
            return str(source.get("skill_tag"))
    return ""


def selected_dashboard_row(dashboard: dict[str, Any], selected_tag: str, focus: str) -> dict[str, Any]:
    rows = [item for item in dashboard.get("skill_dashboard", []) if isinstance(item, dict)]
    selected_lower = str(selected_tag or "").lower()
    focus_lower = str(focus or "").lower()
    for row in rows:
        tag = str(row.get("skill_tag", "")).lower()
        if selected_lower and (selected_lower == tag or selected_lower in tag or tag in selected_lower):
            return row
    for row in rows:
        tag = str(row.get("skill_tag", "")).lower()
        if focus_lower and (focus_lower == tag or focus_lower in tag or tag in focus_lower):
            return row
    return rows[0] if rows else {}


def selected_history_entries(history: dict[str, Any], selected_tag: str) -> list[dict[str, Any]]:
    entries = [item for item in history.get("run_history", []) if isinstance(item, dict)]
    if not selected_tag:
        return entries[:12]
    selected = str(selected_tag)
    return [item for item in entries if str(item.get("skill_tag", "")) == selected][:12]


def selected_skill_packet(
    *,
    dashboard_row: dict[str, Any],
    router: dict[str, Any],
    executor: dict[str, Any],
    history: dict[str, Any],
    history_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    route = router.get("selected_route", {}) if isinstance(router.get("selected_route"), dict) else {}
    result = executor.get("execution_result_summary", {}) if isinstance(executor.get("execution_result_summary"), dict) else {}
    return {
        "skill_tag": dashboard_row.get("skill_tag", route.get("skill_tag", "")),
        "title": dashboard_row.get("title", ""),
        "workspace_readiness": dashboard_row.get("workspace_readiness", "unknown"),
        "coverage_gap_status": dashboard_row.get("coverage_gap_status", "unknown"),
        "source_anchor_count": int(dashboard_row.get("source_anchor_count", 0) or 0),
        "reviewed_notebook_anchor_count": int(dashboard_row.get("reviewed_notebook_anchor_count", 0) or 0),
        "selected_route": {
            "route_id": route.get("route_id", "unknown"),
            "endpoint": route.get("endpoint", ""),
            "dry_run_by_default": bool(route.get("dry_run_by_default", True)),
            "requested_help_level": route.get("requested_help_level", "A2"),
        },
        "executed_dry_run": {
            "artifact_type": result.get("artifact_type", "unknown"),
            "status": result.get("status", "unknown"),
            "result_hash": result.get("result_hash", ""),
            "receipt_status": result.get("receipt", {}).get("status", "unknown")
            if isinstance(result.get("receipt"), dict)
            else "unknown",
            "local_write_started": bool(result.get("local_write_started", False)),
        },
        "latest_checkpoint_hashes": list(dashboard_row.get("latest_checkpoint_hashes", []) or [])[:4]
        or [str(item.get("checkpoint_hash", "")) for item in history_entries if item.get("checkpoint_hash")][:4],
        "help_level_profile": dict(dashboard_row.get("help_level_profile", {}) or history.get("history_summary", {}).get("help_level_profile", {}) or {}),
        "open_operator_confirmations": list(dashboard_row.get("open_operator_confirmations", []) or [])[:8],
        "open_operator_confirmation_count": int(dashboard_row.get("open_operator_confirmation_count", 0) or 0),
        "next_safe_action": next_safe_action(dashboard_row, router, executor),
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def packet_summary(
    dashboard: dict[str, Any],
    router: dict[str, Any],
    executor: dict[str, Any],
    history: dict[str, Any],
    history_entries: list[dict[str, Any]],
    local_cycle_chain_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dashboard_summary = dashboard.get("dashboard_summary", {}) if isinstance(dashboard.get("dashboard_summary"), dict) else {}
    result = executor.get("execution_result_summary", {}) if isinstance(executor.get("execution_result_summary"), dict) else {}
    chain_snapshot = local_cycle_chain_snapshot if isinstance(local_cycle_chain_snapshot, dict) else {}
    return {
        "dashboard_status": dashboard.get("status", "unknown"),
        "router_status": router.get("status", "unknown"),
        "executor_status": executor.get("status", "unknown"),
        "executed_artifact_type": result.get("artifact_type", "unknown"),
        "executed_status": result.get("status", "unknown"),
        "skill_count": dashboard_summary.get("skill_count", 0),
        "workspace_ready_skill_count": dashboard_summary.get("workspace_ready_skill_count", 0),
        "history_entry_count_for_skill": len(history_entries),
        "checkpoint_hash_count": len([item for item in history_entries if item.get("checkpoint_hash")]),
        "help_level_profile": dict(dashboard_summary.get("help_level_profile", {}) or {}),
        "local_cycle_chain_snapshot_status": str(chain_snapshot.get("status", "missing")),
        "local_cycle_chain_snapshot_hash": str(chain_snapshot.get("snapshot_hash", "")),
        "exam_deployment_status": "not_cleared",
    }


def selected_local_cycle_chain_snapshot(
    *,
    provided_snapshot: dict[str, Any] | None,
    python_exam_local_cycle_readiness_review: dict[str, Any] | None,
    python_exam_local_cycle_readiness_handoff: dict[str, Any] | None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None,
) -> dict[str, Any]:
    if isinstance(provided_snapshot, dict):
        return provided_snapshot
    review = python_exam_local_cycle_readiness_review if isinstance(python_exam_local_cycle_readiness_review, dict) else {}
    handoff = python_exam_local_cycle_readiness_handoff if isinstance(python_exam_local_cycle_readiness_handoff, dict) else {}
    workspace_card = (
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {}
    )
    if not review and not handoff and not workspace_card:
        return {}
    snapshot = build_python_exam_local_cycle_chain_snapshot(
        python_exam_local_cycle_readiness_review=review,
        python_exam_local_cycle_readiness_handoff=handoff,
        python_exam_local_cycle_operator_workspace_card=workspace_card,
        public_safe=True,
    )
    return snapshot if isinstance(snapshot, dict) else {}


def independence_trace(
    *,
    dashboard_row: dict[str, Any],
    router: dict[str, Any],
    executor: dict[str, Any],
    history: dict[str, Any],
    history_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    result = executor.get("execution_result_summary", {}) if isinstance(executor.get("execution_result_summary"), dict) else {}
    return {
        "trace_status": "human_reviewable_independence_trace_ready",
        "evidence_mode": "hashes_receipts_help_profile_and_review_steps",
        "no_percentage_claimed": True,
        "route_id": router.get("selected_route", {}).get("route_id", "")
        if isinstance(router.get("selected_route"), dict)
        else "",
        "executor_receipt_id": executor.get("executor_receipt", {}).get("receipt_id", "")
        if isinstance(executor.get("executor_receipt"), dict)
        else "",
        "dry_run_result_hash": result.get("result_hash", ""),
        "checkpoint_hashes": list(dashboard_row.get("latest_checkpoint_hashes", []) or [])[:4]
        or [str(item.get("checkpoint_hash", "")) for item in history_entries if item.get("checkpoint_hash")][:4],
        "help_level_profile": dict(dashboard_row.get("help_level_profile", {}) or history.get("history_summary", {}).get("help_level_profile", {}) or {}),
        "blocker_profile": dict(history.get("history_summary", {}).get("blocker_profile", {}) or {}),
        "reflection_statuses": reflection_statuses(history_entries),
        "open_operator_confirmations": list(dashboard_row.get("open_operator_confirmations", []) or [])[:8],
        "human_review_required": True,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def reflection_statuses(entries: list[dict[str, Any]]) -> list[str]:
    statuses = []
    for entry in entries:
        status = str(entry.get("reflection_status", ""))
        if status and status not in statuses:
            statuses.append(status)
    return statuses[:8]


def source_receipts(
    dashboard: dict[str, Any],
    router: dict[str, Any],
    executor: dict[str, Any],
    history: dict[str, Any],
) -> dict[str, Any]:
    return {
        "dashboard_receipt_id": dashboard.get("coverage_receipt", {}).get("receipt_id", "")
        if isinstance(dashboard.get("coverage_receipt"), dict)
        else "",
        "router_receipt_id": router.get("router_receipt", {}).get("receipt_id", "")
        if isinstance(router.get("router_receipt"), dict)
        else "",
        "executor_receipt_id": executor.get("executor_receipt", {}).get("receipt_id", "")
        if isinstance(executor.get("executor_receipt"), dict)
        else "",
        "history_receipt_id": history.get("export_review_receipt", {}).get("receipt_id", "")
        if isinstance(history.get("export_review_receipt"), dict)
        else "",
        "not_cleared_receipts": True,
        "raw_receipts_returned": False,
    }


def packet_receipt(
    course_id: str,
    dashboard_row: dict[str, Any],
    router: dict[str, Any],
    executor: dict[str, Any],
    history: dict[str, Any],
) -> dict[str, Any]:
    seed = {
        "course_id": course_id,
        "skill_tag": dashboard_row.get("skill_tag", ""),
        "route": router.get("selected_route", {}),
        "executor": executor.get("executor_receipt", {}),
        "history": history.get("export_review_receipt", {}),
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "exam_run_packet_receipt_ready_not_exam_clearance",
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


def next_safe_action(dashboard_row: dict[str, Any], router: dict[str, Any], executor: dict[str, Any]) -> str:
    for source in (executor, router):
        actions = source.get("next_actions", []) if isinstance(source.get("next_actions"), list) else []
        if actions:
            return str(actions[0])
    return str(dashboard_row.get("next_safe_step", "review packet with a human reviewer"))


def packet_next_actions(router: dict[str, Any], executor: dict[str, Any], dashboard_row: dict[str, Any]) -> list[str]:
    action = next_safe_action(dashboard_row, router, executor)
    return [
        "Review the Exam Run Packet before relying on it in any exam-like workflow.",
        action,
        "Keep real-world exam clearance outside UniBot; this packet remains not_cleared.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "exam-run-packet")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
