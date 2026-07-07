from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .public_safety import scan_text


AUTONOMY_SCHEMA_VERSION = "unibot-gretel-autonomous-research-loop-v1"
AUTONOMY_MARKDOWN_TITLE = "UniBot Gretel Autonomous Research Loop"
AUTONOMOUS_LOOP_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-autonomous-research-loop-workspace-card-budget-alignment-v1"
)


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
            "status": "closed_harnessed",
            "goal": "Align extraction completion reports and deferrals with reviewed receipt coverage, intentional deferral evidence, no raw deferral text, no manifest updates, and no exam deployment claims.",
            "allowed_files": [
                "unibot/extraction_completion.py",
                "tests/test_unibot_extraction_completion.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_extraction_completion.py tests/test_unibot_readiness.py -q"],
            "review_gate": "extraction_completion_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "19f9bfe",
                "summary": "Extraction completion release-claim alignment added with reviewed receipt coverage, intentional deferral evidence, public-safety checks, no manifest update, and no exam deployment claims.",
            },
        },
        {
            "work_id": "extraction_human_review_release_review_board_claim_alignment",
            "priority": 49,
            "status": "closed_harnessed",
            "goal": "Align extraction human-review queues and decisions with completion evidence, private artifacts, source-card review, no raw text/public release, no tutor indexing by review alone, and no exam deployment claims.",
            "allowed_files": [
                "unibot/extraction_human_review.py",
                "tests/test_unibot_extraction_human_review.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_extraction_human_review.py tests/test_unibot_readiness.py -q"],
            "review_gate": "extraction_human_review_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "0cecaf4",
                "summary": "Extraction human-review release-claim alignment added with hash-only local review evidence, completion links, private manifest-plan boundaries, no tutor indexing by review alone, and no exam deployment claims.",
            },
        },
        {
            "work_id": "private_tutor_use_flow_release_review_board_claim_alignment",
            "priority": 50,
            "status": "closed_harnessed",
            "goal": "Align the private tutor-use flow with reviewed private manifest evidence, learner-agency boundaries, no public raw course text, no cloud processing, and no exam deployment claims.",
            "allowed_files": [
                "unibot/private_tutor_use_flow.py",
                "tests/test_unibot_private_tutor_use_flow.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_private_tutor_use_flow.py tests/test_unibot_readiness.py -q"],
            "review_gate": "private_tutor_use_flow_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "d850fa2",
                "summary": "Private tutor-use flow release-claim alignment added with reviewed private manifest evidence, operator-confirmed hash-only tutor index, A0-A2 learner-agency boundaries, Help-Ledger evidence, and no exam deployment claims.",
            },
        },
        {
            "work_id": "study_session_release_review_board_claim_alignment",
            "priority": 51,
            "status": "closed_harnessed",
            "goal": "Align study-session plans and receipts with learner reflection, source anchors, private tutor-use evidence, no final-answer outsourcing, no grading, and no exam deployment claims.",
            "allowed_files": [
                "unibot/study_session.py",
                "tests/test_unibot_study_session.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_study_session.py tests/test_unibot_readiness.py -q"],
            "review_gate": "study_session_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "934f817",
                "summary": "Study-session release-claim alignment added with hash-only learning receipts, source anchors, reflection evidence, A6 repeat-task enforcement, no Eigenleistung percentage claims, and no exam deployment claims.",
            },
        },
        {
            "work_id": "notebook_checkpoint_release_review_board_claim_alignment",
            "priority": 52,
            "status": "closed_harnessed",
            "goal": "Align notebook checkpoints with study-session receipts, source anchors, learner reflection, no raw code publication, no final-answer outsourcing, no grading, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_notebook_checkpoint.py",
                "tests/test_unibot_exam_notebook_checkpoint.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_exam_notebook_checkpoint.py tests/test_unibot_readiness.py -q"],
            "review_gate": "notebook_checkpoint_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "fb0b59e",
                "summary": "Notebook checkpoint release-claim alignment added with hash-only local cell evidence, operator-confirmed checkpoint journal writes, A6 repeat-task enforcement, raw-code suppression, and no exam deployment claims.",
            },
        },
        {
            "work_id": "exam_workspace_launch_release_review_board_claim_alignment",
            "priority": 53,
            "status": "closed_harnessed",
            "goal": "Align the exam-workspace launch flow with notebook checkpoints, study receipts, private tutor-use evidence, dry-run boundaries, no raw code publication, no grading, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_workspace_launch_flow.py",
                "tests/test_unibot_exam_workspace_launch_flow.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_exam_workspace_launch_flow.py tests/test_unibot_readiness.py -q"],
            "review_gate": "exam_workspace_launch_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "0a3d05f",
                "summary": "Exam-workspace launch release-claim alignment added with notebook checkpoint, private tutor-use, study receipt, dry-run, raw-code suppression, and no exam deployment claim checks.",
            },
        },
        {
            "work_id": "exam_workspace_run_release_review_board_claim_alignment",
            "priority": 54,
            "status": "closed_harnessed",
            "goal": "Align the controlled exam-workspace run packet with launch, checkpoint, study, tutor, dry-run/operator boundaries, no raw code publication, no grading, no proctoring, no KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_workspace_run.py",
                "tests/test_unibot_exam_workspace_run.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_exam_workspace_run.py tests/test_unibot_readiness.py -q"],
            "review_gate": "exam_workspace_run_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "c6a0dbf",
                "summary": "Exam-workspace run release-claim alignment added with controlled notebook-run evidence, private tutor sidecar, study receipt, Help-Ledger/exam-ledger links, export receipt, runtime isolation, and no exam deployment claims.",
            },
        },
        {
            "work_id": "exam_workspace_run_history_release_review_board_claim_alignment",
            "priority": 55,
            "status": "closed_harnessed",
            "goal": "Align exam-workspace run history and export review with run receipts, session-console hashes, operator confirmations, reflection evidence, no raw notebook/query publication, no grading, no proctoring, no KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_workspace_run_history.py",
                "tests/test_unibot_exam_workspace_run_history.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_exam_workspace_run_history.py tests/test_unibot_readiness.py -q"],
            "review_gate": "exam_workspace_run_history_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "2581243",
                "summary": "Exam-workspace run-history release-claim alignment added with hash-only session-console receipts, checkpoint hashes, operator blockers, reflection evidence, not-cleared export receipts, and no exam deployment claims.",
            },
        },
        {
            "work_id": "exam_workspace_operator_run_release_review_board_claim_alignment",
            "priority": 56,
            "status": "closed_harnessed",
            "goal": "Align the operator-facing Start Exam Workspace run receipt with launch/run/history evidence, individual operator confirmations, runtime isolation, no raw notebook/query publication, no grading, no proctoring, no KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_workspace_operator_run.py",
                "tests/test_unibot_exam_workspace_operator_run.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_exam_workspace_operator_run.py tests/test_unibot_readiness.py -q"],
            "review_gate": "exam_workspace_operator_run_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "b5fee21",
                "summary": "Exam-workspace operator-run release-claim alignment added with Start Exam Workspace view, dry-run default, individual confirmation boundaries, repeat-task stop, not-cleared receipt, and no exam deployment claims.",
            },
        },
        {
            "work_id": "exam_workspace_session_console_release_review_board_claim_alignment",
            "priority": 57,
            "status": "closed_harnessed",
            "goal": "Align the exam-workspace session console with operator-run receipts, run history, local-cycle workspace cards, reflection evidence, no raw notebook/query publication, no grading, no proctoring, no KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_workspace_session_console.py",
                "tests/test_unibot_exam_workspace_session_console.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_exam_workspace_session_console.py tests/test_unibot_readiness.py -q"],
            "review_gate": "exam_workspace_session_console_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "e5d013b",
                "summary": "Exam-workspace session-console release-claim alignment added with operator-run receipt, run-history context, workspace-card status, reflection evidence, hash-only checkpoint receipt, repeated dry-run boundary, and no exam deployment claims.",
            },
        },
        {
            "work_id": "python_exam_local_cycle_start_packet_release_review_board_claim_alignment",
            "priority": 58,
            "status": "closed_harnessed",
            "goal": "Align the Python exam local-cycle start packet with session console/operator-run evidence, safe-cycle gate, local workspace-card prerequisites, no raw notebook/query publication, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/python_exam_local_cycle_start_packet.py",
                "tests/test_unibot_python_exam_local_cycle_start_packet.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_python_exam_local_cycle_start_packet.py tests/test_unibot_readiness.py -q"],
            "review_gate": "python_exam_local_cycle_start_packet_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "72c555c",
                "summary": "Python exam local-cycle start-packet release-claim alignment added with safe-cycle, operator-gate, decision-receipt, source-card, task/checkpoint hash, open/confirmed confirmation, dry-run, and no exam deployment claims.",
            },
        },
        {
            "work_id": "python_exam_local_cycle_readiness_review_release_review_board_claim_alignment",
            "priority": 59,
            "status": "closed_harnessed",
            "goal": "Align the Python exam local-cycle readiness review with start-packet evidence, operator confirmations, source-card/hash metadata, no raw notebook/query publication, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/python_exam_local_cycle_readiness_review.py",
                "tests/test_unibot_python_exam_local_cycle_readiness_review.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_python_exam_local_cycle_readiness_review.py tests/test_unibot_readiness.py -q"],
            "review_gate": "python_exam_local_cycle_readiness_review_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "c0511e5",
                "summary": "Python exam local-cycle readiness-review release-claim alignment added with open-confirmation, fully-confirmed, and missing-packet review recommendations, hash/source-card evidence, read-only dry-run boundary, and no exam deployment claims.",
            },
        },
        {
            "work_id": "python_exam_local_cycle_readiness_handoff_release_review_board_claim_alignment",
            "priority": 60,
            "status": "closed_harnessed",
            "goal": "Align the Python exam local-cycle readiness handoff with readiness-review recommendations, start-packet hashes, source-card metadata, no raw notebook/query publication, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/python_exam_local_cycle_readiness_handoff.py",
                "tests/test_unibot_python_exam_local_cycle_readiness_handoff.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_python_exam_local_cycle_readiness_handoff.py tests/test_unibot_readiness.py -q"],
            "review_gate": "python_exam_local_cycle_readiness_handoff_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "31fc0c8",
                "summary": "Python exam local-cycle readiness-handoff release-claim alignment added with operator-run prefill, manual handoff, attention-state blocking, hash/source-card metadata, dry-run boundaries, and no exam deployment claims.",
            },
        },
        {
            "work_id": "python_exam_local_cycle_operator_workspace_card_release_review_board_claim_alignment",
            "priority": 61,
            "status": "closed_harnessed",
            "goal": "Align the Python exam local-cycle operator workspace card with readiness-review/handoff evidence, operator prefill metadata, source-card/hash metadata, no raw notebook/query publication, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/python_exam_local_cycle_operator_workspace_card.py",
                "tests/test_unibot_python_exam_local_cycle_operator_workspace_card.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_python_exam_local_cycle_operator_workspace_card.py tests/test_unibot_readiness.py -q"],
            "review_gate": "python_exam_local_cycle_operator_workspace_card_release_review_board_claim_traceability",
            "closure_evidence": {
                "commit": "87abb96",
                "summary": "Python exam local-cycle operator workspace-card release-claim alignment added with readiness-review/handoff evidence, operator prefill, Help-Ledger preview, attention-state blocking, hash/source-card metadata, dry-run boundaries, and no exam deployment claims.",
            },
        },
        {
            "work_id": "exam_workspace_session_console_local_cycle_workspace_card_readiness_link_alignment",
            "priority": 62,
            "status": "closed_harnessed",
            "goal": "Link the exam-workspace session console release alignment to the now-harnessed local-cycle operator workspace-card readiness gate, preserving receipt/hash-only evidence and no raw notebook/query, grading, proctoring, KI-detection, or exam deployment claims.",
            "allowed_files": [
                "unibot/exam_workspace_session_console.py",
                "tests/test_unibot_exam_workspace_session_console.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_exam_workspace_session_console.py tests/test_unibot_readiness.py -q"],
            "review_gate": "exam_workspace_session_console_local_cycle_workspace_card_readiness_link_traceability",
            "closure_evidence": {
                "commit": "4543a62",
                "summary": "Exam-workspace session-console release-claim alignment now links the harnessed local-cycle operator workspace-card readiness gate, preserves ready-for-prefill and Help-Ledger hash evidence, and keeps raw notebook/query, grading, proctoring, KI-detection, and exam deployment claims blocked.",
            },
        },
        {
            "work_id": "exam_workspace_run_history_local_cycle_workspace_card_review_link_alignment",
            "priority": 63,
            "status": "closed_harnessed",
            "goal": "Link exam-workspace run history/export review with the harnessed local-cycle operator workspace-card readiness gate, preserving session-console receipt hashes, workspace-card metadata, reflection evidence, no raw notebook/query publication, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_workspace_run_history.py",
                "tests/test_unibot_exam_workspace_run_history.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_exam_workspace_run_history.py tests/test_unibot_readiness.py -q"],
            "review_gate": "exam_workspace_run_history_local_cycle_workspace_card_review_link_traceability",
            "closure_evidence": {
                "commit": "99c0914",
                "summary": "Exam-workspace run-history/export-review release-claim alignment now links the harnessed local-cycle operator workspace-card readiness gate, preserves session-console receipt hashes, workspace-card ready/prefill and Help-Ledger hash metadata, reflection evidence, and no raw notebook/query, grading, proctoring, KI-detection, or exam deployment claims.",
            },
        },
        {
            "work_id": "exam_workspace_operator_run_local_cycle_workspace_card_start_view_link_alignment",
            "priority": 64,
            "status": "closed_harnessed",
            "goal": "Link exam-workspace operator-run Start Exam Workspace view with the harnessed local-cycle operator workspace-card readiness gate, preserving operator-confirmation boundaries, workspace-card metadata, receipt/hash-only evidence, no raw notebook/query publication, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_workspace_operator_run.py",
                "tests/test_unibot_exam_workspace_operator_run.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_exam_workspace_operator_run.py tests/test_unibot_readiness.py -q"],
            "review_gate": "exam_workspace_operator_run_local_cycle_workspace_card_start_view_link_traceability",
            "closure_evidence": {
                "commit": "1064cda",
                "summary": "Exam-workspace operator-run Start Exam Workspace view now links the harnessed local-cycle operator workspace-card readiness gate, preserves workspace-card ready/prefill and Help-Ledger hash metadata, keeps local writes individually confirmed, and blocks raw notebook/query, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "exam_workspace_launch_local_cycle_workspace_card_gate_link_alignment",
            "priority": 65,
            "status": "closed_harnessed",
            "goal": "Link exam-workspace launch dry-run evidence with the harnessed local-cycle operator workspace-card readiness gate, preserving launch/checkpoint/tutor/export metadata, workspace-card prefill evidence, no raw notebook/query publication, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_workspace_launch_flow.py",
                "tests/test_unibot_exam_workspace_launch_flow.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_exam_workspace_launch_flow.py tests/test_unibot_readiness.py -q"],
            "review_gate": "exam_workspace_launch_local_cycle_workspace_card_gate_link_traceability",
            "closure_evidence": {
                "commit": "d06c1b9",
                "summary": "Exam-workspace launch release-claim alignment now links the harnessed local-cycle operator workspace-card readiness gate, preserves launch/checkpoint/tutor/export metadata plus workspace-card prefill and Help-Ledger hash evidence, and blocks raw notebook/query, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "exam_workspace_run_local_cycle_workspace_card_execution_link_alignment",
            "priority": 66,
            "status": "closed_harnessed",
            "goal": "Link exam-workspace run dry-run evidence with the harnessed local-cycle operator workspace-card readiness gate, preserving tutor sidecar, study receipt, notebook checkpoint, export metadata, workspace-card prefill evidence, no raw notebook/query publication, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_workspace_run.py",
                "tests/test_unibot_exam_workspace_run.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_exam_workspace_run.py tests/test_unibot_readiness.py -q"],
            "review_gate": "exam_workspace_run_local_cycle_workspace_card_execution_link_traceability",
            "closure_evidence": {
                "commit": "20eb12b",
                "summary": "Exam-workspace run release-claim alignment now links the harnessed local-cycle operator workspace-card readiness gate, preserves tutor sidecar, study receipt, notebook checkpoint, export metadata, workspace-card prefill and Help-Ledger hash evidence, and blocks raw notebook/query, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "notebook_checkpoint_local_cycle_workspace_card_checkpoint_link_alignment",
            "priority": 67,
            "status": "closed_harnessed",
            "goal": "Link notebook-checkpoint hash-only local cell evidence with the harnessed local-cycle operator workspace-card readiness gate, preserving checkpoint hashes, study receipt metadata, workspace-card prefill evidence, no raw cell/notebook/query publication, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_notebook_checkpoint.py",
                "tests/test_unibot_exam_notebook_checkpoint.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_exam_notebook_checkpoint.py tests/test_unibot_readiness.py -q"],
            "review_gate": "notebook_checkpoint_local_cycle_workspace_card_checkpoint_link_traceability",
            "closure_evidence": {
                "commit": "988cf65",
                "summary": "Notebook-checkpoint release-claim alignment now links hash-only local cell evidence to the harnessed local-cycle operator workspace-card readiness gate, preserves checkpoint and Help-Ledger-preview hashes plus prefill metadata, and blocks raw cell/notebook/query, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "study_session_local_cycle_workspace_card_reflection_link_alignment",
            "priority": 68,
            "status": "closed_harnessed",
            "goal": "Link study-session formative review/reflection evidence with the harnessed local-cycle operator workspace-card readiness gate, preserving prediction/notebook-action/reflection metadata, workspace-card prefill evidence, no raw learner/private text publication, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/study_session.py",
                "tests/test_unibot_study_session.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_study_session.py tests/test_unibot_readiness.py -q"],
            "review_gate": "study_session_local_cycle_workspace_card_reflection_link_traceability",
            "closure_evidence": {
                "commit": "77d12b5",
                "summary": "Study-session release-claim alignment now links formative prediction/notebook-action/reflection evidence to the harnessed local-cycle operator workspace-card readiness gate, preserves reflection and Help-Ledger-preview hashes plus prefill metadata, and blocks raw learner/private text, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "private_tutor_use_flow_local_cycle_workspace_card_help_ledger_link_alignment",
            "priority": 69,
            "status": "closed_harnessed",
            "goal": "Link private tutor-use flow A0-A2 source-anchored help and operator-confirmed Help-Ledger evidence with the harnessed local-cycle operator workspace-card readiness gate, preserving tutor response/help-ledger metadata, workspace-card prefill evidence, no raw query/course text publication, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/private_tutor_use_flow.py",
                "tests/test_unibot_private_tutor_use_flow.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_private_tutor_use_flow.py tests/test_unibot_readiness.py -q"],
            "review_gate": "private_tutor_use_flow_local_cycle_workspace_card_help_ledger_link_traceability",
            "closure_evidence": {
                "commit": "89f4938",
                "summary": "Private tutor-use flow release-claim alignment now links operator-confirmed Help-Ledger event hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves tutor response and ready-for-prefill metadata, and blocks raw query/course text, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "extraction_manifest_apply_local_cycle_workspace_card_manifest_link_alignment",
            "priority": 70,
            "status": "closed_harnessed",
            "goal": "Link private manifest-apply dry-run and operator-confirmed local manifest metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving candidate/apply metadata, workspace-card prefill evidence, no raw extracted text/local path publication, no tutor-indexing by apply alone, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/extraction_manifest_apply.py",
                "tests/test_unibot_extraction_manifest_apply.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_extraction_manifest_apply.py tests/test_unibot_readiness.py -q"],
            "review_gate": "extraction_manifest_apply_local_cycle_workspace_card_manifest_link_traceability",
            "closure_evidence": {
                "commit": "7e16ae9",
                "summary": "Private manifest-apply release-claim alignment now links confirmed manifest and delta hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves candidate/apply and ready-for-prefill metadata, and blocks raw extracted text/local paths, tutor-indexing by apply alone, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "extraction_manifest_update_local_cycle_workspace_card_candidate_link_alignment",
            "priority": 71,
            "status": "closed_harnessed",
            "goal": "Link extraction manifest-update candidate metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving reviewed-candidate hashes and workspace-card prefill evidence, no raw OCR/transcript/local path publication, no manifest writes by update alone, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/extraction_manifest_update.py",
                "tests/test_unibot_extraction_manifest_update.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_extraction_manifest_update.py tests/test_unibot_readiness.py -q"],
            "review_gate": "extraction_manifest_update_local_cycle_workspace_card_candidate_link_traceability",
            "closure_evidence": {
                "commit": "97b8634",
                "summary": "Extraction manifest-update release-claim alignment now links reviewed candidate and candidate-set hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves candidate and ready-for-prefill metadata, and blocks raw OCR/transcript/local paths, manifest writes by update alone, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "extraction_progress_local_cycle_workspace_card_queue_link_alignment",
            "priority": 72,
            "status": "closed_harnessed",
            "goal": "Link extraction progress review queues and receipt metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving progress/queue hashes and workspace-card prefill evidence, no raw extracted text/local path/private artifact publication, no manifest writes or tutor retrieval, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/extraction_progress.py",
                "tests/test_unibot_extraction_progress.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_extraction_progress.py tests/test_unibot_readiness.py -q"],
            "review_gate": "extraction_progress_local_cycle_workspace_card_queue_link_traceability",
            "closure_evidence": {
                "commit": "4414ee2",
                "summary": "Extraction progress release-claim alignment now links progress queue and review hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves review queue and ready-for-prefill metadata, and blocks raw extracted text/local paths/private artifact publication, manifest writes or tutor retrieval, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "extraction_receipt_journal_local_cycle_workspace_card_receipt_link_alignment",
            "priority": 73,
            "status": "closed_harnessed",
            "goal": "Link extraction receipt journal hash-only receipt metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving receipt/journal hashes and workspace-card prefill evidence, no raw extracted text/local path/private artifact publication, no manifest writes/tutor retrieval, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/extraction_receipt_journal.py",
                "tests/test_unibot_extraction_receipt_journal.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_extraction_receipt_journal.py tests/test_unibot_readiness.py -q"],
            "review_gate": "extraction_receipt_journal_local_cycle_workspace_card_receipt_link_traceability",
            "closure_evidence": {
                "commit": "942a59b",
                "summary": "Extraction receipt journal release-claim alignment now links receipt journal and progress-receipt hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves hash-only receipt and ready-for-prefill metadata, and blocks raw extracted text/local paths/private artifact publication, manifest writes or tutor retrieval, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "external_decision_state_local_cycle_workspace_card_gate_link_alignment",
            "priority": 74,
            "status": "closed_harnessed",
            "goal": "Link external decision state gate summaries and hash-only decision metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving local-extraction/exam-authority gate hashes and workspace-card prefill evidence, no raw written decisions/contact data/public raw course text publication, no silent deployment switch, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/decision_state.py",
                "tests/test_unibot_decision_state.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_decision_state.py tests/test_unibot_readiness.py -q"],
            "review_gate": "external_decision_state_local_cycle_workspace_card_gate_link_traceability",
            "closure_evidence": {
                "commit": "dcebb68",
                "summary": "External decision state release-claim alignment now links decision gate and decision-record hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves local-extraction/exam-authority gate and ready-for-prefill metadata, and blocks raw written decisions/contact data/public raw course text publication, silent deployment switches, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "external_decision_record_journal_local_cycle_workspace_card_record_link_alignment",
            "priority": 75,
            "status": "closed_harnessed",
            "goal": "Link external decision record journal hash-only records with the harnessed local-cycle operator workspace-card readiness gate, preserving record/journal hashes and workspace-card prefill evidence, no raw written decisions/contact data/public raw course text publication, no deployment switch, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/external_decision_journal.py",
                "tests/test_unibot_external_decision_journal.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_external_decision_journal.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "external_decision_record_journal_local_cycle_workspace_card_record_link_traceability",
            "closure_evidence": {
                "commit": "59be092",
                "summary": "External decision record journal release-claim alignment now links decision-record journal and gate-summary hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves hash-only record and ready-for-prefill metadata, and blocks raw written decisions/contact data/public raw course text publication, deployment switches, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "stakeholder_decision_journal_local_cycle_workspace_card_request_link_alignment",
            "priority": 76,
            "status": "closed_harnessed",
            "goal": "Link stakeholder decision journal hash-only request/receipt metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving request/journal hashes and workspace-card prefill evidence, no raw request or written-decision text/contact data publication, no automatic gate changes, no grading/proctoring/KI-detection, and no exam clearance claims.",
            "allowed_files": [
                "unibot/decision_journal.py",
                "tests/test_unibot_decision_journal.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_decision_journal.py tests/test_unibot_readiness.py -q"],
            "review_gate": "stakeholder_decision_journal_local_cycle_workspace_card_request_link_traceability",
            "closure_evidence": {
                "commit": "6d7f5d0",
                "summary": "Stakeholder decision journal release-claim alignment now links decision-journal and request/receipt hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves hash-only request/receipt and ready-for-prefill metadata, and blocks raw request or written-decision text/contact data publication, automatic gate changes, grading, proctoring, KI-detection, and exam clearance claims.",
            },
        },
        {
            "work_id": "stakeholder_decision_request_local_cycle_workspace_card_packet_link_alignment",
            "priority": 77,
            "status": "closed_harnessed",
            "goal": "Link stakeholder decision request packet and receipt-template metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving request/packet hashes and workspace-card prefill evidence, no raw written-decision/contact data publication, no automatic external send or approval claim, no grading/proctoring/KI-detection, and no exam clearance claims.",
            "allowed_files": [
                "unibot/decision_request.py",
                "tests/test_unibot_decision_request.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_decision_request.py tests/test_unibot_readiness.py -q"],
            "review_gate": "stakeholder_decision_request_local_cycle_workspace_card_packet_link_traceability",
            "closure_evidence": {
                "commit": "2809248",
                "summary": "Stakeholder decision request release-claim alignment now links request packet and receipt-template hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves request/receipt-template and ready-for-prefill metadata, and blocks raw written-decision/contact data publication, automatic external sends or approval claims, grading, proctoring, KI-detection, and exam clearance claims.",
            },
        },
        {
            "work_id": "stakeholder_submission_bundle_local_cycle_workspace_card_lane_link_alignment",
            "priority": 78,
            "status": "closed_harnessed",
            "goal": "Link stakeholder submission bundle decision-lane and evidence-summary metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving lane/evidence hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no external send or approval claim, no grading/proctoring/KI-detection, and no exam clearance/deployment claims.",
            "allowed_files": [
                "unibot/submission.py",
                "tests/test_unibot_submission.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_submission.py tests/test_unibot_readiness.py -q"],
            "review_gate": "stakeholder_submission_bundle_local_cycle_workspace_card_lane_link_traceability",
            "closure_evidence": {
                "commit": "57fafbd",
                "summary": "Stakeholder submission bundle release-claim alignment now links decision-lane and combined-evidence hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves lane/evidence and ready-for-prefill metadata, and blocks raw private course text/contact data/local path publication, external sends or approval claims, grading, proctoring, KI-detection, and exam clearance/deployment claims.",
            },
        },
        {
            "work_id": "authority_handoff_local_cycle_workspace_card_authority_link_alignment",
            "priority": 79,
            "status": "closed_harnessed",
            "goal": "Link authority handoff reviewer-packet and public-language metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving authority/evidence hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no external send, no legal/approval/exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/handoff.py",
                "tests/test_unibot_handoff.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_handoff.py tests/test_unibot_readiness.py -q"],
            "review_gate": "authority_handoff_local_cycle_workspace_card_authority_link_traceability",
            "closure_evidence": {
                "commit": "9e4b6b9",
                "summary": "Authority handoff release-claim alignment now links reviewer-packet and public-language hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves authority/evidence and ready-for-prefill metadata, and blocks raw private course text/contact data/local path publication, external sends, legal or approval claims, exam clearance, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "review_board_packet_local_cycle_workspace_card_review_link_alignment",
            "priority": 80,
            "status": "closed_harnessed",
            "goal": "Link review-board reviewer-packet and release-claim summary metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving review/evidence hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no external send, no approval/exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/review_board.py",
                "tests/test_unibot_review_board.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_review_board.py tests/test_unibot_readiness.py -q"],
            "review_gate": "review_board_packet_local_cycle_workspace_card_review_link_traceability",
            "closure_evidence": {
                "commit": "3865e19",
                "summary": "Review-board release-claim summary alignment now links reviewer-packet and release-summary hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves review/evidence and ready-for-prefill metadata, and blocks raw private course text/contact data/local path publication, external sends, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "release_runbook_local_cycle_workspace_card_release_link_alignment",
            "priority": 81,
            "status": "closed_harnessed",
            "goal": "Link release-runbook gate and release-evidence metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving release/evidence hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no autonomous public release, no approval/exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/release_runbook.py",
                "tests/test_unibot_release_runbook.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_release_runbook.py tests/test_unibot_readiness.py -q"],
            "review_gate": "release_runbook_local_cycle_workspace_card_release_link_traceability",
            "closure_evidence": {
                "commit": "74b9311",
                "summary": "Release-runbook evidence alignment now links release-gate and release-evidence hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves release/evidence and ready-for-prefill metadata, and blocks raw private course text/contact data/local path publication, autonomous public release, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "publication_package_local_cycle_workspace_card_publication_link_alignment",
            "priority": 82,
            "status": "closed_harnessed",
            "goal": "Link publication-package reproducibility and release-gate metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving publication/evidence hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no autonomous public release, no approval/exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/publication.py",
                "tests/test_unibot_publication.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_publication.py tests/test_unibot_readiness.py -q"],
            "review_gate": "publication_package_local_cycle_workspace_card_publication_link_traceability",
            "closure_evidence": {
                "commit": "7dee620",
                "summary": "Publication-package reproducibility alignment now links publication-reproducibility and release-gate hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves publication/evidence and ready-for-prefill metadata, and blocks raw private course text/contact data/local path publication, autonomous public release, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "bachelor_thesis_package_local_cycle_workspace_card_thesis_link_alignment",
            "priority": 83,
            "status": "closed_harnessed",
            "goal": "Link Gretel bachelor-thesis package authorship/evidence and GLM-method metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving thesis/evidence hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no autonomous university submission, no approval/exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/bachelor_thesis.py",
                "tests/test_unibot_bachelor_thesis.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_bachelor_thesis.py tests/test_unibot_readiness.py -q"],
            "review_gate": "bachelor_thesis_package_local_cycle_workspace_card_thesis_link_traceability",
            "closure_evidence": {
                "commit": "49c1da7",
                "summary": "Gretel bachelor-thesis evaluation alignment now links authorship/evidence and GLM-method hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves thesis/evidence and ready-for-prefill metadata, and blocks raw private course text/contact data/local path publication, autonomous university submission, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "gretel_glm_evolve_lane_local_cycle_workspace_card_glm_link_alignment",
            "priority": 84,
            "status": "closed_harnessed",
            "goal": "Link Gretel/GLM proposal-lane redaction/provider-lock and work-packet metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving GLM proposal/evidence hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous apply/publication, no approval/exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/gretel_glm_evolve.py",
                "tests/test_unibot_gretel_glm_evolve.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_gretel_glm_evolve.py tests/test_unibot_readiness.py -q"],
            "review_gate": "gretel_glm_evolve_lane_local_cycle_workspace_card_glm_link_traceability",
            "closure_evidence": {
                "commit": "89b774a",
                "summary": "Gretel/GLM provider-redaction alignment now links proposal-packet and provider-lock hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves GLM proposal/evidence and ready-for-prefill metadata, and blocks raw private course text/contact data/local path publication, provider calls, autonomous apply/publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "source_card_drift_guard_local_cycle_workspace_card_source_link_alignment",
            "priority": 85,
            "status": "closed_harnessed",
            "goal": "Link source-card drift-guard coverage and required public-source metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving source-card/drift hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no legal/approval/exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/source_cards.py",
                "tests/test_unibot_source_cards.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_source_cards.py tests/test_unibot_readiness.py -q"],
            "review_gate": "source_card_drift_guard_local_cycle_workspace_card_source_link_traceability",
            "closure_evidence": {
                "commit": "f2efef7",
                "summary": "Source-card release-review-board claim alignment now links source-card corpus and drift-report hashes to the harnessed local-cycle operator workspace-card readiness gate, preserves source/drift and ready-for-prefill metadata, and blocks raw private course text/contact data/local path publication, provider calls, autonomous publication, legal/approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "readiness_evidence_snapshot_local_cycle_workspace_card_snapshot_link_alignment",
            "priority": 86,
            "status": "closed_harnessed",
            "goal": "Link readiness evidence snapshot status and scientific-gate metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving snapshot/scientific-gate hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval/exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/readiness.py",
                "tests/test_unibot_readiness.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "tests/test_unibot_autonomous_research_loop.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_readiness.py tests/test_unibot_autonomous_research_loop.py -q"],
            "review_gate": "readiness_evidence_snapshot_local_cycle_workspace_card_snapshot_link_traceability",
            "closure_evidence": {
                "commit": "3ad3e5f",
                "summary": "Readiness evidence snapshots now link snapshot and scientific-gate hashes to the harnessed local-cycle operator workspace-card readiness gate, preserve prefill/hash metadata, and block raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "autonomous_research_loop_local_cycle_workspace_card_budget_link_alignment",
            "priority": 87,
            "status": "closed_harnessed",
            "goal": "Link Gretel autonomous research-loop budget/cadence, next-work receipt, and safety metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving loop/budget hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval/exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/autonomous_research_loop.py",
                "tests/test_unibot_autonomous_research_loop.py",
                "docs/unibot/UNIBOT_GRETEL_AUTONOMOUS_RESEARCH_LOOP.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_autonomous_research_loop.py tests/test_unibot_readiness.py -q"],
            "review_gate": "autonomous_research_loop_local_cycle_workspace_card_budget_link_traceability",
            "closure_evidence": {
                "commit": "2a43b20",
                "summary": "Gretel autonomous research-loop budget/cadence and next-work receipt hashes now link to the harnessed local-cycle operator workspace-card readiness gate, preserving budget/receipt and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "paperclip_evaluation_bridge_local_cycle_workspace_card_control_link_alignment",
            "priority": 88,
            "status": "closed_harnessed",
            "goal": "Link optional Paperclip evaluation bridge control-plane status, request receipt, and non-runtime dependency metadata with the harnessed local-cycle operator workspace-card readiness gate, preserving bridge/control hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/Paperclip runtime activation/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/paperclip_evaluation_bridge.py",
                "tests/test_unibot_paperclip_evaluation_bridge.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_paperclip_evaluation_bridge.py tests/test_unibot_readiness.py -q"],
            "review_gate": "paperclip_evaluation_bridge_local_cycle_workspace_card_control_link_traceability",
            "closure_evidence": {
                "commit": "eb7b327",
                "summary": "Optional Paperclip evaluation bridge control-plane status and request/receipt hashes now link to the harnessed local-cycle operator workspace-card readiness gate, preserving control/receipt and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, Paperclip runtime activation, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "command_center_local_cycle_workspace_card_route_link_alignment",
            "priority": 89,
            "status": "closed_harnessed",
            "goal": "Link UniBot command-center role lanes, active harness sequence, scope status, and no-clearance deployment line with the harnessed local-cycle operator workspace-card readiness gate, preserving command-center/route hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/orchestration.py",
                "tests/test_unibot_orchestration.py",
                "docs/unibot/UNIBOT_COMMAND_CENTER.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_orchestration.py tests/test_unibot_readiness.py -q"],
            "review_gate": "command_center_local_cycle_workspace_card_route_link_traceability",
            "closure_evidence": {
                "commit": "6d2ed1b",
                "summary": "UniBot command-center role lanes, active harness routes, scope status, handoff rules, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving command-center/route and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "completion_audit_local_cycle_workspace_card_closure_link_alignment",
            "priority": 90,
            "status": "closed_harnessed",
            "goal": "Link UniBot completion-audit goal-complete/public-draft status, readiness snapshot, command-center route status, and no-clearance deployment line with the harnessed local-cycle operator workspace-card readiness gate, preserving completion/closure hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/completion_audit.py",
                "tests/test_unibot_completion_audit.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_completion_audit.py tests/test_unibot_readiness.py -q"],
            "review_gate": "completion_audit_local_cycle_workspace_card_closure_link_traceability",
            "closure_evidence": {
                "commit": "85b1667",
                "summary": "UniBot completion-audit public-draft closure status, readiness snapshot evidence, command-center route status, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving completion/closure and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "review_chain_integrity_local_cycle_workspace_card_chain_link_alignment",
            "priority": 91,
            "status": "closed_harnessed",
            "goal": "Link UniBot review-chain integrity metadata, packet/timeline/review/journal status, and next-safe-action evidence with the harnessed local-cycle operator workspace-card readiness gate, preserving chain/integrity hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/review_chain_integrity.py",
                "tests/test_unibot_review_chain_integrity.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_review_chain_integrity.py tests/test_unibot_readiness.py -q"],
            "review_gate": "review_chain_integrity_local_cycle_workspace_card_chain_link_traceability",
            "closure_evidence": {
                "commit": "d8c6612",
                "summary": "UniBot review-chain integrity metadata, packet/timeline/review/journal status, next-safe-action evidence, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving chain/integrity and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "timeline_export_receipt_journal_local_cycle_workspace_card_journal_link_alignment",
            "priority": 92,
            "status": "closed_harnessed",
            "goal": "Link UniBot timeline export receipt journal append/summary metadata, accepted/rejected counts, and no-clearance/local-write boundary with the harnessed local-cycle operator workspace-card readiness gate, preserving journal/summary hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/timeline_export_receipt_journal.py",
                "tests/test_unibot_timeline_export_receipt_journal.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_timeline_export_receipt_journal.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "timeline_export_receipt_journal_local_cycle_workspace_card_journal_link_traceability",
            "closure_evidence": {
                "commit": "bf1359f",
                "summary": "UniBot timeline export receipt journal append/summary metadata, accepted/blocked counts, local-write confirmation boundary, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving journal/summary and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "timeline_export_review_packet_local_cycle_workspace_card_review_link_alignment",
            "priority": 93,
            "status": "closed_harnessed",
            "goal": "Link UniBot timeline export review packet summary, local export receipt, reviewer question counts, and no-clearance/local-write boundary with the harnessed local-cycle operator workspace-card readiness gate, preserving review/receipt hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/timeline_export_review_packet.py",
                "tests/test_unibot_timeline_export_review_packet.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_timeline_export_review_packet.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "timeline_export_review_packet_local_cycle_workspace_card_review_link_traceability",
            "closure_evidence": {
                "commit": "338f1b6",
                "summary": "UniBot timeline export review packet summary metadata, local export receipt, reviewer question counts, local-write confirmation boundary, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving review/receipt and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "exam_packet_timeline_local_cycle_workspace_card_timeline_link_alignment",
            "priority": 94,
            "status": "closed_harnessed",
            "goal": "Link UniBot exam packet timeline events, receipt references, checkpoint hash counts, and no-clearance/local-write boundary with the harnessed local-cycle operator workspace-card readiness gate, preserving timeline/receipt hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_packet_timeline.py",
                "tests/test_unibot_exam_packet_timeline.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_exam_packet_timeline.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "exam_packet_timeline_local_cycle_workspace_card_timeline_link_traceability",
            "closure_evidence": {
                "commit": "58c8882",
                "summary": "UniBot exam packet timeline events, packet receipt references, checkpoint hash counts, export-review preview, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving timeline/receipt and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "exam_run_packet_local_cycle_workspace_card_packet_link_alignment",
            "priority": 95,
            "status": "closed_harnessed",
            "goal": "Link UniBot exam run packet selected skill packet, route execution metadata, packet receipt, local-cycle chain snapshot, and no-clearance/local-write boundary with the harnessed local-cycle operator workspace-card readiness gate, preserving packet/receipt hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_run_packet_builder.py",
                "tests/test_unibot_exam_run_packet.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_exam_run_packet.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "exam_run_packet_local_cycle_workspace_card_packet_link_traceability",
            "closure_evidence": {
                "commit": "e8db021",
                "summary": "UniBot exam run packet selected skill packet, route execution metadata, packet receipt, local-cycle chain snapshot, local-write boundary, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving packet/receipt and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "routed_action_executor_local_cycle_workspace_card_execution_link_alignment",
            "priority": 96,
            "status": "closed_harnessed",
            "goal": "Link UniBot routed action executor dry-run execution metadata, selected route, result/receipt hashes, and no-clearance/local-write boundary with the harnessed local-cycle operator workspace-card readiness gate, preserving execution/receipt hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/routed_action_executor.py",
                "tests/test_unibot_routed_action_executor.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_routed_action_executor.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "routed_action_executor_local_cycle_workspace_card_execution_link_traceability",
            "closure_evidence": {
                "commit": "d390b41",
                "summary": "UniBot routed action executor dry-run execution metadata, selected route, result/receipt hashes, local-write boundary, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving execution/receipt and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "course_per_skill_action_router_local_cycle_workspace_card_route_link_alignment",
            "priority": 97,
            "status": "closed_harnessed",
            "goal": "Link UniBot per-skill action router selected route, route receipt hashes, open-operator-confirmation counts, and no-clearance/local-write boundary with the harnessed local-cycle operator workspace-card readiness gate, preserving route/receipt hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/course_per_skill_action_router.py",
                "tests/test_unibot_course_per_skill_action_router.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_course_per_skill_action_router.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "course_per_skill_action_router_local_cycle_workspace_card_route_link_traceability",
            "closure_evidence": {
                "commit": "e5e4e42",
                "summary": "UniBot per-skill action router selected route metadata, route receipt hashes, open-operator-confirmation counts, local-write boundary, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving route/receipt and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "course_exam_coverage_dashboard_local_cycle_workspace_card_dashboard_link_alignment",
            "priority": 98,
            "status": "closed_harnessed",
            "goal": "Link UniBot course exam coverage dashboard skill readiness rows, coverage receipt hashes, checkpoint/open-confirmation counts, and no-clearance/local-write boundary with the harnessed local-cycle operator workspace-card readiness gate, preserving dashboard/receipt hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/course_exam_coverage_dashboard.py",
                "tests/test_unibot_course_exam_coverage_dashboard.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_course_exam_coverage_dashboard.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "course_exam_coverage_dashboard_local_cycle_workspace_card_dashboard_link_traceability",
            "closure_evidence": {
                "commit": "624fde3",
                "summary": "UniBot course exam coverage dashboard skill readiness rows, coverage receipt hashes, checkpoint/open-confirmation counts, local-write boundary, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving dashboard/receipt and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "material_coverage_run_local_cycle_workspace_card_coverage_link_alignment",
            "priority": 99,
            "status": "closed_harnessed",
            "goal": "Link UniBot material coverage run skill coverage rows, coverage receipt hashes, source/notebook/OCR/video gap counts, and no-clearance/local-write boundary with the harnessed local-cycle operator workspace-card readiness gate, preserving coverage/receipt hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/material_coverage_run.py",
                "tests/test_unibot_material_coverage_run.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_material_coverage_run.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "material_coverage_run_local_cycle_workspace_card_coverage_link_traceability",
            "closure_evidence": {
                "commit": "6c44c96",
                "summary": "UniBot material coverage run skill coverage rows, coverage receipt hashes, source/notebook/OCR/video gap counts, local-write boundary, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving coverage/receipt and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "private_tutor_use_flow_local_cycle_workspace_card_private_use_link_alignment",
            "priority": 100,
            "status": "closed_harnessed",
            "goal": "Link UniBot private tutor use flow private-manifest/index dry-run metadata, receipt hashes, local-private/no-publication boundary, and no-clearance/local-write boundary with the harnessed local-cycle operator workspace-card readiness gate, preserving flow/receipt hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/private_tutor_use_flow.py",
                "tests/test_unibot_private_tutor_use_flow.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_private_tutor_use_flow.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "private_tutor_use_flow_local_cycle_workspace_card_private_use_link_traceability",
            "closure_evidence": {
                "commit": "8142628",
                "summary": "UniBot private tutor use flow private-manifest/index dry-run metadata, flow/receipt hashes, local-private/no-publication boundary, local-write boundary, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving flow/receipt and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "study_session_local_cycle_workspace_card_study_link_alignment",
            "priority": 101,
            "status": "closed_harnessed",
            "goal": "Link UniBot study-session formative learning evidence, study receipt hashes, private tutor flow references, reflection/repeat-task boundary, and no-clearance/local-write boundary with the harnessed local-cycle operator workspace-card readiness gate, preserving study/receipt hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/study_session.py",
                "tests/test_unibot_study_session.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_study_session.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "study_session_local_cycle_workspace_card_study_link_traceability",
            "closure_evidence": {
                "commit": "99a6626",
                "summary": "UniBot study-session formative learning evidence, study/review receipt hashes, private tutor flow references, reflection/repeat-task boundary, local-write boundary, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving study/receipt and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "notebook_checkpoint_local_cycle_workspace_card_checkpoint_receipt_link_alignment",
            "priority": 102,
            "status": "closed_harnessed",
            "goal": "Link UniBot notebook checkpoint local cell evidence, checkpoint receipt hashes, study-session references, operator-confirmed journal boundary, and no-clearance/local-write boundary with the harnessed local-cycle operator workspace-card readiness gate, preserving checkpoint/receipt hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_notebook_checkpoint.py",
                "tests/test_unibot_exam_notebook_checkpoint.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_exam_notebook_checkpoint.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "notebook_checkpoint_local_cycle_workspace_card_checkpoint_receipt_link_traceability",
            "closure_evidence": {
                "commit": "da5e026",
                "summary": "UniBot notebook checkpoint local cell evidence, checkpoint/report/receipt hashes, study-session references, operator-confirmed journal boundary, local-write boundary, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving checkpoint/receipt and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "exam_workspace_launch_local_cycle_workspace_card_launch_receipt_link_alignment",
            "priority": 103,
            "status": "closed_harnessed",
            "goal": "Link UniBot exam workspace launch dry-run receipt, coverage-selected start point, private tutor/study/notebook checkpoint references, operator-reviewed launch boundary, and no-clearance/local-write boundary with the harnessed local-cycle operator workspace-card readiness gate, preserving launch/receipt hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_workspace_launch_flow.py",
                "tests/test_unibot_exam_workspace_launch_flow.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_exam_workspace_launch_flow.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "exam_workspace_launch_local_cycle_workspace_card_launch_receipt_link_traceability",
            "closure_evidence": {
                "commit": "df68605",
                "summary": "UniBot exam workspace launch dry-run evidence, coverage-selected start point, private tutor/study/notebook checkpoint references, export receipt hashes, operator-reviewed local-write boundary, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving launch/receipt and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "exam_workspace_run_local_cycle_workspace_card_run_receipt_link_alignment",
            "priority": 104,
            "status": "closed_harnessed",
            "goal": "Link UniBot exam workspace run dry-run packet, private tutor sidecar, study receipt, Help-Ledger/exam-ledger previews, export receipt, operator-confirmed local-write boundary, and no-clearance boundary with the harnessed local-cycle operator workspace-card readiness gate, preserving run/receipt hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_workspace_run.py",
                "tests/test_unibot_exam_workspace_run.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_exam_workspace_run.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "exam_workspace_run_local_cycle_workspace_card_run_receipt_link_traceability",
            "closure_evidence": {
                "commit": "ae66b36",
                "summary": "UniBot exam workspace run dry-run packet, private tutor sidecar, study receipt, Help-Ledger/exam-ledger receipt hashes, export receipt, operator-confirmed local-write boundary, waiting-mode no-write boundary, and no-clearance deployment line now link to the harnessed local-cycle operator workspace-card readiness gate, preserving run/receipt and ready-for-prefill metadata, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "exam_workspace_run_history_local_cycle_workspace_card_history_receipt_link_alignment",
            "priority": 105,
            "status": "closed_harnessed",
            "goal": "Link UniBot exam workspace run-history export-review metadata, session-console receipt ids, checkpoint hashes, help-level profiles, reflection/review status, export receipt references, operator-confirmation state, and no-clearance boundary with the harnessed local-cycle operator workspace-card readiness gate, preserving history/receipt hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_workspace_run_history.py",
                "tests/test_unibot_exam_workspace_run_history.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_exam_workspace_run_history.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "exam_workspace_run_history_local_cycle_workspace_card_history_receipt_link_traceability",
            "closure_evidence": {
                "commit": "9da9539",
                "summary": "UniBot exam workspace run-history export-review metadata, session-console receipt ids, checkpoint hashes, help-level profiles, reflection/review status, export receipt references, operator-confirmation state, history/receipt hashes, waiting-state receipt hash, no-clearance boundary, and workspace-card ready-for-prefill evidence now link to the harnessed local-cycle operator workspace-card readiness gate while blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "exam_workspace_operator_run_local_cycle_workspace_card_operator_receipt_link_alignment",
            "priority": 106,
            "status": "closed_harnessed",
            "goal": "Link UniBot exam workspace operator-run start view/operator confirmation metadata, launch/run/session-console references, help-ledger preview, operator-confirmed local-write boundary, and no-clearance boundary with the harnessed local-cycle operator workspace-card readiness gate, preserving operator-run receipt hashes and workspace-card prefill evidence, no raw private course text/contact data/local path publication, no provider call/autonomous publication, no approval or exam-clearance claim, no grading/proctoring/KI-detection, and no exam deployment claims.",
            "allowed_files": [
                "unibot/exam_workspace_operator_run.py",
                "tests/test_unibot_exam_workspace_operator_run.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_exam_workspace_operator_run.py tests/test_unibot_readiness.py -q"
            ],
            "review_gate": "exam_workspace_operator_run_local_cycle_workspace_card_operator_receipt_link_traceability",
            "closure_evidence": {
                "commit": "25ae8f2",
                "summary": "UniBot exam workspace operator-run start view, operator-confirmation metadata, launch/run/session-console references, Help-Ledger preview, operator-confirmed local-write boundary, and no-clearance boundary now link to the harnessed local-cycle operator workspace-card readiness gate, preserving operator-run receipt hashes and workspace-card prefill evidence, and blocking raw private course text/contact data/local path publication, provider calls, autonomous publication, approval or exam-clearance claims, grading, proctoring, KI-detection, and exam deployment claims.",
            },
        },
        {
            "work_id": "autonomous_queue_candidate_receipt_gate",
            "priority": 107,
            "status": "closed_harnessed",
            "goal": "Keep the recurring Gretel autonomous loop from reporting an empty next-work lane by exposing one public-safe candidate receipt gate while preserving zero ready work items, bounded file scope, no provider call, no autonomous publication, no exam clearance claim, no grading/proctoring/KI-detection, and no private context ingestion.",
            "allowed_files": [
                "unibot/autonomous_research_loop.py",
                "tests/test_unibot_autonomous_research_loop.py",
                "docs/unibot/UNIBOT_GRETEL_AUTONOMOUS_RESEARCH_LOOP.md",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_autonomous_research_loop.py -q"],
            "review_gate": "autonomous_queue_candidate_public_safe_receipt_traceability",
            "closure_evidence": {
                "commit": "1ec515d",
                "summary": "UniBot autonomous loop candidate receipt gate now keeps the recurring next-work lane explicit without authorizing implementation work, provider calls, autonomous publication, exam clearance, grading, proctoring, KI-detection, or private-context ingestion; its harness blocks unsafe candidates with external effects, Final-Go, or overbroad file scope.",
            },
        },
        {
            "work_id": "autonomous_queue_candidate_rotation_receipt_gate",
            "priority": 108,
            "status": "closed_harnessed",
            "goal": "Keep the recurring Gretel autonomous loop's candidate lane rotatable after a harnessed candidate receipt gate while preserving zero ready work items, one public-safe candidate, bounded file scope, no provider call, no autonomous publication, no exam clearance claim, no grading/proctoring/KI-detection, and no private context ingestion.",
            "allowed_files": [
                "unibot/autonomous_research_loop.py",
                "tests/test_unibot_autonomous_research_loop.py",
                "docs/unibot/UNIBOT_GRETEL_AUTONOMOUS_RESEARCH_LOOP.md",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_autonomous_research_loop.py -q"],
            "review_gate": "autonomous_queue_candidate_rotation_receipt_traceability",
            "closure_evidence": {
                "commit": "c5c9a2e",
                "summary": "UniBot autonomous loop receipt now carries the candidate-review status and exact review hash, and readiness verifies that the receipt hash matches the candidate review before treating the loop gate as green.",
            },
        },
        {
            "work_id": "autonomous_queue_candidate_review_hash_rotation_gate",
            "priority": 109,
            "status": "closed_harnessed",
            "goal": "Keep the recurring Gretel autonomous loop's next candidate lane rotatable after candidate-review hash closure while preserving zero ready work items, one public-safe candidate, bounded file scope, no provider call, no autonomous publication, no exam clearance claim, no grading/proctoring/KI-detection, and no private context ingestion.",
            "allowed_files": [
                "unibot/autonomous_research_loop.py",
                "tests/test_unibot_autonomous_research_loop.py",
                "docs/unibot/UNIBOT_GRETEL_AUTONOMOUS_RESEARCH_LOOP.md",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_autonomous_research_loop.py -q"],
            "review_gate": "autonomous_queue_candidate_review_hash_rotation_traceability",
            "closure_evidence": {
                "commit": "497ac6f",
                "summary": "UniBot readiness now verifies the candidate-rotation receipt status, public-safety status, zero failed contracts, blocked auto-promotion, and loop receipt hash match before treating the autonomous-loop gate as green.",
            },
        },
        {
            "work_id": "autonomous_queue_readiness_rotation_receipt_gate",
            "priority": 110,
            "status": "closed_harnessed",
            "goal": "Keep the recurring Gretel autonomous loop's next candidate lane rotatable after readiness-gated candidate-rotation evidence while preserving zero ready work items, one public-safe candidate, bounded file scope, no provider call, no autonomous publication, no exam clearance claim, no grading/proctoring/KI-detection, and no private context ingestion.",
            "allowed_files": [
                "unibot/autonomous_research_loop.py",
                "tests/test_unibot_autonomous_research_loop.py",
                "docs/unibot/UNIBOT_GRETEL_AUTONOMOUS_RESEARCH_LOOP.md",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_autonomous_research_loop.py -q"],
            "review_gate": "autonomous_queue_readiness_rotation_receipt_traceability",
            "closure_evidence": {
                "commit": "6e15ea5",
                "summary": "UniBot autonomous queue rotated after readiness-gated candidate-rotation evidence, preserving a single non-runnable candidate lane, zero ready work items, bounded scope, and no external/provider/exam-clearance effects.",
            },
        },
        {
            "work_id": "autonomous_queue_single_candidate_continuity_gate",
            "priority": 111,
            "status": "closed_harnessed",
            "goal": "Keep the recurring Gretel autonomous loop's single-candidate continuity auditable after readiness-rotation closure while preserving zero ready work items, one public-safe candidate, bounded file scope, no provider call, no autonomous publication, no exam clearance claim, no grading/proctoring/KI-detection, and no private context ingestion.",
            "allowed_files": [
                "unibot/autonomous_research_loop.py",
                "tests/test_unibot_autonomous_research_loop.py",
                "docs/unibot/UNIBOT_GRETEL_AUTONOMOUS_RESEARCH_LOOP.md",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_autonomous_research_loop.py -q"],
            "review_gate": "autonomous_queue_single_candidate_continuity_traceability",
            "closure_evidence": {
                "commit": "76bbddb",
                "summary": "UniBot autonomous loop now emits a single-candidate continuity receipt proving exactly one candidate, zero ready work items, highest-priority tail selection, bounded scope, and no external/provider/exam-clearance effects.",
            },
        },
        {
            "work_id": "autonomous_queue_continuity_readiness_gate",
            "priority": 112,
            "status": "closed_harnessed",
            "goal": "Keep the recurring Gretel autonomous loop's single-candidate continuity receipt readiness-gatable while preserving zero ready work items, one public-safe candidate, bounded file scope, no provider call, no autonomous publication, no exam clearance claim, no grading/proctoring/KI-detection, and no private context ingestion.",
            "allowed_files": [
                "unibot/readiness.py",
                "tests/test_unibot_readiness.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "unibot/autonomous_research_loop.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_readiness.py tests/test_unibot_autonomous_research_loop.py -q"
            ],
            "review_gate": "autonomous_queue_continuity_readiness_traceability",
            "closure_evidence": {
                "commit": "2c18440",
                "summary": "UniBot readiness now verifies the single-candidate continuity receipt selected status and review gate before treating the autonomous-loop gate as green.",
            },
        },
        {
            "work_id": "autonomous_queue_continuity_docs_traceability_gate",
            "priority": 113,
            "status": "closed_harnessed",
            "goal": "Keep the readiness-gated single-candidate continuity receipt publicly documented and traceable while preserving zero ready work items, one public-safe candidate, bounded file scope, no provider call, no autonomous publication, no exam clearance claim, no grading/proctoring/KI-detection, and no private context ingestion.",
            "allowed_files": [
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "docs/unibot/UNIBOT_GRETEL_AUTONOMOUS_RESEARCH_LOOP.md",
                "tests/test_unibot_readiness.py",
                "unibot/readiness.py",
            ],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_readiness.py tests/test_unibot_autonomous_research_loop.py -q"
            ],
            "review_gate": "autonomous_queue_continuity_docs_traceability",
            "closure_evidence": {
                "commit": "6c16b88",
                "summary": "UniBot readiness now verifies public documentation traceability for the current autonomous candidate, previous closure evidence, and review-gate match rule before treating the autonomous-loop gate as green.",
            },
        },
        {
            "work_id": "autonomous_queue_docs_traceability_negative_harness_gate",
            "priority": 114,
            "status": "closed_harnessed",
            "goal": "Add a negative harness proving missing autonomous-loop documentation traceability blocks readiness while preserving zero ready work items, one public-safe candidate, bounded file scope, no provider call, no autonomous publication, no exam clearance claim, no grading/proctoring/KI-detection, and no private context ingestion.",
            "allowed_files": [
                "unibot/readiness.py",
                "tests/test_unibot_readiness.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_readiness.py -q"],
            "review_gate": "autonomous_queue_docs_traceability_negative_harness",
            "closure_evidence": {
                "commit": "1f7b05d",
                "summary": "UniBot readiness now has a negative docs-traceability harness proving missing current-candidate, previous-closure, or review-gate-rule documentation blocks the autonomous-loop readiness check.",
            },
        },
        {
            "work_id": "autonomous_queue_docs_traceability_negative_evidence_gate",
            "priority": 115,
            "status": "candidate",
            "goal": "Surface the docs-traceability negative harness result in readiness evidence while preserving zero ready work items, one public-safe candidate, bounded file scope, no provider call, no autonomous publication, no exam clearance claim, no grading/proctoring/KI-detection, and no private context ingestion.",
            "allowed_files": [
                "unibot/readiness.py",
                "tests/test_unibot_readiness.py",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
            ],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_readiness.py -q"],
            "review_gate": "autonomous_queue_docs_traceability_negative_evidence",
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
    payload["candidate_receipt"] = build_autonomous_candidate_receipt(payload)
    payload["candidate_review"] = build_autonomous_candidate_review(payload)
    payload["candidate_rotation_receipt"] = build_autonomous_candidate_rotation_receipt(payload)
    payload["single_candidate_continuity_receipt"] = build_single_candidate_continuity_receipt(payload)
    payload["receipt"] = build_autonomous_loop_receipt(payload)
    payload["workspace_card_budget_alignment"] = build_autonomous_loop_workspace_card_alignment(payload)
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "unibot-gretel-autonomous-research-loop")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
    return payload


def build_autonomous_candidate_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    next_work_id = payload.get("next_recommended_work_id", "")
    queue = payload.get("work_queue", [])
    candidate = next((item for item in queue if item.get("work_id") == next_work_id), {})
    candidate_status = str(candidate.get("status", "missing"))
    allowed_files = [str(item) for item in candidate.get("allowed_files", [])] if isinstance(candidate, dict) else []
    receipt = {
        "schema_version": "unibot-gretel-autonomous-candidate-receipt-v1",
        "status": "candidate_receipt_ready",
        "selected_work_id": next_work_id,
        "selected_status": candidate_status,
        "ready_work_items_remain_zero": len([item for item in queue if item.get("status") == "ready"]) == 0,
        "candidate_is_not_auto_ready": candidate_status == "candidate",
        "allowed_files": allowed_files,
        "allowed_file_count": len(allowed_files),
        "acceptance_tests": [str(item) for item in candidate.get("acceptance_tests", [])],
        "review_gate": str(candidate.get("review_gate", "")),
        "candidate_review_status": "candidate_requires_human_or_harness_promotion",
        "promotion_blocker_reason": (
            "candidate lanes are intentionally not runnable work; promotion requires a new closed-harnessed "
            "receipt or an explicit ready work item with bounded scope and tests"
        ),
        "promotion_review_surface": "autonomous_queue_candidate_review",
        "auto_promotion_allowed": False,
        "provider_call_executed": payload.get("safety", {}).get("provider_call_executed") is True,
        "autonomous_github_push": payload.get("safety", {}).get("autonomous_github_push") is True,
        "external_messages_sent": payload.get("safety", {}).get("mail_calendar_chat_actions") is True,
        "final_go": payload.get("safety", {}).get("final_go") is True,
        "blocked_claims": [
            "provider call",
            "autonomous publication",
            "exam clearance claim",
            "grading",
            "proctoring",
            "KI-detection evidence",
            "private context ingestion",
        ],
    }
    receipt["candidate_hash"] = hashlib.sha256(
        json.dumps(
            {
                "selected_work_id": receipt["selected_work_id"],
                "selected_status": receipt["selected_status"],
                "allowed_files": receipt["allowed_files"],
                "allowed_file_count": receipt["allowed_file_count"],
                "acceptance_tests": receipt["acceptance_tests"],
                "review_gate": receipt["review_gate"],
                "candidate_review_status": receipt["candidate_review_status"],
                "promotion_blocker_reason": receipt["promotion_blocker_reason"],
                "promotion_review_surface": receipt["promotion_review_surface"],
                "auto_promotion_allowed": receipt["auto_promotion_allowed"],
                "blocked_claims": receipt["blocked_claims"],
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    scan = scan_text(json.dumps(receipt, ensure_ascii=False), "autonomous-candidate-receipt")
    receipt["public_safety_status"] = scan["status"]
    if (
        scan["status"] != "pass"
        or receipt["provider_call_executed"]
        or receipt["autonomous_github_push"]
        or receipt["external_messages_sent"]
        or receipt["final_go"]
        or not receipt["ready_work_items_remain_zero"]
        or not receipt["candidate_is_not_auto_ready"]
        or receipt["allowed_file_count"] > 4
    ):
        receipt["status"] = "candidate_receipt_blocked"
        if scan["status"] != "pass":
            receipt["public_safety_findings"] = scan["findings"]
    return receipt


def build_autonomous_candidate_review(payload: dict[str, Any]) -> dict[str, Any]:
    candidate_receipt = payload.get("candidate_receipt", {})
    candidate_receipt = candidate_receipt if isinstance(candidate_receipt, dict) else {}
    receipt_hash = hashlib.sha256(
        json.dumps(candidate_receipt, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    ready_items = len([item for item in payload.get("work_queue", []) if item.get("status") == "ready"])
    candidate_items = len([item for item in payload.get("work_queue", []) if item.get("status") == "candidate"])
    contracts = {
        "candidate_receipt_ready": candidate_receipt.get("status") == "candidate_receipt_ready",
        "candidate_matches_next_work": candidate_receipt.get("selected_work_id")
        == payload.get("next_recommended_work_id", ""),
        "candidate_not_auto_runnable": candidate_receipt.get("candidate_is_not_auto_ready") is True
        and candidate_receipt.get("auto_promotion_allowed") is False,
        "bounded_scope_preserved": int(candidate_receipt.get("allowed_file_count", 99) or 99) <= 4,
        "single_candidate_lane_preserved": ready_items == 0 and candidate_items == 1,
        "no_external_effects": candidate_receipt.get("provider_call_executed") is False
        and candidate_receipt.get("autonomous_github_push") is False
        and candidate_receipt.get("external_messages_sent") is False
        and candidate_receipt.get("final_go") is False,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    review = {
        "schema_version": "unibot-gretel-autonomous-candidate-review-v1",
        "status": "candidate_review_ready",
        "selected_work_id": candidate_receipt.get("selected_work_id", ""),
        "selected_status": candidate_receipt.get("selected_status", ""),
        "candidate_receipt_status": candidate_receipt.get("status", "missing"),
        "candidate_receipt_hash": receipt_hash,
        "candidate_review_surface": candidate_receipt.get(
            "promotion_review_surface", "autonomous_queue_candidate_review"
        ),
        "promotion_recommendation": "keep_candidate_not_runnable",
        "promotion_blocker_reason": candidate_receipt.get("promotion_blocker_reason", ""),
        "auto_promotion_allowed": False,
        "ready_work_items": ready_items,
        "candidate_work_items": candidate_items,
        "allowed_file_count": candidate_receipt.get("allowed_file_count", 0),
        "review_gate": candidate_receipt.get("review_gate", ""),
        "allowed_next_actions": [
            "keep_candidate_for_next_budgeted_review",
            "promote_only_by_new_ready_work_item_with_bounded_scope_and_tests",
            "retire_candidate_only_with_closed_harnessed_receipt",
        ],
        "blocked_claims": [
            "provider call",
            "autonomous publication",
            "automatic candidate promotion",
            "exam clearance claim",
            "grading",
            "proctoring",
            "KI-detection evidence",
            "private context ingestion",
        ],
        "contracts": contracts,
        "failed_contract_ids": failed_contract_ids,
        "raw_private_context_shared": False,
        "provider_call_executed": False,
        "autonomous_publication_started": False,
        "final_go": False,
    }
    scan = scan_text(json.dumps(review, ensure_ascii=False), "autonomous-candidate-review")
    review["public_safety_status"] = scan["status"]
    if scan["status"] != "pass" or failed_contract_ids:
        review["status"] = "candidate_review_blocked"
        if scan["status"] != "pass":
            review["public_safety_findings"] = scan["findings"]
    return review


def build_autonomous_candidate_rotation_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    queue = [item for item in payload.get("work_queue", []) if isinstance(item, dict)]
    candidate_receipt = payload.get("candidate_receipt", {})
    candidate_receipt = candidate_receipt if isinstance(candidate_receipt, dict) else {}
    candidate_review = payload.get("candidate_review", {})
    candidate_review = candidate_review if isinstance(candidate_review, dict) else {}
    closed_items = [item for item in queue if item.get("status") == "closed_harnessed"]
    previous_closed = max(closed_items, key=lambda item: int(item.get("priority", 0) or 0), default={})
    selected_work_id = str(candidate_receipt.get("selected_work_id", ""))
    previous_closed_work_id = str(previous_closed.get("work_id", ""))
    previous_closed_commit = str(previous_closed.get("closure_evidence", {}).get("commit", ""))
    candidate_review_hash = (
        hashlib.sha256(json.dumps(candidate_review, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        if candidate_review
        else ""
    )
    contracts = {
        "previous_closed_candidate_present": previous_closed_work_id != "" and previous_closed_commit != "",
        "rotation_advances_work_id": previous_closed_work_id != "" and previous_closed_work_id != selected_work_id,
        "candidate_receipt_ready": candidate_receipt.get("status") == "candidate_receipt_ready",
        "candidate_review_ready": candidate_review.get("status") == "candidate_review_ready",
        "candidate_review_hash_present": candidate_review_hash != "",
        "single_candidate_lane_preserved": len([item for item in queue if item.get("status") == "candidate"]) == 1,
        "zero_ready_items_preserved": len([item for item in queue if item.get("status") == "ready"]) == 0,
        "bounded_scope_preserved": int(candidate_receipt.get("allowed_file_count", 99) or 99) <= 4,
        "no_external_effects": payload.get("safety", {}).get("provider_call_executed") is False
        and payload.get("safety", {}).get("autonomous_github_push") is False
        and payload.get("safety", {}).get("mail_calendar_chat_actions") is False
        and payload.get("safety", {}).get("final_go") is False,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    receipt = {
        "schema_version": "unibot-gretel-autonomous-candidate-rotation-receipt-v1",
        "status": "candidate_rotation_receipt_ready",
        "previous_closed_work_id": previous_closed_work_id,
        "previous_closed_commit": previous_closed_commit,
        "selected_work_id": selected_work_id,
        "selected_status": candidate_receipt.get("selected_status", ""),
        "review_gate": candidate_receipt.get("review_gate", ""),
        "candidate_receipt_hash": candidate_receipt.get("candidate_hash", ""),
        "candidate_review_hash": candidate_review_hash,
        "rotation_recommendation": "keep_new_candidate_non_runnable",
        "auto_promotion_allowed": False,
        "ready_work_items": len([item for item in queue if item.get("status") == "ready"]),
        "candidate_work_items": len([item for item in queue if item.get("status") == "candidate"]),
        "closed_harnessed_work_items": len(closed_items),
        "contracts": contracts,
        "failed_contract_ids": failed_contract_ids,
        "provider_call_executed": False,
        "autonomous_publication_started": False,
        "final_go": False,
    }
    receipt["rotation_hash"] = hashlib.sha256(
        json.dumps(
            {
                "previous_closed_work_id": receipt["previous_closed_work_id"],
                "previous_closed_commit": receipt["previous_closed_commit"],
                "selected_work_id": receipt["selected_work_id"],
                "selected_status": receipt["selected_status"],
                "review_gate": receipt["review_gate"],
                "candidate_receipt_hash": receipt["candidate_receipt_hash"],
                "candidate_review_hash": receipt["candidate_review_hash"],
                "contracts": receipt["contracts"],
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    scan = scan_text(json.dumps(receipt, ensure_ascii=False), "autonomous-candidate-rotation-receipt")
    receipt["public_safety_status"] = scan["status"]
    if scan["status"] != "pass" or failed_contract_ids:
        receipt["status"] = "candidate_rotation_receipt_blocked"
        if scan["status"] != "pass":
            receipt["public_safety_findings"] = scan["findings"]
    return receipt


def build_single_candidate_continuity_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    queue = [item for item in payload.get("work_queue", []) if isinstance(item, dict)]
    candidate_receipt = payload.get("candidate_receipt", {})
    candidate_receipt = candidate_receipt if isinstance(candidate_receipt, dict) else {}
    candidate_items = [item for item in queue if item.get("status") == "candidate"]
    ready_items = [item for item in queue if item.get("status") == "ready"]
    highest_priority_item = max(queue, key=lambda item: int(item.get("priority", 0) or 0), default={})
    selected_work_id = str(candidate_receipt.get("selected_work_id", ""))
    highest_priority_work_id = str(highest_priority_item.get("work_id", ""))
    contracts = {
        "single_candidate_lane_preserved": len(candidate_items) == 1,
        "zero_ready_items_preserved": len(ready_items) == 0,
        "candidate_matches_next_work": selected_work_id == payload.get("next_recommended_work_id", ""),
        "candidate_is_highest_priority_tail": selected_work_id != "" and selected_work_id == highest_priority_work_id,
        "candidate_not_auto_runnable": candidate_receipt.get("candidate_is_not_auto_ready") is True
        and candidate_receipt.get("auto_promotion_allowed") is False,
        "bounded_scope_preserved": int(candidate_receipt.get("allowed_file_count", 99) or 99) <= 4,
        "no_external_effects": payload.get("safety", {}).get("provider_call_executed") is False
        and payload.get("safety", {}).get("autonomous_github_push") is False
        and payload.get("safety", {}).get("mail_calendar_chat_actions") is False
        and payload.get("safety", {}).get("final_go") is False,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    continuity = {
        "schema_version": "unibot-gretel-single-candidate-continuity-receipt-v1",
        "status": "single_candidate_continuity_ready",
        "selected_work_id": selected_work_id,
        "highest_priority_work_id": highest_priority_work_id,
        "selected_status": candidate_receipt.get("selected_status", ""),
        "review_gate": candidate_receipt.get("review_gate", ""),
        "ready_work_items": len(ready_items),
        "candidate_work_items": len(candidate_items),
        "closed_harnessed_work_items": len([item for item in queue if item.get("status") == "closed_harnessed"]),
        "allowed_file_count": candidate_receipt.get("allowed_file_count", 0),
        "candidate_receipt_hash": candidate_receipt.get("candidate_hash", ""),
        "contracts": contracts,
        "failed_contract_ids": failed_contract_ids,
        "auto_promotion_allowed": False,
        "provider_call_executed": False,
        "autonomous_publication_started": False,
        "final_go": False,
    }
    continuity["continuity_hash"] = hashlib.sha256(
        json.dumps(
            {
                "selected_work_id": continuity["selected_work_id"],
                "highest_priority_work_id": continuity["highest_priority_work_id"],
                "review_gate": continuity["review_gate"],
                "ready_work_items": continuity["ready_work_items"],
                "candidate_work_items": continuity["candidate_work_items"],
                "closed_harnessed_work_items": continuity["closed_harnessed_work_items"],
                "candidate_receipt_hash": continuity["candidate_receipt_hash"],
                "contracts": continuity["contracts"],
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    scan = scan_text(json.dumps(continuity, ensure_ascii=False), "single-candidate-continuity-receipt")
    continuity["public_safety_status"] = scan["status"]
    if scan["status"] != "pass" or failed_contract_ids:
        continuity["status"] = "single_candidate_continuity_blocked"
        if scan["status"] != "pass":
            continuity["public_safety_findings"] = scan["findings"]
    return continuity


def build_autonomous_loop_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    hashed = {key: value for key, value in payload.items() if key not in {"generated_at_utc", "receipt"}}
    digest = hashlib.sha256(json.dumps(hashed, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    candidate_review = (
        payload.get("candidate_review", {})
        if isinstance(payload.get("candidate_review"), dict)
        else {}
    )
    candidate_review_hash = (
        hashlib.sha256(json.dumps(candidate_review, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        if candidate_review
        else ""
    )
    candidate_rotation_receipt = (
        payload.get("candidate_rotation_receipt", {})
        if isinstance(payload.get("candidate_rotation_receipt"), dict)
        else {}
    )
    single_candidate_continuity = (
        payload.get("single_candidate_continuity_receipt", {})
        if isinstance(payload.get("single_candidate_continuity_receipt"), dict)
        else {}
    )
    return {
        "schema_version": "unibot-gretel-autonomous-research-loop-receipt-v1",
        "loop_hash": digest,
        "owner": payload["intent_contract"]["owner"],
        "ready_work_items": len([item for item in payload["work_queue"] if item["status"] == "ready"]),
        "candidate_work_items": len([item for item in payload["work_queue"] if item["status"] == "candidate"]),
        "closed_harnessed_work_items": len([item for item in payload["work_queue"] if item["status"] == "closed_harnessed"]),
        "next_recommended_work_id": payload.get("next_recommended_work_id", ""),
        "candidate_receipt_status": payload.get("candidate_receipt", {}).get("status", "missing"),
        "candidate_receipt_hash": payload.get("candidate_receipt", {}).get("candidate_hash", ""),
        "candidate_review_status": candidate_review.get("status", "missing"),
        "candidate_review_hash": candidate_review_hash,
        "candidate_rotation_status": candidate_rotation_receipt.get("status", "missing"),
        "candidate_rotation_hash": candidate_rotation_receipt.get("rotation_hash", ""),
        "single_candidate_continuity_status": single_candidate_continuity.get("status", "missing"),
        "single_candidate_continuity_hash": single_candidate_continuity.get("continuity_hash", ""),
        "provider_call_executed": False,
        "autonomous_github_push": False,
        "human_review_required_for_publication": True,
    }


def autonomous_loop_budget_hash(loop: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "status": loop.get("status", ""),
                "budget_policy": loop.get("budget_policy", {}),
                "run_protocol": loop.get("run_protocol", []),
                "completion_policy": loop.get("completion_policy", ""),
                "always_use_standards": loop.get("intent_contract", {}).get("always_use_standards", []),
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def autonomous_loop_receipt_hash(loop: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "status": loop.get("status", ""),
                "receipt": loop.get("receipt", {}),
                "next_recommended_work_id": loop.get("next_recommended_work_id", ""),
                "safety": loop.get("safety", {}),
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def synthetic_autonomous_loop_workspace_card() -> dict[str, Any]:
    preview_hash = hashlib.sha256(b"synthetic autonomous loop workspace card").hexdigest()
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "pandas",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic autonomous-loop budget prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "pandas",
            "next_safe_action": "review_autonomous_loop_budget_hashes_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_loop_budget_receipt_before_public_claim_use",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__AUTONOMOUS_LOOP_RECEIPT_HASH__",
            "checkpoint_hash": "__AUTONOMOUS_LOOP_BUDGET_HASH__",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "zai-glm-52"],
            "source_anchor_count": 3,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": "A2",
            "preview_hash": preview_hash,
        },
    }


def safe_autonomous_loop_workspace_card(
    workspace_card: dict[str, Any],
    *,
    autonomous_budget_hash: str = "",
    autonomous_receipt_hash: str = "",
) -> dict[str, Any]:
    summary = workspace_card.get("workspace_card_summary", {}) if isinstance(workspace_card.get("workspace_card_summary"), dict) else {}
    ledger = workspace_card.get("help_ledger_preview", {}) if isinstance(workspace_card.get("help_ledger_preview"), dict) else {}
    if not summary and (
        workspace_card.get("help_ledger_preview_hash") is not None
        or workspace_card.get("ready_for_operator_prefill") is not None
        or workspace_card.get("help_ledger_preview_status") is not None
    ):
        summary = workspace_card
    checkpoint_hash = str(summary.get("checkpoint_hash", ""))
    task_hash = str(summary.get("task_hash", ""))
    if autonomous_budget_hash and checkpoint_hash == "__AUTONOMOUS_LOOP_BUDGET_HASH__":
        checkpoint_hash = autonomous_budget_hash
    if autonomous_receipt_hash and task_hash == "__AUTONOMOUS_LOOP_RECEIPT_HASH__":
        task_hash = autonomous_receipt_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", "keep_blocked")),
        "recommendation_reason": str(summary.get("recommendation_reason", "missing_autonomous_loop_budget_gate")),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "help_ledger_preview_status": str(summary.get("help_ledger_preview_status", ledger.get("status", "missing"))),
        "next_safe_action": str(summary.get("next_safe_action", "")),
        "next_safe_user_action": str(summary.get("next_safe_user_action", "")),
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", "")),
        "operator_run_method": str(summary.get("operator_run_method", "POST")),
        "help_level": str(summary.get("help_level", ledger.get("help_level", "A2"))),
        "task_hash": task_hash,
        "checkpoint_hash": checkpoint_hash,
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "help_ledger_preview_hash": str(summary.get("help_ledger_preview_hash", ledger.get("preview_hash", ""))),
        "not_cleared_receipt": bool(workspace_card.get("not_cleared_receipt", True)),
        "exam_deployment_status": "not_cleared",
        "raw_workspace_card_returned": False,
    }


def build_autonomous_loop_workspace_card_alignment(
    loop: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    loop = loop if isinstance(loop, dict) else {}
    budget_hash = autonomous_loop_budget_hash(loop)
    receipt_hash = autonomous_loop_receipt_hash(loop)
    workspace_card = safe_autonomous_loop_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else synthetic_autonomous_loop_workspace_card(),
        autonomous_budget_hash=budget_hash,
        autonomous_receipt_hash=receipt_hash,
    )
    cadence = loop.get("budget_policy", {}).get("cadence", {})
    token_policy = loop.get("budget_policy", {}).get("token_policy", {})
    receipt = loop.get("receipt", {})
    safety = loop.get("safety", {})
    required_readiness_check_ids = [
        "gretel_autonomous_research_loop",
        "python_exam_local_cycle_operator_workspace_card",
        "source_card_drift_guard",
        "readiness_evidence_snapshot",
    ]
    workspace_card_readiness_gate_linked = (
        workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and workspace_card.get("help_ledger_preview_hash") != ""
        and workspace_card.get("exam_deployment_status") == "not_cleared"
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card.get("raw_workspace_card_returned") is False
    )
    contracts = {
        "loop_budget_policy_ready": loop.get("status") == "ready_for_budgeted_recurring_local_runs"
        and cadence.get("recommended_cron") == "every_6_hours"
        and cadence.get("max_active_work_item_per_run") == 1
        and token_policy.get("default_reasoning_effort") == "low",
        "loop_receipt_ready": receipt.get("ready_work_items", 0) <= cadence.get("max_active_work_item_per_run", 0)
        and receipt.get("closed_harnessed_work_items", 0) >= 1
        and receipt.get("next_recommended_work_id") == loop.get("next_recommended_work_id", ""),
        "loop_safety_no_external_effects": safety.get("provider_call_executed") is False
        and safety.get("autonomous_github_push") is False
        and safety.get("mail_calendar_chat_actions") is False
        and safety.get("final_go") is False,
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_autonomous_loop_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("checkpoint_hash") == budget_hash
        and workspace_card.get("task_hash") == receipt_hash,
        "workspace_card_public_metadata_only": workspace_card.get("raw_workspace_card_returned") is False,
        "high_stakes_boundaries_blocked": workspace_card.get("exam_deployment_status") == "not_cleared",
    }
    alignment = {
        "schema_version": AUTONOMOUS_LOOP_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION,
        "status": "ready",
        "budget_hash": budget_hash,
        "receipt_hash": receipt_hash,
        "recommended_cron": cadence.get("recommended_cron", ""),
        "max_active_work_item_per_run": cadence.get("max_active_work_item_per_run", 0),
        "default_reasoning_effort": token_policy.get("default_reasoning_effort", ""),
        "ready_work_items": receipt.get("ready_work_items", 0),
        "closed_harnessed_work_items": receipt.get("closed_harnessed_work_items", 0),
        "next_recommended_work_id": loop.get("next_recommended_work_id", ""),
        "required_readiness_check_ids": required_readiness_check_ids,
        "required_human_gates": [
            "human_review_required",
            "public_safety_required",
            "university_submission_requires_human_review",
            "provider_call_requires_explicit_go_and_redaction_receipt",
            "exam_clearance_requires_written_authority_clearance",
        ],
        "blocked_claims": [
            "raw private course text publication",
            "contact data publication",
            "local path publication",
            "provider call",
            "autonomous publication",
            "approval claim",
            "exam clearance claim",
            "grading",
            "proctoring",
            "KI-detection evidence",
            "exam deployment",
        ],
        "contracts": contracts,
        "failed_contract_ids": sorted(contract_id for contract_id, passed in contracts.items() if not passed),
        "workspace_card_status": workspace_card["status"],
        "workspace_card_selected_skill_tag": workspace_card["selected_skill_tag"],
        "workspace_card_ready_for_operator_prefill": workspace_card["ready_for_operator_prefill"],
        "workspace_card_help_ledger_status": workspace_card["help_ledger_preview_status"],
        "workspace_card_help_ledger_hash_present": workspace_card["help_ledger_preview_hash"] != "",
        "workspace_card_operator_prefill_hash_present": workspace_card["task_hash"] != ""
        and workspace_card["checkpoint_hash"] != "",
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_autonomous_loop_gate_linked": contracts["workspace_card_autonomous_loop_gate_linked"],
        "workspace_card_readiness_gate_claim_linked": "python_exam_local_cycle_operator_workspace_card"
        in required_readiness_check_ids,
        "raw_workspace_card_returned": workspace_card["raw_workspace_card_returned"],
        "public_language": (
            "Autonomous-loop claims are hash-only review aids for cadence, budget, receipt, and safety state; "
            "they do not authorize public release, provider calls, university submission, or exam use."
        ),
    }
    if alignment["failed_contract_ids"]:
        alignment["status"] = "blocked"
    scan = scan_text(json.dumps(alignment, ensure_ascii=False), "autonomous-loop-workspace-card-budget-alignment")
    alignment["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked"
        alignment["public_safety_findings"] = scan["findings"]
    return alignment


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
        "## Workspace-Card Budget Alignment\n\n"
        f"- Status: {loop['workspace_card_budget_alignment']['status']}\n"
        f"- Budget hash: {loop['workspace_card_budget_alignment']['budget_hash']}\n"
        f"- Receipt hash: {loop['workspace_card_budget_alignment']['receipt_hash']}\n"
        f"- Workspace-card gate linked: {loop['workspace_card_budget_alignment']['workspace_card_autonomous_loop_gate_linked']}\n\n"
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
