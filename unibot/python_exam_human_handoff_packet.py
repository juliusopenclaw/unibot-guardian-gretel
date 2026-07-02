from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_HUMAN_HANDOFF_PACKET_SCHEMA_VERSION = "unibot-python-exam-human-handoff-packet-v1"
PYTHON_EXAM_HUMAN_HANDOFF_PACKET_ENDPOINT = "/api/unibot/course/python-exam-human-handoff-packet"


def build_python_exam_human_handoff_packet(
    *,
    python_exam_draft_package_review_console: dict[str, Any] | None = None,
    python_exam_evidence_export_preview: dict[str, Any] | None = None,
    python_exam_confirmed_local_export_draft: dict[str, Any] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    console = python_exam_draft_package_review_console if isinstance(python_exam_draft_package_review_console, dict) else {}
    preview = python_exam_evidence_export_preview if isinstance(python_exam_evidence_export_preview, dict) else {}
    draft = python_exam_confirmed_local_export_draft if isinstance(python_exam_confirmed_local_export_draft, dict) else {}
    packet = handoff_packet(console=console, preview=preview, draft=draft)
    summary = handoff_summary(packet, console, preview, draft)
    copy_markdown = handoff_markdown(packet, summary)
    payload = {
        "schema_version": PYTHON_EXAM_HUMAN_HANDOFF_PACKET_SCHEMA_VERSION,
        "artifact_type": "python_exam_human_handoff_packet",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Human Handoff Packet. It bundles only safe metadata from Draft Package Review Console, "
            "Evidence Export Preview, and Confirmed Local Export Draft: package id, file hashes, review-console "
            "status, A0-A2 profile, review questions, open operator confirmations, notebook checkpoint hash, "
            "receipt-journal summary, review-chain status, not_cleared receipt, and next safe action. It never "
            "returns local paths, raw queries, course raw text, notebook code, values, solutions, final "
            "interpretations, proctoring, AI detection, automatic assessment, or exam clearance."
        ),
        "handoff_summary": summary,
        "handoff_packet": packet,
        "copy_export_view": {
            "format": "markdown",
            "status": "copy_ready",
            "markdown": copy_markdown,
            "markdown_hash": sha256_text(copy_markdown),
            "local_paths_included": False,
            "raw_text_included": False,
            "notebook_code_included": False,
            "exam_deployment_status": "not_cleared",
        },
        "dry_run_default": True,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; das Human Handoff Packet bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def handoff_packet(*, console: dict[str, Any], preview: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    review_summary = console.get("review_summary", {}) if isinstance(console.get("review_summary"), dict) else {}
    package = console.get("package_integrity", {}) if isinstance(console.get("package_integrity"), dict) else {}
    checkpoint = nested(preview, "preview_manifest", "notebook_checkpoint")
    checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
    preview_receipts = nested(preview, "preview_manifest", "evidence_receipts")
    preview_receipts = preview_receipts if isinstance(preview_receipts, dict) else {}
    draft_receipt = draft.get("draft_receipt", {}) if isinstance(draft.get("draft_receipt"), dict) else {}
    return {
        "packet_type": "python_exam_human_handoff_packet",
        "review_console_status": console.get("status", "missing"),
        "draft_status": draft.get("status", "missing"),
        "preview_status": preview.get("status", "missing"),
        "draft_present_status": review_summary.get("draft_present_status", console.get("draft_present_status", "missing")),
        "package": {
            "draft_package_id": first_text(review_summary.get("draft_package_id"), package.get("draft_package_id"), draft.get("draft_package_id")),
            "draft_package_hash": first_text(review_summary.get("draft_package_hash"), package.get("draft_package_hash"), draft.get("draft_package_hash")),
            "file_hash_integrity_status": package.get("status", review_summary.get("file_hash_integrity_status", "missing")),
            "file_count": int(package.get("file_count", 0) or 0),
            "file_hashes": safe_file_hashes(draft),
        },
        "review_console": {
            "manifest_status": review_summary.get("manifest_status", nested(console, "manifest_status", "status")),
            "not_cleared_receipt_status": review_summary.get(
                "not_cleared_receipt_status", nested(console, "not_cleared_receipt_status", "status")
            ),
            "process_log_status": review_summary.get("process_log_status", nested(console, "process_log_status", "status")),
            "next_safe_action": review_summary.get("next_safe_action", ""),
        },
        "help_level_profile": console.get("help_level_profile", {}),
        "review_questions": [str(item) for item in (console.get("review_questions", []) or [])][:12],
        "operator_confirmations": console.get("operator_confirmation_status", {}),
        "notebook_checkpoint": {
            "status": checkpoint.get("status", "missing"),
            "notebook_checkpoint_hash": first_text(
                checkpoint.get("notebook_checkpoint_hash"),
                preview_receipts.get("notebook_checkpoint_hash"),
            ),
            "raw_cell_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
        },
        "receipt_journal_summary": console.get("receipt_journal_status", {}),
        "review_chain_status": console.get("review_chain_status", {}),
        "not_cleared_receipt": {
            "status": nested(console, "not_cleared_receipt_status", "status"),
            "not_cleared_receipt": bool(draft_receipt.get("not_cleared_receipt", True)),
            "exam_deployment_status": "not_cleared",
            "exam_clearance_claimed": False,
        },
        "exam_deployment_status": "not_cleared",
        "local_paths_returned": False,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "values_returned": False,
        "solutions_returned": False,
        "final_interpretations_returned": False,
    }


def handoff_summary(
    packet: dict[str, Any],
    console: dict[str, Any],
    preview: dict[str, Any],
    draft: dict[str, Any],
) -> dict[str, Any]:
    package = packet.get("package", {}) if isinstance(packet.get("package"), dict) else {}
    help_profile = packet.get("help_level_profile", {}) if isinstance(packet.get("help_level_profile"), dict) else {}
    confirmations = packet.get("operator_confirmations", {}) if isinstance(packet.get("operator_confirmations"), dict) else {}
    journal = packet.get("receipt_journal_summary", {}) if isinstance(packet.get("receipt_journal_summary"), dict) else {}
    chain = packet.get("review_chain_status", {}) if isinstance(packet.get("review_chain_status"), dict) else {}
    ready = (
        console.get("status") == "python_exam_draft_package_review_console_ready"
        and preview.get("status") == "python_exam_evidence_export_preview_ready"
        and draft.get("artifact_type") == "python_exam_confirmed_local_export_draft"
        and package.get("file_hash_integrity_status") == "file_hash_integrity_pass"
        and help_profile.get("status") == "a0_a2_only"
        and chain.get("status") == "review_chain_integrity_pass"
        and int(chain.get("issue_count", 0) or 0) == 0
        and int(journal.get("accepted_record_count", 0) or 0) >= 1
        and packet.get("not_cleared_receipt", {}).get("not_cleared_receipt") is True
    )
    return {
        "status": "python_exam_human_handoff_packet_ready" if ready else "python_exam_human_handoff_packet_attention",
        "review_console_status": console.get("status", "missing"),
        "draft_status": draft.get("status", "missing"),
        "preview_status": preview.get("status", "missing"),
        "draft_present_status": packet.get("draft_present_status", "missing"),
        "draft_package_id": package.get("draft_package_id", ""),
        "file_hash_integrity_status": package.get("file_hash_integrity_status", "missing"),
        "file_hash_count": len(package.get("file_hashes", {}) or {}),
        "help_status": help_profile.get("status", "missing"),
        "review_question_count": len(packet.get("review_questions", []) or []),
        "open_operator_confirmation_count": int(confirmations.get("open_operator_confirmation_count", 0) or 0),
        "notebook_checkpoint_hash_present": bool(nested(packet, "notebook_checkpoint", "notebook_checkpoint_hash")),
        "receipt_journal_status": journal.get("status", "missing"),
        "receipt_journal_accepted_record_count": int(journal.get("accepted_record_count", 0) or 0),
        "review_chain_status": chain.get("status", "missing"),
        "not_cleared_receipt_status": nested(packet, "not_cleared_receipt", "status"),
        "copy_export_ready": True,
        "exam_deployment_status": "not_cleared",
        "next_safe_action": (
            "Copy the human handoff packet for review; keep not_cleared and do not expose raw/private content."
            if ready
            else "Resolve human handoff attention items before using this packet for review."
        ),
    }


def handoff_markdown(packet: dict[str, Any], summary: dict[str, Any]) -> str:
    package = packet.get("package", {}) if isinstance(packet.get("package"), dict) else {}
    file_hashes = package.get("file_hashes", {}) if isinstance(package.get("file_hashes"), dict) else {}
    questions = [str(item) for item in (packet.get("review_questions", []) or [])]
    confirmations = packet.get("operator_confirmations", {}) if isinstance(packet.get("operator_confirmations"), dict) else {}
    checkpoint = packet.get("notebook_checkpoint", {}) if isinstance(packet.get("notebook_checkpoint"), dict) else {}
    journal = packet.get("receipt_journal_summary", {}) if isinstance(packet.get("receipt_journal_summary"), dict) else {}
    chain = packet.get("review_chain_status", {}) if isinstance(packet.get("review_chain_status"), dict) else {}
    lines = [
        "# Python Exam Human Handoff Packet",
        f"Status: {summary.get('status', 'unknown')}",
        "Exam deployment: not_cleared",
        f"Draft: {summary.get('draft_present_status', 'unknown')}",
        f"Package ID: {summary.get('draft_package_id', '') or 'missing'}",
        f"File integrity: {summary.get('file_hash_integrity_status', 'missing')}",
        "",
        "## File Hashes",
        *[f"- {name}: {value}" for name, value in sorted(file_hashes.items())],
        "",
        "## Review State",
        f"- Help: {summary.get('help_status', 'missing')}",
        f"- Review chain: {chain.get('status', 'missing')} (issues={chain.get('issue_count', 0)})",
        f"- Receipt journal: {journal.get('status', 'missing')} (accepted={journal.get('accepted_record_count', 0)})",
        f"- Notebook checkpoint hash: {checkpoint.get('notebook_checkpoint_hash', '') or 'missing'}",
        f"- Open operator confirmations: {confirmations.get('open_operator_confirmation_count', 0)}",
        "",
        "## Review Questions",
        *[f"- {item}" for item in questions[:12]],
        "",
        "## Boundary",
        "- No local paths, raw queries, course raw text, notebook code, values, solutions, final interpretations, proctoring, AI detection, grading, or exam clearance.",
        f"- Next safe action: {summary.get('next_safe_action', '')}",
    ]
    return "\n".join(lines)


def safe_file_hashes(draft: dict[str, Any]) -> dict[str, str]:
    hashes = nested(draft, "draft_receipt", "file_hashes")
    if not isinstance(hashes, dict):
        return {}
    return {str(name): str(value) for name, value in sorted(hashes.items())}


def next_actions(summary: dict[str, Any]) -> list[str]:
    return [
        summary.get("next_safe_action", "Review the human handoff packet."),
        "Copy only the provided markdown or handoff_packet metadata.",
        "Keep exam_deployment_status not_cleared and handle real exam clearance outside UniBot.",
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-human-handoff-packet")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
