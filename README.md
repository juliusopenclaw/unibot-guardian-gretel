# UniBot Guardian

This repository is the **separate** implementation track for the UniBot guardian layer.
It is intentionally detached from the Gretel main pipeline.

UniBot is an open-science Socratic Integrity Layer for coding-practice workflows.
It is built for public review, reproducible synthetic evaluation, and university
authority discussion. It is not a proctoring system, an AI detector, an automatic
grader, or an exam-clearance decision system.

Implementation and documentation are led by **Gretel, an AI agent**. GLM-5.2
is currently parked and made no contribution to this v3 foundation; a later
explicitly enabled public-only run may use it only for redacted proposals and
independent reviews. Human reviewers retain merge, publication, ethics, legal,
and real-submission authority. The
full provenance statement is in `AUTHORS.md`.

## Start

- Install for development: `python3 -m pip install --upgrade 'pip>=26.1.2'` and
  `python3 -m pip install -e '.[dev,glm,gateway]'`
- Install the local Mac companion: `unibot companion install`
- Diagnose the local installation without exposing paths or learner data:
  `unibot companion diagnose`
- The installation copies the public runtime into macOS Application Support;
  moving the Git checkout does not change the native-host import path. A
  Developer-ID-signed and notarized bundled interpreter remains a later human
  release requirement.
- In Chrome, load `unibot/browser_extension` as an unpacked extension for the
  public alpha. Its fixed alpha ID is bound to the installed native host.
- Create a reviewable MV3 package without the rest of the repository:
  `unibot extension package --output ./unibot-mantle.zip`
- Create the public extension plus institutional review handoff:
  `unibot release candidate --output ./unibot-review-candidate`
- Verify a candidate's files, hashes, public-safety fields, and source commit
  without changing anything:
  `unibot release audit ./unibot-review-candidate`
- Open `~/Applications/UniBot Companion.app` or click the extension and start a
  fixed or adaptive A0-A4 learning session.
- Start the paired local API: `unibot serve --pair`
- Import a public notebook: `unibot notebook import <https-url-or-local-file>`
- Prepare the institutional review profile: `unibot institution profile`
- Create the compact presentation packet: `unibot institution presentation --markdown`
- Write a hash-bound, public-safe handoff directory:
  `unibot institution bundle --output ./unibot-institution-review`
- Inspect the autonomous lane: `unibot autonomy preflight`
- Health check for the developer API: `GET /api/v2/health` on the selected
  loopback port. Port `8765` remains the CLI default but is not used by the
  Chrome companion transport.
- API base path is rooted under:
  - `127.0.0.1:8765/api/v2/...`
- Legacy `/api/unibot/...` routes remain available for one alpha compatibility
  cycle but require the same local session token over HTTP.

The production-facing alpha extension communicates through Chrome Native
Messaging. It does not store a loopback token or depend on a hard-coded port.
Notebook cell, task, and learner-attempt text stay in process memory; local
session files and voluntary exports contain metadata and hashes only.

## Tests

- Smoke run (recommended):
  - `python3 scripts/unibot_pipeline_smoke.py --run-tests --json`
- Gretel/UniBot loop smoke:
  - `python3 scripts/unibot_gretel_loop_smoke.py --json`
- Loop Lab v2 eval smoke:
  - `python3 scripts/unibot_loop_lab_smoke.py --json`
- Full local smoke + red-team checks are executed by this command as part of the script.
- Focused Mantle 2.1 checks: `python3 -m pytest tests/test_unibot_mantle_v21.py -q`
- Browser interaction checks: `npm run test:browser`
- Headed MV3 package check: `npm run test:extension-package`
- Real macOS Google Chrome canary with the installed local Companion:
  `UNIBOT_CHROME_EXECUTABLE=/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome npm run test:chrome-canary`
- The release-candidate bundle records a clean Git commit hash and refuses to
  build from a dirty working tree. It is still a public-draft handoff, not a
  merge, publication, institutional approval, or exam release.

## Open Science Boundary

- Three Golden Rules are defined in `docs/unibot/UNIBOT_GOLDEN_RULES.md`.
- The public roadmap is in `docs/unibot/UNIBOT_OPEN_SCIENCE_ROADMAP.md`.
- The safe Gretel/GLM-5.2 proposal lane is in
  `docs/unibot/UNIBOT_GRETEL_GLM_EVOLVE_LANE.md`.
- The Gretel-built bachelor-thesis-style research package is in
  `docs/unibot/UNIBOT_GRETEL_BACHELOR_THESIS_PACKAGE.md`.
- The budgeted Gretel autonomous research loop is in
  `docs/unibot/UNIBOT_GRETEL_AUTONOMOUS_RESEARCH_LOOP.md`.
- The local-first v3 controller, rollout gates, and human merge boundary are in
  `docs/unibot/UNIBOT_AUTONOMY_V3.md`.
- The active v2 policy and product queue are in
  `docs/unibot/UNIBOT_AUTONOMY_V2.md` and `unibot/autonomy_work_items.json`.
- The local companion, A0-A4 contract, report semantics, and known browser
  boundary are documented in `docs/unibot/UNIBOT_MANTLE_V21.md`.
- The human-review packet for Prüfungsamt and Inklusionsbüro is documented in
  `docs/unibot/UNIBOT_REGULATORY_PROFILE_V1.md`.
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
- GLM can suggest plans and tests through the redacted proposal lane. Gretel
  applies reviewed changes in an isolated branch; neither system may merge,
  claim clearance, or request private context.
