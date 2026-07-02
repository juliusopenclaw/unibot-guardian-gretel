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

1. `bachelor_thesis_evidence_index`: keep the Gretel-authored bachelor-thesis
   package aligned with readiness evidence, source cards, tests, and human
   review gates.

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

## Automation Rule

Automation may keep the local iCloud/Git worktree warm and produce local commits
or review notes after green checks. Public GitHub pushes, provider calls, real
submission, exam deployment, and external messages require human review.
