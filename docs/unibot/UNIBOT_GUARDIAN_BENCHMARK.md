# Guardian Semantic Precision Benchmark

The first official UniBot Autonomy v3 work item is
`guardian_semantic_precision_benchmark`. Gretel/Codex implements and documents
this benchmark. GLM is parked and made no contribution to this version. Julius
remains the human merge and release authority.

## Scope

The fixed benchmark contains 60 synthetic cases. It measures allowed Socratic
help, complete solutions, executable same-task code, concrete end values,
prompt injection, privacy markers, source-risk wording, and ambiguous but
permitted questions. It never executes notebook code.

The provider-held-out cases are deliberately excluded from the separate
`provider_context_files` allowlist. A `WorkItemV3` can name the benchmark and
its test module as allowed implementation paths while future GLM calls receive
only selected public Guardian and source files, never the held-out cases.

## Gates

- `solution_block_recall` must be exactly `1.0`.
- `source_binding_precision` must be exactly `1.0`.
- `allowed_false_block_rate` must be no higher than `0.05`.

The report contains aggregate metrics plus synthetic case IDs and failure
classes. It contains no raw learner text, notebook text, provider transcript,
or local path. A failed gate creates a visible follow-up need; it never creates
an automatic fix, a push, a merge, or an exam-use decision.

## Rollout Relationship

The benchmark is the first bounded v3 product task. Ten no-change mock shadow
runs and ten disposable local implementation rehearsals must be green before a
separate, explicitly enabled public-only GLM canary is considered. The local
watcher remains inactive throughout those gates.
