# UniBot Adaptive Tasks

Status: practice-only task generation, not grading.

The adaptive task layer is implemented in `unibot.adaptive_tasks` and exposed
through:

- `POST /api/unibot/tasks/adaptive-plan`

The browser side panel includes an `Uebungsaufgaben erzeugen` action that calls
this endpoint with locally inferred skill-state signals. If the API is offline,
the side panel shows a minimal practice-only fallback.

## Purpose

When the Help Ledger or local session state suggests a learning gap, such as
`python_lists`, `pandas`, `boxplots`, or `debugging`, UniBot should recommend
small follow-up tasks. The goal is to restore the learner's own next step, not
to generate a solution.

## Inputs

- local `skill_state`
- reviewed material metadata from the course-material manifest
- synthetic fallback templates

## Output

Each task includes:

- `skill_tag`
- `difficulty`
- `micro_goal`
- `task_prompt`
- `socratic_checks`
- `expected_student_artifacts`
- `source_reference`
- `help_policy`

## Boundaries

The plan is practice-only. It does not create grades, exam judgments, AI
detection evidence, or accommodation decisions. Public plans use only public-safe
material summaries and synthetic task text. Private course content remains local
and is referenced only by metadata and hashes.

## Source Boundary Alignment

Public adaptive plans include a `source_boundary_alignment` block. It checks
that task source references are either public-summary material IDs or synthetic
fallbacks, that private course material remains excluded, and that each task
preserves learner agency through predictions, smallest own attempts, reflection,
and help-level logging.

The alignment names readiness checks, source-card IDs, and human gates. It is a
review aid only. It does not authorize private course text, local paths, exam
material, student data, grading, or exam deployment.
