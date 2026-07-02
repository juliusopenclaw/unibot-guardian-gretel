from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .public_safety import scan_text


PYTHON_EXAM_DRAFT_PACKAGE_REVIEW_CONSOLE_SCHEMA_VERSION = "unibot-python-exam-draft-package-review-console-v1"
PYTHON_EXAM_DRAFT_PACKAGE_REVIEW_CONSOLE_ENDPOINT = "/api/unibot/course/python-exam-draft-package-review-console"


def build_python_exam_draft_package_review_console(
    *,
    python_exam_confirmed_local_export_draft: dict[str, Any] | None = None,
    python_exam_evidence_export_preview: dict[str, Any] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    draft = python_exam_confirmed_local_export_draft if isinstance(python_exam_confirmed_local_export_draft, dict) else {}
    preview = python_exam_evidence_export_preview if isinstance(python_exam_evidence_export_preview, dict) else {}
    review = review_summary(draft, preview)
    payload = {
        "schema_version": PYTHON_EXAM_DRAFT_PACKAGE_REVIEW_CONSOLE_SCHEMA_VERSION,
        "artifact_type": "python_exam_draft_package_review_console",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": review["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Draft Package Review Console. It reviews a planned or written Python exam local export "
            "draft using package id, file hashes, manifest status, not_cleared receipt, process log, Help-Level "
            "profile, review questions, operator confirmations, review-chain status, receipt-journal status, and "
            "next safe action. It never returns local paths, raw queries, course raw text, notebook code, values, "
            "solutions, final interpretations, proctoring, AI detection, automatic assessment, or exam clearance."
        ),
        "review_summary": review,
        "package_integrity": package_integrity(draft),
        "manifest_status": manifest_status(draft),
        "not_cleared_receipt_status": not_cleared_receipt_status(draft),
        "process_log_status": process_log_status(draft),
        "help_level_profile": help_level_profile(preview),
        "review_questions": review_questions(preview),
        "operator_confirmation_status": operator_confirmation_status(draft, preview),
        "review_chain_status": review_chain_status(preview),
        "receipt_journal_status": receipt_journal_status(preview),
        "console_sections": console_sections(draft, preview, review),
        "dry_run_default": True,
        "local_export_draft_written": bool(draft.get("local_export_draft_written", False)),
        "draft_present_status": "written" if draft.get("local_export_draft_written") else "preview_only",
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; die Draft Package Review Console bleibt not_cleared."
        ),
        "next_actions": next_actions(review),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def review_summary(draft: dict[str, Any], preview: dict[str, Any]) -> dict[str, Any]:
    integrity = package_integrity(draft)
    help_status = help_level_profile(preview).get("status", "missing")
    chain = review_chain_status(preview)
    journal = receipt_journal_status(preview)
    not_cleared = not_cleared_receipt_status(draft)
    process = process_log_status(draft)
    ready = (
        draft.get("artifact_type") == "python_exam_confirmed_local_export_draft"
        and integrity.get("status") == "file_hash_integrity_pass"
        and not_cleared.get("status") == "not_cleared_receipt_present"
        and process.get("status") == "process_log_present"
        and help_status == "a0_a2_only"
        and chain.get("status") == "review_chain_integrity_pass"
        and int(chain.get("issue_count", 0) or 0) == 0
        and int(journal.get("accepted_record_count", 0) or 0) >= 1
    )
    status = "python_exam_draft_package_review_console_ready" if ready else "python_exam_draft_package_review_console_attention"
    return {
        "status": status,
        "draft_present_status": "written" if draft.get("local_export_draft_written") else "preview_only",
        "source_draft_status": draft.get("status", "missing"),
        "source_preview_status": preview.get("status", "missing"),
        "draft_package_id": first_text(draft.get("draft_package_id"), nested(draft, "draft_receipt", "draft_package_id")),
        "draft_package_hash": first_text(draft.get("draft_package_hash"), nested(draft, "draft_receipt", "draft_package_hash")),
        "file_hash_integrity_status": integrity.get("status", "missing"),
        "manifest_status": manifest_status(draft).get("status", "missing"),
        "not_cleared_receipt_status": not_cleared.get("status", "missing"),
        "process_log_status": process.get("status", "missing"),
        "help_status": help_status,
        "review_question_count": len(review_questions(preview)),
        "review_chain_status": chain.get("status", "missing"),
        "receipt_journal_status": journal.get("status", "missing"),
        "open_operator_confirmation_count": operator_confirmation_status(draft, preview).get("open_operator_confirmation_count", 0),
        "local_export_draft_written": bool(draft.get("local_export_draft_written", False)),
        "exam_deployment_status": "not_cleared",
        "next_safe_action": (
            "Use the review console as human-review evidence; keep not_cleared and expose only hashes/receipts."
            if ready
            else "Resolve draft package review attention items before relying on this package."
        ),
    }


def package_integrity(draft: dict[str, Any]) -> dict[str, Any]:
    file_manifest = [item for item in (draft.get("draft_file_manifest", []) or []) if isinstance(item, dict)]
    receipt_hashes = nested(draft, "draft_receipt", "file_hashes")
    receipt_hashes = receipt_hashes if isinstance(receipt_hashes, dict) else {}
    manifest_hashes = {str(item.get("file_name", "")): str(item.get("sha256", "")) for item in file_manifest}
    missing = sorted(name for name in receipt_hashes if name not in manifest_hashes)
    mismatched = sorted(name for name, value in receipt_hashes.items() if manifest_hashes.get(name) not in {"", str(value)})
    extra = sorted(name for name in manifest_hashes if name not in receipt_hashes)
    package_id = first_text(draft.get("draft_package_id"), nested(draft, "draft_receipt", "draft_package_id"))
    package_hash = first_text(draft.get("draft_package_hash"), nested(draft, "draft_receipt", "draft_package_hash"))
    status = "file_hash_integrity_pass" if package_id and package_hash and not missing and not mismatched and len(file_manifest) >= 3 else "file_hash_integrity_attention"
    return {
        "status": status,
        "draft_package_id": package_id,
        "draft_package_hash": package_hash,
        "file_count": len(file_manifest),
        "receipt_file_hash_count": len(receipt_hashes),
        "manifest_file_hash_count": len(manifest_hashes),
        "missing_file_hashes": missing,
        "mismatched_file_hashes": mismatched,
        "extra_file_hashes": extra,
        "local_paths_returned": False,
        "exam_deployment_status": "not_cleared",
    }


def manifest_status(draft: dict[str, Any]) -> dict[str, Any]:
    files = file_artifact_types(draft)
    present = files.get("manifest.json") == "python_exam_local_export_draft_manifest"
    return {
        "status": "manifest_present" if present else "manifest_missing",
        "artifact_type": files.get("manifest.json", ""),
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def not_cleared_receipt_status(draft: dict[str, Any]) -> dict[str, Any]:
    files = file_artifact_types(draft)
    receipt = draft.get("draft_receipt", {}) if isinstance(draft.get("draft_receipt"), dict) else {}
    present = (
        files.get("not_cleared_receipt.json") == "python_exam_local_export_draft_not_cleared_receipt"
        and receipt.get("not_cleared_receipt") is True
        and receipt.get("exam_deployment_status") == "not_cleared"
    )
    return {
        "status": "not_cleared_receipt_present" if present else "not_cleared_receipt_attention",
        "not_cleared_receipt": bool(receipt.get("not_cleared_receipt", False)),
        "exam_deployment_status": "not_cleared",
        "exam_clearance_claimed": False,
    }


def process_log_status(draft: dict[str, Any]) -> dict[str, Any]:
    files = file_artifact_types(draft)
    present = files.get("process_log.json") == "python_exam_local_export_draft_process_log"
    return {
        "status": "process_log_present" if present else "process_log_missing",
        "artifact_type": files.get("process_log.json", ""),
        "exam_deployment_status": "not_cleared",
        "local_paths_returned": False,
    }


def help_level_profile(preview: dict[str, Any]) -> dict[str, Any]:
    profile = nested(preview, "preview_manifest", "help_level_profile")
    profile = profile if isinstance(profile, dict) else {}
    levels = profile.get("profile", {}) if isinstance(profile.get("profile"), dict) else {}
    nonstandard = sum(int(count or 0) for level, count in levels.items() if str(level) not in {"A0", "A1", "A2"})
    return {
        "status": profile.get("status", "a0_a2_only" if nonstandard == 0 and levels else "missing"),
        "profile": levels,
        "allowed_help_boundary": "A0-A2",
        "nonstandard_help_event_count": nonstandard,
        "exam_deployment_status": "not_cleared",
    }


def review_questions(preview: dict[str, Any]) -> list[str]:
    questions = nested(preview, "human_review_packet", "review_questions")
    return [str(item) for item in (questions or [])][:12] if isinstance(questions, list) else []


def operator_confirmation_status(draft: dict[str, Any], preview: dict[str, Any]) -> dict[str, Any]:
    profile = nested(preview, "preview_manifest", "operator_confirmation_profile")
    profile = profile if isinstance(profile, dict) else {}
    return {
        "status": profile.get("status", "missing"),
        "open_operator_confirmation_count": int(profile.get("open_operator_confirmation_count", 0) or 0),
        "confirmed_local_write_step_count": int(profile.get("confirmed_local_write_step_count", 0) or 0),
        "local_export_draft_write_confirmed": bool(draft.get("operator_confirmed_local_export_draft_write", False)),
        "local_export_draft_written": bool(draft.get("local_export_draft_written", False)),
        "local_writes_require_confirmation": True,
        "exam_deployment_status": "not_cleared",
    }


def review_chain_status(preview: dict[str, Any]) -> dict[str, Any]:
    chain = nested(preview, "preview_manifest", "review_chain_status")
    chain = chain if isinstance(chain, dict) else {}
    return {
        "status": chain.get("status", "missing"),
        "issue_count": int(chain.get("issue_count", 0) or 0),
        "checked_link_count": int(chain.get("checked_link_count", 0) or 0),
        "exam_deployment_status": "not_cleared",
    }


def receipt_journal_status(preview: dict[str, Any]) -> dict[str, Any]:
    journal = nested(preview, "preview_manifest", "receipt_journal_summary")
    journal = journal if isinstance(journal, dict) else {}
    return {
        "status": journal.get("status", "missing"),
        "record_count": int(journal.get("record_count", 0) or 0),
        "accepted_record_count": int(journal.get("accepted_record_count", 0) or 0),
        "blocked_record_count": int(journal.get("blocked_record_count", 0) or 0),
        "exam_deployment_status": "not_cleared",
    }


def console_sections(draft: dict[str, Any], preview: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    integrity = package_integrity(draft)
    help_profile = help_level_profile(preview)
    confirmations = operator_confirmation_status(draft, preview)
    chain = review_chain_status(preview)
    journal = receipt_journal_status(preview)
    return [
        section("Draft Package", summary.get("draft_present_status", "missing"), [
            f"package id: {summary.get('draft_package_id', '') or 'missing'}",
            f"written: {bool(summary.get('local_export_draft_written', False))}",
        ]),
        section("File Hash Integrity", integrity.get("status", "missing"), [
            f"files: {integrity.get('file_count', 0)}",
            f"mismatches: {len(integrity.get('mismatched_file_hashes', []) or [])}",
        ]),
        section("A0-A2 Help", help_profile.get("status", "missing"), [
            f"profile: {json.dumps(help_profile.get('profile', {}), sort_keys=True)}",
            f"nonstandard: {help_profile.get('nonstandard_help_event_count', 0)}",
        ]),
        section("Review Chain", chain.get("status", "missing"), [
            f"issues: {chain.get('issue_count', 0)}",
            f"checked links: {chain.get('checked_link_count', 0)}",
        ]),
        section("Receipt Journal", journal.get("status", "missing"), [
            f"accepted: {journal.get('accepted_record_count', 0)}",
            f"records: {journal.get('record_count', 0)}",
        ]),
        section("Operator Confirmations", confirmations.get("status", "missing"), [
            f"open: {confirmations.get('open_operator_confirmation_count', 0)}",
            f"draft write confirmed: {bool(confirmations.get('local_export_draft_write_confirmed', False))}",
        ]),
    ]


def section(title: str, status: str, lines: list[str]) -> dict[str, Any]:
    return {
        "title": title,
        "status": status,
        "lines": lines[:4],
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def file_artifact_types(draft: dict[str, Any]) -> dict[str, str]:
    return {
        str(item.get("file_name", "")): str(item.get("artifact_type", ""))
        for item in (draft.get("draft_file_manifest", []) or [])
        if isinstance(item, dict)
    }


def next_actions(summary: dict[str, Any]) -> list[str]:
    return [
        summary.get("next_safe_action", "Review the draft package console."),
        "Use package id, file hashes, and not_cleared receipt for human review only.",
        "Do not expose local paths, raw course text, notebook code, values, or solutions.",
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-draft-package-review-console")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
