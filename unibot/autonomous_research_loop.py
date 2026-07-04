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
            "status": "closed_harnessed",
            "goal": "Align release runbook evidence with readiness snapshots, review-board gates, and manual-publication boundaries.",
            "allowed_files": [
                "unibot/release_runbook.py",
                "tests/test_unibot_release_runbook.py",
                "docs/unibot/UNIBOT_RELEASE_RUNBOOK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_release_runbook.py tests/test_unibot_readiness.py -q"],
            "review_gate": "manual_release_evidence_traceability",
            "closure_evidence": {
                "commit": "be671ff",
                "summary": "Release runbook evidence alignment added with readiness snapshot, review-board, GitHub issue, source-card, and human-gate contracts.",
            },
        },
        {
            "work_id": "compliance_drift_evidence_alignment",
            "priority": 12,
            "status": "closed_harnessed",
            "goal": "Keep compliance matrix requirements aligned with source-card drift, readiness evidence, and human authority gates.",
            "allowed_files": [
                "unibot/compliance.py",
                "tests/test_unibot_compliance.py",
                "docs/unibot/UNIBOT_COMPLIANCE_MATRIX.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_compliance.py tests/test_unibot_readiness.py -q"],
            "review_gate": "compliance_source_bound_human_gated",
            "closure_evidence": {
                "commit": "92cb2f1",
                "summary": "Compliance drift alignment added with requirement-to-readiness, source-card, human-gate, and readiness-protection mapping.",
            },
        },
        {
            "work_id": "pilot_protocol_evidence_alignment",
            "priority": 13,
            "status": "closed_harnessed",
            "goal": "Align pilot protocol consent, ethics, data, and readiness evidence with source cards and human review gates.",
            "allowed_files": [
                "unibot/pilot.py",
                "tests/test_unibot_pilot.py",
                "docs/unibot/UNIBOT_PILOT_PROTOCOL.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_pilot.py tests/test_unibot_readiness.py -q"],
            "review_gate": "pilot_ethics_data_human_review_traceability",
            "closure_evidence": {
                "commit": "30a81a8",
                "summary": "Pilot evidence alignment added with consent, ethics, data, session-flow, release-boundary, source-card, readiness, and human-gate mapping.",
            },
        },
        {
            "work_id": "data_protection_evidence_alignment",
            "priority": 14,
            "status": "closed_harnessed",
            "goal": "Align data-protection screening with pilot records, retention, access, source cards, and human review gates.",
            "allowed_files": [
                "unibot/privacy.py",
                "tests/test_unibot_privacy.py",
                "docs/unibot/UNIBOT_DATA_PROTECTION_SCREENING.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_privacy.py tests/test_unibot_readiness.py -q"],
            "review_gate": "datenschutz_pilot_records_human_review_traceability",
            "closure_evidence": {
                "commit": "4b5fbbc",
                "summary": "Data-protection evidence alignment added with processing principles, pilot records, retention, public-boundary, exam-boundary, source-card, risk, readiness, and human-gate mapping.",
            },
        },
        {
            "work_id": "glm_provider_redaction_evidence_alignment",
            "priority": 15,
            "status": "closed_harnessed",
            "goal": "Align the GLM proposal lane with redaction receipts, provider-call locks, source cards, and human review gates.",
            "allowed_files": [
                "unibot/gretel_glm_evolve.py",
                "tests/test_unibot_gretel_glm_evolve.py",
                "docs/unibot/UNIBOT_GRETEL_GLM_EVOLVE_LANE.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_gretel_glm_evolve.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "glm_redacted_proposal_provider_lock_human_review_traceability",
            "closure_evidence": {
                "commit": "a41b060",
                "summary": "GLM provider redaction alignment added with source-basis, redaction-receipt, provider-lock, proposal-validation, apply/publish/Final-Go, readiness, and human-gate mapping.",
            },
        },
        {
            "work_id": "open_science_reproducibility_release_alignment",
            "priority": 16,
            "status": "closed_harnessed",
            "goal": "Align publication, open-science roadmap, reproducibility evidence, release gates, and bachelor-thesis claims.",
            "allowed_files": [
                "unibot/publication.py",
                "tests/test_unibot_publication.py",
                "docs/unibot/UNIBOT_PUBLICATION_PACKAGE.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_publication.py tests/test_unibot_readiness.py -q"],
            "review_gate": "open_science_reproducibility_release_human_review_traceability",
            "closure_evidence": {
                "commit": "ecfa4f8",
                "summary": "Publication reproducibility alignment added with public reproduction, manual release, authority/compliance, Gretel/GLM thesis, autonomy, release-gate, source-card, and human-gate mapping.",
            },
        },
        {
            "work_id": "course_material_public_boundary_alignment",
            "priority": 17,
            "status": "closed_harnessed",
            "goal": "Align course-material public summaries, private-source exclusions, adaptive task demos, and readiness gates.",
            "allowed_files": [
                "unibot/materials.py",
                "tests/test_unibot_materials.py",
                "docs/unibot/UNIBOT_COURSE_MATERIALS.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_materials.py tests/test_unibot_readiness.py -q"],
            "review_gate": "course_material_public_private_boundary_traceability",
            "closure_evidence": {
                "commit": "ca9c426",
                "summary": "Course-material public boundary alignment added with public/private material contracts, source cards, readiness gates, and human gates.",
            },
        },
        {
            "work_id": "adaptive_task_source_boundary_alignment",
            "priority": 18,
            "status": "closed_harnessed",
            "goal": "Align adaptive practice plans with public material summaries, source boundaries, learner-agency evidence, and readiness gates.",
            "allowed_files": [
                "unibot/adaptive_tasks.py",
                "tests/test_unibot_adaptive_tasks.py",
                "docs/unibot/UNIBOT_ADAPTIVE_TASKS.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_adaptive_tasks.py tests/test_unibot_readiness.py -q"],
            "review_gate": "adaptive_tasks_public_material_source_boundary_traceability",
            "closure_evidence": {
                "commit": "00bc10e",
                "summary": "Adaptive task source-boundary alignment added with public-summary source contracts, learner-agency checks, readiness gates, and public-summary excerpt hardening.",
            },
        },
        {
            "work_id": "evaluation_learner_agency_boundary_alignment",
            "priority": 19,
            "status": "closed_harnessed",
            "goal": "Align evaluation packets with adaptive learner-agency evidence, source boundaries, source cards, and readiness gates.",
            "allowed_files": [
                "unibot/evaluation.py",
                "tests/test_unibot_evaluation.py",
                "docs/unibot/UNIBOT_DEMO_TEST_PLAN.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_evaluation.py tests/test_unibot_readiness.py -q"],
            "review_gate": "evaluation_learner_agency_source_boundary_traceability",
            "closure_evidence": {
                "commit": "7c04e0d",
                "summary": "Evaluation learner-agency boundary alignment added with adaptive trace, rubric, measurement-exclusion, source-card, readiness, and human-gate contracts.",
            },
        },
        {
            "work_id": "bachelor_thesis_evaluation_claim_alignment",
            "priority": 20,
            "status": "closed_harnessed",
            "goal": "Align the Gretel-authored bachelor-thesis package with evaluation learner-agency evidence, adaptive task boundaries, source cards, and readiness gates.",
            "allowed_files": [
                "unibot/bachelor_thesis.py",
                "tests/test_unibot_bachelor_thesis.py",
                "docs/unibot/UNIBOT_GRETEL_BACHELOR_THESIS_PACKAGE.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_bachelor_thesis.py tests/test_unibot_readiness.py -q"],
            "review_gate": "bachelor_thesis_evaluation_claim_traceability",
            "closure_evidence": {
                "commit": "5fcdbfe",
                "summary": "Bachelor-thesis evaluation claim alignment added with learner-agency, adaptive boundary, source-card, high-stakes exclusion, readiness, and human-gate traceability.",
            },
        },
        {
            "work_id": "review_board_thesis_evaluation_claim_alignment",
            "priority": 21,
            "status": "closed_harnessed",
            "goal": "Align review-board packets with bachelor-thesis evaluation claims, learner-agency evidence, source cards, and human gates.",
            "allowed_files": [
                "unibot/review_board.py",
                "tests/test_unibot_review_board.py",
                "docs/unibot/UNIBOT_REVIEW_BOARD_PACKET.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_review_board.py tests/test_unibot_readiness.py -q"],
            "review_gate": "review_board_thesis_evaluation_claim_traceability",
            "closure_evidence": {
                "commit": "20a66a0",
                "summary": "Review-board thesis evaluation claim alignment added with learner-agency reviewer mapping, high-stakes red lines, source-card, readiness, and human-gate contracts.",
            },
        },
        {
            "work_id": "release_runbook_review_board_claim_alignment",
            "priority": 22,
            "status": "closed_harnessed",
            "goal": "Align release runbook review steps with review-board thesis evaluation claims, public language controls, source cards, and human gates.",
            "allowed_files": [
                "unibot/release_runbook.py",
                "tests/test_unibot_release_runbook.py",
                "docs/unibot/UNIBOT_RELEASE_RUNBOOK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_release_runbook.py tests/test_unibot_readiness.py -q"],
            "review_gate": "release_runbook_review_board_thesis_claim_traceability",
            "closure_evidence": {
                "commit": "77f5b61",
                "summary": "Release runbook review-board thesis/evaluation claim contract added with adaptive/evaluation/readiness links, public-language controls, and human gates.",
            },
        },
        {
            "work_id": "compliance_release_review_board_claim_alignment",
            "priority": 23,
            "status": "closed_harnessed",
            "goal": "Align compliance requirements with release-runbook review-board thesis/evaluation claims, public language controls, source cards, and human gates.",
            "allowed_files": [
                "unibot/compliance.py",
                "tests/test_unibot_compliance.py",
                "docs/unibot/UNIBOT_COMPLIANCE_MATRIX.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_compliance.py tests/test_unibot_readiness.py -q"],
            "review_gate": "compliance_release_review_board_thesis_claim_traceability",
            "closure_evidence": {
                "commit": "6170a9a",
                "summary": "Compliance release-review-board claim contract added with release-runbook, review-board thesis/evaluation, readiness, and human-gate checks.",
            },
        },
        {
            "work_id": "pilot_release_review_board_claim_alignment",
            "priority": 24,
            "status": "closed_harnessed",
            "goal": "Align pilot protocol evidence with release-runbook review-board thesis/evaluation claims, participant safety, public language controls, and human gates.",
            "allowed_files": [
                "unibot/pilot.py",
                "tests/test_unibot_pilot.py",
                "docs/unibot/UNIBOT_PILOT_PROTOCOL.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_pilot.py tests/test_unibot_readiness.py -q"],
            "review_gate": "pilot_release_review_board_thesis_claim_traceability",
            "closure_evidence": {
                "commit": "582c574",
                "summary": "Pilot release-review-board claim contract added with synthetic learner-agency boundaries, adaptive evidence, readiness links, and human gates.",
            },
        },
        {
            "work_id": "data_protection_release_review_board_claim_alignment",
            "priority": 25,
            "status": "closed_harnessed",
            "goal": "Align data-protection screening with pilot release-review-board thesis/evaluation claims, processing boundaries, public language controls, and human gates.",
            "allowed_files": [
                "unibot/privacy.py",
                "tests/test_unibot_privacy.py",
                "docs/unibot/UNIBOT_DATA_PROTECTION_SCREENING.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_privacy.py tests/test_unibot_readiness.py -q"],
            "review_gate": "data_protection_release_review_board_thesis_claim_traceability",
            "closure_evidence": {
                "commit": "447a37e",
                "summary": "Data-protection release-review-board claim contract added with pilot/release/review-board thesis/evaluation readiness links, processing boundaries, and human gates.",
            },
        },
        {
            "work_id": "publication_release_review_board_claim_alignment",
            "priority": 26,
            "status": "closed_harnessed",
            "goal": "Align publication package evidence with pilot, data-protection, release-runbook, and review-board thesis/evaluation claims before public release review.",
            "allowed_files": [
                "unibot/publication.py",
                "tests/test_unibot_publication.py",
                "docs/unibot/UNIBOT_PUBLICATION_PACKAGE.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_publication.py tests/test_unibot_readiness.py -q"],
            "review_gate": "publication_release_review_board_thesis_claim_traceability",
            "closure_evidence": {
                "commit": "d794a40",
                "summary": "Publication release-review-board claim contract and trace added with pilot/data-protection/release/review-board thesis/evaluation links, public release boundaries, and human gates.",
            },
        },
        {
            "work_id": "github_issue_release_review_board_claim_alignment",
            "priority": 27,
            "status": "closed_harnessed",
            "goal": "Align GitHub issue bundle drafts with publication release-review-board thesis/evaluation claims, manual publication controls, public language, and human gates.",
            "allowed_files": [
                "unibot/github_issues.py",
                "tests/test_unibot_github_issues.py",
                "docs/unibot/UNIBOT_GITHUB_ISSUE_BUNDLE.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_github_issues.py tests/test_unibot_readiness.py -q"],
            "review_gate": "github_issue_release_review_board_thesis_claim_traceability",
            "closure_evidence": {
                "commit": "16dcbb3",
                "summary": "GitHub issue bundle claim contract added with publication/release/review-board thesis/evaluation links, manual issue publication controls, public language boundaries, and human gates.",
            },
        },
        {
            "work_id": "feedback_triage_release_review_board_claim_alignment",
            "priority": 28,
            "status": "closed_harnessed",
            "goal": "Align feedback triage records with GitHub issue, publication, release-review-board thesis/evaluation claims, public language controls, and human gates.",
            "allowed_files": [
                "unibot/triage.py",
                "tests/test_unibot_triage.py",
                "docs/unibot/UNIBOT_FEEDBACK_TRIAGE.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_triage.py tests/test_unibot_readiness.py -q"],
            "review_gate": "feedback_triage_release_review_board_thesis_claim_traceability",
            "closure_evidence": {
                "commit": "c74e157",
                "summary": "Feedback triage claim alignment added with downstream GitHub issue, publication, release-runbook, review-board, readiness, and human-gate links.",
            },
        },
        {
            "work_id": "demo_feedback_release_review_board_claim_alignment",
            "priority": 29,
            "status": "closed_harnessed",
            "goal": "Align validated demo feedback records with feedback triage, GitHub issue, publication, release-review-board thesis/evaluation claims, public language controls, and human gates.",
            "allowed_files": [
                "unibot/feedback.py",
                "tests/test_unibot_feedback.py",
                "docs/unibot/UNIBOT_DEMO_FEEDBACK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_feedback.py tests/test_unibot_readiness.py -q"],
            "review_gate": "demo_feedback_release_review_board_thesis_claim_traceability",
            "closure_evidence": {
                "commit": "9940ac7",
                "summary": "Demo feedback claim alignment added with local-only/public-summary-only boundaries, downstream triage/issue/publication/review-board readiness links, and human gates.",
            },
        },
        {
            "work_id": "local_demo_release_review_board_claim_alignment",
            "priority": 30,
            "status": "closed_harnessed",
            "goal": "Align local demo run scenarios with demo feedback, triage, GitHub issue, publication, release-review-board thesis/evaluation claims, public language controls, and human gates.",
            "allowed_files": [
                "unibot/demo.py",
                "tests/test_unibot_demo.py",
                "docs/unibot/UNIBOT_DEMO_TEST_PLAN.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_demo.py tests/test_unibot_readiness.py -q"],
            "review_gate": "local_demo_release_review_board_thesis_claim_traceability",
            "closure_evidence": {
                "commit": "4cd091d",
                "summary": "Local demo run claim alignment added with practice-only/local-only/public-summary boundaries, downstream demo-feedback/triage/issue/publication/review-board readiness links, and human gates.",
            },
        },
        {
            "work_id": "browser_extension_release_review_board_claim_alignment",
            "priority": 31,
            "status": "closed_harnessed",
            "goal": "Align the browser extension and sidepanel demo handoff with local demo, feedback, triage, GitHub issue, publication, release-review-board thesis/evaluation claims, public language controls, and human gates.",
            "allowed_files": [
                "unibot/browser_extension/sidepanel.js",
                "tests/test_unibot_browser_extension.py",
                "docs/unibot/UNIBOT_DEMO_TEST_PLAN.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_browser_extension.py tests/test_unibot_readiness.py -q"],
            "review_gate": "browser_extension_release_review_board_thesis_claim_traceability",
            "closure_evidence": {
                "commit": "3db6902",
                "summary": "Browser sidepanel release-review-board claim alignment added with local demo, demo feedback, triage, GitHub issue, readiness, and human-gate links.",
            },
        },
        {
            "work_id": "browser_manifest_content_boundary_claim_alignment",
            "priority": 32,
            "status": "closed_harnessed",
            "goal": "Align the browser extension manifest and content-script boundary with sidepanel handoff, local demo, publication, release-review-board claims, public language controls, and human gates.",
            "allowed_files": [
                "unibot/browser_extension/manifest.json",
                "unibot/browser_extension/content.js",
                "tests/test_unibot_browser_extension.py",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_browser_extension.py tests/test_unibot_readiness.py -q"],
            "review_gate": "browser_manifest_content_boundary_claim_traceability",
            "closure_evidence": {
                "commit": "1032d84",
                "summary": "Browser manifest and content-script boundary claim alignment added with bounded permissions, sidepanel/local-demo links, human gates, and no exam-security claims.",
            },
        },
        {
            "work_id": "notebook_handoff_release_review_board_claim_alignment",
            "priority": 33,
            "status": "closed_harnessed",
            "goal": "Align the notebook handoff with browser demo, local demo, feedback, publication, release-review-board claims, public language controls, and human gates.",
            "allowed_files": [
                "unibot/notebooks.py",
                "tests/test_unibot_notebooks.py",
                "docs/unibot/UNIBOT_DEMO_TEST_PLAN.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_notebooks.py tests/test_unibot_readiness.py -q"],
            "review_gate": "notebook_handoff_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "74c074a",
                "summary": "Notebook handoff claim alignment added with browser, manifest, local-demo, feedback, publication, review-board, readiness, and human-gate links.",
            },
        },
        {
            "work_id": "redteam_release_review_board_claim_alignment",
            "priority": 34,
            "status": "closed_harnessed",
            "goal": "Align red-team smoke evidence with notebook, browser, local demo, publication, release-review-board claims, public language controls, and human gates.",
            "allowed_files": [
                "unibot/redteam.py",
                "tests/test_unibot_redteam.py",
                "docs/unibot/UNIBOT_DEMO_TEST_PLAN.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_redteam.py tests/test_unibot_readiness.py -q"],
            "review_gate": "redteam_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "639a2cb",
                "summary": "Red-team smoke claim alignment added with hash/category evidence, notebook, browser, local-demo, publication, review-board, readiness, and human-gate links.",
            },
        },
        {
            "work_id": "source_card_release_review_board_claim_alignment",
            "priority": 35,
            "status": "closed_harnessed",
            "goal": "Align source-card evidence with red-team, notebook, publication, release-review-board claims, public language controls, and human gates.",
            "allowed_files": [
                "unibot/source_cards.py",
                "tests/test_unibot_source_cards.py",
                "docs/unibot/UNIBOT_SOURCE_CARDS.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_source_cards.py tests/test_unibot_readiness.py -q"],
            "review_gate": "source_card_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "bda02d3",
                "summary": "Source-card claim alignment added with drift checks, public-link-only source rules, red-team, notebook, publication, review-board, readiness, and human-gate links.",
            },
        },
        {
            "work_id": "threat_model_release_review_board_claim_alignment",
            "priority": 36,
            "status": "closed_harnessed",
            "goal": "Align the threat model with source cards, red-team evidence, publication, release-review-board claims, public language controls, and human gates.",
            "allowed_files": [
                "docs/unibot/UNIBOT_THREAT_MODEL.md",
                "unibot/redteam.py",
                "tests/test_unibot_redteam.py",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_redteam.py tests/test_unibot_readiness.py -q"],
            "review_gate": "threat_model_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "fb2c4e9",
                "summary": "Threat-model claim alignment added with source-card, red-team, publication, release-runbook, review-board, readiness, and human-gate links.",
            },
        },
        {
            "work_id": "review_board_packet_release_claim_summary_alignment",
            "priority": 37,
            "status": "closed_harnessed",
            "goal": "Align review-board packet summaries with source cards, threat model, red-team, publication, public language controls, and human gates.",
            "allowed_files": [
                "unibot/review_board.py",
                "tests/test_unibot_review_board.py",
                "docs/unibot/UNIBOT_REVIEW_BOARD_PACKET.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_review_board.py tests/test_unibot_readiness.py -q"],
            "review_gate": "review_board_packet_release_claim_summary_traceability",
            "closure_evidence": {
                "commit": "bf2c654",
                "summary": "Review-board release-claim summaries aligned with source cards, threat model, red-team, publication, public language controls, and human gates.",
            },
        },
        {
            "work_id": "authority_handoff_release_review_board_claim_alignment",
            "priority": 38,
            "status": "closed_harnessed",
            "goal": "Align authority handoff drafts with review-board summaries, source cards, red-team, compliance, public language controls, provider gates, and human gates.",
            "allowed_files": [
                "unibot/handoff.py",
                "tests/test_unibot_handoff.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_handoff.py tests/test_unibot_readiness.py -q"],
            "review_gate": "authority_handoff_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "5867d66",
                "summary": "Authority handoff release-claim alignment added with review-board, source-card, red-team, compliance, public language, provider-gate, and human-gate links.",
            },
        },
        {
            "work_id": "stakeholder_submission_release_review_board_claim_alignment",
            "priority": 39,
            "status": "closed_harnessed",
            "goal": "Align stakeholder submission bundle lanes with review-board summaries, authority handoff, source cards, extraction/privacy decisions, public language controls, and human gates.",
            "allowed_files": [
                "unibot/submission.py",
                "tests/test_unibot_submission.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_submission.py tests/test_unibot_readiness.py -q"],
            "review_gate": "stakeholder_submission_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "408debe",
                "summary": "Stakeholder submission release-claim alignment added with review-board, authority-handoff, source-card, privacy/extraction, public language, and human-gate links.",
            },
        },
        {
            "work_id": "stakeholder_decision_request_release_review_board_claim_alignment",
            "priority": 40,
            "status": "closed_harnessed",
            "goal": "Align single-lane stakeholder decision requests with submission-bundle evidence, receipt boundaries, review-board summaries, public language controls, and human gates.",
            "allowed_files": [
                "unibot/decision_request.py",
                "tests/test_unibot_decision_request.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_decision_request.py tests/test_unibot_readiness.py -q"],
            "review_gate": "stakeholder_decision_request_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "99060f6",
                "summary": "Stakeholder decision request release-claim alignment added with submission-bundle, receipt-boundary, review-board, Datenschutz, public-safety, and human-gate links.",
            },
        },
        {
            "work_id": "stakeholder_decision_journal_release_review_board_claim_alignment",
            "priority": 41,
            "status": "closed_harnessed",
            "goal": "Align stakeholder decision journals with decision-request receipts, hash-only references, submission-bundle evidence, public language controls, and human gates.",
            "allowed_files": [
                "unibot/decision_journal.py",
                "tests/test_unibot_decision_journal.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_decision_journal.py tests/test_unibot_readiness.py -q"],
            "review_gate": "stakeholder_decision_journal_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "a6052b7",
                "summary": "Stakeholder decision journal release-claim alignment added with hash-only records, request/receipt traceability, no raw decision storage, no tool-send, and human-gate links.",
            },
        },
        {
            "work_id": "external_decision_record_journal_release_review_board_claim_alignment",
            "priority": 42,
            "status": "closed_harnessed",
            "goal": "Align external decision record journals with validated decision records, hash-only references, no deployment switch, public language controls, and human gates.",
            "allowed_files": [
                "unibot/external_decision_journal.py",
                "tests/test_unibot_external_decision_journal.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_external_decision_journal.py tests/test_unibot_readiness.py -q"],
            "review_gate": "external_decision_record_journal_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "e785479",
                "summary": "External decision record journal release-claim alignment added with validated record hashes, no raw decision storage, no deployment switch, and human-gate links.",
            },
        },
        {
            "work_id": "external_decision_state_release_review_board_claim_alignment",
            "priority": 43,
            "status": "closed_harnessed",
            "goal": "Align external decision state derivation with validated records, no raw references, no silent deployment switch, public language controls, and human gates.",
            "allowed_files": [
                "unibot/decision_state.py",
                "tests/test_unibot_decision_state.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_decision_state.py tests/test_unibot_readiness.py -q"],
            "review_gate": "external_decision_state_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "05fb04e",
                "summary": "External decision state release-claim alignment added with validated record derivation, hash-only references, no silent deployment switch, and human-gate links.",
            },
        },
        {
            "work_id": "extraction_receipt_journal_release_review_board_claim_alignment",
            "priority": 44,
            "status": "closed_harnessed",
            "goal": "Align extraction receipt journals with hash-only receipt storage, local-only processing evidence, no tutor-manifest update by receipt alone, and human-review gates.",
            "allowed_files": [
                "unibot/extraction_receipt_journal.py",
                "tests/test_unibot_extraction_receipt_journal.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_extraction_receipt_journal.py tests/test_unibot_readiness.py -q"],
            "review_gate": "extraction_receipt_journal_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "51b537a",
                "summary": "Extraction receipt journal release-claim alignment added with hash-only receipt records, local-private evidence boundaries, human-review links, no manifest update by receipt alone, and high-stakes claim blocks.",
            },
        },
        {
            "work_id": "extraction_progress_release_review_board_claim_alignment",
            "priority": 45,
            "status": "closed_harnessed",
            "goal": "Align extraction progress reports with receipt metadata, review queues, manifest-update boundaries, no raw text or local paths, and no exam deployment claims.",
            "allowed_files": [
                "unibot/extraction_progress.py",
                "tests/test_unibot_extraction_progress.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_extraction_progress.py tests/test_unibot_readiness.py -q"],
            "review_gate": "extraction_progress_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "8562658",
                "summary": "Extraction progress release-claim alignment added with receipt metadata, hash-only review queues, private manifest-candidate boundaries, no raw text or local paths, and no exam deployment claims.",
            },
        },
        {
            "work_id": "extraction_manifest_update_release_review_board_claim_alignment",
            "priority": 46,
            "status": "closed_harnessed",
            "goal": "Align extraction manifest update plans with reviewed receipt candidates, private metadata-only apply boundaries, no file writes by planning, no public release, and no exam deployment claims.",
            "allowed_files": [
                "unibot/extraction_manifest_update.py",
                "tests/test_unibot_extraction_manifest_update.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_extraction_manifest_update.py tests/test_unibot_readiness.py -q"],
            "review_gate": "extraction_manifest_update_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "49d4fa2",
                "summary": "Extraction manifest update release-claim alignment added with reviewed receipt candidates, private metadata-only boundaries, no file writes by planning, no public release, and no exam deployment claims.",
            },
        },
        {
            "work_id": "extraction_manifest_apply_release_review_board_claim_alignment",
            "priority": 47,
            "status": "closed_harnessed",
            "goal": "Align private manifest apply dry-runs and confirmed private writes with operator confirmation, metadata-only outputs, local path suppression, no tutor indexing, and no exam deployment claims.",
            "allowed_files": [
                "unibot/extraction_manifest_apply.py",
                "tests/test_unibot_extraction_manifest_apply.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_extraction_manifest_apply.py tests/test_unibot_readiness.py -q"],
            "review_gate": "extraction_manifest_apply_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "fbda8fe",
                "summary": "Private manifest apply release-claim alignment added with dry-run/no-write proof, operator-confirmed private metadata writes, path/raw-text suppression, no tutor indexing, and no exam deployment claims.",
            },
        },
        {
            "work_id": "extraction_completion_release_review_board_claim_alignment",
            "priority": 48,
            "status": "ready",
            "goal": "Align extraction completion reports and deferrals with reviewed receipt coverage, intentional deferral evidence, no raw deferral text, no manifest updates, and no exam deployment claims.",
            "allowed_files": [
                "unibot/extraction_completion.py",
                "tests/test_unibot_extraction_completion.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_extraction_completion.py tests/test_unibot_readiness.py -q"],
            "review_gate": "extraction_completion_release_review_board_claim_traceability",
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
