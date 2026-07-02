from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_manual_confirmation_console import safe_help_level
from .python_exam_manual_cycle_closure_ledger import safe_post_cycle_intake
from .python_exam_manual_cycle_evidence_binder import safe_launch_receipt
from .python_exam_manual_cycle_launch_receipt import safe_manual_confirmation_console
from .python_exam_manual_cycle_review_packet import safe_review_timeline
from .python_exam_manual_cycle_review_timeline import safe_closure_ledger
from .python_exam_manual_post_cycle_receipt_intake import safe_evidence_binder


PYTHON_EXAM_MANUAL_REVIEW_EXPORT_PREVIEW_SCHEMA_VERSION = "unibot-python-exam-manual-review-export-preview-v1"
PYTHON_EXAM_MANUAL_REVIEW_EXPORT_PREVIEW_ENDPOINT = "/api/unibot/course/python-exam-manual-review-export-preview"

EXPORT_PREVIEW_RECOMMENDATIONS = {
    "keep_export_preview_open",
    "request_hash_completion",
    "ready_for_human_export_review",
    "reject_export_preview",
}


def build_python_exam_manual_review_export_preview(
    *,
    python_exam_manual_cycle_review_packet: dict[str, Any] | None = None,
    python_exam_manual_cycle_review_timeline: dict[str, Any] | None = None,
    python_exam_manual_cycle_closure_ledger: dict[str, Any] | None = None,
    python_exam_manual_post_cycle_receipt_intake: dict[str, Any] | None = None,
    python_exam_manual_cycle_evidence_binder: dict[str, Any] | None = None,
    python_exam_manual_cycle_launch_receipt: dict[str, Any] | None = None,
    python_exam_manual_confirmation_console: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    review_packet = (
        python_exam_manual_cycle_review_packet if isinstance(python_exam_manual_cycle_review_packet, dict) else {}
    )
    review_timeline = (
        python_exam_manual_cycle_review_timeline if isinstance(python_exam_manual_cycle_review_timeline, dict) else {}
    )
    closure_ledger = (
        python_exam_manual_cycle_closure_ledger if isinstance(python_exam_manual_cycle_closure_ledger, dict) else {}
    )
    post_cycle_intake = (
        python_exam_manual_post_cycle_receipt_intake
        if isinstance(python_exam_manual_post_cycle_receipt_intake, dict)
        else {}
    )
    evidence_binder = (
        python_exam_manual_cycle_evidence_binder if isinstance(python_exam_manual_cycle_evidence_binder, dict) else {}
    )
    launch_receipt = python_exam_manual_cycle_launch_receipt if isinstance(python_exam_manual_cycle_launch_receipt, dict) else {}
    manual_console = (
        python_exam_manual_confirmation_console if isinstance(python_exam_manual_confirmation_console, dict) else {}
    )
    packet_view = safe_review_packet(review_packet)
    timeline_view = safe_review_timeline(review_timeline)
    closure_view = safe_closure_ledger(closure_ledger)
    intake_view = safe_post_cycle_intake(post_cycle_intake)
    binder_view = safe_evidence_binder(evidence_binder)
    launch_view = safe_launch_receipt(launch_receipt)
    console_view = safe_manual_confirmation_console(manual_console)
    selected = str(
        selected_skill_tag
        or packet_view.get("selected_skill_tag", "")
        or timeline_view.get("selected_skill_tag", "")
        or closure_view.get("selected_skill_tag", "")
        or intake_view.get("selected_skill_tag", "")
        or binder_view.get("selected_skill_tag", "")
        or launch_view.get("selected_skill_tag", "")
        or console_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    manifest = export_manifest_preview(
        packet_view=packet_view,
        timeline_view=timeline_view,
        closure_view=closure_view,
        intake_view=intake_view,
        binder_view=binder_view,
        launch_view=launch_view,
        console_view=console_view,
    )
    summary = export_preview_summary(selected_skill_tag=selected, packet_view=packet_view, manifest=manifest)
    receipt = export_preview_receipt(summary, manifest)
    payload = {
        "schema_version": PYTHON_EXAM_MANUAL_REVIEW_EXPORT_PREVIEW_SCHEMA_VERSION,
        "artifact_type": "python_exam_manual_review_export_preview",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_manual_review_export_preview_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Manual Review Export Preview. It consumes only Manual Cycle Review Packet, Review "
            "Timeline, Closure Ledger, Post-Cycle Receipt Intake, Evidence Binder, Launch Receipt, and Manual "
            "Confirmation Console metadata to build an exportable hash-only preview for human review before "
            "archiving or submission. It creates no export, writes nothing, and exposes only recommendation "
            "state, missing/accepted hashes, Source-Card anchors, task/checkpoint hashes, Help-Ledger hash, "
            "operator reflection hash, receipt hashes, timeline event hashes, export manifest hash, and one "
            "export-preview recommendation. It never returns raw queries, course raw text, notebook code, local "
            "paths, values, solutions, final interpretations, scores, rankings, grades, proctoring, AI detection, "
            "automatic grading, or exam clearance claims."
        ),
        "manual_review_export_preview_endpoint": PYTHON_EXAM_MANUAL_REVIEW_EXPORT_PREVIEW_ENDPOINT,
        "selected_skill_tag": selected,
        "export_preview_summary": summary,
        "export_preview_recommendation": summary["export_preview_recommendation"],
        "export_manifest_preview": manifest,
        "manual_review_export_preview_receipt": receipt,
        "dry_run_default": True,
        "export_created": False,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; die Export Preview bleibt not_cleared."
        ),
        "next_actions": [
            f"Export preview recommendation: {summary['export_preview_recommendation']}.",
            "Use this preview only for human review before a later explicit export decision.",
            "Keep raw notebook work, values, local files, scoring, and real exam clearance outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_review_packet(packet: dict[str, Any]) -> dict[str, Any]:
    summary = packet.get("review_packet_summary", {}) if isinstance(packet.get("review_packet_summary"), dict) else {}
    body = packet.get("review_packet_body", {}) if isinstance(packet.get("review_packet_body"), dict) else {}
    receipt = (
        packet.get("manual_cycle_review_packet_receipt", {})
        if isinstance(packet.get("manual_cycle_review_packet_receipt"), dict)
        else {}
    )
    receipt_hashes = summary.get("receipt_hashes") or body.get("receipt_hashes", {})
    if not isinstance(receipt_hashes, dict):
        receipt_hashes = {}
    accepted_hashes = summary.get("accepted_post_cycle_hashes") or body.get("accepted_post_cycle_hashes", {})
    if not isinstance(accepted_hashes, dict):
        accepted_hashes = {}
    return {
        "status": str(packet.get("status", "missing")),
        "selected_skill_tag": str(packet.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "packet_recommendation": str(
            packet.get("packet_recommendation") or summary.get("packet_recommendation", "keep_review_packet_open")
        ),
        "packet_recommendation_reason": str(summary.get("packet_recommendation_reason", "")),
        "timeline_recommendation": str(summary.get("timeline_recommendation") or body.get("timeline_recommendation", "")),
        "closure_decision": str(summary.get("closure_decision") or body.get("closure_decision", "")),
        "post_cycle_recommendation": str(summary.get("post_cycle_recommendation") or body.get("post_cycle_recommendation", "")),
        "missing_required_hashes": [str(item) for item in (summary.get("missing_required_hashes") or body.get("missing_required_hashes", []) or [])][:12],
        "accepted_post_cycle_hashes": accepted_hashes,
        "task_hash": str(summary.get("task_hash") or body.get("task_hash", "")),
        "checkpoint_hash": str(summary.get("checkpoint_hash") or body.get("checkpoint_hash", "")),
        "notebook_checkpoint_hash": str(summary.get("notebook_checkpoint_hash") or body.get("notebook_checkpoint_hash", "")),
        "help_ledger_hash": str(summary.get("help_ledger_hash") or body.get("help_ledger_hash", "")),
        "operator_reflection_hash": str(summary.get("operator_reflection_hash") or body.get("operator_reflection_hash", "")),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids") or body.get("source_card_ids", []) or [])][:8],
        "source_anchor_hash_count": int(summary.get("source_anchor_hash_count", body.get("source_anchor_hash_count", 0)) or 0),
        "receipt_hashes": {str(key): str(value) for key, value in receipt_hashes.items()},
        "timeline_event_hashes": [str(item) for item in (summary.get("timeline_event_hashes") or body.get("timeline_event_hashes", []) or [])][:12],
        "timeline_event_count": int(summary.get("timeline_event_count", body.get("timeline_event_count", 0)) or 0),
        "packet_receipt_hash": str(receipt.get("receipt_hash", "")),
        "next_safe_review_action": str(summary.get("next_safe_review_action") or body.get("next_safe_review_action", "")),
        "help_level": safe_help_level(str(summary.get("help_level") or body.get("help_level", "A2"))),
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def export_manifest_preview(
    *,
    packet_view: dict[str, Any],
    timeline_view: dict[str, Any],
    closure_view: dict[str, Any],
    intake_view: dict[str, Any],
    binder_view: dict[str, Any],
    launch_view: dict[str, Any],
    console_view: dict[str, Any],
) -> dict[str, Any]:
    receipt_hashes = dict(packet_view.get("receipt_hashes", {}) or {})
    receipt_hashes["packet_receipt_hash"] = packet_view.get("packet_receipt_hash", "")
    manifest_seed = {
        "packet_recommendation": packet_view.get("packet_recommendation", ""),
        "timeline_recommendation": packet_view.get("timeline_recommendation") or timeline_view.get("timeline_review_recommendation", ""),
        "closure_decision": packet_view.get("closure_decision") or closure_view.get("closure_ledger_decision", ""),
        "missing_required_hashes": packet_view.get("missing_required_hashes", []),
        "accepted_post_cycle_hashes": packet_view.get("accepted_post_cycle_hashes", {}),
        "task_hash": packet_view.get("task_hash") or closure_view.get("task_hash", ""),
        "checkpoint_hash": packet_view.get("checkpoint_hash") or closure_view.get("checkpoint_hash", ""),
        "source_card_ids": packet_view.get("source_card_ids") or closure_view.get("source_card_ids", []),
        "timeline_event_hashes": packet_view.get("timeline_event_hashes", []),
        "receipt_hashes": receipt_hashes,
        "exam_deployment_status": "not_cleared",
    }
    manifest_hash = sha256_text(json.dumps(manifest_seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "manual_review_export_manifest_preview_ready",
        "export_manifest_hash": manifest_hash,
        "packet_recommendation": manifest_seed["packet_recommendation"],
        "timeline_recommendation": manifest_seed["timeline_recommendation"],
        "closure_decision": manifest_seed["closure_decision"],
        "post_cycle_recommendation": packet_view.get("post_cycle_recommendation") or intake_view.get("post_cycle_review_recommendation", ""),
        "launch_decision": closure_view.get("launch_decision") or launch_view.get("launch_decision", ""),
        "manual_confirmation_action": closure_view.get("manual_confirmation_action") or console_view.get("next_manual_confirmation_action", ""),
        "missing_required_hashes": list(packet_view.get("missing_required_hashes", []) or [])[:12],
        "accepted_post_cycle_hashes": packet_view.get("accepted_post_cycle_hashes", {}),
        "source_card_ids": list(packet_view.get("source_card_ids") or closure_view.get("source_card_ids", []) or [])[:8],
        "source_anchor_hash_count": int(packet_view.get("source_anchor_hash_count", closure_view.get("source_anchor_hash_count", 0)) or 0),
        "task_hash": packet_view.get("task_hash") or closure_view.get("task_hash", ""),
        "checkpoint_hash": packet_view.get("checkpoint_hash") or closure_view.get("checkpoint_hash", ""),
        "notebook_checkpoint_hash": packet_view.get("notebook_checkpoint_hash") or closure_view.get("notebook_checkpoint_hash", ""),
        "help_ledger_hash": packet_view.get("help_ledger_hash") or closure_view.get("help_ledger_hash", binder_view.get("help_ledger_preview_hash", "")),
        "operator_reflection_hash": packet_view.get("operator_reflection_hash") or closure_view.get("operator_reflection_hash", ""),
        "receipt_hashes": receipt_hashes,
        "timeline_event_hashes": list(packet_view.get("timeline_event_hashes") or timeline_view.get("timeline_event_hashes", []) or [])[:12],
        "timeline_event_count": int(packet_view.get("timeline_event_count", timeline_view.get("timeline_event_count", 0)) or 0),
        "next_safe_review_action": packet_view.get("next_safe_review_action") or timeline_view.get("next_safe_review_action", ""),
        "help_level": safe_help_level(str(packet_view.get("help_level", timeline_view.get("help_level", "A2")))),
        "export_created": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def export_preview_summary(
    *,
    selected_skill_tag: str,
    packet_view: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    packet_recommendation = packet_view.get("packet_recommendation", "keep_review_packet_open")
    if packet_view.get("status") != "python_exam_manual_cycle_review_packet_ready":
        recommendation = "keep_export_preview_open"
        reason = "review_packet_missing_or_not_ready"
    elif packet_recommendation == "ready_for_human_packet_review":
        recommendation = "ready_for_human_export_review"
        reason = "review_packet_ready_for_human_export_review"
    elif packet_recommendation == "request_hash_completion":
        recommendation = "request_hash_completion"
        reason = "review_packet_requests_hash_completion"
    elif packet_recommendation == "reject_review_packet":
        recommendation = "reject_export_preview"
        reason = "review_packet_rejected"
    else:
        recommendation = "keep_export_preview_open"
        reason = "review_packet_still_open"
    return {
        "status": "python_exam_manual_review_export_preview_ready",
        "selected_skill_tag": selected_skill_tag,
        "export_preview_recommendation": recommendation,
        "export_preview_reason": reason,
        "allowed_export_preview_recommendations": sorted(EXPORT_PREVIEW_RECOMMENDATIONS),
        "packet_recommendation": packet_recommendation,
        "timeline_recommendation": manifest.get("timeline_recommendation", ""),
        "closure_decision": manifest.get("closure_decision", ""),
        "missing_required_hashes": list(manifest.get("missing_required_hashes", []) or [])[:12],
        "accepted_post_cycle_hashes": manifest.get("accepted_post_cycle_hashes", {}),
        "task_hash": manifest.get("task_hash", ""),
        "checkpoint_hash": manifest.get("checkpoint_hash", ""),
        "notebook_checkpoint_hash": manifest.get("notebook_checkpoint_hash", ""),
        "help_ledger_hash": manifest.get("help_ledger_hash", ""),
        "operator_reflection_hash": manifest.get("operator_reflection_hash", ""),
        "source_card_ids": list(manifest.get("source_card_ids", []) or [])[:8],
        "source_anchor_hash_count": int(manifest.get("source_anchor_hash_count", 0) or 0),
        "receipt_hashes": manifest.get("receipt_hashes", {}),
        "timeline_event_hashes": list(manifest.get("timeline_event_hashes", []) or [])[:12],
        "timeline_event_count": int(manifest.get("timeline_event_count", 0) or 0),
        "export_manifest_hash": manifest.get("export_manifest_hash", ""),
        "next_safe_review_action": manifest.get("next_safe_review_action", ""),
        "help_level": safe_help_level(str(manifest.get("help_level", "A2"))),
        "export_created": False,
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def export_preview_receipt(summary: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "manifest": manifest,
        "exam_deployment_status": "not_cleared",
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "manual_review_export_preview_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "export_preview_recommendation": summary.get("export_preview_recommendation", "keep_export_preview_open"),
        "export_manifest_hash": summary.get("export_manifest_hash", ""),
        "not_cleared_receipt": True,
        "export_created": False,
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-manual-review-export-preview")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
