from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .public_safety import scan_text


AUTONOMY_SCHEMA_VERSION = "unibot-gretel-autonomous-research-loop-v1"
AUTONOMY_MARKDOWN_TITLE = "UniBot Gretel Autonomous Research Loop"


def build_unibot_intent_contract() -> dict[str, Any]:
    return {
        "schema_version": "unibot-gretel-intent-contract-v1",
        "status": "active_public_research_contract",
        "owner": "Gretel",
        "human_gate": "Julius or another human reviewer",
        "north_star": (
            "Build UniBot as a public, source-bound, bachelor-thesis-level research project "
            "that helps coding learners practice without outsourcing their own work, leaking "
            "private material, or claiming exam clearance."
        ),
        "product_intents": [
            {
                "intent_id": "socratic_integrity_layer",
                "must_do": "Convert learner requests and external AI output into Socratic prompts, reflection, and bounded help levels.",
                "must_not": "Provide final answers, complete code fixes, grading decisions, proctoring claims, or AI-detection evidence.",
            },
            {
                "intent_id": "open_science_reproducibility",
                "must_do": "Keep docs, source cards, synthetic tests, readiness gates, and red-team scenarios reproducible for public review.",
                "must_not": "Use private course files, real exam artifacts, raw external transcripts, personal data, or local paths in public artifacts.",
            },
            {
                "intent_id": "glm_scientific_engineering",
                "must_do": "Use GLM-5.2 only as a redacted proposal lane for architecture, harness, documentation, and tests.",
                "must_not": "Let GLM apply code, publish GitHub changes, request private context, call providers by default, or issue Final-Go.",
            },
            {
                "intent_id": "autonomous_quality_loop",
                "must_do": "Continuously select small, testable improvements and turn every accepted idea into a harness, source note, or review entry.",
                "must_not": "Spend unbounded tokens, broaden scope without evidence, or treat passing narrow tests as proof of broad completion.",
            },
        ],
        "always_use_standards": [
            "Three Golden Rules",
            "public-safety scan",
            "readiness check",
            "source cards",
            "red-team scenarios",
            "synthetic fixtures",
            "review-board/open-decision register",
            "Gretel/GLM proposal-only lane",
            "human review for publication, university submission, provider calls, and exam clearance",
        ],
    }


def build_autonomy_budget_policy() -> dict[str, Any]:
    return {
        "schema_version": "unibot-gretel-autonomy-budget-policy-v1",
        "status": "budgeted_reasonable_autonomy",
        "cadence": {
            "recommended_cron": "every_6_hours",
            "max_active_work_item_per_run": 1,
            "max_candidate_files_changed_per_run": 4,
            "prefer_smallest_safe_patch": True,
        },
        "token_policy": {
            "default_reasoning_effort": "low",
            "escalate_to_medium_only_when": [
                "a focused test fails and local code inspection identifies a bounded fix",
                "a public-safety/readiness gate fails",
                "the next work item affects API contracts or publication gates",
            ],
            "never_use_high_for_routine_monitoring": True,
            "provider_call_default": "disabled",
        },
        "allowed_autonomous_actions": [
            "inspect public repo state",
            "run focused tests",
            "run public-safety and readiness checks",
            "edit public docs, tests, and code inside this repository",
            "commit local changes after green focused checks",
            "prepare GitHub issue bundles or PR text for human review",
        ],
        "blocked_autonomous_actions": [
            "publish or push to GitHub without explicit human review",
            "send email, calendar, chat, or webhook messages",
            "call GLM/Z.AI/OpenAI or another provider without explicit go and redaction receipt",
            "ingest private course materials or real exam data",
            "claim exam clearance, grading authority, proctoring reliability, or AI-detection evidence",
            "set Final-Go",
        ],
    }


def build_autonomous_work_queue() -> list[dict[str, Any]]:
    return [
        {
            "work_id": "intent_contract_regression_pack",
            "priority": 1,
            "status": "closed_harnessed",
            "goal": "Keep Gretel's UniBot intent, standards, and autonomous-loop boundaries testable.",
            "allowed_files": [
                "unibot/autonomous_research_loop.py",
                "tests/test_unibot_autonomous_research_loop.py",
                "docs/unibot/UNIBOT_GRETEL_AUTONOMOUS_RESEARCH_LOOP.md",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_autonomous_research_loop.py -q"],
            "review_gate": "public_safety_and_readiness_pass",
            "closure_evidence": {
                "commit": "fa942b0",
                "summary": "Autonomous loop, intent contract, budget policy, API routes, docs, and tests added.",
            },
        },
        {
            "work_id": "scientific_evaluation_depth",
            "priority": 2,
            "status": "closed_harnessed",
            "goal": "Add richer synthetic evaluation dimensions for Socratic help quality, source anchoring, and refusal clarity.",
            "allowed_files": ["unibot/evaluation.py", "tests/test_unibot_evaluation.py", "docs/unibot/UNIBOT_DEMO_TEST_PLAN.md"],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_evaluation.py tests/test_unibot_redteam.py -q"],
            "review_gate": "no_exam_claims_no_private_data",
            "closure_evidence": {
                "commit": "2b6473b",
                "summary": "Scientific quality rubric added for Socratic help, source grounding, refusal clarity, privacy, and learner agency.",
            },
        },
        {
            "work_id": "github_review_packet_hardening",
            "priority": 3,
            "status": "closed_harnessed",
            "goal": "Make GitHub issue and review packets clearer for outside scientific reviewers without auto-publishing.",
            "allowed_files": ["unibot/github_issues.py", "tests/test_unibot_github_issues.py", "docs/unibot/UNIBOT_GITHUB_ISSUE_BUNDLE.md"],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_github_issues.py tests/test_unibot_publication.py -q"],
            "review_gate": "manual_publication_only",
            "closure_evidence": {
                "commit": "9a28675",
                "summary": "Manual review contract, evidence requirements, publication gate, and manual-publish invariant added to issue drafts.",
            },
        },
        {
            "work_id": "autonomy_progress_memory",
            "priority": 4,
            "status": "closed_harnessed",
            "goal": "Keep the autonomous loop from repeating completed work by recording closed items, next candidates, and evidence.",
            "allowed_files": [
                "unibot/autonomous_research_loop.py",
                "tests/test_unibot_autonomous_research_loop.py",
                "docs/unibot/UNIBOT_GRETEL_AUTONOMOUS_RESEARCH_LOOP.md",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_autonomous_research_loop.py -q"],
            "review_gate": "progress_memory_public_safe",
            "closure_evidence": {
                "commit": "5d16846",
                "summary": "Closed completed queue items, added explicit progress evidence, and exposed next recommended work.",
            },
        },
        {
            "work_id": "readiness_perf_guard",
            "priority": 5,
            "status": "closed_harnessed",
            "goal": "Add a lightweight readiness performance note or guard so recurring low-budget runs avoid accidentally expensive full-suite paths.",
            "allowed_files": ["unibot/readiness.py", "tests/test_unibot_readiness.py", "docs/unibot/UNIBOT_READINESS_CHECK.md"],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_readiness.py -q"],
            "review_gate": "reasonable_token_and_runtime_budget",
            "closure_evidence": {
                "commit": "c6581a3",
                "summary": "Readiness runtime guard added for focused recurring checks, low reasoning effort, and escalated full-suite/provider work.",
            },
        },
        {
            "work_id": "source_card_drift_guard",
            "priority": 6,
            "status": "closed_harnessed",
            "goal": "Keep source-card coverage and readiness evidence aligned so scientific claims stay source-bound as the project grows.",
            "allowed_files": [
                "unibot/source_cards.py",
                "unibot/readiness.py",
                "tests/test_unibot_readiness.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_readiness.py -q"],
            "review_gate": "source_bound_public_science",
            "closure_evidence": {
                "commit": "afeb0d5",
                "summary": "Source-card drift report, API route, readiness gate, stale-source harness, and public docs added.",
            },
        },
        {
            "work_id": "bachelor_thesis_evidence_index",
            "priority": 7,
            "status": "closed_harnessed",
            "goal": "Keep the Gretel-authored bachelor-thesis package aligned with readiness evidence, source cards, tests, and human review gates.",
            "allowed_files": [
                "unibot/bachelor_thesis.py",
                "tests/test_unibot_bachelor_thesis.py",
                "docs/unibot/UNIBOT_GRETEL_BACHELOR_THESIS_PACKAGE.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_bachelor_thesis.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "thesis_claims_source_bound_and_human_gated",
            "closure_evidence": {
                "commit": "400fc92",
                "summary": "Bachelor-thesis evidence index added with claim-to-test/readiness/source-card/human-gate mapping.",
            },
        },
        {
            "work_id": "readiness_evidence_snapshot",
            "priority": 8,
            "status": "closed_harnessed",
            "goal": "Create a compact public-safe readiness evidence snapshot so recurring Gretel runs can compare scientific gate coverage over time.",
            "allowed_files": [
                "unibot/readiness.py",
                "tests/test_unibot_readiness.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_readiness.py -q"],
            "review_gate": "public_safe_reproducible_readiness_evidence",
            "closure_evidence": {
                "commit": "19d6f8c",
                "summary": "Readiness evidence snapshot added with stable hash, scientific gate coverage, compact public-safe summary, docs, and tests.",
            },
        },
        {
            "work_id": "review_board_evidence_alignment",
            "priority": 9,
            "status": "closed_harnessed",
            "goal": "Align review-board packets with readiness evidence snapshots and thesis claims so human reviewers can audit gates quickly.",
            "allowed_files": [
                "unibot/review_board.py",
                "tests/test_unibot_review_board.py",
                "docs/unibot/UNIBOT_REVIEW_BOARD_PACKET.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_review_board.py tests/test_unibot_readiness.py -q"],
            "review_gate": "human_review_evidence_traceability",
            "closure_evidence": {
                "commit": "f449f88",
                "summary": "Review-board evidence alignment added with reviewer-to-thesis-claim, readiness-gate, source-card, and human-gate mapping.",
            },
        },
        {
            "work_id": "feedback_issue_evidence_traceability",
            "priority": 10,
            "status": "closed_harnessed",
            "goal": "Align feedback triage and GitHub issue packets with readiness evidence so public reviewer follow-up remains traceable and manual.",
            "allowed_files": [
                "unibot/github_issues.py",
                "unibot/triage.py",
                "tests/test_unibot_github_issues.py",
                "docs/unibot/UNIBOT_GITHUB_ISSUE_BUNDLE.md",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_github_issues.py tests/test_unibot_publication.py -q"],
            "review_gate": "manual_public_feedback_traceability",
            "closure_evidence": {
                "commit": "99d36ff",
                "summary": "Feedback-derived GitHub issues now carry readiness-gate, source-card, human-gate, and evidence-snapshot traceability.",
            },
        },
        {
            "work_id": "release_runbook_evidence_alignment",
            "priority": 11,
            "status": "ready",
            "goal": "Align release runbook evidence with readiness snapshots, review-board gates, and manual-publication boundaries.",
            "allowed_files": [
                "unibot/release_runbook.py",
                "tests/test_unibot_release_runbook.py",
                "docs/unibot/UNIBOT_RELEASE_RUNBOOK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_release_runbook.py tests/test_unibot_readiness.py -q"],
            "review_gate": "manual_release_evidence_traceability",
        },
    ]


def build_autonomous_research_loop() -> dict[str, Any]:
    intent = build_unibot_intent_contract()
    budget = build_autonomy_budget_policy()
    queue = build_autonomous_work_queue()
    payload = {
        "schema_version": AUTONOMY_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ready_for_budgeted_recurring_local_runs",
        "intent_contract": intent,
        "budget_policy": budget,
        "work_queue": queue,
        "run_protocol": [
            "Start with git status and public-safety/readiness state.",
            "Select at most one ready or candidate work item.",
            "Inspect relevant files before editing.",
            "Make the smallest public-safe improvement that advances the intent.",
            "Add or update a focused test or documentation gate.",
            "Run focused tests, public-safety scan, readiness, and any affected smoke.",
            "Commit locally only when green; do not push automatically.",
            "Leave a concise review note with changed files, checks, risks, and next work item.",
        ],
        "completion_policy": (
            "The loop is never considered complete merely because one run passes. It remains an ongoing "
            "research-maintenance lane until a human retires or replaces it."
        ),
        "next_recommended_work_id": next(
            (item["work_id"] for item in queue if item["status"] == "ready"),
            next((item["work_id"] for item in queue if item["status"] == "candidate"), ""),
        ),
        "safety": {
            "raw_private_context_shared": False,
            "provider_call_executed": False,
            "autonomous_github_push": False,
            "mail_calendar_chat_actions": False,
            "final_go": False,
        },
    }
    payload["receipt"] = build_autonomous_loop_receipt(payload)
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "unibot-gretel-autonomous-research-loop")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
    return payload


def build_autonomous_loop_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    hashed = {key: value for key, value in payload.items() if key not in {"generated_at_utc", "receipt"}}
    digest = hashlib.sha256(json.dumps(hashed, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "schema_version": "unibot-gretel-autonomous-research-loop-receipt-v1",
        "loop_hash": digest,
        "owner": payload["intent_contract"]["owner"],
        "ready_work_items": len([item for item in payload["work_queue"] if item["status"] == "ready"]),
        "candidate_work_items": len([item for item in payload["work_queue"] if item["status"] == "candidate"]),
        "closed_harnessed_work_items": len([item for item in payload["work_queue"] if item["status"] == "closed_harnessed"]),
        "next_recommended_work_id": payload.get("next_recommended_work_id", ""),
        "provider_call_executed": False,
        "autonomous_github_push": False,
        "human_review_required_for_publication": True,
    }


def build_autonomous_research_markdown() -> str:
    loop = build_autonomous_research_loop()
    intent_lines = "\n".join(
        f"- `{item['intent_id']}`: {item['must_do']} Blocked: {item['must_not']}"
        for item in loop["intent_contract"]["product_intents"]
    )
    standard_lines = "\n".join(f"- {item}" for item in loop["intent_contract"]["always_use_standards"])
    queue_lines = "\n".join(
        f"- `{item['work_id']}` ({item['status']}): {item['goal']}" for item in loop["work_queue"]
    )
    closure_lines = "\n".join(
        f"- `{item['work_id']}`: {item.get('closure_evidence', {}).get('commit', 'n/a')} - {item.get('closure_evidence', {}).get('summary', '')}"
        for item in loop["work_queue"]
        if item["status"] == "closed_harnessed"
    )
    blocked_lines = "\n".join(f"- {item}" for item in loop["budget_policy"]["blocked_autonomous_actions"])
    return (
        f"# {AUTONOMY_MARKDOWN_TITLE}\n\n"
        f"Status: {loop['status']}\n\n"
        f"Public safety: {loop['public_safety_status']}\n\n"
        "## North Star\n\n"
        f"{loop['intent_contract']['north_star']}\n\n"
        "## Product Intents\n\n"
        f"{intent_lines}\n\n"
        "## Always-Use Standards\n\n"
        f"{standard_lines}\n\n"
        "## Budget Policy\n\n"
        f"- Cadence: {loop['budget_policy']['cadence']['recommended_cron']}\n"
        f"- Default reasoning effort: {loop['budget_policy']['token_policy']['default_reasoning_effort']}\n"
        f"- Max active work item per run: {loop['budget_policy']['cadence']['max_active_work_item_per_run']}\n\n"
        "## Blocked Autonomous Actions\n\n"
        f"{blocked_lines}\n\n"
        "## Work Queue\n\n"
        f"{queue_lines}\n\n"
        "## Closed Harnessed Work\n\n"
        f"{closure_lines or '- none'}\n\n"
        "## Receipt\n\n"
        f"- Loop hash: {loop['receipt']['loop_hash']}\n"
        f"- Ready items: {loop['receipt']['ready_work_items']}\n"
        f"- Candidate items: {loop['receipt']['candidate_work_items']}\n"
        f"- Closed harnessed items: {loop['receipt']['closed_harnessed_work_items']}\n"
        f"- Next recommended work: {loop['receipt']['next_recommended_work_id']}\n"
        f"- Autonomous GitHub push: {loop['receipt']['autonomous_github_push']}\n"
    )
