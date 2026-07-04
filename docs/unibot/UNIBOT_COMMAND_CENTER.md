# UniBot Command Center

Status: public-safe coordination draft, not exam clearance.

## Purpose

The command center is the project-management layer for parallel UniBot chats.
It keeps one canonical implementation hub, stable role lanes, a handoff
contract, material queue status, source-evidence status, and acceptance gates.

Older chats and workbench artifacts are treated as evidence inputs. They do not
become parallel source-of-truth implementations. Every implementation slice
returns through the local UniBot hub and must leave a public-safe handoff.

The command center also carries a workspace-card route alignment. Role lanes,
active harness routes, scope status, and the no-clearance deployment line are
linked to the harnessed local-cycle operator workspace-card readiness gate
through hashes only. The alignment preserves operator-prefill evidence without
exposing raw workspace data, private course text, contact data, local paths,
provider prompts, notebook code, or exam artifacts.

## Golden Rules

- PM-GR1 Generalisieren: useful case work becomes reusable UniBot capability.
- PM-GR2 Harness Engineering: important workflows need runnable checks,
  metrics, logs, and regression coverage.
- PM-GR3 Recursive Self-Improvement: recurring failures become tests, rubrics,
  prompts, metrics, or backlog tasks.

Safety rules remain active at the same time:

- GR1 no final solution, complete code fix, inserted values, or final
  interpretation.
- GR2 no private data, raw external AI transcript, local path, secret, or raw
  private course text in public artifacts.
- GR3 preserve own attempt, next step, reflection, help level, and source
  boundary without automatic grading.

## Role Lanes

- `policy_basis`: source cards, authority rationale, non-goals.
- `course_material_pipeline`: local material review queues and source-card
  inputs.
- `exam_gateway`: A0-A2 gateway, freeze, notebook, ledger, export.
- `tutor_rag`: source-grounded course tutor and exam-scope map.
- `ui_gretel_orbit`: notebook main stage, tutor sidecar, ledger/status layer.
- `qa_redteam`: smoke, unit, red-team, loop, public-safety regression checks.
- `stakeholder_packet`: review-board packet for institutional stakeholders.

## Handoff Contract

Every chat hands back:

- `role_id`
- `goal`
- `changed_files`
- `tests`
- `risks`
- `evidence`
- `next_step`

External live actions require explicit Julius-Go or Final-Go. Real exam use
stays blocked until written authority clearance exists.

## API

- `POST /api/unibot/orchestration/command-center`
- `POST /api/unibot/orchestration/command-center-markdown`
- `POST /api/unibot/orchestration/context-packet`
- `POST /api/unibot/orchestration/handoff/validate`
- `POST /api/unibot/completion-audit`
- `POST /api/unibot/course/extraction-queue`
- `POST /api/unibot/course/extraction-run-manifest`
- `POST /api/unibot/course/extraction-decision-packet`
- `POST /api/unibot/course/extraction-decision/validate`
- `POST /api/unibot/course/extraction-decision/local-intake`
- `POST /api/unibot/course/extraction-decision/local-intake/record`
  provide the local rights/privacy Decision-Record intake path. The intake
  packet exposes the template, hash-only journal gate, OCR-first readiness,
  receipt-journal status, and post-run report status without raw decisions,
  raw course text, or local paths.
- `POST /api/unibot/course/extraction-decision/workspace/prepare`
- `POST /api/unibot/course/extraction-decision/workspace/record`
  prepare the local `~/.unibot_guardian` Decision-Record workspace. The
  workspace writes a JSON template plus hash-only manifest, validates or records
  the decision into the hash-only journal, and returns a dry-run receipt showing
  whether OCR-first Batch 1 would be start-ready. It never starts OCR by itself.
- `POST /api/unibot/course/ocr-first/operator-run`
  is the controlled Batch-1 execution path. It checks the current workspace
  dry-run receipt, requires `operator_confirmed_dry_run: true` before private
  OCR starts, writes hash-only receipts, and returns Progress/Manifest/Tutor
  Coverage summaries without raw text or local paths.
- `POST /api/unibot/course/extraction-operator-packet`
- `POST /api/unibot/course/extraction-batch-plan`
- `POST /api/unibot/course/extraction-batch-receipt-packet`
  accept `job_types: ["ocr"]` or `job_types: ["transcription"]` for OCR-first
  and video-separate planning.
- `POST /api/unibot/course/private-extraction/run-batch`
  accepts `job_types: ["ocr"]`, `receipt_journal_path`, and
  `decision_record_journal_path` so OCR-first Batch 1 can run from a previously
  accepted hash-only local-extraction decision record without returning raw
  decision text, raw OCR text, or local paths.
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
- `POST /api/unibot/exam-workspace/session-console`
- `POST /api/unibot/exam-workspace/run-history-export-review`
- `POST /api/unibot/exam-workspace/run-dry-run`
- `POST /api/unibot/exam-workspace/launch-flow/dry-run`
- `POST /api/unibot/course/extraction-deferral/validate`
- `POST /api/unibot/course/extraction-completion-report`
- `POST /api/unibot/course/extraction-progress-report`
- `POST /api/unibot/course/extraction-manifest-update-plan`
- `POST /api/unibot/course/tutor-coverage-plan`
- `POST /api/unibot/course/material-coverage/run`
- `POST /api/unibot/course/exam-skill-drilldown`
- `POST /api/unibot/course/study-session-plan`
- `POST /api/unibot/course/study-session-receipt/validate`
- `POST /api/unibot/course/study-session-review-report`
- `POST /api/unibot/institutional-clearance/board`
- `POST /api/unibot/institutional-clearance/validate`
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

The readiness check includes the command center. A green command center means
the project can be orchestrated efficiently; it does not mean the exam mode is
approved.

The side panel now exposes a Skill-to-Workspace dry-run action: it uses the
Exam-Skill-Drilldown selected skill to prefill the Start Exam Workspace operator
run with A0-A2, checkpoint-template metadata, source-card metadata, Help-Ledger
preview metadata, and individual operator confirmations. It remains dry-run by
default and `not_cleared`.

The Session Console is the next work surface: it keeps the selected skill,
workspace state, checkpoint hash, tutor state, Help-Ledger preview, export
receipt, and open confirmations visible across repeated dry-runs for the same
skill while staying hash-only and `not_cleared`.

The Run-History Export Review turns those repeated dry-runs into a
human-reviewable package with checkpoint hashes, help-level profile, blockers,
operator-confirmation profile, export receipt, and reflection status. It is not
a grade, not proctoring, not detection, and not exam clearance.

The completion audit is stricter than readiness. It may report
`public_draft_ready` while keeping `goal_complete` false when technical course
extraction queues are still open. Written real-world exam clearance is tracked
as a reminder, not as a technical delivery blocker.

The extraction queue is also stricter than the compiler plan. It creates
metadata-only OCR/transcription jobs and keeps them blocked until a rights and
privacy decision exists.

The extraction decision packet is the next gate. It validates a role-based
decision record, stores only a hash of the written reference, and authorizes
local private OCR/transcription only. It is not Datenschutz approval, legal
advice, exam clearance, or public release permission.

The extraction operator packet is the execution harness for after that decision.
It remains metadata-only and gives a private checklist, bounded job batch, and
receipt contract. Receipt validation proves local-private extraction evidence
through hashes and review status, not through raw transcript or OCR text.

The extraction batch plan is the project-manager work queue for the same phase.
It groups all queued OCR/transcription jobs into stable receipt-gated batches,
shows missing receipt counts, and points to the next batch. It does not run OCR,
transcribe video, or expose local paths.

The extraction batch receipt packet turns the selected batch into exact receipt
templates, local operator steps, and a human-review checklist. It is the handoff
between planning and local private execution, but still contains no raw text,
transcripts, or local paths.

The private extraction runner is the first controlled local execution harness.
It currently supports DOCX, text-PDF, and PPTX containers after a valid local
extraction decision, writes raw text only to private local artifacts, and
appends hash-only receipts for human review. It does not support video
transcription, image-only PDF OCR, public release, or automatic tutor indexing.

The extraction progress report aggregates receipt batches into human-review
queues and private manifest-update candidates. It keeps extracted raw text out
of public artifacts while making missing, duplicate, invalid, pending, and
reviewed receipt state visible to the project manager.

The extraction receipt journal is the durable handoff between local private
operator work and project management. It stores accepted receipt evidence as
hash-only local JSONL and can feed progress, batch, manifest, tutor coverage,
and study APIs through `receipt_journal_path`. It does not store raw OCR text,
transcripts, private artifact references, local paths, or authority decisions.

The extraction human-review apply plan is the missing control point after OCR
receipts and before tutor metadata. It records reviewer decisions hash-only,
can append `reviewed_for_private_tutor` receipts for accepted items, and returns
private manifest/tutor-coverage previews. It does not write manifests, index
the tutor, expose raw review notes, expose local paths, or clear exam
deployment.

The private manifest apply dry-run is the controlled metadata write gate after
review. It computes a delta plus ExamScopeMap and Tutor-Coverage previews, and
only writes the local private manifest when `operator_confirmed_manifest_apply`
is true. Even then it writes metadata only; tutor indexing and exam deployment
remain separate explicit steps.

The extraction completion report is the final classifier for this workstream.
It distinguishes genuinely complete extraction, reviewed/failed/skipped receipt
coverage, valid intentional deferral, and still-missing jobs. A deferral record
must name scope, reviewer roles, reason, job coverage, no raw-text release, and
`not_cleared` exam status. It is evidence of postponement only, not permission
to publish, index, grade, proctor, or deploy.

The extraction manifest update plan is the final metadata bridge before the
course tutor can use newly reviewed extraction output. It converts reviewed
receipts into private manifest update candidates, but does not write files or
publish extracted text.

The tutor coverage plan forecasts current versus projected skill readiness
after reviewed candidates are applied. This keeps the course tutor exact to the
exam scope and makes remaining material gaps visible before rebuilding
retrieval.

The study session plan turns the current reviewed tutor anchors into practical
retrieval, notebook, reflection, and spaced-review tasks. It is how the course
tutor becomes usable for learning while staying source-bound and non-grading.

The study session receipt and review report are the learning-evidence harness
for that plan. Receipts validate prediction, retrieval response, source anchor,
smallest notebook action, help level, and reflection as hashes and flags only.
The review report aggregates those receipts for human review, without raw
student text, automatic grading, AI detection, or Eigenleistung percentages.

The institutional clearance board is the stakeholder gate above that. It
prepares scope-specific written records for public draft, local extraction,
formative pilot, and controlled exam gateway. The validator checks roles,
allowed modes, help levels, and red-line clauses, but it still does not create
real exam clearance or deploy anything by itself.

The stakeholder submission bundle is the project-manager handoff for the two
external decisions that still cannot be solved inside the codebase. It packages
rights/privacy extraction review and exam-gateway authority review into two
public-safe lanes with validator endpoints, record templates, evidence
summaries, and careful message drafts. It is not sent automatically and does not
claim approval.

The stakeholder decision request is the one-lane next step after that bundle.
It turns either the rights/privacy lane or the exam-gateway lane into a manual
review packet with a request id, evidence hashes, checklist, Markdown export,
and receipt template. A valid receipt can prove that a human request was
manually sent, but it still does not authorize extraction, accept a written
decision record, or change `exam_deployment_status`.

The stakeholder decision journal is the local process log for that human gate.
It records prepared requests and validated manual request receipts as JSONL with
hashes and statuses only. It is useful for project management continuity across
chats, but it is not a decision record, not a sending tool, and not a deployment
or extraction switch.

The external decision-state packet is the intake harness for written responses.
It validates extraction and exam clearance records together, stores only hashes,
and derives the next project gates. Even a valid exam clearance record does not
silently deploy the exam mode; deployment remains an explicit manual gate.

The external decision-record journal is the durable evidence layer after that
intake. It records validated written extraction, deferral, exam-clearance, or
manual-go references as local hash-only JSONL. Completion audit can read it via
`decision_record_journal_path`, but the journal still does not send messages,
store raw written decisions, or change `exam_deployment_status`.
