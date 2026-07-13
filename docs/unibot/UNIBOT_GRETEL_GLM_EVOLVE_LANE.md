# UniBot Gretel GLM Evolve Lane

Status: active public-safe proposal and independent-review lane; not exam
release and not autonomous merge.

## Purpose

Gretel may use a redacted GLM-5.2 work packet to ask for architecture, harness,
documentation, and test proposals for UniBot. Gretel applies a validated
proposal locally through Codex automation. GLM then performs an independent
review. A human remains responsible for merge, release, ethics, legal review,
and real submission.

## Contract

- Default model hint: `zai/glm-5.2`.
- Official SDK pin: `zai-sdk==0.2.3`.
- Provider scope: `public-unibot-only`.
- Provider calls: at most two per work item, 60,000 combined input tokens,
  8,192 combined output tokens, and 20 USD per month.
- Credentials: dedicated macOS Keychain item only.
- Allowed input: public UniBot docs, public-safe module and test names,
  synthetic scenarios, source-card identifiers, source URLs, aggregate test
  status, and non-private snippets.
- Blocked input: private course files, mailbox exports, real exam notebooks,
  solution keys, personal data, health or accommodation records, local
  filesystem details, credentials, raw model transcripts, and confidential
  Gretel case material.
- Allowed output: problem understanding, patch outline, test plan, risk flags,
  scientific-rigor notes, generalization rule, confidence, and blocked reason.
- Blocked output: direct apply, external send, GitHub push or merge, Final-Go,
  exam-clearance claims, or requests for private context.

## Scientific Standard

Every accepted GLM idea must become one of:

- a regression test,
- a red-team scenario,
- a source-card or documentation improvement,
- a review-board/open-decision entry, or
- a documented blocked reason.

This keeps recursive self-improvement testable instead of aesthetic. A proposal
that cannot be verified stays a note, not a system change.

## Interfaces

- `POST /api/unibot/gretel-glm-evolve/work-packet`
- `POST /api/unibot/gretel-glm-evolve/validate-proposal`
- `POST /api/unibot/gretel-glm-evolve/markdown`
- `unibot autonomy preflight`
- `unibot autonomy run --stage proposal --provider-go public-unibot-only`
- `unibot autonomy run --stage review --provider-go public-unibot-only`

The v1 work packet remains compatible. Autonomy v2 additionally builds context
only from selected files already tracked by Git, validates `GLMProposalV1` and
`GLMReviewV1`, and stores hash-only local run summaries. No ready product work,
missing Keychain material, a stale price source, a leak finding, or an exhausted
budget stops before a provider call.

## Provider Redaction Alignment

The generated lane includes `glm_provider_redaction_alignment`. It maps the GLM
source basis, redaction receipt, provider-call lock, proposal validation, and
apply/publish/Final-Go boundary to source cards, readiness checks, and human
review gates.

Proposal-packet and provider-lock hashes are also linked to the harnessed
local-cycle operator workspace-card readiness gate. The public alignment keeps
only metadata, hashes, source-card IDs, readiness state, and human gates; it
does not return raw workspace-card data, raw private context, provider prompts,
contact data, local paths, or exam artifacts.

The alignment must remain `ready` before any public draft can describe the lane
as GLM-ready. It is still only a review aid: it does not authorize a provider
call, publish action, external send, code application, university submission, or
Final-Go.

## Review Rule

A proposal is blocked when it requests autonomous apply, raw private context,
Final-Go, external actions, or fails the public-safety scan. A proposal is also
blocked when required review fields are missing.
