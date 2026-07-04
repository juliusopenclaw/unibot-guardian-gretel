# UniBot Gretel Autonomous Research Loop

Status: budgeted recurring local research lane, not autonomous public release.

## Purpose

Gretel should keep improving UniBot as autonomously as is reasonable while
staying inside the project's safety, privacy, scientific, and publication
standards. The loop is designed for continuous small improvements, not for
unbounded token use or unsupervised external actions.

## North Star

Build UniBot as a public, source-bound, bachelor-thesis-level research project
that helps coding learners practice without outsourcing their own work, leaking
private material, or claiming exam clearance.

## Always-Use Standards

- Three Golden Rules.
- Public-safety scan.
- Readiness check.
- Source cards.
- Red-team scenarios.
- Synthetic fixtures.
- Review-board/open-decision register.
- Gretel/GLM proposal-only lane.
- Human review for publication, university submission, provider calls, and exam
  clearance.

## Budgeted 24/7 Mode

Recommended cadence: every 6 hours.

Per run:

- inspect public repo state,
- select at most one work item,
- change at most four candidate files,
- run focused tests and readiness gates,
- commit locally only when green,
- do not push publicly without human review.

Default reasoning effort should stay low. Escalation is allowed only for a
bounded failing test, a failing public-safety/readiness gate, or an API/release
contract change.

## Blocked Autonomous Actions

- No autonomous GitHub push or public release.
- No email, calendar, chat, or webhook sends.
- No GLM/Z.AI/OpenAI/provider call without explicit go and a redaction receipt.
- No private course material or real exam data ingestion.
- No exam clearance, grading authority, proctoring reliability, or AI-detection
  evidence claims.
- No Final-Go.

## Current Work Queue

- `stakeholder_submission_bundle_local_cycle_workspace_card_lane_link_alignment`
  is ready. It should link stakeholder submission bundle decision-lane and
  evidence-summary metadata with the harnessed local-cycle operator
  workspace-card readiness gate, preserving lane/evidence hashes and
  workspace-card prefill evidence, no raw private course text/contact data/local
  path publication, no external send or approval claim, no
  grading/proctoring/KI-detection, and no exam clearance/deployment claims.

## Closed Harnessed Work

- `stakeholder_decision_request_local_cycle_workspace_card_packet_link_alignment`:
  closed in `2809248` with stakeholder decision request release-claim links from
  request packet and receipt-template hashes to the harnessed local-cycle
  operator workspace-card readiness gate, request/receipt-template and
  ready-for-prefill metadata, and blocked raw written-decision/contact data
  publication, automatic external sends or approval claims, grading,
  proctoring, KI-detection, and exam clearance claims.

- `stakeholder_decision_journal_local_cycle_workspace_card_request_link_alignment`:
  closed in `6d7f5d0` with stakeholder decision journal release-claim links
  from decision-journal and request/receipt hashes to the harnessed local-cycle
  operator workspace-card readiness gate, hash-only request/receipt and
  ready-for-prefill metadata, and blocked raw request or written-decision
  text/contact data publication, automatic gate changes, grading, proctoring,
  KI-detection, and exam clearance claims.

- `external_decision_record_journal_local_cycle_workspace_card_record_link_alignment`:
  closed in `59be092` with external decision record journal release-claim links
  from decision-record journal and gate-summary hashes to the harnessed
  local-cycle operator workspace-card readiness gate, hash-only record and
  ready-for-prefill metadata, and blocked raw written decisions/contact
  data/public raw course text publication, deployment switches, grading,
  proctoring, KI-detection, and exam deployment claims.

- `external_decision_state_local_cycle_workspace_card_gate_link_alignment`:
  closed in `dcebb68` with external decision state release-claim links from
  decision gate and decision-record hashes to the harnessed local-cycle
  operator workspace-card readiness gate, local-extraction/exam-authority gate
  and ready-for-prefill metadata, and blocked raw written decisions/contact
  data/public raw course text publication, silent deployment switches, grading,
  proctoring, KI-detection, and exam deployment claims.

- `extraction_receipt_journal_local_cycle_workspace_card_receipt_link_alignment`:
  closed in `942a59b` with extraction receipt journal release-claim links from
  receipt journal and progress-receipt hashes to the harnessed local-cycle
  operator workspace-card readiness gate, hash-only receipt and
  ready-for-prefill metadata, and blocked raw extracted text/local
  paths/private artifact publication, manifest writes or tutor retrieval,
  grading, proctoring, KI-detection, and exam deployment claims.

- `extraction_progress_local_cycle_workspace_card_queue_link_alignment`:
  closed in `4414ee2` with extraction progress release-claim links from
  progress queue and review hashes to the harnessed local-cycle operator
  workspace-card readiness gate, review queue and ready-for-prefill metadata,
  and blocked raw extracted text/local paths/private artifact publication,
  manifest writes or tutor retrieval, grading, proctoring, KI-detection, and
  exam deployment claims.

- `extraction_manifest_update_local_cycle_workspace_card_candidate_link_alignment`:
  closed in `97b8634` with extraction manifest-update release-claim links from
  reviewed candidate and candidate-set hashes to the harnessed local-cycle
  operator workspace-card readiness gate, candidate and ready-for-prefill
  metadata, and blocked raw OCR/transcript/local paths, manifest writes by
  update alone, grading, proctoring, KI-detection, and exam deployment claims.

- `extraction_manifest_apply_local_cycle_workspace_card_manifest_link_alignment`:
  closed in `7e16ae9` with private manifest-apply release-claim links from
  confirmed manifest and delta hashes to the harnessed local-cycle operator
  workspace-card readiness gate, candidate/apply and ready-for-prefill
  metadata, and blocked raw extracted text/local paths, tutor-indexing by apply
  alone, grading, proctoring, KI-detection, and exam deployment claims.

- `private_tutor_use_flow_local_cycle_workspace_card_help_ledger_link_alignment`:
  closed in `89f4938` with private tutor-use flow release-claim links from
  operator-confirmed Help-Ledger event hashes to the harnessed local-cycle
  operator workspace-card readiness gate, tutor response and ready-for-prefill
  metadata, and blocked raw query/course text, grading, proctoring,
  KI-detection, and exam deployment claims.

- `study_session_local_cycle_workspace_card_reflection_link_alignment`:
  closed in `77d12b5` with study-session release-claim links from formative
  prediction/notebook-action/reflection evidence to the harnessed local-cycle
  operator workspace-card readiness gate, reflection and Help-Ledger-preview
  hashes, prefill metadata, and blocked raw learner/private text, grading,
  proctoring, KI-detection, and exam deployment claims.

- `notebook_checkpoint_local_cycle_workspace_card_checkpoint_link_alignment`:
  closed in `988cf65` with notebook-checkpoint release-claim links from
  hash-only local cell evidence to the harnessed local-cycle operator
  workspace-card readiness gate, checkpoint and Help-Ledger-preview hashes,
  prefill metadata, and blocked raw cell/notebook/query, grading, proctoring,
  KI-detection, and exam deployment claims.

- `exam_workspace_run_local_cycle_workspace_card_execution_link_alignment`:
  closed in `20eb12b` with exam-workspace run release-claim links to the
  harnessed local-cycle operator workspace-card readiness gate, tutor sidecar,
  study receipt, notebook checkpoint, export metadata, workspace-card prefill
  and Help-Ledger hash evidence, and blocked raw notebook/query, grading,
  proctoring, KI-detection, and exam deployment claims.

- `exam_workspace_launch_local_cycle_workspace_card_gate_link_alignment`:
  closed in `d06c1b9` with launch release-claim links to the harnessed
  local-cycle operator workspace-card readiness gate, launch/checkpoint/tutor/
  export metadata, workspace-card prefill and Help-Ledger hash evidence, and
  blocked raw notebook/query, grading, proctoring, KI-detection, and exam
  deployment claims.

- `exam_workspace_operator_run_local_cycle_workspace_card_start_view_link_alignment`:
  closed in `1064cda` with Start Exam Workspace links to the harnessed
  local-cycle operator workspace-card readiness gate, workspace-card
  ready/prefill and Help-Ledger hash metadata, individual local-write
  confirmation boundaries, and blocked raw notebook/query, grading, proctoring,
  KI-detection, and exam deployment claims.

- `exam_workspace_run_history_local_cycle_workspace_card_review_link_alignment`:
  closed in `99c0914` with run-history/export-review release-claim links to the
  harnessed local-cycle operator workspace-card readiness gate, session-console
  receipt hashes, workspace-card ready/prefill and Help-Ledger hash metadata,
  reflection evidence, and blocked raw notebook/query, grading, proctoring,
  KI-detection, and exam deployment claims.

- `exam_workspace_session_console_local_cycle_workspace_card_readiness_link_alignment`:
  closed in `4543a62` with session-console release-claim links to the harnessed
  local-cycle operator workspace-card readiness gate, ready-for-prefill and
  Help-Ledger hash evidence, and blocked raw notebook/query, grading,
  proctoring, KI-detection, and exam deployment claims.

- `intent_contract_regression_pack`: closed in `fa942b0` with autonomous loop,
  intent contract, budget policy, API routes, docs, and tests.
- `scientific_evaluation_depth`: closed in `2b6473b` with a public-safe
  scientific quality rubric for Socratic help, source grounding, refusal
  clarity, privacy, and learner agency.
- `github_review_packet_hardening`: closed in `9a28675` with manual review
  contract, evidence requirements, publication gate, and manual-publish
  invariant.
- `autonomy_progress_memory`: closed in `5d16846` with completed queue items,
  explicit progress evidence, and next recommended work.
- `readiness_perf_guard`: closed in `c6581a3` with a focused runtime guard for
  recurring readiness checks, low reasoning effort, and escalated
  full-suite/provider work.
- `source_card_drift_guard`: closed in `afeb0d5` with source-card drift report,
  API route, readiness gate, stale-source harness, and public docs.
- `bachelor_thesis_evidence_index`: closed in `400fc92` with claim-to-test,
  readiness-check, source-card, and human-gate evidence mapping for the
  Gretel-authored bachelor-thesis package.
- `readiness_evidence_snapshot`: closed in `19d6f8c` with stable-hash
  readiness evidence snapshot, scientific gate coverage, public-safe summary,
  docs, and tests.
- `review_board_evidence_alignment`: closed in `f449f88` with reviewer-to-thesis
  claim, readiness-gate, source-card, and human-gate evidence mapping.
- `feedback_issue_evidence_traceability`: closed in `99d36ff` with
  feedback-derived GitHub issues mapped to readiness gates, source cards, human
  gates, and the evidence-snapshot contract.
- `release_runbook_evidence_alignment`: closed in `be671ff` with readiness
  snapshot, review-board, GitHub issue, source-card, and human-gate contracts
  for release review.
- `compliance_drift_evidence_alignment`: closed in `92cb2f1` with
  requirement-to-readiness, source-card, human-gate, and readiness-protection
  mapping.
- `pilot_protocol_evidence_alignment`: closed in `30a81a8` with consent,
  ethics, data, session-flow, release-boundary, source-card, readiness, and
  human-gate mapping.
- `data_protection_evidence_alignment`: closed in `4b5fbbc` with processing
  principles, pilot records, retention, public-boundary, exam-boundary,
  source-card, risk, readiness, and human-gate mapping.
- `glm_provider_redaction_evidence_alignment`: closed in `a41b060` with
  source-basis, redaction-receipt, provider-lock, proposal-validation,
  apply/publish/Final-Go, readiness, and human-gate mapping.
- `open_science_reproducibility_release_alignment`: closed in `ecfa4f8` with
  public reproduction, manual release, authority/compliance, Gretel/GLM thesis,
  autonomy, release-gate, source-card, and human-gate mapping.
- `course_material_public_boundary_alignment`: closed in `ca9c426` with
  public/private material contracts, source cards, readiness gates, and human
  gates for course-material publication boundaries.
- `adaptive_task_source_boundary_alignment`: closed in `00bc10e` with
  public-summary source contracts, learner-agency checks, readiness gates, and
  public-summary excerpt hardening.
- `evaluation_learner_agency_boundary_alignment`: closed in `7c04e0d` with
  adaptive trace, rubric, measurement-exclusion, source-card, readiness, and
  human-gate contracts.
- `bachelor_thesis_evaluation_claim_alignment`: closed in `5fcdbfe` with
  learner-agency, adaptive boundary, source-card, high-stakes exclusion,
  readiness, and human-gate traceability.
- `review_board_thesis_evaluation_claim_alignment`: closed in `20a66a0` with
  learner-agency reviewer mapping, high-stakes red lines, source-card,
  readiness, and human-gate contracts.
- `release_runbook_review_board_claim_alignment`: closed in `77f5b61` with
  review-board thesis/evaluation claim contract, adaptive/evaluation/readiness
  links, public-language controls, and human gates.
- `compliance_release_review_board_claim_alignment`: closed in `6170a9a` with
  release-review-board claim contract, release-runbook, review-board
  thesis/evaluation, readiness, and human-gate checks.
- `pilot_release_review_board_claim_alignment`: closed in `582c574` with
  synthetic learner-agency boundaries, adaptive evidence, readiness links, and
  human gates.
- `data_protection_release_review_board_claim_alignment`: closed in `447a37e`
  with pilot/release/review-board thesis/evaluation readiness links, processing
  boundaries, and human gates.
- `publication_release_review_board_claim_alignment`: closed in `d794a40` with
  pilot/data-protection/release/review-board thesis/evaluation trace links, public
  release boundaries, and human gates.
- `github_issue_release_review_board_claim_alignment`: closed in `16dcbb3`
  with publication/release/review-board thesis/evaluation claim contracts,
  manual issue publication controls, public language boundaries, and human
  gates.
- `feedback_triage_release_review_board_claim_alignment`: closed in `c74e157`
  with downstream GitHub issue, publication, release-runbook, review-board,
  readiness, and human-gate links for sanitized feedback triage.


- `demo_feedback_release_review_board_claim_alignment`: closed in `9940ac7`
  with local-only/public-summary-only boundaries, downstream triage/issue,
  publication/review-board readiness links, and human gates.

- `local_demo_release_review_board_claim_alignment`: closed in `4cd091d` with
  practice-only/local-only/public-summary boundaries, downstream demo-feedback,
  triage/issue/publication/review-board readiness links, and human gates.

- `browser_extension_release_review_board_claim_alignment`: closed in `3db6902`
  with sidepanel release-review-board claim links to local demo, demo feedback,
  triage, GitHub issue, readiness, and human gates.

- `browser_manifest_content_boundary_claim_alignment`: closed in `1032d84` with
  bounded manifest permissions, content-script boundary, sidepanel/local-demo
  links, human gates, and no exam-security claims.

- `notebook_handoff_release_review_board_claim_alignment`: closed in `74c074a`
  with browser, manifest/content-boundary, local-demo, feedback, publication,
  review-board, readiness, and human-gate links for the practice notebook
  handoff.

- `redteam_release_review_board_claim_alignment`: closed in `639a2cb` with
  hash/category-only red-team evidence, notebook, browser, local-demo,
  publication, review-board, readiness, and human-gate links.

- `source_card_release_review_board_claim_alignment`: closed in `bda02d3`
  with drift checks, public-link-only source rules, red-team, notebook,
  publication, review-board, readiness, and human-gate links.

- `threat_model_release_review_board_claim_alignment`: closed in `fb2c4e9`
  with source-card, red-team, publication, release-runbook, review-board,
  readiness, and human-gate links for threat-model risk language.
- `review_board_packet_release_claim_summary_alignment`: closed in `bf2c654`
  with review-board release-claim summaries aligned to source cards, threat
  model, red-team, publication, public language controls, and human gates.
- `authority_handoff_release_review_board_claim_alignment`: closed in `5867d66`
  with authority handoff release-claim alignment across review-board,
  source-card, red-team, compliance, public language, provider-gate, and
  human-gate controls.
- `stakeholder_submission_release_review_board_claim_alignment`: closed in
  `408debe` with stakeholder submission release-claim alignment across
  review-board, authority-handoff, source-card, privacy/extraction, public
  language, and human-gate controls.
- `stakeholder_decision_request_release_review_board_claim_alignment`: closed
  in `99060f6` with stakeholder decision request release-claim alignment across
  submission-bundle, receipt-boundary, review-board, Datenschutz,
  public-safety, and human-gate controls.
- `stakeholder_decision_journal_release_review_board_claim_alignment`: closed
  in `a6052b7` with stakeholder decision journal release-claim alignment across
  hash-only records, request/receipt traceability, no raw decision storage, no
  tool-send, and human-gate controls.
- `external_decision_record_journal_release_review_board_claim_alignment`:
  closed in `e785479` with external decision record journal release-claim
  alignment across validated record hashes, no raw decision storage, no
  deployment switch, and human-gate controls.
- `external_decision_state_release_review_board_claim_alignment`: closed in
  `05fb04e` with external decision state release-claim alignment across
  validated record derivation, hash-only references, no silent deployment
  switch, and human-gate controls.
- `extraction_receipt_journal_release_review_board_claim_alignment`: closed in
  `51b537a` with extraction receipt journal release-claim alignment across
  hash-only receipt records, local-private evidence boundaries, human-review
  links, no manifest update by receipt alone, and high-stakes claim blocks.
- `extraction_progress_release_review_board_claim_alignment`: closed in
  `8562658` with extraction progress release-claim alignment across receipt
  metadata, hash-only review queues, private manifest-candidate boundaries, no
  raw text or local paths, and no exam deployment claims.
- `extraction_manifest_update_release_review_board_claim_alignment`: closed in
  `49d4fa2` with extraction manifest update release-claim alignment across
  reviewed receipt candidates, private metadata-only boundaries, no file writes
  by planning, no public release, and no exam deployment claims.
- `extraction_manifest_apply_release_review_board_claim_alignment`: closed in
  `fbda8fe` with private manifest apply release-claim alignment across
  dry-run/no-write proof, operator-confirmed private metadata writes,
  path/raw-text suppression, no tutor indexing, and no exam deployment claims.
- `extraction_completion_release_review_board_claim_alignment`: closed in
  `19f9bfe` with reviewed receipt coverage, intentional deferral evidence,
  public-safety checks, no manifest updates, and no exam deployment claims.
- `extraction_human_review_release_review_board_claim_alignment`: closed in
  `0cecaf4` with hash-only local review evidence, completion links, private
  manifest-plan boundaries, no tutor indexing by review alone, and no exam
  deployment claims.
- `private_tutor_use_flow_release_review_board_claim_alignment`: closed in
  `d850fa2` with reviewed private manifest evidence, operator-confirmed
  hash-only tutor index, A0-A2 learner-agency boundaries, Help-Ledger evidence,
  and no exam deployment claims.
- `study_session_release_review_board_claim_alignment`: closed in `934f817`
  with hash-only learning receipts, source anchors, reflection evidence, A6
  repeat-task enforcement, no Eigenleistung percentage claims, and no exam
  deployment claims.
- `notebook_checkpoint_release_review_board_claim_alignment`: closed in
  `fb0b59e` with hash-only local cell evidence, operator-confirmed checkpoint
  journal writes, A6 repeat-task enforcement, raw-code suppression, and no exam
  deployment claims.
- `exam_workspace_launch_release_review_board_claim_alignment`: closed in
  `0a3d05f` with notebook checkpoint, private tutor-use, study receipt,
  dry-run, raw-code suppression, and no exam deployment claim checks.
- `exam_workspace_run_release_review_board_claim_alignment`: closed in
  `c6a0dbf` with controlled notebook-run evidence, private tutor sidecar, study
  receipt, Help-Ledger/exam-ledger links, export receipt, runtime isolation,
  and no exam deployment claims.
- `exam_workspace_run_history_release_review_board_claim_alignment`: closed in
  `2581243` with hash-only session-console receipts, checkpoint hashes,
  operator blockers, reflection evidence, not-cleared export receipts, and no
  exam deployment claims.
- `exam_workspace_operator_run_release_review_board_claim_alignment`: closed in
  `b5fee21` with Start Exam Workspace view, dry-run default, individual
  confirmation boundaries, repeat-task stop, not-cleared receipt, and no exam
  deployment claims.
- `exam_workspace_session_console_release_review_board_claim_alignment`: closed
  in `e5d013b` with operator-run receipt, run-history context, workspace-card
  status, reflection evidence, hash-only checkpoint receipt, repeated dry-run
  boundary, and no exam deployment claims.
- `python_exam_local_cycle_start_packet_release_review_board_claim_alignment`:
  closed in `72c555c` with safe-cycle, operator-gate, decision-receipt,
  source-card, task/checkpoint hash, open/confirmed confirmation, dry-run, and
  no exam deployment claims.
- `python_exam_local_cycle_readiness_review_release_review_board_claim_alignment`:
  closed in `c0511e5` with open-confirmation, fully-confirmed, and
  missing-packet review recommendations, hash/source-card evidence, read-only
  dry-run boundary, and no exam deployment claims.
- `python_exam_local_cycle_readiness_handoff_release_review_board_claim_alignment`:
  closed in `31fc0c8` with operator-run prefill, manual handoff,
  attention-state blocking, hash/source-card metadata, dry-run boundaries, and
  no exam deployment claims.
- `python_exam_local_cycle_operator_workspace_card_release_review_board_claim_alignment`:
  closed in `87abb96` with readiness-review/handoff evidence, operator
  prefill, Help-Ledger preview, attention-state blocking, hash/source-card
  metadata, dry-run boundaries, and no exam deployment claims.

## Automation Rule

Automation may keep the local iCloud/Git worktree warm and produce local commits
or review notes after green checks. Public GitHub pushes, provider calls, real
submission, exam deployment, and external messages require human review.
