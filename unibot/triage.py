from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .feedback import read_demo_feedback
from .guardian import stable_hash
from .public_safety import scan_text


FEEDBACK_TRIAGE_SCHEMA_VERSION = "unibot-feedback-triage-v1"

SCENARIO_COMPONENTS = {
    "demo_setup": "browser_extension",
    "demo_prompt_card": "guardian_prompt_cards",
    "demo_block_solution": "postfilter",
    "demo_allowed_flow_and_ledger": "ledger_and_scoring",
    "demo_adaptive_tasks": "adaptive_tasks",
    "demo_notebook_template": "notebooks",
    "demo_redteam_smoke": "redteam_readiness",
}

SCENARIO_TEST_HINTS = {
    "demo_setup": "Run browser-extension static tests and local API health check.",
    "demo_prompt_card": "Run prompt-card and sidepanel tests.",
    "demo_block_solution": "Run postfilter and red-team solution-leakage tests.",
    "demo_allowed_flow_and_ledger": "Run ledger, score, and public-summary tests.",
    "demo_adaptive_tasks": "Run adaptive task-plan and sidepanel tests.",
    "demo_notebook_template": "Run notebook generation and audit tests.",
    "demo_redteam_smoke": "Run red-team and readiness tests.",
}


def build_feedback_triage(
    path: str | Path | None = None,
    records: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    public_records = _public_feedback_records(path=path, records=records)
    items = [_triage_item(record) for record in public_records if _needs_follow_up(record)]
    items.sort(key=lambda item: (item["priority_rank"], item["scenario_id"], item["feedback_id"]))
    for item in items:
        item.pop("priority_rank", None)

    report = {
        "schema_version": FEEDBACK_TRIAGE_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ready" if items else "empty",
        "feedback_count": len(public_records),
        "triage_count": len(items),
        "items": items,
        "public_policy": "Triage uses sanitized feedback metadata only; no screenshots, copied free text, local paths, emails, health/accommodation details, or real exam data.",
    }
    scan = scan_text(json.dumps(report, ensure_ascii=False), "feedback-triage")
    report["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        report["status"] = "blocked"
        report["public_safety_findings"] = scan["findings"]
    return report


def build_feedback_triage_markdown(
    path: str | Path | None = None,
    records: Iterable[dict[str, Any]] | None = None,
) -> str:
    triage = build_feedback_triage(path=path, records=records)
    lines = [
        "# UniBot Demo Feedback Triage",
        "",
        f"Status: {triage['status']}",
        "",
        f"Feedback: {triage['feedback_count']}",
        f"Triage items: {triage['triage_count']}",
        "",
        "Boundary: public-safe maintenance queue only, not exam evidence.",
        "",
    ]
    for item in triage["items"]:
        lines.extend(
            [
                f"## {item['priority']} {item['scenario_id']}",
                "",
                f"- Component: {item['component']}",
                f"- Outcome: {item['outcome']}",
                f"- Severity: {item['severity']}",
                f"- Feedback ID: `{item['feedback_id']}`",
                f"- Suggested test: {item['suggested_test']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _public_feedback_records(
    path: str | Path | None = None,
    records: Iterable[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if records is None:
        payload = read_demo_feedback(path)
        raw_records = payload.get("records", [])
    else:
        raw_records = list(records)

    public_records = []
    for record in raw_records:
        feedback = record.get("feedback") if isinstance(record, dict) and "feedback" in record else record
        if not isinstance(feedback, dict):
            continue
        public_records.append(_normalize_public_record(feedback))
    return public_records


def _normalize_public_record(record: dict[str, Any]) -> dict[str, Any]:
    scenario_id = str(record.get("scenario_id", "unknown") or "unknown")
    outcome = str(record.get("outcome", "unknown") or "unknown")
    severity = str(record.get("severity", "minor") or "minor")
    feedback_id = str(record.get("feedback_id", "") or "")
    if not feedback_id:
        feedback_id = stable_hash(json.dumps(record, ensure_ascii=False, sort_keys=True))[:16]
    return {
        "feedback_id": feedback_id,
        "scenario_id": scenario_id,
        "outcome": outcome,
        "severity": severity,
        "button_or_endpoint_hash": stable_hash(str(record.get("button_or_endpoint", "")))[:12],
        "has_public_safe_text": bool(record.get("has_public_safe_text", False)),
        "has_follow_up_note": bool(record.get("has_follow_up_note", False)),
    }


def _needs_follow_up(record: dict[str, Any]) -> bool:
    return record["outcome"] in {"fail", "blocked", "confusing"} or record["severity"] in {"major", "critical"}


def _priority(record: dict[str, Any]) -> tuple[str, int]:
    if record["severity"] == "critical" or record["outcome"] == "blocked":
        return "P0", 0
    if record["severity"] == "major" or record["outcome"] == "fail":
        return "P1", 1
    if record["outcome"] == "confusing":
        return "P2", 2
    return "P3", 3


def _triage_item(record: dict[str, Any]) -> dict[str, Any]:
    priority, priority_rank = _priority(record)
    scenario_id = record["scenario_id"]
    component = SCENARIO_COMPONENTS.get(scenario_id, "unibot_general")
    title = f"[{priority}] UniBot demo feedback: {scenario_id}"
    return {
        "triage_id": stable_hash(f"{record['feedback_id']}:{scenario_id}:{priority}")[:16],
        "feedback_id": record["feedback_id"],
        "priority": priority,
        "priority_rank": priority_rank,
        "scenario_id": scenario_id,
        "component": component,
        "outcome": record["outcome"],
        "severity": record["severity"],
        "suggested_test": SCENARIO_TEST_HINTS.get(scenario_id, "Run UniBot targeted tests and readiness."),
        "issue_draft": {
            "title": title,
            "labels": ["unibot", "demo-feedback", priority.lower(), component],
            "body": (
                "Public-safe UniBot demo feedback triage.\n\n"
                f"- Scenario: `{scenario_id}`\n"
                f"- Component: `{component}`\n"
                f"- Outcome: `{record['outcome']}`\n"
                f"- Severity: `{record['severity']}`\n"
                f"- Feedback ID: `{record['feedback_id']}`\n"
                f"- Suggested test: {SCENARIO_TEST_HINTS.get(scenario_id, 'Run UniBot targeted tests and readiness.')}\n\n"
                "No free-text feedback, screenshots, private data, local paths, or real exam material included."
            ),
        },
    }
