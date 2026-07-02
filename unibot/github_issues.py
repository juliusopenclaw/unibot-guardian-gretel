from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .public_safety import scan_text
from .triage import build_feedback_triage


GITHUB_ISSUE_BUNDLE_SCHEMA_VERSION = "unibot-github-issue-bundle-v1"


def build_github_issue_bundle(
    path: str | Path | None = None,
    records: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    triage = build_feedback_triage(path=path, records=records)
    issues = [_issue_from_triage_item(item) for item in triage["items"]]
    bundle = {
        "schema_version": GITHUB_ISSUE_BUNDLE_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ready" if issues else "empty",
        "source_triage_status": triage["status"],
        "issue_count": len(issues),
        "issues": issues,
        "public_policy": "Draft issues use sanitized triage metadata only; no private data, screenshots, copied free text, local paths, or real exam material.",
        "publishing_note": "Review manually before creating GitHub issues. Do not claim exam clearance.",
    }
    scan = scan_text(json.dumps(bundle, ensure_ascii=False), "github-issue-bundle")
    bundle["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        bundle["status"] = "blocked"
        bundle["public_safety_findings"] = scan["findings"]
    return bundle


def build_github_issue_bundle_markdown(
    path: str | Path | None = None,
    records: Iterable[dict[str, Any]] | None = None,
) -> str:
    bundle = build_github_issue_bundle(path=path, records=records)
    lines = [
        "# UniBot GitHub Issue Bundle",
        "",
        f"Status: {bundle['status']}",
        f"Issues: {bundle['issue_count']}",
        "",
        "Boundary: public-safe draft issues only, not exam evidence or clearance.",
        "",
    ]
    for issue in bundle["issues"]:
        lines.extend(
            [
                f"## {issue['title']}",
                "",
                f"- File: `{issue['filename']}`",
                f"- Labels: {', '.join(issue['labels'])}",
                "",
                issue["body"],
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _issue_from_triage_item(item: dict[str, Any]) -> dict[str, Any]:
    draft = item["issue_draft"]
    labels = sorted(set(str(label) for label in draft.get("labels", [])))
    filename = f"{item['priority'].lower()}-{item['scenario_id']}-{item['triage_id']}.md"
    return {
        "issue_id": item["triage_id"],
        "feedback_id": item["feedback_id"],
        "filename": filename,
        "title": draft["title"],
        "labels": labels,
        "body": draft["body"],
        "priority": item["priority"],
        "component": item["component"],
        "scenario_id": item["scenario_id"],
        "suggested_test": item["suggested_test"],
    }
