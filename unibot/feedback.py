from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .demo import build_local_demo_run
from .guardian import stable_hash
from .public_safety import scan_text


DEMO_FEEDBACK_SCHEMA_VERSION = "unibot-demo-feedback-v1"
DEFAULT_FEEDBACK_PATH = Path.home() / ".unibot_guardian" / "demo_feedback.jsonl"

ALLOWED_OUTCOMES = {"pass", "fail", "blocked", "confusing", "not_tested"}
ALLOWED_SEVERITIES = {"info", "minor", "major", "critical"}
REQUIRED_FIELDS = ["scenario_id", "what_i_tried", "expected", "what_happened", "button_or_endpoint"]


def demo_feedback_template() -> dict[str, Any]:
    demo = build_local_demo_run()
    return {
        "schema_version": DEMO_FEEDBACK_SCHEMA_VERSION,
        "status": "template",
        "allowed_scenario_ids": [scenario["scenario_id"] for scenario in demo["scenarios"]],
        "allowed_outcomes": sorted(ALLOWED_OUTCOMES),
        "allowed_severities": sorted(ALLOWED_SEVERITIES),
        "required_fields": REQUIRED_FIELDS,
        "fields": {
            "scenario_id": "",
            "outcome": "fail",
            "severity": "minor",
            "what_i_tried": "",
            "expected": "",
            "what_happened": "",
            "button_or_endpoint": "",
            "public_safe_text": "",
            "private_data_removed": True,
            "follow_up_needed": "",
        },
        "public_safety_policy": "Remove private data, emails, local paths, health/accommodation details, real exam work, and raw private course text before sharing.",
    }


def resolve_feedback_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get("UNIBOT_DEMO_FEEDBACK_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_FEEDBACK_PATH


def normalize_demo_feedback(raw: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "scenario_id": str(raw.get("scenario_id", "") or "").strip(),
        "outcome": str(raw.get("outcome", "fail") or "fail").strip().lower(),
        "severity": str(raw.get("severity", "minor") or "minor").strip().lower(),
        "what_i_tried": str(raw.get("what_i_tried", "") or "").strip(),
        "expected": str(raw.get("expected", "") or "").strip(),
        "what_happened": str(raw.get("what_happened", "") or "").strip(),
        "button_or_endpoint": str(raw.get("button_or_endpoint", raw.get("which_button_or_endpoint", "")) or "").strip(),
        "public_safe_text": str(
            raw.get("public_safe_text", raw.get("screenshot_or_copied_public_safe_text", "")) or ""
        ).strip(),
        "private_data_removed": bool(raw.get("private_data_removed", False)),
        "follow_up_needed": str(raw.get("follow_up_needed", "") or "").strip(),
    }
    if normalized["outcome"] not in ALLOWED_OUTCOMES:
        normalized["outcome"] = "fail"
    if normalized["severity"] not in ALLOWED_SEVERITIES:
        normalized["severity"] = "minor"
    return normalized


def validate_demo_feedback(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"status": "invalid", "issues": ["feedback_must_be_object"], "findings": []}

    normalized = normalize_demo_feedback(raw)
    demo = build_local_demo_run()
    allowed_scenarios = {scenario["scenario_id"] for scenario in demo["scenarios"]}
    issues: list[str] = []

    for field in REQUIRED_FIELDS:
        if not normalized.get(field):
            issues.append(f"missing_{field}")
    if normalized["scenario_id"] and normalized["scenario_id"] not in allowed_scenarios:
        issues.append("unknown_scenario_id")
    if normalized["outcome"] not in ALLOWED_OUTCOMES:
        issues.append("invalid_outcome")
    if normalized["severity"] not in ALLOWED_SEVERITIES:
        issues.append("invalid_severity")
    if normalized["private_data_removed"] is not True:
        issues.append("private_data_not_confirmed_removed")

    scan_payload = "\n".join(
        [
            normalized["scenario_id"],
            normalized["what_i_tried"],
            normalized["expected"],
            normalized["what_happened"],
            normalized["button_or_endpoint"],
            normalized["public_safe_text"],
            normalized["follow_up_needed"],
        ]
    )
    scan = scan_text(scan_payload, "demo-feedback")
    if scan["status"] != "pass":
        issues.append("feedback_not_public_safe")

    public_record = _to_public_feedback_record(normalized)
    return {
        "schema_version": DEMO_FEEDBACK_SCHEMA_VERSION,
        "status": "blocked" if issues else "ok",
        "issues": issues,
        "findings": scan["findings"],
        "feedback_id": public_record["feedback_id"],
        "public_record": public_record if not issues else _blocked_record(normalized, public_record["feedback_id"]),
        "storage_policy": "store locally only after validation; public summaries exclude free text",
    }


def append_demo_feedback(feedback: dict[str, Any], path: str | Path | None = None) -> dict[str, Any]:
    validation = validate_demo_feedback(feedback)
    if validation["status"] != "ok":
        return {
            "status": "blocked_not_stored",
            "validation": validation,
            "storage_policy": "unsafe or incomplete demo feedback is not written",
        }
    feedback_path = resolve_feedback_path(path)
    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": DEMO_FEEDBACK_SCHEMA_VERSION,
        "stored_at_utc": datetime.now(timezone.utc).isoformat(),
        "feedback": validation["public_record"],
        "storage_policy": "local-only jsonl; public summaries exclude free text",
    }
    with feedback_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return {"status": "stored", "path": str(feedback_path), "record": record}


def read_demo_feedback(path: str | Path | None = None, limit: int | None = None) -> dict[str, Any]:
    feedback_path = resolve_feedback_path(path)
    if not feedback_path.exists():
        return {"status": "empty", "path": str(feedback_path), "count": 0, "records": []}

    rows = []
    with feedback_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    if limit is not None:
        rows = rows[-max(0, int(limit)) :]
    return {"status": "ok", "path": str(feedback_path), "count": len(rows), "records": rows}


def summarize_demo_feedback(path: str | Path | None = None) -> dict[str, Any]:
    payload = read_demo_feedback(path)
    records = [row.get("feedback", {}) for row in payload.get("records", [])]
    by_scenario: dict[str, int] = {}
    by_outcome: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    needs_follow_up = 0

    for record in records:
        scenario = str(record.get("scenario_id", "unknown"))
        outcome = str(record.get("outcome", "unknown"))
        severity = str(record.get("severity", "unknown"))
        by_scenario[scenario] = by_scenario.get(scenario, 0) + 1
        by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
        by_severity[severity] = by_severity.get(severity, 0) + 1
        if outcome in {"fail", "blocked", "confusing"} or severity in {"major", "critical"}:
            needs_follow_up += 1

    return {
        "schema_version": "unibot-demo-feedback-summary-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": payload["status"],
        "path": payload["path"],
        "feedback_count": len(records),
        "needs_follow_up_count": needs_follow_up,
        "by_scenario": by_scenario,
        "by_outcome": by_outcome,
        "by_severity": by_severity,
        "storage_policy": "summary excludes free text and private details",
    }


def export_public_demo_feedback_summary(path: str | Path | None = None) -> dict[str, Any]:
    summary = summarize_demo_feedback(path)
    return {
        "schema_version": summary["schema_version"],
        "generated_at_utc": summary["generated_at_utc"],
        "feedback_count": summary["feedback_count"],
        "needs_follow_up_count": summary["needs_follow_up_count"],
        "by_scenario": summary["by_scenario"],
        "by_outcome": summary["by_outcome"],
        "by_severity": summary["by_severity"],
        "public_policy": "no screenshots, copied free text, local paths, emails, health/accommodation details, or real exam data",
    }


def _to_public_feedback_record(normalized: dict[str, Any]) -> dict[str, Any]:
    digest_input = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
    return {
        "feedback_id": stable_hash(digest_input)[:16],
        "scenario_id": normalized["scenario_id"],
        "outcome": normalized["outcome"],
        "severity": normalized["severity"],
        "button_or_endpoint": normalized["button_or_endpoint"],
        "private_data_removed": normalized["private_data_removed"],
        "has_public_safe_text": bool(normalized["public_safe_text"]),
        "has_follow_up_note": bool(normalized["follow_up_needed"]),
        "text_hash": stable_hash(
            "\n".join(
                [
                    normalized["what_i_tried"],
                    normalized["expected"],
                    normalized["what_happened"],
                    normalized["public_safe_text"],
                    normalized["follow_up_needed"],
                ]
            )
        ),
    }


def _blocked_record(normalized: dict[str, Any], feedback_id: str) -> dict[str, Any]:
    return {
        "feedback_id": feedback_id,
        "scenario_id": normalized.get("scenario_id", ""),
        "outcome": normalized.get("outcome", "fail"),
        "severity": normalized.get("severity", "minor"),
        "private_data_removed": normalized.get("private_data_removed", False),
        "blocked_reason": "not stored; fix validation issues and remove private data",
    }
