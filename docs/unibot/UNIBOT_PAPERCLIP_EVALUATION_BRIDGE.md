# UniBot Paperclip Evaluation Bridge

Status: optional local-control-plane spike, not a runtime dependency.

## Purpose

Paperclip may be evaluated as a self-hosted multi-agent control board for
complex UniBot work streams. It can hold roles, tickets, budgets, and review
state. It must not become the UniBot browser-extension backend and must not
apply code, publish to GitHub, send messages, or execute provider calls without
explicit review.

## System Role

- UniBot Chrome Extension remains the Socratic Mantel: side panel, local API,
  output review, prompt card, ledger and receipts.
- GLM-5.2 remains a redacted proposal model through the Gretel GLM Evolve Lane.
- Paperclip is optional coordination around the project, not the source of
  scientific evidence and not an exam-security mechanism.

## Allowed Paperclip Roles

- GLM Proposal Reviewer
- Harness Engineer
- Extension QA
- Docs/Source-Card Reviewer

Each role may produce proposals, risk flags, test ideas, and documentation
notes. Codex and human review remain the apply and release gate.

## Bridge Contract

The local bridge is `paperclip_evaluation_bridge_v1`.

Input:

- redacted UniBot work-packet hash,
- public-safe goal,
- allowed public module/test names,
- budget class,
- review gate.

Output:

- ticket-id hash,
- agent role,
- status in `proposal_ready`, `blocked`, `needs_codex_review`, or `discarded`,
- cost class,
- proposal availability flag,
- safety flags proving no provider call, no autonomous apply, no private raw
  context, no external action, and no Final-Go.

## Blockers

The bridge blocks requests that make Paperclip a critical path, request browser
permissions, execute provider calls, share private context, request autonomous
apply, request external actions, or claim Final-Go.

## Sources

- Paperclip Website: https://paperclip.ing/
- Paperclip GitHub: https://github.com/paperclipai/paperclip
- Z.AI GLM-5.2 Docs: https://docs.z.ai/guides/llm/glm-5.2
- Z.AI Coding Plan Overview: https://docs.z.ai/devpack/overview
