from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .exam_skill_drilldown import build_exam_skill_drilldown
from .exam_workspace_operator_run import build_exam_workspace_operator_run_dry_run
from .materials import sha256_text
from .public_safety import scan_text


SKILL_TO_WORKSPACE_LIVE_FLOW_SCHEMA_VERSION = "unibot-skill-to-workspace-live-flow-v1"
SKILL_TO_WORKSPACE_LIVE_FLOW_ENDPOINT = "/api/unibot/course/skill-to-workspace-live-flow"
OPERATOR_RUN_ENDPOINT = "/api/unibot/exam-workspace/operator-run"


def build_skill_to_workspace_live_flow(
    *,
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
    operator_confirmed_checkpoint_store: bool = False,
    operator_confirmed_exam_workspace_run: bool = False,
    operator_confirmed_manifest_apply: bool = False,
    operator_confirmed_tutor_index_build: bool = False,
    operator_confirmed_help_ledger_append: bool = False,
    operator_confirmed_exam_ledger_append: bool = False,
    public_safe: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    help_level = safe_help_level(requested_help_level)
    drilldown = build_exam_skill_drilldown(
        safe_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=str(decision_record_journal_path) if decision_record_journal_path else None,
        receipts=receipts,
        receipt_journal_path=str(receipt_journal_path) if receipt_journal_path else None,
        private_manifest_path=str(private_manifest_path) if private_manifest_path else None,
        manifest_apply_journal_path=str(manifest_apply_journal_path) if manifest_apply_journal_path else None,
        tutor_index_path=str(tutor_index_path) if tutor_index_path else None,
        tutor_index_journal_path=str(tutor_index_journal_path) if tutor_index_journal_path else None,
        focus_query=focus_query,
        selected_skill_tag=selected_skill_tag,
        public_safe=public_safe,
    )
    selected = drilldown.get("selected_skill", {}) if isinstance(drilldown.get("selected_skill"), dict) else {}
    selected_tag = str(selected.get("skill_tag") or selected_skill_tag or "").strip()
    live = drilldown.get("skill_to_workspace_live_flow", {}) if isinstance(drilldown.get("skill_to_workspace_live_flow"), dict) else {}
    ready = live.get("status") == "ready_to_execute_operator_dry_run"
    operator = {}
    if ready:
        operator = build_exam_workspace_operator_run_dry_run(
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
            focus_query=selected_tag,
            query=selected_tag,
            requested_help_level=help_level,
            exam_status=exam_status,
            student_reflection=student_reflection,
            study_receipt=study_receipt or default_study_receipt(selected),
            notebook_checkpoint=notebook_checkpoint,
            cell_source=cell_source,
            cell_index=cell_index,
            cell_id=cell_id,
            cell_type=cell_type,
            checkpoint_journal_path=checkpoint_journal_path,
            operator_confirmed_checkpoint_store=operator_confirmed_checkpoint_store,
            operator_confirmed_exam_workspace_run=operator_confirmed_exam_workspace_run,
            operator_confirmed_manifest_apply=operator_confirmed_manifest_apply,
            operator_confirmed_tutor_index_build=operator_confirmed_tutor_index_build,
            operator_confirmed_help_ledger_append=operator_confirmed_help_ledger_append,
            operator_confirmed_exam_ledger_append=operator_confirmed_exam_ledger_append,
            public_safe=public_safe,
        )
    summary = live_flow_summary(drilldown, operator, ready=ready, help_level=help_level)
    report = {
        "schema_version": SKILL_TO_WORKSPACE_LIVE_FLOW_SCHEMA_VERSION,
        "artifact_type": "skill_to_workspace_live_flow",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Skill-to-Workspace Live Flow. It selects one Python exam skill from the Exam-Skill-Drilldown, "
            "prefills the Start Exam Workspace Operator Run with A0-A2 help, source-card metadata, notebook "
            "checkpoint template, Help-Ledger preview, and explicit operator confirmations, then executes the "
            "operator dry-run by default. It returns only safe metadata and never returns raw queries, course raw "
            "text, notebook code, local paths, values, solutions, final interpretations, proctoring, AI detection, "
            "automatic grading, or exam clearance."
        ),
        "flow_endpoint": SKILL_TO_WORKSPACE_LIVE_FLOW_ENDPOINT,
        "drilldown_status": drilldown.get("status", "unknown"),
        "operator_run_status": operator.get("status", "not_started_skill_not_ready"),
        "exam_skill_drilldown": drilldown,
        "live_flow_summary": summary,
        "selected_skill": safe_selected_skill(selected),
        "source_anchor_metadata": safe_source_anchor_metadata(selected),
        "operator_prefill": operator_prefill(drilldown, help_level=help_level),
        "notebook_checkpoint_template": drilldown.get("notebook_checkpoint_template", {}),
        "help_ledger_preview_template": drilldown.get("help_ledger_preview_template", {}),
        "operator_confirmation_matrix": operator.get("operator_confirmation_matrix", dry_run_confirmation_matrix()),
        "start_exam_workspace_view": operator.get("start_exam_workspace_view", {}),
        "dry_run_receipt": operator.get("dry_run_receipt", {}),
        "operator_dry_run": operator,
        "dry_run_default": True,
        "a0_a2_only": summary["a0_a2_only"],
        "local_writes_requested": bool(
            (operator.get("operator_confirmation_matrix", {}) if isinstance(operator.get("operator_confirmation_matrix"), dict) else {}).get(
                "local_writes_requested",
                False,
            )
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
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Skill-to-Workspace Flow bleibt not_cleared."
        ),
        "next_actions": live_flow_next_actions(summary, drilldown, operator),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def safe_help_level(requested_help_level: str) -> str:
    level = str(requested_help_level or "A2").strip().upper()
    return level if level in {"A0", "A1", "A2"} else "A2"


def default_study_receipt(selected_skill: dict[str, Any]) -> dict[str, Any]:
    return {
        "prediction_present": False,
        "retrieval_response_present": bool(selected_skill.get("source_card_ids")),
        "notebook_action_present": False,
        "reflection_present": False,
    }


def safe_selected_skill(selected: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_tag": selected.get("skill_tag", ""),
        "title": selected.get("title", ""),
        "exam_task_type": selected.get("exam_task_type", ""),
        "exam_workspace_readiness": selected.get("exam_workspace_readiness", "unknown"),
        "start_button_enabled": bool(selected.get("start_button_enabled", False)),
        "recommended_help_level": "A2",
        "source_anchor_count": selected.get("source_anchor_count", 0),
        "reviewed_notebook_anchor_count": selected.get("reviewed_notebook_anchor_count", 0),
        "source_card_ids": list(selected.get("source_card_ids", []) or [])[:8],
    }


def safe_source_anchor_metadata(selected: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_tag": selected.get("skill_tag", ""),
        "source_card_ids": list(selected.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": selected.get("source_anchor_count", 0),
        "reviewed_notebook_anchor_count": selected.get("reviewed_notebook_anchor_count", 0),
        "source_anchor_ids_returned": False,
        "raw_anchor_text_returned": False,
        "local_paths_returned": False,
    }


def operator_prefill(drilldown: dict[str, Any], *, help_level: str) -> dict[str, Any]:
    template = drilldown.get("operator_payload_template", {}) if isinstance(drilldown.get("operator_payload_template"), dict) else {}
    checkpoint = drilldown.get("notebook_checkpoint_template", {}) if isinstance(drilldown.get("notebook_checkpoint_template"), dict) else {}
    selected = drilldown.get("selected_skill", {}) if isinstance(drilldown.get("selected_skill"), dict) else {}
    source_card_ids = list(template.get("source_card_ids", selected.get("source_card_ids", [])) or [])[:8]
    prefill_seed = {
        "course_id": template.get("course_id", drilldown.get("course_id", "")),
        "selected_skill_tag": template.get("selected_skill_tag", selected.get("skill_tag", "")),
        "source_card_ids": source_card_ids,
        "task_id": template.get("task_id", checkpoint.get("task_id", "")),
        "requested_help_level": help_level,
        "checkpoint_template_hash": template.get("notebook_checkpoint_template_hash", ""),
    }
    return {
        "status": "prefill_ready" if template.get("status") == "template_ready" else "prefill_waiting_for_skill_readiness",
        "endpoint": OPERATOR_RUN_ENDPOINT if template.get("endpoint") else "",
        "method": "POST" if template.get("endpoint") else "",
        "selected_skill_tag": prefill_seed["selected_skill_tag"],
        "task_id": prefill_seed["task_id"],
        "source_card_ids": source_card_ids,
        "source_anchor_count": selected.get("source_anchor_count", template.get("source_anchor_count", 0)),
        "requested_help_level": help_level,
        "exam_status": "strict",
        "dry_run_default": True,
        "operator_confirmations_default": "all_false_dry_run",
        "notebook_checkpoint_template_hash": prefill_seed["checkpoint_template_hash"],
        "prefill_hash": sha256_text(json.dumps(prefill_seed, sort_keys=True, ensure_ascii=False)),
        "raw_query_included": False,
        "raw_cell_included": False,
        "raw_source_text_included": False,
        "notebook_code_included": False,
        "local_paths_returned": False,
        "exam_deployment_status": "not_cleared",
    }


def dry_run_confirmation_matrix() -> dict[str, Any]:
    return {
        "status": "not_started_skill_not_ready",
        "confirmed_count": 0,
        "write_step_count": 6,
        "default_policy": "dry_run_until_individual_operator_confirmation",
        "steps": {},
        "local_writes_requested": False,
    }


def live_flow_summary(
    drilldown: dict[str, Any],
    operator: dict[str, Any],
    *,
    ready: bool,
    help_level: str,
) -> dict[str, Any]:
    operator_status = str(operator.get("status", "not_started_skill_not_ready"))
    receipt = operator.get("dry_run_receipt", {}) if isinstance(operator.get("dry_run_receipt"), dict) else {}
    confirmations = (
        operator.get("operator_confirmation_matrix", {}) if isinstance(operator.get("operator_confirmation_matrix"), dict) else {}
    )
    if not ready:
        status = "skill_to_workspace_live_flow_waiting_for_skill_readiness"
    elif operator_status in {"exam_workspace_operator_dry_run_ready", "exam_workspace_operator_ready_with_confirmed_local_writes"}:
        status = "skill_to_workspace_live_flow_ready"
    else:
        status = "skill_to_workspace_live_flow_attention"
    return {
        "status": status,
        "selected_skill_tag": (drilldown.get("selected_skill", {}) if isinstance(drilldown.get("selected_skill"), dict) else {}).get(
            "skill_tag",
            "",
        ),
        "drilldown_status": drilldown.get("status", "unknown"),
        "operator_run_status": operator_status,
        "operator_receipt_status": receipt.get("status", "not_started"),
        "receipt_id": receipt.get("receipt_id", ""),
        "requested_help_level": help_level,
        "a0_a2_only": help_level in {"A0", "A1", "A2"},
        "dry_run_default": True,
        "operator_confirmation_status": confirmations.get("status", "not_started_skill_not_ready"),
        "confirmed_operator_step_count": confirmations.get("confirmed_count", 0),
        "write_step_count": confirmations.get("write_step_count", 6),
        "local_writes_requested": bool(confirmations.get("local_writes_requested", False)),
        "not_cleared_receipt": bool(receipt.get("not_cleared_receipt", True)),
        "exam_deployment_status": "not_cleared",
    }


def live_flow_next_actions(
    summary: dict[str, Any],
    drilldown: dict[str, Any],
    operator: dict[str, Any],
) -> list[str]:
    if summary["status"] == "skill_to_workspace_live_flow_ready":
        return [
            "Review the Start Exam Workspace dry-run receipt before enabling any local write confirmation.",
            "Use A0-A2 only; do not request solutions, values, complete code, or final interpretations.",
            "Keep UniBot not_cleared until real-world exam approval is handled outside the tool.",
        ]
    if summary["status"] == "skill_to_workspace_live_flow_waiting_for_skill_readiness":
        return list(drilldown.get("next_actions", []) or [])[:5]
    return list(operator.get("next_actions", []) or drilldown.get("next_actions", []) or [])[:5]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "skill-to-workspace-live-flow")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
