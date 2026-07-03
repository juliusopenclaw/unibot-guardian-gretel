# UniBot Feedback Triage

Status: public-safe maintenance queue, not exam evidence.

The feedback triage layer is implemented in `unibot.triage` and exposed through:

- `POST /api/unibot/demo-feedback/triage`
- `POST /api/unibot/demo-feedback/triage-markdown`

## Purpose

After a demo tester submits validated feedback, UniBot can create a public-safe
triage queue. The queue maps each failing or confusing demo scenario to a
component, priority, suggested test, and GitHub-style issue draft.

## Safety Boundary

Triage uses sanitized feedback metadata only. It does not include screenshots,
copied free text, emails, local paths, health or accommodation details, real exam
work, or raw private course text.

## Review-Board Claim Alignment

The generated triage report includes `claim_alignment` with the contract
`unibot-feedback-triage-release-review-board-claim-alignment-v1`. This keeps
sanitized feedback follow-up aligned with the GitHub issue bundle, publication
package, release runbook, review-board thesis/evaluation boundary, and public
safety gates.

The contract does not create issues, approve publication, recruit participants,
call providers, clear exam use, or approve a thesis submission. It only gives a
human reviewer traceable readiness and human-gate evidence.

## Priority Rules

- `P0`: blocked outcome or critical severity
- `P1`: fail outcome or major severity
- `P2`: confusing outcome
- `P3`: lower-priority follow-up

## Output

Each triage item includes:

- `triage_id`
- `feedback_id`
- `priority`
- `scenario_id`
- `component`
- `suggested_test`
- `issue_draft`
