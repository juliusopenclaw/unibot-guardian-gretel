from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from unibot.public_safety import scan_text


ROOT = Path(__file__).resolve().parent
EXAM_ROOT = Path(os.environ.get("UNIBOT_EXAM_WORKSPACE_ROOT", ROOT / "knowledge" / "exam_workspace"))
ALLOWED_HELP_LEVELS = ("A0", "A1", "A2")
ALWAYS_ALLOWED_HELP_LEVELS = ("A2",)
NON_STANDARD_HELP_LEVELS = ("A3", "A4", "A5")
BLOCKED_HELP_LEVELS = ("A6",)
EXAM_CONTROLLED_MODE = "exam_controlled_gateway"
SOLUTION_MARKERS = re.compile(
    r"\b("
    r"fertige\s+loesung|fertige\s+lösung|komplette?\s+loesung|komplette?\s+lösung|"
    r"komplette[nr]?\s+code|vollstaendige[nr]?\s+code|vollständige[nr]?\s+code|complete\s+code|"
    r"finale\s+interpretation|werte\s+einsetzen|setze\s+die\s+werte|insert\s+values|"
    r"write\s+all|solve\s+this|solution\s+key"
    r")\b",
    re.I,
)


def workspace(course_id: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(course_id or "default"))
    return EXAM_ROOT / safe


def _ensure_paths(course_id: str) -> tuple[Path, Path]:
    root = workspace(course_id)
    material_root = root / "materials"
    ledger_path = root / "exam_help_ledger.json"
    material_root.mkdir(parents=True, exist_ok=True)
    return material_root, ledger_path


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_json_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def _append_json_line(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _is_blocked_help_level(help_level: str) -> bool:
    return help_level in BLOCKED_HELP_LEVELS


def _is_non_standard_help_level(help_level: str) -> bool:
    return help_level in NON_STANDARD_HELP_LEVELS


def _contains_solution_request(text: str) -> list[str]:
    categories: list[str] = []
    lowered = text.lower()
    if SOLUTION_MARKERS.search(lowered):
        categories.append("solution_like_request")
    if "fertige lösung" in lowered or "complete code" in lowered:
        categories.append("complete_code")
    return categories


def _redact_for_ledger(value: Any) -> str:
    text = str(value or "")
    findings = scan_text(text, "exam_ledger").get("findings", [])
    if findings:
        return ""
    return text


def start_exam_gateway_session(payload: dict[str, Any]) -> dict[str, Any]:
    course_id = str(payload.get("course_id", "default"))
    session_id = str(payload.get("session_id") or uuid.uuid4())
    workspace_root = workspace(course_id)
    workspace_root.mkdir(parents=True, exist_ok=True)
    session_path = workspace_root / "sessions" / f"{session_id}.json"
    session = {
        "artifact_type": "exam_controlled_gateway_session",
        "mode": EXAM_CONTROLLED_MODE,
        "status": "started",
        "session_id": session_id,
        "course_id": course_id,
        "allowed_help_levels": list(ALLOWED_HELP_LEVELS),
        "workflow": {
            "help_ledger": True,
        },
        "exam_deployment_status": "not_cleared",
        "independence_evidence_policy": "keine Prozentzahl, nur qualitative Hilfelückenanalyse",
        "notebook_session_id": payload.get("notebook_session_id"),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(json.dumps(session, ensure_ascii=False), encoding="utf-8")
    return session


def import_exam_materials(payload: dict[str, Any]) -> dict[str, Any]:
    course_id = str(payload.get("course_id", "default"))
    files = payload.get("files", [])
    material_root, _ = _ensure_paths(course_id)
    imported = 0
    if not isinstance(files, list):
        return {"status": "invalid", "reason": "files-must-be-list"}
    for item in files:
        name = str((item or {}).get("name", "material.txt"))
        content_b64 = str((item or {}).get("content_base64", ""))
        try:
            payload_bytes = base64.b64decode(content_b64.encode("ascii"))
            decoded = payload_bytes.decode("utf-8", errors="replace")
        except Exception:
            decoded = ""
        target = material_root / name.replace("/", "_")
        target.write_text(decoded, encoding="utf-8")
        imported += 1
    return {
        "status": "imported",
        "course_id": course_id,
        "source": str(payload.get("source", "")),
        "file_count": imported,
    }


def freeze_exam_materials(payload: dict[str, Any]) -> dict[str, Any]:
    course_id = str(payload.get("course_id", "default"))
    material_root, _ = _ensure_paths(course_id)
    stamp = material_root / "_frozen.txt"
    stamp.write_text(
        json.dumps({"course_id": course_id, "exam_rule": payload.get("exam_rule", "A0-A2 only")}, ensure_ascii=False),
        encoding="utf-8",
    )
    return {"status": "frozen", "course_id": course_id, "exam_rule": payload.get("exam_rule", "A0-A2 only")}


def open_exam_notebook(payload: dict[str, Any]) -> dict[str, Any]:
    course_id = str(payload.get("course_id", "default"))
    filename = str(payload.get("filename", "exam_notebook.ipynb"))
    workspace_root = workspace(course_id)
    notebook_root = workspace_root / "notebooks"
    notebook_root.mkdir(parents=True, exist_ok=True)
    session = start_exam_gateway_session({"course_id": course_id})
    session_id = session["session_id"]
    notebook_path = notebook_root / filename
    encoded = str(payload.get("content_base64", ""))
    try:
        raw = base64.b64decode(encoded.encode("ascii")).decode("utf-8")
    except Exception:
        raw = "{}"
    notebook = json.loads(raw) if raw else {"cells": []}
    if payload.get("strip_outputs"):
        for cell in notebook.get("cells", []):
            if isinstance(cell, dict):
                cell["outputs"] = []
    notebook_path.write_text(json.dumps(notebook, ensure_ascii=False), encoding="utf-8")
    return {
        "status": "opened",
        "session_id": session_id,
        "notebook": notebook,
        "notebook_path": str(notebook_path),
    }


def run_exam_notebook_cell(payload: dict[str, Any]) -> dict[str, Any]:
    source = str(payload.get("source", ""))
    run_id = _hash(source + str(payload.get("cell_index", "")) + str(payload.get("course_id", "")))[:16]
    return {
        "artifact_type": "exam_notebook_cell_run",
        "status": "kernel-unavailable",
        "message": "Kernel execution intentionally blocked in this gateway mode.",
        "notebook_work_sha256": _hash(source),
        "session_id": str(payload.get("session_id")),
        "cell_index": int(payload.get("cell_index", 0)),
        "execution_id": run_id,
    }


def exam_tutor_response(payload: dict[str, Any]) -> dict[str, Any]:
    course_id = str(payload.get("course_id", "default"))
    help_level = str(payload.get("help_level_requested", "A2")).strip().upper() or "A2"
    query = str(payload.get("query", ""))
    cell_context = payload.get("cell_context", {})
    written_decision_reference = str(payload.get("written_decision_reference", "") or "").strip()
    solution_categories = _contains_solution_request(query)
    non_standard_without_decision = _is_non_standard_help_level(help_level) and not written_decision_reference

    if _is_blocked_help_level(help_level) or solution_categories or non_standard_without_decision:
        categories = solution_categories or []
        if "solution_like_request" not in categories and not categories:
            categories = ["non_standard_help_requires_written_decision" if non_standard_without_decision else "solution_like_request"]
        if _is_blocked_help_level(help_level):
            categories.append("block_a6")
        if non_standard_without_decision:
            categories.append("non_standard_help_requires_written_decision")
        entry = {
            "artifact_type": "unibot_exam_ledger_entry",
            "help_level": help_level,
            "course_id": course_id,
            "cell_context": cell_context,
            "status": "blocked",
            "blocked": True,
            "repeat_task_required": True,
            "allowed": False,
            "categories": sorted(set(categories)),
            "prompt_sha256": _hash(query),
            "response_sha256": "",
            "raw_transcript_stored": False,
        }
        return {
            "status": "blocked",
            "help_ledger_entry": entry,
            "message": "Im exam_controlled Gateway sind A6 und loesungsartige Hilfe gesperrt; A3-A5 brauchen eine schriftliche Ausnahme.",
            "categories": entry["categories"],
        }

    safe_hint = (
        f"Bitte benenne einen ersten Teilschritt zu: „{query.strip() or 'der Aufgabe'}“ "
        "und begründe, was du zuerst prüfen möchtest."
    )
    if help_level not in ALLOWED_HELP_LEVELS:
        help_level = "A2"
    entry = {
        "artifact_type": "unibot_exam_ledger_entry",
        "help_level": help_level,
        "course_id": course_id,
        "cell_context": cell_context,
        "status": "ok",
        "blocked": False,
        "repeat_task_required": False,
        "allowed": True,
        "categories": [],
        "prompt_sha256": _hash(query),
        "response_sha256": _hash(safe_hint),
        "raw_transcript_stored": False,
        "source": "system",
        "source_card": {"topic": cell_context.get("topic", "jupyter-colab") if isinstance(cell_context, dict) else ""},
        "non_standard_help": False,
    }
    if written_decision_reference and _is_non_standard_help_level(str(payload.get("help_level_requested", "")).strip().upper()):
        entry["help_level"] = str(payload.get("help_level_requested", "")).strip().upper()
        entry["categories"] = ["non_standard_written_decision"]
        entry["non_standard_help"] = True
        entry["written_decision_reference_hash"] = _hash(written_decision_reference)
    return {
        "status": "ok",
        "help_ledger_entry": entry,
        "safe_hint": safe_hint,
        "message": "Sokratischer Zwischenhinweis",
        "source_card": entry["source_card"],
    }


def append_exam_ledger_event(payload: dict[str, Any]) -> dict[str, Any]:
    course_id = str(payload.get("course_id", "default"))
    _, ledger_path = _ensure_paths(course_id)
    help_level = str(payload.get("help_level", "A2"))
    prompt = str(payload.get("prompt", ""))
    raw_response = str(payload.get("raw_response", ""))
    cell_categories = _contains_solution_request(prompt + " " + raw_response)
    written_decision_reference = str(payload.get("written_decision_reference", "") or "").strip()
    non_standard_without_decision = _is_non_standard_help_level(help_level) and not written_decision_reference
    blocked = (
        _is_blocked_help_level(help_level)
        or any("solution_like_request" in c or "complete_code" in c for c in [cell_categories])
        or non_standard_without_decision
    )

    if blocked:
        categories = [*([*cell_categories] if cell_categories else ["solution_like_request"])]
        if _is_blocked_help_level(help_level):
            categories.append("complete_code")
        if non_standard_without_decision:
            categories.append("non_standard_help_requires_written_decision")
        status = "blocked"
        repeat_task_required = True
        allowed = False
    else:
        categories = ["non_standard_written_decision"] if _is_non_standard_help_level(help_level) else []
        status = "appended"
        repeat_task_required = False
        allowed = True

    record = {
        "artifact_type": "unibot_exam_ledger_event",
        "record_id": str(uuid.uuid4()),
        "course_id": course_id,
        "session_id": str(payload.get("session_id", "")),
        "gateway_session_id": str(payload.get("gateway_session_id", "")),
        "cell_index": int(payload.get("cell_index", 0) or 0),
        "cell_id": payload.get("cell_id", ""),
        "cell_type": payload.get("cell_type", ""),
        "help_level": help_level,
        "decision": str(payload.get("decision", "blocked" if blocked else "allowed")),
        "source": payload.get("source", ""),
        "source_card_ids": payload.get("source_card_ids", []),
        "allowed": allowed,
        "blocked": blocked,
        "repeat_task_required": repeat_task_required,
        "categories": categories,
        "non_standard_help": _is_non_standard_help_level(help_level),
        "raw_transcript_stored": False,
        "prompt_sha256": _hash(prompt),
        "response_sha256": _hash(raw_response),
        "prompt": "",
        "raw_response": "",
        "notebook_work_sha256": str(payload.get("notebook_work_sha256", "")),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "student_reflection": _redact_for_ledger(str(payload.get("student_reflection", ""))),
    }
    if written_decision_reference:
        record["written_decision_reference_hash"] = _hash(written_decision_reference)
    _append_json_line(ledger_path, record)
    summary = read_exam_help_ledger(course_id)["help_level_profile"]
    result = dict(record)
    result.pop("prompt", None)
    result.pop("raw_response", None)
    result.pop("student_reflection", None)
    return {
        "status": status,
        "record": result,
        "ledger_summary": {"help_level_profile": summary},
        "path_policy": "local-only exam ledger path is not included in public exports",
    }


def read_exam_help_ledger(course_id: str) -> dict[str, Any]:
    _, ledger_path = _ensure_paths(course_id)
    records = _load_json_lines(ledger_path)
    profile: dict[str, int] = {}
    for record in records:
        profile[str(record.get("help_level", "A2"))] = profile.get(str(record.get("help_level", "A2")), 0) + 1
    return {"status": "ok", "course_id": course_id, "count": len(records), "records": records, "help_level_profile": profile}


def export_exam_package(payload: dict[str, Any]) -> dict[str, Any]:
    course_id = str(payload.get("course_id", "default"))
    ledger = payload.get("help_ledger")
    if not isinstance(ledger, list):
        ledger = read_exam_help_ledger(course_id).get("records", [])
    sanitized_ledger = [sanitize_exam_export_entry(entry) for entry in ledger if isinstance(entry, dict)]
    notebook = payload.get("notebook")
    notebook_sha = _hash(json.dumps(notebook, ensure_ascii=False, sort_keys=True)) if isinstance(notebook, dict) else ""
    process_log = sanitize_process_log(payload.get("session_log", []))
    material_root, _ = _ensure_paths(course_id)
    freeze_receipt = material_root / "_frozen.txt"
    gateway_summary = {
        "entry_count": len(sanitized_ledger),
        "help_level_profile": help_level_profile(sanitized_ledger),
        "blocked_count": len([entry for entry in sanitized_ledger if entry.get("blocked")]),
    }
    package_id = _hash(f"{course_id}:{notebook_sha}:{json.dumps(gateway_summary, sort_keys=True)}")[:20]
    return {
        "artifact_type": "exam_authority_package",
        "package_id": package_id,
        "course_id": course_id,
        "status": "ready_for_human_review_not_exam_clearance",
        "exam_deployment_status": "not_cleared",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "material_manifest": {
            "freeze_status": "frozen" if freeze_receipt.exists() else "not_frozen_in_payload",
            "source_files_policy": "source files stay local; export uses hashes, manifest status, and reviewer-readable summaries",
        },
        "notebook_receipt": {
            "included": isinstance(notebook, dict),
            "notebook_sha256": notebook_sha,
            "outputs_policy": "strip or summarize outputs before authority review",
        },
        "process_log": process_log,
        "help_ledger": sanitized_ledger,
        "independence_evidence_profile": {"no_percentage_claim": True},
        "technical_confirmation": {
            "human_reviewable_independence_evidence": True,
            "independence_percentage_claimed": False,
            "raw_transcripts_included": False,
            "automatic_grading_included": False,
            "proctoring_included": False,
            "ai_detection_included": False,
        },
        "gateway_help_ledger_summary": gateway_summary,
        "recovery_hint": (
            "If A6 or solution-like help was seen, require a new own attempt or repeat task; "
            "do not convert the ledger into a grade or percentage of Eigenleistung."
        ),
    }


def sanitize_exam_export_entry(entry: dict[str, Any]) -> dict[str, Any]:
    source_card_ids = entry.get("source_card_ids", [])
    if not isinstance(source_card_ids, list):
        source_card_ids = []
    cell_context = entry.get("cell_context", {})
    if not isinstance(cell_context, dict):
        cell_context = {}
    return {
        "artifact_type": entry.get("artifact_type", "unibot_exam_ledger_entry"),
        "course_id": entry.get("course_id", ""),
        "session_id": entry.get("session_id", ""),
        "cell_index": entry.get("cell_index", cell_context.get("cell_index", "")),
        "cell_id": entry.get("cell_id", ""),
        "cell_type": entry.get("cell_type", cell_context.get("cell_type", "")),
        "help_level": entry.get("help_level", "A2"),
        "decision": entry.get("decision", entry.get("status", "")),
        "allowed": bool(entry.get("allowed", False)),
        "blocked": bool(entry.get("blocked", False)),
        "repeat_task_required": bool(entry.get("repeat_task_required", False)),
        "categories": list(entry.get("categories", []) or [])[:8],
        "source_card_ids": source_card_ids[:8],
        "prompt_sha256": entry.get("prompt_sha256", ""),
        "response_sha256": entry.get("response_sha256", ""),
        "notebook_work_sha256": entry.get("notebook_work_sha256", ""),
        "raw_transcript_stored": False,
        "human_review_required": True,
        "non_standard_help": bool(entry.get("non_standard_help", False)),
        "written_decision_reference_hash": entry.get("written_decision_reference_hash", ""),
    }


def sanitize_process_log(raw_log: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_log, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in raw_log[:50]:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "name": str(item.get("name", item.get("step", "")))[:80],
                "status": str(item.get("status", ""))[:80],
                "artifact_type": str(item.get("artifact_type", ""))[:80],
                "timestamp_utc": str(item.get("timestamp_utc", ""))[:80],
            }
        )
    return rows


def help_level_profile(entries: list[dict[str, Any]]) -> dict[str, int]:
    profile: dict[str, int] = {}
    for entry in entries:
        help_level = str(entry.get("help_level", "A2"))
        profile[help_level] = profile.get(help_level, 0) + 1
    return profile
