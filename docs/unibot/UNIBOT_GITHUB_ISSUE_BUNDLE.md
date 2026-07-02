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
- publication gate `human_review_before_github_create`,
- `manual_publish_only = true`.

Reviewers must confirm that the draft uses sanitized metadata only, names a
focused test or readiness gate, can be closed by code, docs, tests, or a
documented blocked reason, and does not claim exam clearance, grading authority,
proctoring reliability, or AI-detection evidence.

## Public Contribution Rule

Contributors should work from synthetic tasks, source cards, public-safe tests,
and these issue drafts only. Exam deployment, official grading, proctoring, and
KI-detection use remain out of scope.
