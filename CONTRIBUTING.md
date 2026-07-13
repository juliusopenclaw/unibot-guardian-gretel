# Contributing to UniBot Guardian

Thank you for helping build a safer, source-grounded, open-science tutor layer.

Implementation and documentation are led by Gretel, an AI agent. GLM-5.2 may
propose or review a bounded public-safe change. Julius or another named human
reviewer remains responsible for merge, publication, ethics, legal assessment,
and any real submission. See `AUTHORS.md`.

## Scope

Good contributions include:

- public source cards and source-quality notes,
- synthetic evaluation tasks,
- red-team cases,
- public-safety and privacy tests,
- Socratic A0-A2 tutoring improvements,
- documentation, reproducibility, and release-gate improvements.

Do not contribute private course files, real exam work, raw model transcripts,
personal data, health or accommodation records, mailbox exports, local
filesystem details, credentials, or confidential Gretel case material.

## Standards

- Keep the three Golden Rules intact.
- Preserve student cognitive work; do not provide final solutions.
- Use source anchors for claims.
- State uncertainty and limitations.
- Add or update tests for behavior changes.
- Keep exam deployment status `not_cleared` unless written authority clearance
  exists and is reviewed outside the codebase.
- Model-generated ideas are proposals only until reviewed and tested.
- A work item must name a product or research delta. Receipt-only, hash-only,
  or readiness-only churn is not accepted unless it repairs a failing safety
  gate.
- Automated work is limited to one item and four candidate files per cycle.
- Automated changes use a `gretel/` branch and a draft pull request. They never
  merge themselves.

## Local Checks

Run:

```bash
python3 scripts/unibot_pipeline_smoke.py --run-tests --json
```

For focused changes, run the relevant `tests/test_unibot_*.py` file first, then
the smoke script before review.

## Pull Request Checklist

- Public-safety scan still passes.
- Red-team smoke still passes.
- No private data or real exam material was added.
- New behavior has a regression test or documented blocked reason.
- Documentation describes the boundary and limitations.
- No claim of proctoring, grading, AI detection evidence, accommodation
  decision, legal advice, or exam clearance was introduced.
- The pull request identifies Gretel, the model role, provider-call status,
  tests, remaining uncertainty, and the human decision required.
