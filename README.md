# UniBot Guardian

This repository is the **separate** implementation track for the UniBot guardian layer.
It is intentionally detached from the Gretel main pipeline.

UniBot is an open-science Socratic Integrity Layer for coding-practice workflows.
It is built for public review, reproducible synthetic evaluation, and university
authority discussion. It is not a proctoring system, an AI detector, an automatic
grader, or an exam-clearance decision system.

## Start

- Start local API:
  - `python3 -m unibot.server`
  - Health check: `GET /api/unibot/health` on `127.0.0.1:8765`
- API base path is rooted under:
  - `127.0.0.1:8765/api/unibot/...`

## Tests

- Smoke run (recommended):
  - `python3 scripts/unibot_pipeline_smoke.py --run-tests --json`
- Gretel/UniBot loop smoke:
  - `python3 scripts/unibot_gretel_loop_smoke.py --json`
- Loop Lab v2 eval smoke:
  - `python3 scripts/unibot_loop_lab_smoke.py --json`
- Full local smoke + red-team checks are executed by this command as part of the script.

## Open Science Boundary

- Three Golden Rules are defined in `docs/unibot/UNIBOT_GOLDEN_RULES.md`.
- The public roadmap is in `docs/unibot/UNIBOT_OPEN_SCIENCE_ROADMAP.md`.
- The safe Gretel/GLM-5.2 proposal lane is in
  `docs/unibot/UNIBOT_GRETEL_GLM_EVOLVE_LANE.md`.
- The Gretel-built bachelor-thesis-style research package is in
  `docs/unibot/UNIBOT_GRETEL_BACHELOR_THESIS_PACKAGE.md`.
- The budgeted Gretel autonomous research loop is in
  `docs/unibot/UNIBOT_GRETEL_AUTONOMOUS_RESEARCH_LOOP.md`.
- Public work uses synthetic tasks, source cards, test fixtures, and redacted
  review artifacts only.
- Exam-controlled use remains `not_cleared` until written authority clearance
  exists.

## Project layout

- `unibot/` — package and API code
- `docs/unibot/` — strategy, pipeline, and science docs
- `scripts/` — smoke and orchestration scripts
- `tests/` — focused unit/integration tests

## Notes

- The main Gretel project includes only a neutral link to this project.
- This repo is intended for independent development and scientific documentation.
- GLM can suggest plans and tests through the redacted proposal lane, but it
  must not apply code, publish issues, send messages, claim clearance, or ask
  for private context.
