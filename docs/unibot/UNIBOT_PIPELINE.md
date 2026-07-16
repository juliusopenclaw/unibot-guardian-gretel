# UniBot Guardian Pipeline

Status: separate track, not main pipeline.

## North Star

UniBot is a Socratic Integrity Layer around browser-based coding tools such as
Google Colab with Gemini, Jupyter AI, and Codex-like web tools. UniBot does not
claim to be a proctoring system, an AI detector, an automatic grader, or an
official disability-accommodation decision system.

## Product Modes

- `practice_overlay`: visible practice mantle over Colab/Gemini or Jupyter.
- `selftest_guardian`: private independence score, no grade.
- `exam_controlled`: blocked unless there is written approval from the relevant
  exam authority and a controlled AI channel or managed exam environment.

See also: [UniBot Colab/Gemini Mantle-Gateway Concept](./UNIBOT_COLAB_GEMINI_MANTLE_GATEWAY_CONCEPT.md)
for the current public-safe architecture and policy rationale.

## P0: Separate Project Boundary

- Keep UniBot files under `unibot/` and `docs/unibot/`.
- Do not edit `docs/brainstorm_to_pipeline.md` or other main-pipeline files for
  UniBot implementation work.
- Use public language: "beantragt" or "nicht offiziell freigegeben" until a real
  written approval exists.
- Hard non-goals: no proctoring, no AI detection as evidence, no automatic
  grading, no decision on Nachteilsausgleich, no health data processing without
  a clear legal/privacy basis.

## P1: Guardian MVP

- Generate Socratic Prompt Cards for external AI tools.
- Classify pasted external AI output before the learner uses it.
- Block final solutions, complete code fixes, inserted values, final
  interpretations, private data, and weak/false source claims.
- Store Help Ledger entries with raw-output hashes, classifications, help level,
  skill tags, and allowed hints; do not store raw external AI output by default.
- Keep the Independence Score private and formative.
- Expose the local-only JSON API:
  - `GET /api/unibot/health`
  - `POST /api/unibot/prompt-card`
  - `POST /api/unibot/review-output`
  - `POST /api/unibot/practice-flow`
  - `POST /api/unibot/notebook-template`
  - `POST /api/unibot/notebook/audit`
  - `POST /api/unibot/public-safety-scan`
  - `POST /api/unibot/materials/manifest`
  - `POST /api/unibot/materials/public-summary`
  - `POST /api/unibot/materials/validate`
  - `POST /api/unibot/course/intake-scan`
  - `POST /api/unibot/course/index/build`
  - `POST /api/unibot/course/exam-scope`
  - `POST /api/unibot/course/compiler-plan`
  - `POST /api/unibot/course/extraction-queue`
  - `POST /api/unibot/course/extraction-run-manifest`
  - `POST /api/unibot/course/extraction-decision-packet`
  - `POST /api/unibot/course/extraction-decision/validate`
  - `POST /api/unibot/course/extraction-operator-packet`
  - `POST /api/unibot/course/extraction-batch-plan`
  - `POST /api/unibot/course/extraction-batch-receipt-packet`
    accept `job_types: ["ocr"]` or `job_types: ["transcription"]` for OCR-first
    and video-separate planning.
  - `POST /api/unibot/course/private-extraction/run-batch`
  - `POST /api/unibot/course/video-transcription/run-batch`
  - `POST /api/unibot/course/extraction-receipt/validate`
  - `POST /api/unibot/course/extraction-receipts/append`
  - `POST /api/unibot/course/extraction-receipts/list`
  - `POST /api/unibot/course/extraction-receipts/summary`
  - `POST /api/unibot/course/extraction-review/validate`
  - `POST /api/unibot/course/extraction-review/apply-plan`
  - `POST /api/unibot/course/extraction-manifest/apply-dry-run`
  - `POST /api/unibot/course/tutor-index/dry-run`
  - `POST /api/unibot/course/tutor-index/respond-dry-run`
  - `POST /api/unibot/course/private-tutor-use-flow/dry-run`
  - `POST /api/unibot/exam-workspace/notebook-checkpoint/adapt`
  - `POST /api/unibot/exam-workspace/operator-run`
  - `POST /api/unibot/exam-workspace/run-dry-run`
  - `POST /api/unibot/exam-workspace/launch-flow/dry-run`
  - `POST /api/unibot/course/extraction-deferral/validate`
  - `POST /api/unibot/course/extraction-completion-report`
  - `POST /api/unibot/course/extraction-progress-report`
  - `POST /api/unibot/course/extraction-manifest-update-plan`
  - `POST /api/unibot/course/tutor-coverage-plan`
  - `POST /api/unibot/course/material-coverage/run`
  - `POST /api/unibot/course/study-session-plan`
  - `POST /api/unibot/course/study-session-receipt/validate`
  - `POST /api/unibot/course/study-session-review-report`
  - `POST /api/unibot/institutional-clearance/board`
  - `POST /api/unibot/institutional-clearance/validate`
  - `POST /api/unibot/institutional/profile`
  - `POST /api/unibot/institutional/presentation`
  - `POST /api/unibot/institutional/presentation-markdown`
  - `POST /api/unibot/stakeholder/submission-bundle`
  - `POST /api/unibot/stakeholder/submission-bundle-markdown`
  - `POST /api/unibot/stakeholder/decision-request`
  - `POST /api/unibot/stakeholder/decision-request-markdown`
  - `POST /api/unibot/stakeholder/decision-request/validate-receipt`
  - `POST /api/unibot/stakeholder/decision-journal/append`
  - `POST /api/unibot/stakeholder/decision-journal/append-prepared-request`
  - `POST /api/unibot/stakeholder/decision-journal/list`
  - `POST /api/unibot/stakeholder/decision-journal/summary`
  - `POST /api/unibot/stakeholder/decision-state`
  - `POST /api/unibot/stakeholder/decision-record-journal/append`
  - `POST /api/unibot/stakeholder/decision-record-journal/list`
  - `POST /api/unibot/stakeholder/decision-record-journal/summary`
  - `POST /api/unibot/tutor/respond`
  - `POST /api/unibot/tutor/next-task`
  - `POST /api/unibot/course/eval/run`
  - `POST /api/unibot/orchestration/command-center`
  - `POST /api/unibot/orchestration/command-center-markdown`
  - `POST /api/unibot/orchestration/context-packet`
  - `POST /api/unibot/orchestration/handoff/validate`
  - `POST /api/unibot/tasks/adaptive-plan`
  - `POST /api/unibot/ledger/append`
  - `POST /api/unibot/ledger/list`
  - `POST /api/unibot/ledger/summary`
  - `POST /api/unibot/ledger/public-summary`
  - `POST /api/unibot/redteam/run`
  - `POST /api/unibot/demo-run`
  - `POST /api/unibot/demo-run-markdown`
  - `POST /api/unibot/demo-feedback/template`
  - `POST /api/unibot/demo-feedback/validate`
  - `POST /api/unibot/demo-feedback/append`
  - `POST /api/unibot/demo-feedback/list`
  - `POST /api/unibot/demo-feedback/summary`
  - `POST /api/unibot/demo-feedback/public-summary`
  - `POST /api/unibot/demo-feedback/triage`
  - `POST /api/unibot/demo-feedback/triage-markdown`
  - `POST /api/unibot/github-issue-bundle`
  - `POST /api/unibot/github-issue-bundle-markdown`
  - `POST /api/unibot/authority-packet`
  - `POST /api/unibot/authority-packet-markdown`
  - `POST /api/unibot/evaluation-packet`
  - `POST /api/unibot/evaluation-packet-markdown`
  - `POST /api/unibot/evaluation-tasks`
  - `POST /api/unibot/pilot-protocol`
  - `POST /api/unibot/pilot-protocol-markdown`
  - `POST /api/unibot/data-protection-screening`
  - `POST /api/unibot/data-protection-screening-markdown`
  - `POST /api/unibot/review-board-packet`
  - `POST /api/unibot/review-board-packet-markdown`
  - `POST /api/unibot/publication-package`
  - `POST /api/unibot/publication-package-markdown`
  - `POST /api/unibot/readiness-check`
  - `POST /api/unibot/readiness-markdown`
  - `POST /api/unibot/gretel-glm-evolve/work-packet`
  - `POST /api/unibot/gretel-glm-evolve/validate-proposal`
  - `POST /api/unibot/gretel-glm-evolve/markdown`
  - `POST /api/unibot/release-runbook`
  - `POST /api/unibot/release-runbook-markdown`
  - `POST /api/unibot/compliance-matrix`
  - `POST /api/unibot/compliance-matrix-markdown`
  - `POST /api/exam/session/start`
  - `POST /api/exam/materials/import`
  - `POST /api/exam/materials/freeze`
  - `POST /api/exam/notebook/open`
  - `POST /api/exam/notebook/run-cell`
  - `POST /api/exam/tutor/respond`
  - `POST /api/exam/ledger/append`
  - `POST /api/exam/export-package`
- Run locally with `python3 -m unibot.server`.
- Public-safety scanning must block obvious private data, raw external AI
  transcript markers, local paths, secrets, and private course-material
  references before GitHub publication.
- Course materials use a separate local manifest. Private slides, captions,
  transcripts, notebooks, and exercise sheets stay local until permission,
  extraction status, review status, skill tags, source cards, and SHA evidence
  are explicit. Public summaries never expose local paths or raw private course
  text.
- The controlled exam workspace endpoint links a notebook-cell checkpoint,
  private tutor sidecar, Help-Ledger evidence, Study-Receipt validation, and an
  export receipt in one dry-run or locally confirmed run. It is technically
  shippable while still reminding the operator that real exam use remains
  `exam_deployment_status: not_cleared`.
- The material coverage run condenses local course-material metadata, extraction
  receipt evidence, private manifest status, hash-only tutor-index anchors, and
  notebook exercise readiness into one per-skill control report. It picks the
  next technical Exam-Workspace start point without exposing raw text, notebook
  code, local paths, or any exam clearance claim.
- The exam skill drilldown turns the per-skill coverage report into a selectable
  Python exam skill map. It marks the selected skill, shows OCR/video/source
  gaps, and prepares the dry-run operator action template without returning raw
  course text, raw query, notebook code, local paths, grading, proctoring, KI
  detection, or clearance claims.
- The Skill-to-Workspace live flow in the side panel uses that drilldown to
  prefill the Start Exam Workspace operator dry-run for the selected skill. It
  carries only skill tags, source-card/anchor counts, checkpoint-template
  metadata, Help-Ledger preview metadata, and explicit operator confirmations;
  dry-run remains the default.
- The Exam Workspace Session Console is the compact work surface after the live
  flow. It summarizes selected skill, workspace status, notebook checkpoint
  hash, A0-A2 tutor state, Help-Ledger preview, export receipt, open
  confirmations, and repeat dry-run receipt evidence without returning raw
  queries, course raw text, notebook code, local paths, grading, proctoring, KI
  detection, or clearance claims.
- The Run-History Export Review aggregates Session Console runs into a
  human-reviewable package: selected skills, checkpoint hashes, help-level
  profile, Help-Ledger preview metadata, blockers, operator-confirmation
  profile, export receipt, and reflection status. It is hash-only and remains
  `not_cleared`.
- The exam workspace launch flow turns that coverage-selected start point into
  a preconfigured dry-run: A2 query template, notebook cell checkpoint,
  source-anchor hint, Help-Ledger preview, and export receipt. It writes
  nothing by default and still returns no raw query, notebook code, private
  text, local paths, grading, proctoring, KI detection, or clearance claim.
- The notebook checkpoint adapter accepts a locally captured cell or hash-only
  checkpoint and returns only hashes, Study-Receipt validation, Help-Ledger
  preview, and optional hash-only journal evidence. Raw cells, notebook code,
  local paths, complete solutions, inserted values, and final interpretations
  never appear in the report.
- The Start Exam Workspace operator run merges material coverage, notebook
  checkpoint, A2 tutor state, Help-Ledger preview, export receipt, and explicit
  operator confirmations into one human-readable dry-run view. Each local write
  remains individually confirmed; the default receipt is dry-run and
  `not_cleared`.
- Course extraction queues are metadata-only planning artifacts for local OCR
  and video transcription. They include a rights/privacy gate and must not run
  extraction or expose raw OCR/transcript text before a written decision.
- Extraction decision packets define the minimum role-based rights/privacy
  decision record for local OCR/transcription. Validation hashes the written
  reference and authorizes only local private extraction, never exam deployment
  or public raw text release.
- Extraction operator packets turn a valid local-extraction decision into a
  private execution checklist and bounded job batch. They do not perform OCR or
  transcription. Receipt validation records job status, raw-text hash, character
  count, private artifact hash, and human-review state without publishing raw
  extracted text or local paths.
- Extraction batch plans turn all queued OCR/transcription work into stable,
  receipt-gated batches. They show counts, batch ids, expected receipts, missing
  receipts, and the next batch, but they remain plan-only and do not perform
  extraction or expose local paths.
- Extraction batch receipt packets turn one selected batch into receipt
  templates, operator steps, and a human-review checklist. They are still
  packet-only: no OCR, transcription, local paths, or raw extracted text.
- Private extraction runs are the first local-only execution harness. After a
  valid rights/privacy decision, they can extract text from supported DOCX,
  text-PDF, and PPTX containers into private local artifacts and append
  hash-only receipts. Public reports expose only adapter counts, job ids,
  hashes, character counts, and review state; raw text and local paths are
  never returned. Image-only PDFs and videos still require separate approved
  local adapters.
- Extraction progress reports aggregate receipt batches into a human review
  queue and private manifest-update candidates. They are the gate between local
  private OCR/transcription receipts and reviewed course-tutor metadata.
- Extraction receipt journals persist accepted extraction receipts as local
  JSONL with hashes, counts, job ids, material ids, and review state only. They
  let progress, batch, manifest, coverage, and study APIs consume
  `receipt_journal_path` without exposing raw OCR text, transcripts, private
  artifact references, or local paths.
- Extraction human-review apply plans accept individual hash-only reviewer
  decisions for ready receipts. Accepted items append a new
  `reviewed_for_private_tutor` receipt plus a hash-only review record, then
  produce private manifest-update and tutor-coverage previews. They do not
  write manifests, start tutor indexing, return raw review notes, expose local
  paths, or clear exam deployment.
- Private manifest apply dry-runs are the controlled write gate after human
  review. They compute a metadata delta, projected ExamScopeMap, and
  Tutor-Coverage preview. A local private manifest is written only with
  `operator_confirmed_manifest_apply: true`; the route still never writes raw
  OCR/transcript text, exposes local paths, starts tutor indexing, or clears
  exam deployment.
- Extraction deferral validation and completion reports make the final
  extraction gate explicit. Completion can be shown by no queued jobs, reviewed
  receipts for every queued job, failed/skipped receipts where appropriate, or
  a role-reviewed intentional deferral record. Deferral is not extraction, not
  tutor indexing, not public release permission, and not exam clearance.
- Extraction manifest update plans convert reviewed receipts into private
  tutor manifest metadata candidates. They do not write files and they do not
  contain raw OCR text, raw transcripts, local paths, grades, or exam decisions.
- Tutor coverage plans forecast current and projected ExamScopeMap skill
  readiness after reviewed private manifest candidates are applied. They are
  forecast-only and help prioritize remaining course-material gaps.
- Study session plans turn reviewed tutor anchors into retrieval-first,
  notebook-close practice with reflection, spacing, and A0-A2 help boundaries.
  They are practice-only and do not grade, solve, proctor, or publish raw
  course text.
- Study session receipts validate one completed learning task as hash-only
  evidence: prediction, retrieval response, smallest notebook action, source
  anchor, help level, and reflection. They block missing evidence, forbidden
  raw/private fields, and A6/final-solution exposure; raw student text is not
  stored.
- Study session review reports aggregate those receipts into a human-reviewable
  evidence profile. They can show help-level patterns, source anchors,
  blocked repeats, and missing receipts, but they must not grade, rank, run AI
  detection, or claim an Eigenleistung percentage.
- Institutional clearance boards define the human decision lanes for public
  draft, local private extraction, formative pilot, and the future controlled
  exam gateway. Validation checks role coverage, scope-safe modes, A0-A2 help
  limits, and anti-proctoring/anti-detection/anti-grading clauses. It stores
  only a hash of the written reference and never switches real exam deployment.
- Stakeholder submission bundles combine the two remaining external gates into
  human-reviewable decision lanes: rights/privacy for local extraction and
  written authority review for a future controlled exam gateway. They include
  validator endpoints, record templates, evidence summaries, message drafts,
  and must-not-claim lists. They do not send anything or claim approval.
- Stakeholder decision requests select exactly one submission lane and produce
  a public-safe manual review packet, Markdown review export, and receipt
  template. Receipt validation stores only hashes and manual-submission status;
  it does not authorize extraction, accept a written decision, send messages, or
  clear exam use.
- Stakeholder decision journals store local JSONL process evidence for prepared
  requests and validated manual request receipts. They store hashes, statuses,
  lane ids, and summary counts only. They do not store mail text, written
  decision text, personal names, raw course material, or local course paths, and
  they do not authorize extraction or exam deployment.
- External decision-state packets validate incoming written decision records and
  derive next gates without storing raw decision text. They can show local
  extraction as authorized by record and exam clearance as formally valid while
  still keeping `exam_deployment_status` at `not_cleared` until a deliberate
  manual deployment switch exists.
- External decision-record journals persist validated incoming written decision
  records as local hash-only evidence. They store scope metadata, validation
  status, reviewer-role coverage, decision-reference hashes, and gate flags
  only. They do not store raw written decisions, send requests, record personal
  contact data, or switch exam deployment. Completion audit can consume
  `decision_record_journal_path` as human-reviewable evidence for the extraction
  deferral and exam-authority gates.
- The private text-container extraction runner can also consume
  `decision_record_journal_path` for the local-extraction gate. This lets
  OCR-first Batch 1 run from an accepted hash-only journal record without
  resending raw decision text. Receipts still go through the local hash-only
  receipt journal and human review before tutor indexing.
- The local extraction decision intake endpoints
  `/api/unibot/course/extraction-decision/local-intake` and
  `/api/unibot/course/extraction-decision/local-intake/record` are the operator
  bridge from a written rights/privacy decision to the OCR-first workflow. They
  expose the decision template, validate/store only hash-only journal evidence,
  and summarize OCR readiness plus Progress/Manifest/Tutor-Coverage status from
  the receipt journal.
- The local Decision-Record workspace endpoints
  `/api/unibot/course/extraction-decision/workspace/prepare` and
  `/api/unibot/course/extraction-decision/workspace/record` create the
  `~/.unibot_guardian` operator workspace: generated JSON template, hash-only
  manifest, decision/receipt journal targets, and a dry-run receipt proving
  whether OCR-first Batch 1 is start-ready. These routes do not run OCR and do
  not return raw decisions, raw course text, or local paths.
- The controlled OCR-first operator endpoint
  `/api/unibot/course/ocr-first/operator-run` is the preferred Batch-1 run
  harness. It checks the dry-run receipt first, requires explicit operator
  confirmation, executes only the planned OCR Batch-1 job ids, writes hash-only
  receipts, and immediately returns Progress/Manifest/Tutor-Coverage summaries
  from the receipt journal.
- Adaptive tasks are generated from local skill-state signals and reviewed
  material metadata. They contain micro-goals, Socratic checks, expected student
  artifacts, and help policies, but no final solutions, no official grading,
  and no raw private course material.
- Help Ledger storage defaults to `~/.unibot_guardian/help_ledger.jsonl`, stays
  local-only, stores raw external AI output only as a hash, and redacts
  reflections if they contain private or sensitive markers.
- Source Cards are available both as documentation and through the local API:
  - `POST /api/unibot/source-cards`
  - `POST /api/unibot/source-card`
  - `POST /api/unibot/source-card-drift-report`
  - `POST /api/unibot/gretel-loop/run`
  - `POST /api/unibot/gretel-glm-evolve/work-packet`
  - `POST /api/unibot/gretel-glm-evolve/validate-proposal`
  - `POST /api/unibot/loop-lab/run`
- Practice notebooks are generated as public-safe `.ipynb` payloads with fixed
  cells for Ziel, Vorhersage, eigener Versuch, Fehler, Quellencheck,
  Gemini/Colab-Promptkarte, UniBot Postfilter, Reflexion, and Help-Ledger. Code
  cell outputs are empty, and raw external AI transcripts are never embedded.
- Red-Team Smokes must run before authority demos or public release. Required
  checks cover solution leakage, privacy leakage, source risk, not-cleared
  `exam_controlled`, A6 repeat-task behavior, notebook audit failure, public
  leakage, ledger redaction, and allowed low-level Socratic hints.
- Local demo runs provide a step-by-step practice test script for the user:
  setup, prompt card, postfilter, ledger, adaptive tasks, notebook handoff, and
  red-team smoke. The demo is public-safe and practice-only, not exam clearance.
- Demo feedback uses a local public-safe issue contract. Unsafe or incomplete
  feedback is blocked and not stored. Public summaries contain counts by
  scenario, outcome, and severity, but no screenshots, copied free text, private
  data, real exam work, or raw private course text.
- The browser side panel exposes Demo-Feedback validation and local storage
  actions. Offline validation can flag obvious issues, but storage requires the
  local UniBot API.
- Demo feedback triage converts sanitized feedback metadata into priorities,
  components, suggested tests, and public-safe GitHub-style issue drafts.
- GitHub issue bundles collect those drafts into a manual-review package for
  public collaboration. They do not publish automatically and remain public-safe.
- Release runbooks provide a public quickstart, contributor rules, release
  gates, troubleshooting, and public-language rules. They are a GitHub
  collaboration guide, not an exam-release permission.
- Compliance matrices connect source cards to product rules, controls, blocked
  uses, reviewers, and verification evidence. They are authority-review drafts,
  not legal advice or exam clearance.
- Authority handoff packets must compile product boundary, modes, non-goals,
  data flow, review questions, source cards, notebook audit, ledger public
  summary, and red-team status without private data or raw external KI outputs.
- Orchestration command-center packets define the canonical UniBot hub, role
  lanes for parallel chats, the handoff contract, sprint order, material queue
  counts, source-evidence basis, and acceptance gates. They are coordination
  artifacts, not authority approval.
- Evaluation packets must provide a public-safe master-thesis pilot scaffold:
  synthetic tasks, codebook, formative measures, consent boundaries, stop rules,
  data-management limits, quality gates, and source cards. They must not include
  real exam data, grades, medical/accommodation personal data, raw external KI
  outputs, or private course material.
- Pilot protocols must provide participant information, consent checklist,
  data-management plan, ethics review triggers, session flow, stop rules, and
  readiness gates before any real participant study.
- Data-protection screenings must provide processing principles, processing
  activities, risk register, open Datenschutz decisions, and review gates. They
  are planning drafts, not Datenschutz approval.
- Publication packages must provide a System Card, Data Card, limitations,
  release gates, included/excluded artifact groups, and collaboration note for a
  public GitHub-style draft. Release-ready means public-safe draft only, never
  exam deployment or official clearance.
- Review board packets compile reviewer-specific evidence packets, open decision
  lists, and cross-cutting red lines for internal authority review.
- Institutional clearance boards sit one step after the review board: they make
  scope-specific written decisions machine-checkable while keeping the default
  `exam_deployment_status` at `not_cleared`.
- Readiness checks aggregate public-safety scan, red-team, publication gates,
  review board packet, evaluation packet, authority handoff, notebook audit, source cards, course
  material policy, adaptive task plan, local demo run, demo feedback contract,
  GitHub issue bundle, release runbook, compliance matrix, pilot protocol,
  data-protection screening, and exam boundary. `public_draft_ready` means ready
  for public draft review and local practice demo only, not exam deployment.
- Gretel loop smokes simulate public-safe exam rehearsal with a DeepSeek-compatible
  student agent. The default mode is deterministic mock-first; live Gretel,
  live UniBot, and live DeepSeek are explicit opt-ins. Reports use artifact type
  `unibot_gretel_exam_loop_report`, cite the Golden Rules, store raw external AI
  output only as hashes, and block final solutions, private data, and
  exam-controlled external AI without written approval.
- Loop Lab v2 scales the Gretel loop into a 25-case eval dataset with graders,
  run-history, regression checks, and public-safe backlog items. It uses artifact
  type `unibot_loop_lab_report_v2`; GR1/GR2/GR3 remain hard gates, and persisted
  reports under `.unibot_loop_runs/` must pass public-safety scanning before
  storage.

## Pipeline Execution

Badgyal can use one concrete handoff command to run this track from the repo root:

- `python3 scripts/unibot_pipeline_smoke.py`
- `python3 scripts/unibot_pipeline_smoke.py --json` for machine-readable output.
- `python3 scripts/unibot_pipeline_smoke.py --run-tests` to include the full `tests/test_unibot_*.py` suite.
- `python3 scripts/unibot_pipeline_smoke.py --run-tests --json` for machine-readable combined report.
- `python3 scripts/unibot_gretel_loop_smoke.py --json` to run the standalone
  Gretel/UniBot/DeepSeek-compatible loop gate.
- `python3 scripts/unibot_loop_lab_smoke.py --json` to run the 25-case Loop Lab
  v2 evaluation suite.
- `python3 scripts/unibot_loop_lab_smoke.py --json --persist` to store a
  public-safe local history run and enable regression comparison.
- Optional live transports: add `--gretel-url http://127.0.0.1:4173`,
  `--unibot-url http://127.0.0.1:8765`, or `--deepseek-live` with
  `DEEPSEEK_API_KEY`. Do not use live DeepSeek with real exam, private course,
  email, health, accommodation, or local-path data.

The smoke run checks the full local API path (prompt card, postfilter, practice
flow), notebook generation/audit, source-card coverage, red-team outcome,
readiness gate, publication gate, Gretel loop contract, Loop Lab v2 contract,
and review-board packet contract.

## P1: Browser Mantel Spike

- Provide a Chrome Manifest V3 extension under `unibot/browser_extension/`.
- Use a content script to show a visible practice banner and read user-selected
  text from Colab/Jupyter pages.
- Use the side panel for prompt cards, pasted AI-output review, help level, and
  reflection.
- Show adaptive practice tasks in the side panel by sending local skill-state
  signals to `POST /api/unibot/tasks/adaptive-plan`; if the local API is not
  reachable, show a simple offline practice-only fallback.
- Let the user copy a generated notebook JSON template from the side panel and
  save it as `.ipynb` for Colab/Jupyter practice.
- Prefer the local UniBot API at `127.0.0.1:8765`; if it is not running, keep a
  visible offline fallback so the user can still copy prompt cards and review
  obvious high-risk output.
- Document the technical limit: a normal MV3 extension cannot be treated as hard
  exam security. If DOM access breaks or permissions are insufficient, the flow
  falls back to copy/paste review.

## P2: Exam-Ready Variant

- Build the controlled AI channel through UniBot or a managed local Jupyter
  environment as a technical artifact; real written approval remains a visible
  real-world reminder before actual exam deployment.
- Ensure raw model output is filtered before display.
- Prepare and review the authority packet with Pruefungsamt, Inklusionsbuero,
  Datenschutz, IT/SZI, and module owners before any exam-controlled use.

## Badgyal Work Rule

Badgyal may work on this track only when the task explicitly says "UniBot
separat" or references files under `unibot/` or `docs/unibot/`.
