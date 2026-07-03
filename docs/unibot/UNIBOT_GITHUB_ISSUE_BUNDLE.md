# UniBot GitHub Issue Bundle

Status: public-safe draft issue package, not automatic publication.

The GitHub issue bundle is implemented in `unibot.github_issues` and exposed
through:

- `POST /api/unibot/github-issue-bundle`
- `POST /api/unibot/github-issue-bundle-markdown`

## Purpose

Validated demo feedback becomes triage metadata. The issue bundle converts that
metadata into GitHub-style issue drafts with titles, labels, bodies, priority,
component, scenario, and suggested tests.

## Boundary

The bundle does not create GitHub issues automatically. It must be reviewed
manually before publication. It never includes screenshots, copied free text,
emails, local paths, health or accommodation details, real exam work, or raw
private course text.

## Manual Review Contract

Every issue draft carries:

- review checklist,
- evidence requirements,
- readiness check IDs,
- source-card IDs,
- human gates,
- publication gate `human_review_before_github_create`,
- `manual_publish_only = true`.

Reviewers must confirm that the draft uses sanitized metadata only, names a
focused test or readiness gate, can be closed by code, docs, tests, or a
documented blocked reason, and does not claim exam clearance, grading authority,
proctoring reliability, or AI-detection evidence.

## Evidence Traceability

The generated bundle includes `evidence_traceability`, a compact public-safe map
from each sanitized feedback issue to:

- the relevant readiness gates,
- source-card IDs for the claim area,
- human gates that still control publication and public-safety review, and
- the readiness evidence snapshot contract used for low-budget comparison.

This traceability layer does not publish anything to GitHub. It only prepares a
manual reviewer to confirm that public follow-up remains source-bound,
readiness-gated, and free of private feedback text.

It also carries a manual publication review-board claim contract:
`unibot-github-issue-release-review-board-claim-alignment-v1`. That contract
keeps issue drafts aligned with the publication package, release runbook,
review-board thesis/evaluation boundary, and public-safety gates. It does not
create GitHub issues, approve publication, authorize provider calls, or imply
exam clearance.

## Public Contribution Rule

Contributors should work from synthetic tasks, source cards, public-safe tests,
and these issue drafts only. Exam deployment, official grading, proctoring, and
KI-detection use remain out of scope.
