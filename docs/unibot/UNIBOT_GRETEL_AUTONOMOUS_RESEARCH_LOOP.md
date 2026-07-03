# UniBot Gretel Autonomous Research Loop

Status: budgeted recurring local research lane, not autonomous public release.

## Purpose

Gretel should keep improving UniBot as autonomously as is reasonable while
staying inside the project's safety, privacy, scientific, and publication
standards. The loop is designed for continuous small improvements, not for
unbounded token use or unsupervised external actions.

## North Star

Build UniBot as a public, source-bound, bachelor-thesis-level research project
that helps coding learners practice without outsourcing their own work, leaking
private material, or claiming exam clearance.

## Always-Use Standards

- Three Golden Rules.
- Public-safety scan.
- Readiness check.
- Source cards.
- Red-team scenarios.
- Synthetic fixtures.
- Review-board/open-decision register.
- Gretel/GLM proposal-only lane.
- Human review for publication, university submission, provider calls, and exam
  clearance.

## Budgeted 24/7 Mode

Recommended cadence: every 6 hours.

Per run:

- inspect public repo state,
- select at most one work item,
- change at most four candidate files,
- run focused tests and readiness gates,
- commit locally only when green,
- do not push publicly without human review.

Default reasoning effort should stay low. Escalation is allowed only for a
bounded failing test, a failing public-safety/readiness gate, or an API/release
contract change.

## Blocked Autonomous Actions

- No autonomous GitHub push or public release.
- No email, calendar, chat, or webhook sends.
- No GLM/Z.AI/OpenAI/provider call without explicit go and a redaction receipt.
- No private course material or real exam data ingestion.
- No exam clearance, grading authority, proctoring reliability, or AI-detection
  evidence claims.
- No Final-Go.

## Current Work Queue

1. `demo_feedback_release_review_board_claim_alignment`: align validated demo
   feedback records with feedback triage, GitHub issue, publication,
   release-review-board thesis/evaluation claims, public language controls, and human gates.

## Closed Harnessed Work

- `intent_contract_regression_pack`: closed in `fa942b0` with autonomous loop,
  intent contract, budget policy, API routes, docs, and tests.
- `scientific_evaluation_depth`: closed in `2b6473b` with a public-safe
  scientific quality rubric for Socratic help, source grounding, refusal
  clarity, privacy, and learner agency.
- `github_review_packet_hardening`: closed in `9a28675` with manual review
  contract, evidence requirements, publication gate, and manual-publish
  invariant.
- `autonomy_progress_memory`: closed in `5d16846` with completed queue items,
  explicit progress evidence, and next recommended work.
- `readiness_perf_guard`: closed in `c6581a3` with a focused runtime guard for
  recurring readiness checks, low reasoning effort, and escalated
  full-suite/provider work.
- `source_card_drift_guard`: closed in `afeb0d5` with source-card drift report,
  API route, readiness gate, stale-source harness, and public docs.
- `bachelor_thesis_evidence_index`: closed in `400fc92` with claim-to-test,
  readiness-check, source-card, and human-gate evidence mapping for the
  Gretel-authored bachelor-thesis package.
- `readiness_evidence_snapshot`: closed in `19d6f8c` with stable-hash
  readiness evidence snapshot, scientific gate coverage, public-safe summary,
  docs, and tests.
- `review_board_evidence_alignment`: closed in `f449f88` with reviewer-to-thesis
  claim, readiness-gate, source-card, and human-gate evidence mapping.
- `feedback_issue_evidence_traceability`: closed in `99d36ff` with
  feedback-derived GitHub issues mapped to readiness gates, source cards, human
  gates, and the evidence-snapshot contract.
- `release_runbook_evidence_alignment`: closed in `be671ff` with readiness
  snapshot, review-board, GitHub issue, source-card, and human-gate contracts
  for release review.
- `compliance_drift_evidence_alignment`: closed in `92cb2f1` with
  requirement-to-readiness, source-card, human-gate, and readiness-protection
  mapping.
- `pilot_protocol_evidence_alignment`: closed in `30a81a8` with consent,
  ethics, data, session-flow, release-boundary, source-card, readiness, and
  human-gate mapping.
- `data_protection_evidence_alignment`: closed in `4b5fbbc` with processing
  principles, pilot records, retention, public-boundary, exam-boundary,
  source-card, risk, readiness, and human-gate mapping.
- `glm_provider_redaction_evidence_alignment`: closed in `a41b060` with
  source-basis, redaction-receipt, provider-lock, proposal-validation,
  apply/publish/Final-Go, readiness, and human-gate mapping.
- `open_science_reproducibility_release_alignment`: closed in `ecfa4f8` with
  public reproduction, manual release, authority/compliance, Gretel/GLM thesis,
  autonomy, release-gate, source-card, and human-gate mapping.
- `course_material_public_boundary_alignment`: closed in `ca9c426` with
  public/private material contracts, source cards, readiness gates, and human
  gates for course-material publication boundaries.
- `adaptive_task_source_boundary_alignment`: closed in `00bc10e` with
  public-summary source contracts, learner-agency checks, readiness gates, and
  public-summary excerpt hardening.
- `evaluation_learner_agency_boundary_alignment`: closed in `7c04e0d` with
  adaptive trace, rubric, measurement-exclusion, source-card, readiness, and
  human-gate contracts.
- `bachelor_thesis_evaluation_claim_alignment`: closed in `5fcdbfe` with
  learner-agency, adaptive boundary, source-card, high-stakes exclusion,
  readiness, and human-gate traceability.
- `review_board_thesis_evaluation_claim_alignment`: closed in `20a66a0` with
  learner-agency reviewer mapping, high-stakes red lines, source-card,
  readiness, and human-gate contracts.
- `release_runbook_review_board_claim_alignment`: closed in `77f5b61` with
  review-board thesis/evaluation claim contract, adaptive/evaluation/readiness
  links, public-language controls, and human gates.
- `compliance_release_review_board_claim_alignment`: closed in `6170a9a` with
  release-review-board claim contract, release-runbook, review-board
  thesis/evaluation, readiness, and human-gate checks.
- `pilot_release_review_board_claim_alignment`: closed in `582c574` with
  synthetic learner-agency boundaries, adaptive evidence, readiness links, and
  human gates.
- `data_protection_release_review_board_claim_alignment`: closed in `447a37e`
  with pilot/release/review-board thesis/evaluation readiness links, processing
  boundaries, and human gates.
- `publication_release_review_board_claim_alignment`: closed in `d794a40` with
  pilot/data-protection/release/review-board thesis/evaluation trace links, public
  release boundaries, and human gates.
- `github_issue_release_review_board_claim_alignment`: closed in `16dcbb3`
  with publication/release/review-board thesis/evaluation claim contracts,
  manual issue publication controls, public language boundaries, and human
  gates.
- `feedback_triage_release_review_board_claim_alignment`: closed in `c74e157`
  with downstream GitHub issue, publication, release-runbook, review-board,
  readiness, and human-gate links for sanitized feedback triage.


## Automation Rule

Automation may keep the local iCloud/Git worktree warm and produce local commits
or review notes after green checks. Public GitHub pushes, provider calls, real
submission, exam deployment, and external messages require human review.
