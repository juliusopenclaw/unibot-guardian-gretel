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
