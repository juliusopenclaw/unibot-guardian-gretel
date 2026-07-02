from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .public_safety import scan_text
from .triage import build_feedback_triage


GITHUB_ISSUE_BUNDLE_SCHEMA_VERSION = "unibot-github-issue-bundle-v1"


def build_issue_review_contract() -> dict[str, Any]:
    return {
        "schema_version": "unibot-github-issue-review-contract-v1",
        "status": "manual_review_required",
        "review_checklist": [
            "Confirm the draft uses sanitized triage metadata only.",
            "Confirm the scenario is synthetic or public-safe.",
            "Confirm the issue does not claim exam clearance, grading authority, proctoring reliability, or AI-detection evidence.",
            "Confirm at least one focused test or readiness gate is named.",
            "Confirm the issue can be closed by code, docs, tests, or a documented blocked reason.",
        ],
        "evidence_requirements": [
            "affected component",
            "scenario id",
            "priority",
            "suggested focused test",
            "public-safety status",
            "manual publication decision",
        ],
        "publication_gate": "human_review_before_github_create",
        "manual_publish_only": True,
    }


def build_github_issue_bundle(
    path: str | Path | None = None,
    records: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    triage = build_feedback_triage(path=path, records=records)
    issues = [_issue_from_triage_item(item) for item in triage["items"]]
    review_contract = build_issue_review_contract()
    bundle = {
        "schema_version": GITHUB_ISSUE_BUNDLE_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ready" if issues else "empty",
        "source_triage_status": triage["status"],
        "issue_count": len(issues),
        "review_contract": review_contract,
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
                f"- Publication gate: {issue['publication_gate']}",
                f"- Manual publish only: {issue['manual_publish_only']}",
                "",
                issue["body"],
                "",
                "Review checklist:",
                *[f"- {item}" for item in issue["review_checklist"]],
                "",
                "Evidence requirements:",
                *[f"- {item}" for item in issue["evidence_requirements"]],
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _issue_from_triage_item(item: dict[str, Any]) -> dict[str, Any]:
    draft = item["issue_draft"]
    contract = build_issue_review_contract()
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
        "review_checklist": contract["review_checklist"],
        "evidence_requirements": contract["evidence_requirements"],
        "publication_gate": contract["publication_gate"],
        "manual_publish_only": contract["manual_publish_only"],
    }
