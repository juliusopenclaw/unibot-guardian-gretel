# UniBot Gretel GLM Evolve Lane

Status: public-safe proposal lane, not autonomous development and not exam
release.

## Purpose

Gretel may use a redacted GLM-5.2 work packet to ask for architecture, harness,
documentation, and test proposals for UniBot. GLM is a reviewer and idea
generator only. Codex and a human reviewer remain responsible for applying code,
publishing artifacts, and deciding release scope.

## Contract

- Default model hint: `zai/glm-5.2`.
- Default status: `prepared_no_provider_call`.
- Allowed input: public UniBot docs, public-safe module and test names,
  synthetic scenarios, source-card identifiers, source URLs, aggregate test
  status, and non-private snippets.
- Blocked input: private course files, mailbox exports, real exam notebooks,
  solution keys, personal data, health or accommodation records, local
  filesystem details, credentials, raw model transcripts, and confidential
  Gretel case material.
- Allowed output: problem understanding, patch outline, test plan, risk flags,
  scientific-rigor notes, generalization rule, confidence, and blocked reason.
- Blocked output: direct apply, external send, GitHub publication, Final-Go,
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

The work packet contains only public-safe metadata and explicitly reports
whether a provider call happened. The default is no provider call.

## Provider Redaction Alignment

The generated lane includes `glm_provider_redaction_alignment`. It maps the GLM
source basis, redaction receipt, provider-call lock, proposal validation, and
apply/publish/Final-Go boundary to source cards, readiness checks, and human
review gates.

The alignment must remain `ready` before any public draft can describe the lane
as GLM-ready. It is still only a review aid: it does not authorize a provider
call, publish action, external send, code application, university submission, or
Final-Go.

## Review Rule

A proposal is blocked when it requests autonomous apply, raw private context,
Final-Go, external actions, or fails the public-safety scan. A proposal is also
blocked when required review fields are missing.
