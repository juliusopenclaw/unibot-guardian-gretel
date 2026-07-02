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
