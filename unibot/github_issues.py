from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .public_safety import scan_text
from .triage import build_feedback_triage


GITHUB_ISSUE_BUNDLE_SCHEMA_VERSION = "unibot-github-issue-bundle-v1"
GITHUB_ISSUE_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-github-issue-release-review-board-claim-alignment-v1"
)

GLOBAL_MANUAL_PUBLICATION_READINESS_CHECK_IDS = [
    "github_issue_bundle",
    "publication_package",
    "release_runbook",
    "review_board_packet",
    "gretel_bachelor_thesis_package",
    "evaluation_packet",
    "public_safety",
]

GLOBAL_MANUAL_PUBLICATION_HUMAN_GATES = [
    "human_review_before_github_create",
    "human_submission_review_required",
    "public_safety_required",
]

SCENARIO_EVIDENCE_MAP = {
    "demo_setup": {
        "readiness_check_ids": ["public_safety", "local_demo_run", "readiness_runtime_guard"],
        "source_card_ids": ["chrome-content-scripts", "chrome-limited-use"],
    },
    "demo_prompt_card": {
        "readiness_check_ids": ["evaluation_packet", "source_card_drift_guard", "gretel_bachelor_thesis_package"],
        "source_card_ids": ["vanlehn-2011", "uoc-ki-lehre", "dfg-gwp"],
    },
    "demo_block_solution": {
        "readiness_check_ids": ["redteam", "evaluation_packet", "exam_boundary"],
        "source_card_ids": ["uoc-ki-faq", "uoc-hilfsmittel", "eu-ai-act-2024"],
    },
    "demo_allowed_flow_and_ledger": {
        "readiness_check_ids": ["notebook_template", "demo_feedback_contract", "public_safety"],
        "source_card_ids": ["dfg-gwp", "gdpr-2016-679"],
    },
    "demo_adaptive_tasks": {
        "readiness_check_ids": ["adaptive_task_plan", "course_material_policy", "source_card_drift_guard"],
        "source_card_ids": ["vanlehn-2011", "kulik-fletcher-2016", "dfg-gwp"],
    },
    "demo_notebook_template": {
        "readiness_check_ids": ["notebook_template", "source_cards", "public_safety"],
        "source_card_ids": ["google-colab-gemini", "jupyter-ai", "dfg-gwp"],
    },
    "demo_redteam_smoke": {
        "readiness_check_ids": ["redteam", "readiness_runtime_guard", "publication_package"],
        "source_card_ids": ["openai-evals", "dfg-gwp"],
    },
}

FALLBACK_EVIDENCE = {
    "readiness_check_ids": ["public_safety", "readiness_runtime_guard"],
    "source_card_ids": ["dfg-gwp"],
}


def build_issue_review_contract() -> dict[str, Any]:
    return {
        "schema_version": "unibot-github-issue-review-contract-v1",
        "status": "manual_review_required",
        "review_checklist": [
            "Confirm the draft uses sanitized triage metadata only.",
            "Confirm the scenario is synthetic or public-safe.",
            "Confirm the issue does not claim exam clearance, grading authority, proctoring reliability, or AI-detection evidence.",
            "Confirm at least one focused test or readiness gate is named.",
            "Confirm the evidence traceability fields match the issue scenario.",
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
    traceability = build_issue_evidence_traceability(issues)
    bundle = {
        "schema_version": GITHUB_ISSUE_BUNDLE_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ready" if issues else "empty",
        "source_triage_status": triage["status"],
        "issue_count": len(issues),
        "review_contract": review_contract,
        "evidence_traceability": traceability,
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


def build_issue_evidence_traceability(issues: Iterable[dict[str, Any]]) -> dict[str, Any]:
    issue_rows = [
        {
            "issue_id": issue["issue_id"],
            "scenario_id": issue["scenario_id"],
            "component": issue["component"],
            "priority": issue["priority"],
            "readiness_check_ids": issue["readiness_check_ids"],
            "source_card_ids": issue["source_card_ids"],
            "human_gates": issue["human_gates"],
            "manual_publish_only": issue["manual_publish_only"],
        }
        for issue in issues
    ]
    traceability = {
        "schema_version": "unibot-github-issue-evidence-traceability-v1",
        "status": "ready" if issue_rows else "empty",
        "issue_count": len(issue_rows),
        "manual_publish_only": all(row["manual_publish_only"] for row in issue_rows),
        "publication_gate": "human_review_before_github_create",
        "readiness_snapshot_contract": {
            "expected_schema_version": "unibot-readiness-evidence-snapshot-v1",
            "required_status": "ready",
            "use": "Use the latest readiness evidence snapshot to confirm issue follow-up remains public-safe and science-gated.",
        },
        "manual_publication_claim_contract": {
            "expected_schema_version": GITHUB_ISSUE_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
            "required_publication_release_review_board_schema_version": (
                "unibot-publication-release-review-board-claim-alignment-v1"
            ),
            "required_review_board_thesis_evaluation_schema_version": (
                "unibot-review-board-thesis-evaluation-claim-alignment-v1"
            ),
            "required_readiness_check_ids": [
                "github_issue_bundle",
                "publication_package",
                "release_runbook",
                "review_board_packet",
                "gretel_bachelor_thesis_package",
                "evaluation_packet",
                "public_safety",
            ],
            "required_human_gates": GLOBAL_MANUAL_PUBLICATION_HUMAN_GATES,
            "manual_publish_only": True,
            "use": "GitHub issue drafts must carry publication/review-board thesis-evaluation boundaries without creating issues or implying release approval.",
        },
        "issues": issue_rows,
        "unique_readiness_check_ids": sorted({check_id for row in issue_rows for check_id in row["readiness_check_ids"]}),
        "unique_source_card_ids": sorted({source_id for row in issue_rows for source_id in row["source_card_ids"]}),
        "required_human_gates": sorted({gate for row in issue_rows for gate in row["human_gates"]}),
        "policy": "Feedback-derived issue drafts stay sanitized, source-bound, readiness-gated, and manually published only.",
    }
    required_check_ids = set(traceability["manual_publication_claim_contract"]["required_readiness_check_ids"])
    present_check_ids = set(traceability["unique_readiness_check_ids"])
    traceability["missing_release_review_board_claim_check_ids"] = sorted(required_check_ids - present_check_ids)
    required_human_gates = set(traceability["manual_publication_claim_contract"]["required_human_gates"])
    present_human_gates = set(traceability["required_human_gates"])
    traceability["missing_release_review_board_claim_human_gates"] = sorted(required_human_gates - present_human_gates)
    if (
        traceability["missing_release_review_board_claim_check_ids"]
        or traceability["missing_release_review_board_claim_human_gates"]
    ) and issue_rows:
        traceability["status"] = "blocked"
    scan = scan_text(json.dumps(traceability, ensure_ascii=False), "github-issue-evidence-traceability")
    traceability["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        traceability["status"] = "blocked"
    return traceability


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
                f"- Readiness checks: {', '.join(issue['readiness_check_ids'])}",
                f"- Source cards: {', '.join(issue['source_card_ids'])}",
                f"- Human gates: {', '.join(issue['human_gates'])}",
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
    evidence = SCENARIO_EVIDENCE_MAP.get(item["scenario_id"], FALLBACK_EVIDENCE)
    readiness_check_ids = sorted(set(evidence["readiness_check_ids"]) | set(GLOBAL_MANUAL_PUBLICATION_READINESS_CHECK_IDS))
    human_gates = sorted(set(GLOBAL_MANUAL_PUBLICATION_HUMAN_GATES))
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
        "readiness_check_ids": readiness_check_ids,
        "source_card_ids": list(evidence["source_card_ids"]),
        "human_gates": human_gates,
        "review_checklist": contract["review_checklist"],
        "evidence_requirements": contract["evidence_requirements"],
        "publication_gate": contract["publication_gate"],
        "manual_publish_only": contract["manual_publish_only"],
    }
