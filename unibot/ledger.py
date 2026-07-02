from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .guardian import HELP_LEVEL_DEDUCTIONS, normalize_help_level, stable_hash
from .public_safety import scan_text


LEDGER_SCHEMA_VERSION = "unibot-guardian-ledger-v1"
DEFAULT_LEDGER_PATH = Path.home() / ".unibot_guardian" / "help_ledger.jsonl"

ALLOWED_EVENT_KEYS = {
    "mode",
    "tool",
    "task_id",
    "skill_tags",
    "raw_output_hash",
    "classification",
    "allowed_hint",
    "help_level",
    "privacy_flags",
    "source_card_ids",
    "student_reflection",
    "timestamp_utc",
}


def resolve_ledger_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get("UNIBOT_LEDGER_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_LEDGER_PATH


def sanitize_event(event: dict[str, Any]) -> dict[str, Any]:
    cleaned = {key: event.get(key) for key in ALLOWED_EVENT_KEYS if key in event}
    cleaned.setdefault("mode", "practice_overlay")
    cleaned.setdefault("tool", "unknown")
    cleaned.setdefault("task_id", stable_hash(json.dumps(event, sort_keys=True, ensure_ascii=False))[:12])
    cleaned.setdefault("skill_tags", [])
    cleaned.setdefault("classification", [])
    cleaned.setdefault("privacy_flags", [])
    cleaned.setdefault("source_card_ids", [])
    cleaned["help_level"] = normalize_help_level(cleaned.get("help_level"))
    cleaned.setdefault("allowed_hint", "")
    cleaned.setdefault("raw_output_hash", stable_hash(""))
    cleaned.setdefault("timestamp_utc", datetime.now(timezone.utc).isoformat())

    reflection = str(cleaned.get("student_reflection", "") or "").strip()
    reflection_scan = scan_text(reflection, "student_reflection")
    if reflection_scan["findings"]:
        cleaned["student_reflection"] = ""
        cleaned["reflection_redacted"] = True
        cleaned["reflection_privacy_flags"] = sorted({finding["type"] for finding in reflection_scan["findings"]})
    else:
        cleaned["student_reflection"] = reflection
        cleaned["reflection_redacted"] = False
        cleaned["reflection_privacy_flags"] = []

    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "stored_at_utc": datetime.now(timezone.utc).isoformat(),
        "event": cleaned,
        "storage_policy": "local-only jsonl; raw external AI output is never stored",
    }


def append_ledger_event(event: dict[str, Any], path: str | Path | None = None) -> dict[str, Any]:
    record = sanitize_event(event)
    ledger_path = resolve_ledger_path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "status": "stored",
        "path": str(ledger_path),
        "record": record,
    }


def read_ledger(path: str | Path | None = None, limit: int | None = None) -> dict[str, Any]:
    ledger_path = resolve_ledger_path(path)
    if not ledger_path.exists():
        return {"status": "empty", "path": str(ledger_path), "count": 0, "events": []}

    rows = []
    with ledger_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    if limit is not None:
        rows = rows[-max(0, int(limit)) :]
    return {"status": "ok", "path": str(ledger_path), "count": len(rows), "events": rows}


def summarize_ledger(path: str | Path | None = None) -> dict[str, Any]:
    payload = read_ledger(path)
    events = [row.get("event", {}) for row in payload.get("events", [])]
    by_help_level: dict[str, int] = {}
    by_skill: dict[str, int] = {}
    blocked_count = 0
    privacy_count = 0
    max_deduction = 0

    for event in events:
        help_level = normalize_help_level(event.get("help_level"))
        by_help_level[help_level] = by_help_level.get(help_level, 0) + 1
        max_deduction = max(max_deduction, HELP_LEVEL_DEDUCTIONS[help_level])
        classifications = event.get("classification", []) or []
        privacy_flags = event.get("privacy_flags", []) or []
        if classifications:
            blocked_count += 1
        if privacy_flags or event.get("reflection_redacted"):
            privacy_count += 1
        for skill in event.get("skill_tags", []) or []:
            by_skill[skill] = by_skill.get(skill, 0) + 1

    return {
        "status": payload["status"],
        "path": payload["path"],
        "event_count": len(events),
        "blocked_or_flagged_count": blocked_count,
        "privacy_event_count": privacy_count,
        "by_help_level": by_help_level,
        "by_skill": by_skill,
        "max_deduction": max_deduction,
        "note": "Summary is formative and private; it is not a grade or official assessment.",
    }


def export_public_ledger_summary(path: str | Path | None = None) -> dict[str, Any]:
    summary = summarize_ledger(path)
    return {
        "schema_version": "unibot-guardian-ledger-summary-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "event_count": summary["event_count"],
        "blocked_or_flagged_count": summary["blocked_or_flagged_count"],
        "privacy_event_count": summary["privacy_event_count"],
        "by_help_level": summary["by_help_level"],
        "by_skill": summary["by_skill"],
        "max_deduction": summary["max_deduction"],
        "storage_policy": "public summary excludes raw external AI output and student reflections",
        "assessment_policy": "private formative selftest only; no grade",
    }
