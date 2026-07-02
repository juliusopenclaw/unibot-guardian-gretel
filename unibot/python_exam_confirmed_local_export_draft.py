from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_CONFIRMED_LOCAL_EXPORT_DRAFT_SCHEMA_VERSION = "unibot-python-exam-confirmed-local-export-draft-v1"
PYTHON_EXAM_CONFIRMED_LOCAL_EXPORT_DRAFT_ENDPOINT = "/api/unibot/course/python-exam-confirmed-local-export-draft"
DEFAULT_PYTHON_EXAM_EXPORT_DRAFT_DIR = Path.home() / ".unibot_guardian" / "python_exam_export_drafts"


def resolve_python_exam_export_draft_dir(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get("UNIBOT_PYTHON_EXAM_EXPORT_DRAFT_DIR")
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_PYTHON_EXAM_EXPORT_DRAFT_DIR


def build_python_exam_confirmed_local_export_draft(
    *,
    python_exam_evidence_export_preview: dict[str, Any] | None = None,
    export_draft_dir: str | Path | None = None,
    operator_confirmed_local_export_draft_write: bool = False,
    public_safe: bool = True,
) -> dict[str, Any]:
    preview = python_exam_evidence_export_preview if isinstance(python_exam_evidence_export_preview, dict) else {}
    draft_files = build_draft_files(preview)
    preview_ready = preview.get("status") == "python_exam_evidence_export_preview_ready"
    write_confirmed = bool(operator_confirmed_local_export_draft_write and preview_ready)
    receipt = draft_receipt(preview, draft_files, write_confirmed)
    write_result = write_draft_package(
        draft_files=draft_files,
        receipt=receipt,
        export_draft_dir=export_draft_dir,
        confirmed=write_confirmed,
    )
    summary = draft_summary(preview, draft_files, receipt, write_result, operator_confirmed_local_export_draft_write)
    payload = {
        "schema_version": PYTHON_EXAM_CONFIRMED_LOCAL_EXPORT_DRAFT_SCHEMA_VERSION,
        "artifact_type": "python_exam_confirmed_local_export_draft",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Confirmed Local Export Draft. Dry-run is the default. A local hash-based draft package "
            "is written only when operator_confirmed_local_export_draft_write is true. The API output returns only "
            "manifest/receipt metadata, counts, hashes, write status, and not_cleared state. It never returns raw "
            "queries, course raw text, notebook code, local paths, values, solutions, final interpretations, "
            "proctoring, AI detection, automatic assessment, or exam clearance."
        ),
        "draft_summary": summary,
        "write_preview": write_preview(draft_files, receipt),
        "draft_receipt": receipt,
        "draft_file_manifest": public_file_manifest(draft_files),
        "operator_confirmation_required_for_local_write": True,
        "operator_confirmed_local_export_draft_write": bool(operator_confirmed_local_export_draft_write),
        "dry_run_default": True,
        "local_export_draft_written": bool(write_result.get("written", False)),
        "local_export_package_written": bool(write_result.get("written", False)),
        "draft_file_count": len(draft_files),
        "draft_package_id": receipt.get("draft_package_id", ""),
        "draft_package_hash": receipt.get("draft_package_hash", ""),
        "local_paths_returned": False,
        "export_draft_dir_returned": False,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "values_returned": False,
        "solutions_returned": False,
        "final_interpretations_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der lokale Export-Draft bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def build_draft_files(preview: dict[str, Any]) -> dict[str, dict[str, Any]]:
    manifest = preview.get("preview_manifest", {}) if isinstance(preview.get("preview_manifest"), dict) else {}
    human = preview.get("human_review_packet", {}) if isinstance(preview.get("human_review_packet"), dict) else {}
    preview_summary = preview.get("preview_summary", {}) if isinstance(preview.get("preview_summary"), dict) else {}
    preview_receipt = preview.get("preview_receipt", {}) if isinstance(preview.get("preview_receipt"), dict) else {}
    selected_skill_tag = first_text(preview.get("selected_skill_tag"), manifest.get("selected_skill_tag"), preview_summary.get("selected_skill_tag"))
    evidence = manifest.get("evidence_receipts", {}) if isinstance(manifest.get("evidence_receipts"), dict) else {}
    draft_manifest = {
        "artifact_type": "python_exam_local_export_draft_manifest",
        "selected_skill_tag": selected_skill_tag,
        "preview_status": preview.get("status", "missing"),
        "readiness_snapshot": manifest.get("readiness_snapshot", {}),
        "cockpit_step_count": len(manifest.get("cockpit_steps", []) or []),
        "live_control_action_count": len(manifest.get("live_control_actions", []) or []),
        "evidence_receipts": evidence,
        "help_level_profile": manifest.get("help_level_profile", {}),
        "operator_confirmation_profile": manifest.get("operator_confirmation_profile", {}),
        "review_chain_status": manifest.get("review_chain_status", {}),
        "notebook_checkpoint": manifest.get("notebook_checkpoint", {}),
        "receipt_journal_summary": manifest.get("receipt_journal_summary", {}),
        "human_review_questions": [str(item) for item in (human.get("review_questions", []) or [])][:12],
        "preview_receipt_id": preview_receipt.get("receipt_id", ""),
        "preview_receipt_hash": preview_receipt.get("receipt_hash", ""),
        "exam_deployment_status": "not_cleared",
        "raw_query_included": False,
        "raw_text_included": False,
        "raw_cell_included": False,
        "notebook_code_included": False,
        "local_paths_included": False,
        "values_included": False,
        "solutions_included": False,
        "final_interpretations_included": False,
    }
    process_log = {
        "artifact_type": "python_exam_local_export_draft_process_log",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "selected_skill_tag": selected_skill_tag,
        "source_artifacts": {
            "preview": preview.get("artifact_type", "missing"),
            "preview_status": preview.get("status", "missing"),
            "human_review_status": human.get("status", "missing"),
            "review_chain_status": nested(manifest, "review_chain_status", "status"),
            "receipt_journal_status": nested(manifest, "receipt_journal_summary", "status"),
        },
        "steps": [
            "validated Evidence Export Preview metadata",
            "assembled hash-only draft manifest",
            "assembled process log and not_cleared receipt",
            "local write remains pending unless operator confirmation is true",
        ],
        "exam_deployment_status": "not_cleared",
        "dry_run_default": True,
        "raw_text_included": False,
        "notebook_code_included": False,
        "local_paths_included": False,
    }
    not_cleared_receipt = {
        "artifact_type": "python_exam_local_export_draft_not_cleared_receipt",
        "selected_skill_tag": selected_skill_tag,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "preview_receipt_id": preview_receipt.get("receipt_id", ""),
        "operator_confirmation_required_for_local_write": True,
        "does_not_authorize_exam_deployment": True,
        "does_not_grade": True,
        "does_not_proctor": True,
        "does_not_detect_ai": True,
        "raw_text_included": False,
        "notebook_code_included": False,
        "local_paths_included": False,
    }
    return {
        "manifest.json": draft_manifest,
        "process_log.json": process_log,
        "not_cleared_receipt.json": not_cleared_receipt,
    }


def draft_receipt(
    preview: dict[str, Any],
    draft_files: dict[str, dict[str, Any]],
    confirmed: bool,
) -> dict[str, Any]:
    package_hash = sha256_text(json.dumps(draft_files, sort_keys=True, ensure_ascii=False))
    package_id = package_hash[:20]
    return {
        "status": "local_export_draft_receipt_ready_not_exam_clearance",
        "draft_package_id": package_id,
        "draft_package_hash": package_hash,
        "source_preview_receipt_id": nested(preview, "preview_receipt", "receipt_id"),
        "source_preview_receipt_hash": nested(preview, "preview_receipt", "receipt_hash"),
        "selected_skill_tag": first_text(preview.get("selected_skill_tag"), nested(preview, "preview_summary", "selected_skill_tag")),
        "file_count": len(draft_files),
        "file_hashes": {name: sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=False)) for name, payload in draft_files.items()},
        "local_write_confirmed": bool(confirmed),
        "operator_confirmation_required_for_local_write": True,
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def write_draft_package(
    *,
    draft_files: dict[str, dict[str, Any]],
    receipt: dict[str, Any],
    export_draft_dir: str | Path | None,
    confirmed: bool,
) -> dict[str, Any]:
    if not confirmed:
        return {"status": "write_preview_ready", "written": False, "file_count": len(draft_files)}
    target_root = resolve_python_exam_export_draft_dir(export_draft_dir)
    package_dir = target_root / str(receipt.get("draft_package_id", "draft"))
    package_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in draft_files.items():
        (package_dir / name).write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (package_dir / "draft_receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "status": "local_export_draft_written",
        "written": True,
        "file_count": len(draft_files) + 1,
    }


def draft_summary(
    preview: dict[str, Any],
    draft_files: dict[str, dict[str, Any]],
    receipt: dict[str, Any],
    write_result: dict[str, Any],
    confirmed: bool,
) -> dict[str, Any]:
    preview_ready = preview.get("status") == "python_exam_evidence_export_preview_ready"
    if confirmed and preview_ready and write_result.get("written"):
        status = "python_exam_confirmed_local_export_draft_written"
        next_safe_action = "Review the locally written draft package by receipt; keep not_cleared and do not treat it as exam clearance."
    elif confirmed and not preview_ready:
        status = "python_exam_confirmed_local_export_draft_blocked_preview_not_ready"
        next_safe_action = "Resolve Evidence Export Preview attention items before writing a local draft package."
    else:
        status = "python_exam_confirmed_local_export_draft_preview_ready" if preview_ready else "python_exam_confirmed_local_export_draft_attention"
        next_safe_action = "Review the write preview; write only after explicit operator confirmation."
    return {
        "status": status,
        "selected_skill_tag": receipt.get("selected_skill_tag", ""),
        "source_preview_status": preview.get("status", "missing"),
        "draft_package_id": receipt.get("draft_package_id", ""),
        "draft_package_hash": receipt.get("draft_package_hash", ""),
        "draft_file_count": len(draft_files),
        "write_result_status": write_result.get("status", "unknown"),
        "local_export_draft_written": bool(write_result.get("written", False)),
        "operator_confirmed_local_export_draft_write": bool(confirmed),
        "operator_confirmation_required_for_local_write": True,
        "dry_run_default": True,
        "exam_deployment_status": "not_cleared",
        "next_safe_action": next_safe_action,
    }


def write_preview(draft_files: dict[str, dict[str, Any]], receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "ready_to_write_with_operator_confirmation",
        "would_write": True,
        "file_count": len(draft_files) + 1,
        "draft_package_id": receipt.get("draft_package_id", ""),
        "draft_package_hash": receipt.get("draft_package_hash", ""),
        "file_names": sorted([*draft_files.keys(), "draft_receipt.json"]),
        "operator_confirmation_required_for_local_write": True,
        "raw_text_included": False,
        "notebook_code_included": False,
        "local_paths_included": False,
        "exam_deployment_status": "not_cleared",
    }


def public_file_manifest(draft_files: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "file_name": name,
            "artifact_type": payload.get("artifact_type", ""),
            "sha256": sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=False)),
            "raw_text_included": False,
            "notebook_code_included": False,
            "local_paths_included": False,
            "exam_deployment_status": "not_cleared",
        }
        for name, payload in sorted(draft_files.items())
    ]


def next_actions(summary: dict[str, Any]) -> list[str]:
    if summary.get("local_export_draft_written"):
        return [
            summary.get("next_safe_action", "Review the local draft package by receipt."),
            "Use only the receipt id/hash and file manifest in public handoffs.",
            "Keep exam_deployment_status not_cleared and retain real exam clearance as an external reminder.",
        ]
    return [
        summary.get("next_safe_action", "Review the export draft write preview."),
        "Set operator_confirmed_local_export_draft_write only for a deliberate local write.",
        "Keep the draft package hash-only and not_cleared.",
    ]


def first_text(*values: Any) -> str:
    for value in values:
        text = str(value or "")
        if text:
            return text
    return ""


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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-confirmed-local-export-draft")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
