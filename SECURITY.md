# Security Policy

## Supported Scope

UniBot Guardian is currently a local public-draft prototype. Security review
focuses on public-safety boundaries, data minimisation, local-only defaults,
and prevention of accidental publication of sensitive material.

## Please Report

- private or sensitive data appearing in public artifacts,
- raw model transcript leakage,
- local filesystem details appearing in API responses,
- credential leakage,
- unsafe claims of exam clearance, grading, proctoring, or AI detection,
- external actions that happen without explicit human approval.

## Please Do Not Include

Do not include real student data, private course material, health or
accommodation records, mailbox exports, credentials, or real exam work in a
public report. Use synthetic fixtures and redacted descriptions.

## Response Standard

Security-relevant reports should become one of:

- a public-safety regression test,
- a red-team scenario,
- a documentation boundary update,
- a release gate, or
- a documented blocked reason.

No automated system, model proposal, test, or review packet may grant exam
deployment clearance.
