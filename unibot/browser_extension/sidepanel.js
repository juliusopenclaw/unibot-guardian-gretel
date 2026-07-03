const browserExtensionReleaseReviewBoardClaimAlignment = Object.freeze({
  schema_version: "unibot-browser-extension-release-review-board-claim-alignment-v1",
  status: "ready",
  practice_only: true,
  local_only: true,
  public_summary_only: true,
  manual_publication_claim_contract: {
    expected_schema_version: "unibot-browser-extension-release-review-board-claim-alignment-v1",
    required_local_demo_claim_schema_version: "unibot-local-demo-release-review-board-claim-alignment-v1",
    required_demo_feedback_claim_schema_version: "unibot-demo-feedback-release-review-board-claim-alignment-v1",
    required_feedback_triage_claim_schema_version: "unibot-feedback-triage-release-review-board-claim-alignment-v1",
    required_github_issue_claim_schema_version: "unibot-github-issue-release-review-board-claim-alignment-v1",
    required_readiness_check_ids: [
      "browser_extension_demo_handoff",
      "local_demo_run",
      "demo_feedback_contract",
      "demo_feedback_triage",
      "github_issue_bundle",
      "publication_package",
      "release_runbook",
      "review_board_packet",
      "public_safety"
    ],
    required_human_gates: [
      "human_review_before_github_create",
      "human_submission_review_required",
      "public_safety_required"
    ],
    use: "Browser sidepanel handoff remains practice-only and traceable before demo, feedback, issue, publication, or review-board work."
  },
  blocked_claims: ["exam clearance", "official grading", "proctoring", "KI-detection evidence"]
});

const task = document.querySelector("#task");
const help = document.querySelector("#help");
const external = document.querySelector("#external");
const reflection = document.querySelector("#reflection");
const notebookCell = document.querySelector("#notebookCell");
const result = document.querySelector("#result");
const confirmCheckpointStore = document.querySelector("#confirmCheckpointStore");
const confirmExamWorkspaceRun = document.querySelector("#confirmExamWorkspaceRun");
const confirmManifestApply = document.querySelector("#confirmManifestApply");
const confirmTutorIndexBuild = document.querySelector("#confirmTutorIndexBuild");
const confirmHelpLedgerAppend = document.querySelector("#confirmHelpLedgerAppend");
const confirmExamLedgerAppend = document.querySelector("#confirmExamLedgerAppend");
const confirmTimelineExportReceiptJournalAppend = document.querySelector("#confirmTimelineExportReceiptJournalAppend");
const confirmDrillLoopProgressJournalAppend = document.querySelector("#confirmDrillLoopProgressJournalAppend");
const confirmLocalExportDraftWrite = document.querySelector("#confirmLocalExportDraftWrite");
const feedbackScenario = document.querySelector("#feedbackScenario");
const feedbackOutcome = document.querySelector("#feedbackOutcome");
const feedbackSeverity = document.querySelector("#feedbackSeverity");
const feedbackEndpoint = document.querySelector("#feedbackEndpoint");
const feedbackTried = document.querySelector("#feedbackTried");
const feedbackExpected = document.querySelector("#feedbackExpected");
const feedbackHappened = document.querySelector("#feedbackHappened");
const feedbackPublicText = document.querySelector("#feedbackPublicText");
const feedbackPrivateRemoved = document.querySelector("#feedbackPrivateRemoved");
let lastExamSkillDrilldown = null;
let lastExamSessionConsoleReceipt = null;
let lastPerSkillActionRouter = null;
let lastRoutedActionExecutor = null;
let lastCourseExamCoverageDashboard = null;
let lastExamWorkspaceOperatorRun = null;
let lastExamRunHistoryExportReview = null;
let lastNotebookCheckpointAdapter = null;
let lastExamRunPacket = null;
let lastExamPacketTimeline = null;
let lastTimelineExportReviewPacket = null;
let lastTimelineExportReceiptJournalAppend = null;
let lastTimelineExportReceiptJournalSummary = null;
let lastReviewChainIntegrityCheck = null;
let lastPythonExamReadinessConsole = null;
let lastPythonExamCockpitFlow = null;
let lastPythonExamLiveControlSurface = null;
let lastPythonExamEvidenceExportPreview = null;
let lastPythonExamTutorDrillPack = null;
let lastPythonExamDrillSessionRunner = null;
let lastPythonExamDrillSessionReviewLoop = null;
let lastPythonExamDrillLoopControlPanel = null;
let lastPythonExamDrillLoopProgressJournal = null;
let lastPythonExamResumeLauncher = null;
let lastPythonExamActiveStudyLoopDashboard = null;
let lastPythonExamActiveStudyGuidedRunner = null;
let lastPythonExamGuidedActionExecutionBridge = null;
let lastPythonExamSafeCycleConsole = null;
let lastPythonExamSafeCycleOperatorGate = null;
let lastPythonExamOperatorGateDecisionReceipt = null;
let lastPythonExamLocalCycleStartPacket = null;
let lastPythonExamLocalCycleReadinessReview = null;
let lastPythonExamLocalCycleReadinessHandoff = null;
let lastPythonExamLocalCycleWorkspaceCard = null;
let lastPythonExamLocalCycleChainSnapshot = null;
let lastPythonExamManualConfirmationConsole = null;
let lastPythonExamManualCycleLaunchReceipt = null;
let lastPythonExamManualCycleEvidenceBinder = null;
let lastPythonExamManualPostCycleReceiptIntake = null;
let lastPythonExamManualCycleClosureLedger = null;
let lastPythonExamManualCycleReviewTimeline = null;
let lastPythonExamManualCycleReviewPacket = null;
let lastPythonExamManualReviewExportPreview = null;
let lastPythonExamManualReviewExportAuthorizationGate = null;
let lastPythonExamManualExportReviewQueue = null;
let lastPythonExamManualExportReviewerPacket = null;
let lastPythonExamManualArchiveDecisionDraft = null;
let lastPythonExamManualFinalReviewHandoff = null;
let lastPythonExamManualFinalReviewReceiptLedger = null;
let lastPythonExamFinalReviewLedgerIntegrityGate = null;
let lastPythonExamFinalManualReviewConsole = null;
let lastPythonExamFinalManualReviewActionLock = null;
let lastPythonExamLockedFinalReviewBoard = null;
let lastPythonExamLockedFinalReviewGapResolver = null;
let lastPythonExamConfirmedLocalExportDraft = null;
let lastPythonExamDraftPackageReviewConsole = null;
let lastPythonExamHumanHandoffPacket = null;
let lastPythonExamFullLocalRehearsalPack = null;
let lastPythonExamRehearsalPlaybackGapCoach = null;
let lastPythonExamGapCoachGuidedLoop = null;
let lastPythonExamGuidedLoopControlSurface = null;
let lastSkillToWorkspaceLiveFlow = null;
let lastSkillToWorkspaceSessionCarryover = null;
let examSessionConsoleReports = [];

const skillSignalPatterns = {
  python_lists: /list|listen|append|index|slice/g,
  loops: /loop|for |while |schleife/g,
  dictionaries: /dict|keyerror|woerterbuch|keys|values/g,
  functions: /function|def |return|funktion/g,
  numpy: /numpy|np\.|array/g,
  pandas: /pandas|dataframe|df\.|csv/g,
  boxplots: /boxplot|median|quartile|iqr/g,
  debugging: /error|traceback|debug|fehlermeldung/g,
  colab_jupyter: /colab|jupyter|notebook|cell|zelle/g,
  general_python: /python|code|variable|wert/g
};

function helpLevel() {
  return help.value.slice(0, 2);
}

function skillTags(text) {
  const lower = text.toLowerCase();
  const tags = [];
  if (/list|listen|append|index|slice/.test(lower)) tags.push("python_lists");
  if (/loop|for |while |schleife/.test(lower)) tags.push("loops");
  if (/dict|keyerror|woerterbuch|keys|values/.test(lower)) tags.push("dictionaries");
  if (/function|def |return|funktion/.test(lower)) tags.push("functions");
  if (/numpy|np\.|array/.test(lower)) tags.push("numpy");
  if (/pandas|dataframe|df\.|csv/.test(lower)) tags.push("pandas");
  if (/boxplot|median|quartile|iqr/.test(lower)) tags.push("boxplots");
  if (/error|traceback|debug|fehlermeldung/.test(lower)) tags.push("debugging");
  if (/colab|jupyter|notebook|cell|zelle/.test(lower)) tags.push("colab_jupyter");
  return tags.length ? tags : ["general_python"];
}

function localSkillState() {
  const combined = [task.value, external.value, reflection.value].join("\n");
  const tags = skillTags(combined);
  const highHelp = ["A4", "A5", "A6"].includes(helpLevel()) ? 1 : 0;
  return tags.reduce((state, tag) => {
    const pattern = skillSignalPatterns[tag] || skillSignalPatterns.general_python;
    const matches = combined.toLowerCase().match(pattern) || [];
    state[tag] = {
      signals: Math.max(1, matches.length),
      high_help_events: highHelp,
      last_help_level: helpLevel()
    };
    return state;
  }, {});
}

function promptCard() {
  const tags = skillTags(task.value);
  return [
    "Du bist ein sokratischer Python-Neuro-Tutor.",
    "Gib keine finale Loesung, keinen vollstaendigen Code, keine konkreten Werte und keine abgabefertige Interpretation.",
    "Stelle zuerst 1-3 Rueckfragen, dann maximal einen kleinen Konzept-Hinweis.",
    "Markiere Unsicherheit und nenne, welche Kursquelle oder offizielle Dokumentation geprueft werden sollte.",
    "",
    `Aufgabe/Problem: ${task.value.trim()}`,
    `Skill-Fokus: ${tags.join(", ")}`
  ].join("\n");
}

async function callUniBot(path, payload) {
  try {
    const response = await fetch(`http://127.0.0.1:8765${path}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (_error) {
    return null;
  }
}

function classifyLocally(text) {
  const flags = [];
  const lower = text.toLowerCase();
  if (/fertige|komplette|complete|final answer|abgabefertig/.test(lower)) flags.push("final_solution");
  if (/```|import pandas|import numpy|plt\.|df\.|def /.test(text)) flags.push("code_fix_or_complete_code");
  if (/\w+\s*=\s*\[[0-9.,\s-]{5,}\]/.test(text)) flags.push("values_inserted");
  if (/@|matrikel|diagnose|attest|\/Users\/|api[_-]?key|password/.test(lower)) flags.push("private_or_sensitive_data");
  return flags;
}

function offlineAdaptivePlan() {
  const tags = Object.keys(localSkillState());
  const templates = {
    python_lists: "Liste mit drei Messwerten anlegen, Index 0 und -1 vorhersagen, dann append/extend begruenden.",
    loops: "Schleife erst als Pseudocode schreiben, dann nur die erste Bedingung testen.",
    dictionaries: "Zwei Gruppenlabels als Keys skizzieren und einen moeglichen KeyError vorhersagen.",
    functions: "Eingabe, Ausgabe und einen Testfall fuer eine kleine Funktion formulieren.",
    numpy: "Array-Form und erwarteten Mittelwert vor dem Ausfuehren vorhersagen.",
    pandas: "df.head(), df.dtypes und fehlende Werte pruefen, bevor eine Spalte genutzt wird.",
    boxplots: "Messwert, Gruppe und Einheit festlegen, aber noch keine finale Interpretation schreiben.",
    debugging: "Traceback-Zeile, Fehlertyp und kleinsten naechsten Test notieren.",
    colab_jupyter: "Ziel, Vorhersage, eigener Versuch, Fehler und Reflexion im Notebook ausfuellen.",
    general_python: "Den kleinsten selbst pruefbaren Python-Schritt formulieren."
  };
  return {
    status: "offline",
    tasks: tags.slice(0, 3).map((tag) => ({
      skill_tag: tag,
      task_prompt: templates[tag] || templates.general_python,
      socratic_checks: [
        "Was erwartest du vor dem Ausfuehren?",
        "Welcher kleinste Schritt ist deiner?",
        "Welche Hilfe-Stufe wurde genutzt?"
      ],
      assessment_policy: "practice-only, no grade"
    }))
  };
}

function renderAdaptivePlan(plan, sourceLabel) {
  const lines = [
    sourceLabel,
    `Status: ${plan.status}`,
    `Aufgaben: ${(plan.tasks || []).length}`,
    ""
  ];
  (plan.tasks || []).forEach((item, index) => {
    lines.push(`${index + 1}. ${item.skill_tag} - ${item.task_prompt}`);
    if (item.micro_goal) lines.push(`   Ziel: ${item.micro_goal}`);
    (item.socratic_checks || []).slice(0, 3).forEach((check) => lines.push(`   ? ${check}`));
    lines.push(`   Policy: ${item.assessment_policy || "practice-only, no grade"}`);
    lines.push("");
  });
  return lines.join("\n").trim();
}

function renderCommandCenter(center, sourceLabel) {
  const material = center.material_status || {};
  const scope = center.scope_status || {};
  const next = center.next_sprint || {};
  const lines = [
    sourceLabel,
    `Status: ${center.status || "unknown"}`,
    `Exam: ${(center.deployment_line || {}).exam_deployment_status || "not_cleared"}`,
    `Rollen: ${(center.role_lanes || []).length}`,
    `Materialien: ${material.record_count || 0} records, ${material.private_tutor_index_count || 0} Tutor-Anker`,
    `Queues: OCR ${material.ocr_queue_count || 0}, Transkription ${material.transcription_queue_count || 0}, Quarantaene ${material.solution_or_exam_quarantine_count || 0}`,
    `Scope: ${scope.ready_skill_count || 0} Skills bereit, ${scope.needs_review_skill_count || 0} brauchen Review`,
    `Naechster Sprint: ${next.focus || "unbekannt"}`,
    next.outcome ? `Outcome: ${next.outcome}` : "",
    "",
    "Gates:",
    ...((center.acceptance_gates || []).slice(0, 5).map((gate) => `- ${gate}`))
  ];
  return lines.filter(Boolean).join("\n");
}

function renderCompilerPlan(plan, sourceLabel) {
  const counts = plan.counts || {};
  const sourceCounts = plan.source_card_counts || {};
  const topSourceCards = Object.entries(sourceCounts)
    .slice(0, 5)
    .map(([source, count]) => `${source}: ${count}`)
    .join(", ");
  return [
    sourceLabel,
    `Status: ${plan.status || "unknown"}`,
    `Exam: ${plan.exam_deployment_status || "not_cleared"}`,
    `Dateien: ${counts.total_file_count || 0}`,
    `Records: ${counts.record_count || 0}`,
    `Private Tutor Index: ${counts.private_tutor_index_count || 0}`,
    `Review ready: ${counts.review_ready_count || 0}`,
    `OCR Queue: ${counts.ocr_queue_count || 0}`,
    `Transkriptionsqueue: ${counts.transcription_queue_count || 0}`,
    `Quarantaene: ${counts.solution_or_exam_quarantine_count || 0}`,
    topSourceCards ? `Source Cards: ${topSourceCards}` : "",
    "",
    "Naechste Schritte:",
    ...((plan.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].filter(Boolean).join("\n");
}

function renderExtractionQueue(queue, sourceLabel) {
  const counts = queue.counts || {};
  const rights = queue.rights_gate || {};
  return [
    sourceLabel,
    `Status: ${queue.status || "unknown"}`,
    `Exam: ${queue.exam_deployment_status || "not_cleared"}`,
    `Jobs: ${counts.job_count || 0}`,
    `OCR: ${counts.ocr_job_count || 0}`,
    `Transkription: ${counts.transcription_job_count || 0}`,
    `Quarantaene: ${counts.quarantine_count || 0}`,
    `Rechte-Gate: ${rights.authorized ? "autorisiert" : "blockiert bis Entscheidung"}`,
    "",
    "Naechste Schritte:",
    ...((queue.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderDecisionPacket(packet, sourceLabel) {
  const queue = packet.queue_summary || {};
  return [
    sourceLabel,
    `Status: ${packet.status || "unknown"}`,
    `Exam: ${packet.exam_deployment_status || "not_cleared"}`,
    `Jobs im Scope: ${queue.job_count || 0}`,
    `Reviewer: ${(packet.required_reviewer_roles || []).join(", ")}`,
    "",
    "Entscheidungen:",
    ...((packet.required_decisions || []).slice(0, 6).map((item) => `- ${item}`)),
    "",
    `Grenze: ${packet.decision_boundary || "not approval"}`
  ].join("\n");
}

function renderLocalDecisionIntake(packet, sourceLabel) {
  const decision = packet.decision_validation || {};
  const ocr = packet.ocr_first_readiness || {};
  const receipt = packet.receipt_journal_summary || {};
  const reports = packet.post_run_report_summary || {};
  return [
    sourceLabel,
    `Status: ${packet.status || "unknown"}`,
    `Exam: ${packet.exam_deployment_status || "not_cleared"}`,
    `Decision: ${decision.status || "missing"} (${decision.decision_record_source || "missing"})`,
    `OCR-first: ${ocr.status || "unknown"}, jobs: ${ocr.job_count || 0}, batches: ${ocr.batch_count || 0}`,
    `Receipts: ${receipt.progress_receipt_count || 0}, Review-ready: ${reports.ready_for_human_review_count || 0}`,
    `Manifest candidates: ${reports.manifest_candidate_count || 0}`,
    `Tutor coverage: ${reports.tutor_coverage_status || "unknown"}`,
    `Raw decision returned: ${packet.raw_decision_record_returned ? "ja" : "nein"}`,
    `Raw text returned: ${packet.raw_text_returned ? "ja" : "nein"}`,
    `Local paths returned: ${packet.local_paths_returned ? "ja" : "nein"}`,
    "",
    "Naechste Schritte:",
    ...((packet.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderLocalDecisionWorkspace(packet, sourceLabel) {
  const dryRun = packet.dry_run_receipt || {};
  const ocr = packet.ocr_first_readiness || {};
  const files = packet.workspace_files || {};
  return [
    sourceLabel,
    `Status: ${packet.status || "unknown"}`,
    `Exam: ${packet.exam_deployment_status || "not_cleared"}`,
    `Template: ${(files.template || {}).status || "unknown"}`,
    `Manifest: ${(files.manifest || {}).status || "unknown"}`,
    `Dry-run: ${dryRun.status || "unknown"}`,
    `Decision valid: ${dryRun.decision_valid ? "ja" : "nein"}`,
    `OCR Batch 1 ready: ${dryRun.ocr_first_batch_1_start_ready ? "ja" : "nein"}`,
    `OCR Batch 1 jobs: ${dryRun.ocr_first_batch_1_job_count || (ocr.next_batch || {}).job_count || 0}`,
    `Receipt-Journal erreichbar: ${dryRun.receipt_journal_reachable ? "ja" : "nein"}`,
    `Reports erreichbar: ${dryRun.post_run_reports_reachable ? "ja" : "nein"}`,
    `Real OCR started: ${dryRun.real_ocr_started ? "ja" : "nein"}`,
    `Raw decision returned: ${packet.raw_decision_record_returned ? "ja" : "nein"}`,
    `Local paths returned: ${packet.local_paths_returned ? "ja" : "nein"}`,
    "",
    "Naechste Schritte:",
    ...((packet.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderOperatorPacket(packet, sourceLabel) {
  const queue = packet.queue_summary || {};
  const decision = packet.decision_validation || {};
  return [
    sourceLabel,
    `Status: ${packet.status || "unknown"}`,
    `Exam: ${packet.exam_deployment_status || "not_cleared"}`,
    `Decision: ${decision.status || "missing"}`,
    `Jobs: ${queue.job_count || 0} (Batch: ${packet.job_batch_count || 0})`,
    `OCR: ${queue.ocr_job_count || 0}, Transkription: ${queue.transcription_job_count || 0}`,
    `Grenze: ${packet.execution_boundary || "no extraction performed"}`,
    "",
    "Checkliste:",
    ...((packet.operator_checklist || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPrivateExtractionRun(report, sourceLabel) {
  const counts = report.counts || {};
  const decision = report.decision_validation || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Decision: ${decision.status || "missing"}`,
    `Candidates: ${counts.candidate_job_count || 0}, supported: ${counts.supported_candidate_count || 0}`,
    `Selected: ${counts.selected_job_count || 0}, extracted: ${counts.extracted_private_count || 0}`,
    `Receipts: ${counts.receipt_count || 0}, stored: ${counts.stored_receipt_count || 0}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "local private extraction only"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderOcrFirstOperatorRun(report, sourceLabel) {
  const dryRun = report.workspace_dry_run_receipt || {};
  const selected = report.selected_batch || {};
  const privateRun = report.private_run_summary || {};
  const reports = report.post_run_reports || {};
  const progress = reports.progress || {};
  const manifest = reports.manifest_update || {};
  const coverage = reports.tutor_coverage || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Dry-run: ${dryRun.status || "unknown"}`,
    `Operator confirmed: ${report.operator_confirmed_dry_run ? "ja" : "nein"}`,
    `Batch: ${selected.batch_index || 0}, jobs: ${selected.job_count || 0}`,
    `Private run: ${privateRun.status || "not_started"}`,
    `Receipts stored: ${privateRun.stored_receipt_count || 0}`,
    `Progress: ${progress.status || "unknown"}, Review-ready: ${progress.ready_for_human_review_count || 0}`,
    `Manifest: ${manifest.status || "unknown"}, Candidates: ${manifest.candidate_count || 0}`,
    `Coverage: ${coverage.status || "unknown"}`,
    `Real OCR started: ${report.real_ocr_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderVideoTranscriptionRun(report, sourceLabel) {
  const counts = report.counts || {};
  const decision = report.decision_validation || {};
  const caps = report.adapter_capabilities || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Decision: ${decision.status || "missing"}`,
    `Videos: ${counts.candidate_video_job_count || 0}, Sidecars: ${counts.sidecar_candidate_count || 0}`,
    `Selected: ${counts.selected_job_count || 0}, transcribed: ${counts.transcribed_private_count || 0}`,
    `Receipts: ${counts.receipt_count || 0}, stored: ${counts.stored_receipt_count || 0}`,
    `Adapter: sidecar=${caps.sidecar_transcript ? "ja" : "nein"}, ffmpeg=${caps.ffmpeg ? "ja" : "nein"}, whisper=${caps.whisper ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "local private video transcription only"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderExtractionProgress(report, sourceLabel) {
  const queue = report.queue_summary || {};
  const receipts = report.receipt_summary || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Jobs: ${queue.job_count || 0}`,
    `Receipts: ${receipts.receipt_count || 0}, invalid: ${receipts.invalid_receipt_count || 0}`,
    `Review Queue: ${receipts.ready_for_human_review_count || 0}`,
    `Tutor-Kandidaten: ${receipts.eligible_for_private_tutor_index_count || 0}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderExtractionReceiptJournal(summary, sourceLabel) {
  return [
    sourceLabel,
    `Status: ${summary.status || "unknown"}`,
    `Records: ${summary.record_count || 0}`,
    `Accepted: ${summary.accepted_record_count || 0}, blocked: ${summary.blocked_record_count || 0}`,
    `Review Queue: ${summary.ready_for_human_review_count || 0}`,
    `Tutor-Kandidaten: ${summary.eligible_for_private_tutor_index_count || 0}`,
    `Progress Receipts: ${summary.progress_receipt_count || 0}`,
    "",
    "By Job Type:",
    ...Object.entries(summary.by_job_type || {}).map(([jobType, count]) => `- ${jobType}: ${count}`),
    "",
    `Grenze: ${summary.gate_policy || "journal does not authorize gates"}`
  ].join("\n");
}

function renderExtractionHumanReviewPlan(plan, sourceLabel) {
  const queue = plan.review_queue_summary || {};
  const decisions = plan.review_decision_summary || {};
  const manifest = (plan.post_review_reports || {}).manifest_update || {};
  const coverage = (plan.post_review_reports || {}).tutor_coverage || {};
  return [
    sourceLabel,
    `Status: ${plan.status || "unknown"}`,
    `Exam: ${plan.exam_deployment_status || "not_cleared"}`,
    `Review Queue: ${queue.pre_review_ready_count || 0} -> ${queue.post_review_ready_count || 0}`,
    `Reviewed: ${queue.post_reviewed_for_private_tutor_count || 0}`,
    `Decisions: ${decisions.submitted_review_decision_count || 0}, appended: ${decisions.appended_review_receipt_count || 0}`,
    `Manifest: ${manifest.status || "unknown"}, Candidates: ${manifest.candidate_count || 0}`,
    `Coverage: ${coverage.status || "unknown"}, Uplift: ${coverage.ready_skill_uplift || 0}`,
    `Manifest written: ${plan.manifest_written ? "ja" : "nein"}`,
    `Tutor indexing: ${plan.tutor_indexing_started ? "ja" : "nein"}`,
    `Raw text returned: ${plan.raw_text_returned ? "ja" : "nein"}`,
    `Local paths returned: ${plan.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${plan.execution_boundary || "review plan only"}`,
    "",
    "Naechste Schritte:",
    ...((plan.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPrivateManifestApplyDryRun(report, sourceLabel) {
  const candidates = report.candidate_summary || {};
  const manifest = report.private_manifest_summary || {};
  const scope = (report.exam_scope_preview || {}).projected_scope_summary || {};
  const coverage = report.tutor_coverage_preview || {};
  const apply = report.apply_result || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Candidates: ${candidates.candidate_count || 0}, Delta: ${candidates.records_to_apply_count || 0}`,
    `Manifest: existing ${manifest.existing_record_count || 0}, projected ${manifest.projected_record_count || 0}`,
    `Scope ready: ${scope.ready_skill_count || 0}/${scope.skill_count || 0}, Uplift: ${scope.ready_skill_uplift || 0}`,
    `Coverage: ${coverage.status || "unknown"}, Kandidaten: ${coverage.candidate_material_count || 0}`,
    `Operator confirmed: ${report.operator_confirmed_manifest_apply ? "ja" : "nein"}`,
    `Apply: ${apply.status || "not_requested"}, written: ${report.manifest_written ? "ja" : "nein"}`,
    `Tutor indexing: ${report.tutor_indexing_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "dry-run only"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPrivateTutorIndexDryRun(report, sourceLabel) {
  const manifest = report.private_manifest_summary || {};
  const preview = report.index_preview || {};
  const scope = report.exam_scope_preview || {};
  const build = report.build_result || {};
  const gaps = scope.priority_coverage_gaps || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Manifest: ${manifest.status || "missing"}, Records: ${manifest.record_count || 0}, tutor-ready: ${manifest.tutor_usable_record_count || 0}`,
    `Anchors: ${preview.anchor_count || 0}, Skills indexed: ${preview.indexed_skill_count || 0}, missing: ${preview.missing_skill_count || 0}`,
    `Operator confirmed: ${report.operator_confirmed_tutor_index_build ? "ja" : "nein"}`,
    `Build: ${build.status || "not_requested"}, written: ${report.tutor_index_built ? "ja" : "nein"}`,
    `Journal: ${report.tutor_index_journal_written ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "dry-run only"}`,
    "",
    "Prioritaere Luecken:",
    ...(gaps.slice(0, 5).map((item) => `- ${item.skill_tag}: ${item.next_review_need}`)),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPrivateIndexTutorResponse(response, sourceLabel) {
  const selected = response.selected_skill || {};
  const index = response.index_summary || {};
  const ledger = response.help_ledger_preview || {};
  const anchors = response.source_anchors || [];
  return [
    sourceLabel,
    `Status: ${response.status || "unknown"}`,
    `Exam: ${response.exam_deployment_status || "not_cleared"}`,
    `Skill: ${selected.skill_tag || "unknown"} (${selected.readiness || "unknown"})`,
    `Anchors: ${anchors.length}, Index anchors: ${index.anchor_count || 0}, Skills: ${index.indexed_skill_count || 0}`,
    `Help: ${response.effective_help_level || "A2"}, Query raw returned: ${response.raw_query_returned ? "ja" : "nein"}`,
    `Ledger: ${(ledger.source_anchor_ids || []).join(", ") || "none"}`,
    `Raw text returned: ${response.raw_text_returned ? "ja" : "nein"}`,
    `Local paths returned: ${response.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${response.execution_boundary || "dry-run only"}`,
    "",
    response.answer_markdown || "",
    "",
    "Fragen:",
    ...((response.socratic_questions || []).slice(0, 3).map((item) => `- ${item}`)),
    "",
    "Naechste Schritte:",
    ...((response.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPrivateTutorUseFlow(report, sourceLabel) {
  const manifest = report.manifest_apply_summary || {};
  const index = report.tutor_index_summary || {};
  const response = report.tutor_response_summary || {};
  const ledger = report.ledger_append_summary || {};
  const receipt = report.study_receipt_validation || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Manifest: ${manifest.status || "unknown"}, written: ${manifest.manifest_written ? "ja" : "nein"}`,
    `Index: ${index.status || "unknown"}, built: ${index.tutor_index_built ? "ja" : "nein"}, anchors: ${index.anchor_count || 0}`,
    `Tutor: ${response.status || "unknown"}, skill: ${response.skill_tag || "unknown"}, help: ${response.effective_help_level || "A2"}`,
    `Ledger: ${ledger.status || "unknown"}, written: ${ledger.ledger_written ? "ja" : "nein"}`,
    `Study receipt: ${receipt.status || "unknown"}, repeat: ${receipt.repeat_task_required ? "ja" : "nein"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "dry-run only"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderExamWorkspaceRun(report, sourceLabel) {
  const session = report.session_summary || {};
  const materials = report.material_freeze_summary || {};
  const notebook = report.notebook_checkpoint || {};
  const sidecar = report.tutor_sidecar || {};
  const ledger = report.exam_ledger_append_summary || {};
  const pack = report.export_package_summary || {};
  const evidence = report.cell_evidence_link || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Session: ${session.status || "unknown"}, Help: ${(session.allowed_help_levels || []).join(", ") || "A0-A2"}`,
    `Materials: ${materials.status || "unknown"}, freeze: ${materials.freeze_written ? "ja" : "nein"}`,
    `Notebook: ${notebook.run_status || "unknown"}, cell: ${notebook.cell_task_id || "unknown"}`,
    `Tutor: ${sidecar.status || "unknown"}, help: ${sidecar.effective_help_level || "A2"}, anchors: ${sidecar.source_anchor_count || 0}`,
    `Study receipt: ${evidence.study_receipt_status || "unknown"}`,
    `Exam ledger: ${ledger.status || "unknown"}, written: ${ledger.ledger_written ? "ja" : "nein"}`,
    `Export: ${pack.status || "unknown"}, not_cleared: ${pack.not_cleared_receipt ? "ja" : "nein"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "dry-run only"}`,
    "",
    sidecar.answer_markdown || "",
    "",
    "Fragen:",
    ...((sidecar.socratic_questions || []).slice(0, 3).map((item) => `- ${item}`)),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderNotebookCheckpointAdapter(report, sourceLabel) {
  const checkpoint = report.notebook_checkpoint || {};
  const receipt = report.study_receipt_summary || {};
  const ledger = report.help_ledger_preview || {};
  const journal = report.checkpoint_journal_summary || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Checkpoint: ${checkpoint.status || "unknown"}, task: ${checkpoint.task_id || "unknown"}`,
    `Cell hash: ${checkpoint.cell_source_sha256 || "missing"}`,
    `Study receipt: ${receipt.status || "unknown"}, repeat: ${receipt.repeat_task_required ? "ja" : "nein"}`,
    `Help-Ledger preview: ${ledger.status || "unknown"}, written: ${ledger.ledger_written ? "ja" : "nein"}`,
    `Journal: ${journal.status || "unknown"}, written: ${journal.checkpoint_journal_written ? "ja" : "nein"}`,
    `Raw cell returned: ${report.raw_cell_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "hash-only checkpoint"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderExamWorkspaceLaunchFlow(report, sourceLabel) {
  const coverage = report.coverage_summary || {};
  const start = coverage.start_point || {};
  const config = report.launch_configuration || {};
  const checkpoint = config.notebook_cell_checkpoint || {};
  const anchor = config.source_anchor_hint || {};
  const run = report.exam_workspace_run_summary || {};
  const ledger = report.help_ledger_preview || {};
  const receipt = report.export_receipt || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Coverage: ${coverage.status || "unknown"}, ready: ${coverage.ready_skill_count || 0}/${coverage.skill_count || 0}`,
    `Startpunkt: ${start.status || "unknown"} ${start.skill_tag || ""}`,
    `Help: ${config.help_level || "A2"}, coerced: ${config.requested_help_level_coerced ? "ja" : "nein"}`,
    `A2-Template: ${config.query_template || "waiting for ready start point"}`,
    `Anchors: ${anchor.source_anchor_count || 0}, Source cards: ${(anchor.source_card_ids || []).join(", ") || "none"}`,
    `Notebook: ${checkpoint.cell_task_id || checkpoint.status || "unknown"}, code returned: ${checkpoint.notebook_code_returned ? "ja" : "nein"}`,
    `Workspace: ${run.status || "unknown"}, tutor: ${run.tutor_status || "unknown"}, receipt: ${run.study_receipt_status || "unknown"}`,
    `Help-Ledger: ${ledger.status || "unknown"}, exam written: ${ledger.exam_ledger_written ? "ja" : "nein"}`,
    `Export: ${receipt.status || "unknown"}, not_cleared: ${receipt.not_cleared_receipt ? "ja" : "nein"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "dry-run launch only"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderExamWorkspaceOperatorRun(report, sourceLabel) {
  const view = report.start_exam_workspace_view || {};
  const receipt = report.dry_run_receipt || {};
  const confirmations = report.operator_confirmation_matrix || {};
  const steps = confirmations.steps || {};
  const sections = view.sections || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `View: ${view.title || "Start Exam Workspace"} (${view.status || "unknown"})`,
    `Receipt: ${receipt.receipt_id || "missing"}, export: ${receipt.export_status || "unknown"}`,
    `Skill: ${receipt.selected_skill_tag || "unknown"}, Help: ${receipt.effective_help_level || "A2"}`,
    `Checkpoint: ${receipt.notebook_checkpoint_status || "unknown"}`,
    `Operator confirmations: ${confirmations.confirmed_count || 0}/${confirmations.write_step_count || 0}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw cell returned: ${report.raw_cell_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "operator dry-run only"}`,
    "",
    "Start Exam Workspace:",
    ...(sections.map((section) => `- ${section.title}: ${section.status}`)),
    "",
    "Confirmations:",
    ...(Object.keys(steps).map((key) => `- ${key}: ${steps[key].confirmed ? "confirmed" : "dry-run"}; ${steps[key].status || "unknown"}`)),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderExtractionDeferralValidation(validation, sourceLabel) {
  return [
    sourceLabel,
    `Status: ${validation.status || "unknown"}`,
    `Scope: ${validation.deferral_scope || "missing"}`,
    `Decision: ${validation.decision_status || "missing"}`,
    `Job Types: ${(validation.deferred_job_types || []).join(", ") || "none"}`,
    `Issues: ${(validation.issues || []).join(", ") || "keine"}`,
    `Raw Reference Stored: ${validation.raw_decision_reference_stored ? "ja" : "nein"}`,
    `Grenze: ${validation.policy || "deferral is not extraction or exam clearance"}`
  ].join("\n");
}

function renderExtractionCompletionReport(report, sourceLabel) {
  const jobs = report.job_summary || {};
  const receipts = report.receipt_summary || {};
  const deferral = report.deferral_summary || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Jobs offen: ${jobs.open_job_count || 0}, missing: ${jobs.missing_job_count || 0}`,
    `Receipts reviewed/failed/skipped: ${jobs.completed_by_reviewed_receipt_count || 0}`,
    `Deferral: ${deferral.status || "missing"}, deferred jobs: ${jobs.deferred_job_count || 0}`,
    `Invalid Receipts: ${receipts.invalid_receipt_count || 0}`,
    `Grenze: ${report.execution_boundary || "classification only"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderExtractionBatchPlan(plan, sourceLabel) {
  const coverage = plan.coverage || {};
  const backlog = plan.receipt_backlog || {};
  const next = plan.next_batch || {};
  return [
    sourceLabel,
    `Status: ${plan.status || "unknown"}`,
    `Exam: ${plan.exam_deployment_status || "not_cleared"}`,
    `Jobs: ${coverage.job_count || 0}`,
    `Filter: ${(coverage.job_type_filter || []).join(", ") || "alle"}`,
    `Batches: ${coverage.batch_count || 0} x ${coverage.batch_size || 0}`,
    `OCR: ${coverage.ocr_job_count || 0}, Transkription: ${coverage.transcription_job_count || 0}`,
    `Receipts: ${backlog.valid_receipt_count || 0}/${backlog.expected_receipt_count || 0}`,
    `Missing: ${backlog.missing_receipt_count || 0}, invalid: ${backlog.invalid_receipt_count || 0}`,
    `Next Batch: ${next.batch_index || "-"} ${next.status || ""}`,
    `Grenze: ${plan.execution_boundary || "plan only"}`,
    "",
    "Naechste Schritte:",
    ...((plan.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderBatchReceiptPacket(packet, sourceLabel) {
  const batch = packet.selected_batch || {};
  const validation = packet.receipt_validation_summary || {};
  const templates = packet.receipt_templates || [];
  return [
    sourceLabel,
    `Status: ${packet.status || "unknown"}`,
    `Exam: ${packet.exam_deployment_status || "not_cleared"}`,
    `Batch: ${batch.batch_index || "-"} ${batch.status || ""}`,
    `Jobs: ${batch.job_count || 0}`,
    `Templates: ${templates.length}`,
    `Receipts: ${validation.valid_receipt_count || 0}, invalid: ${validation.invalid_receipt_count || 0}`,
    `Review Queue: ${validation.ready_for_human_review_count || 0}`,
    `Tutor-Kandidaten: ${validation.eligible_for_private_tutor_index_count || 0}`,
    `Grenze: ${packet.execution_boundary || "packet only"}`,
    "",
    "Operator-Schritte:",
    ...((packet.local_operator_steps || []).slice(0, 5).map((item) => `- ${item}`)),
    "",
    "Review:",
    ...((packet.human_review_checklist || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderManifestUpdatePlan(plan, sourceLabel) {
  const receipts = plan.receipt_summary || {};
  const candidates = plan.candidate_summary || {};
  return [
    sourceLabel,
    `Status: ${plan.status || "unknown"}`,
    `Exam: ${plan.exam_deployment_status || "not_cleared"}`,
    `Progress: ${plan.progress_status || "unknown"}`,
    `Receipts: ${receipts.valid_receipt_count || 0}, reviewed: ${receipts.eligible_for_private_tutor_index_count || 0}`,
    `Kandidaten: ${candidates.candidate_count || 0}, ready: ${candidates.ready_to_apply_private_count || 0}`,
    `Blocked: ${candidates.blocked_candidate_count || 0}, missing job metadata: ${candidates.source_job_metadata_missing_count || 0}`,
    `Grenze: ${plan.execution_boundary || "metadata update plan only"}`,
    "",
    "Naechste Schritte:",
    ...((plan.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderTutorCoveragePlan(plan, sourceLabel) {
  const current = plan.current_scope_summary || {};
  const projected = plan.projected_scope_summary || {};
  const gaps = plan.priority_skill_gaps || [];
  return [
    sourceLabel,
    `Status: ${plan.status || "unknown"}`,
    `Exam: ${plan.exam_deployment_status || "not_cleared"}`,
    `Aktuell bereit: ${current.ready_skill_count || 0}/${current.skill_count || 0}`,
    `Prognose bereit: ${projected.ready_skill_count || 0}/${projected.skill_count || 0}`,
    `Uplift: ${projected.ready_skill_uplift || 0}, Kandidaten: ${projected.candidate_material_count || 0}`,
    `Grenze: ${plan.execution_boundary || "forecast only"}`,
    "",
    "Prioritaere Luecken:",
    ...(gaps.slice(0, 5).map((item) => `- ${item.skill_tag}: ${item.projected_readiness}; ${item.next_review_need}`)),
    "",
    "Naechste Schritte:",
    ...((plan.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderMaterialCoverageRun(report, sourceLabel) {
  const material = report.material_summary || {};
  const extraction = report.extraction_gap_summary || {};
  const manifest = report.private_manifest_summary || {};
  const index = report.private_tutor_index_summary || {};
  const coverage = report.coverage_summary || {};
  const start = report.next_exam_workspace_start_point || {};
  const skills = report.skill_coverage || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Materialien: ${material.record_count || 0}, Files: ${material.total_file_count || 0}`,
    `Luecken: OCR=${extraction.ocr_job_count || 0}, Video=${extraction.transcription_job_count || 0}`,
    `Manifest: ${manifest.status || "unknown"}, Records: ${manifest.record_count || 0}`,
    `Index: ${index.status || "unknown"}, Anchors: ${index.anchor_count || 0}, Skills: ${index.indexed_skill_count || 0}`,
    `Workspace-ready: ${coverage.exam_workspace_ready_skill_count || 0}/${coverage.skill_count || 0}`,
    `Startpunkt: ${start.status || "unknown"} ${start.skill_tag || ""}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "coverage only"}`,
    "",
    "Skills:",
    ...(skills.slice(0, 7).map((item) => (
      `- ${item.skill_tag}: ${item.exam_workspace_readiness}; anchors=${item.source_anchor_count || 0}; OCR=${item.ocr_gap_count || 0}; Video=${item.video_transcription_gap_count || 0}; Notebook=${(item.notebook_exercise || {}).status || "unknown"}`
    ))),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderExamSkillDrilldown(report, sourceLabel) {
  const coverage = report.coverage_summary || {};
  const selected = report.selected_skill || {};
  const action = report.workspace_start_action || {};
  const gaps = report.material_gap_queue || [];
  const skills = report.skill_map || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Auswahl: ${selected.skill_tag || "none"} (${selected.exam_workspace_readiness || "unknown"})`,
    `Workspace-Aktion: ${action.status || "unknown"} ${action.endpoint || ""}`,
    `Bereite Skills: ${(coverage.ready_skill_tags || []).join(", ") || "keine"}`,
    `Luecken-Skills: ${(coverage.gap_skill_tags || []).slice(0, 8).join(", ") || "keine"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "skill drilldown only"}`,
    "",
    "Skill-Map:",
    ...(skills.slice(0, 9).map((item) => (
      `- ${item.selected ? "* " : ""}${item.skill_tag}: ${item.exam_workspace_readiness}; anchors=${item.source_anchor_count || 0}; OCR=${item.ocr_gap_count || 0}; Video=${item.video_transcription_gap_count || 0}; Notebook=${(item.notebook_exercise || {}).status || "unknown"}`
    ))),
    "",
    "Material-Luecken:",
    ...(gaps.slice(0, 5).map((item) => `- ${item.skill_tag}: OCR=${item.ocr_gap_count || 0}, Video=${item.video_transcription_gap_count || 0}; ${item.next_step || ""}`)),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function skillWorkspaceOperatorPayload(drilldown) {
  const template = drilldown.operator_payload_template || {};
  const selected = drilldown.selected_skill || {};
  const checkpoint = drilldown.notebook_checkpoint_template || {};
  const sourceCards = template.source_card_ids || selected.source_card_ids || checkpoint.source_card_ids || [];
  const selectedSkill = template.selected_skill_tag || selected.skill_tag || template.focus_query || task.value;
  return {
    course_id: template.course_id || drilldown.course_id,
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    ledger_path: "~/.unibot_guardian/help_ledger.jsonl",
    checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
    focus_query: selectedSkill,
    query: selectedSkill,
    selected_skill_tag: selectedSkill,
    task_id: template.task_id || checkpoint.task_id || "",
    source_card_ids: sourceCards,
    requested_help_level: helpLevel() === "A0" || helpLevel() === "A1" ? helpLevel() : "A2",
    exam_status: "strict",
    student_reflection: reflection.value,
    cell_source: notebookCell.value,
    cell_index: checkpoint.cell_index_default || 0,
    cell_type: checkpoint.cell_type_default || "code",
    operator_confirmed_checkpoint_store: confirmCheckpointStore.checked,
    operator_confirmed_exam_workspace_run: confirmExamWorkspaceRun.checked,
    operator_confirmed_manifest_apply: confirmManifestApply.checked,
    operator_confirmed_tutor_index_build: confirmTutorIndexBuild.checked,
    operator_confirmed_help_ledger_append: confirmHelpLedgerAppend.checked,
    operator_confirmed_exam_ledger_append: confirmExamLedgerAppend.checked,
    study_receipt: {
      prediction_present: Boolean(task.value.trim()),
      retrieval_response_present: Boolean(sourceCards.length),
      notebook_action_present: Boolean(notebookCell.value.trim()),
      reflection_present: Boolean(reflection.value.trim()),
    },
    public_safe: true
  };
}

function skillWorkspaceLiveFlowPayload() {
  return {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    ledger_path: "~/.unibot_guardian/help_ledger.jsonl",
    checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
    focus_query: task.value,
    selected_skill_tag: task.value,
    requested_help_level: helpLevel() === "A0" || helpLevel() === "A1" ? helpLevel() : "A2",
    exam_status: "strict",
    student_reflection: reflection.value,
    cell_source: notebookCell.value,
    cell_index: 0,
    cell_type: "code",
    operator_confirmed_checkpoint_store: confirmCheckpointStore.checked,
    operator_confirmed_exam_workspace_run: confirmExamWorkspaceRun.checked,
    operator_confirmed_manifest_apply: confirmManifestApply.checked,
    operator_confirmed_tutor_index_build: confirmTutorIndexBuild.checked,
    operator_confirmed_help_ledger_append: confirmHelpLedgerAppend.checked,
    operator_confirmed_exam_ledger_append: confirmExamLedgerAppend.checked,
    study_receipt: {
      prediction_present: Boolean(task.value.trim()),
      notebook_action_present: Boolean(notebookCell.value.trim()),
      reflection_present: Boolean(reflection.value.trim()),
    },
    public_safe: true
  };
}

function skillWorkspaceSessionCarryoverPayload() {
  return {
    ...skillWorkspaceLiveFlowPayload(),
    skill_to_workspace_live_flow: lastSkillToWorkspaceLiveFlow,
    review_chain_integrity_check: lastReviewChainIntegrityCheck,
    timeline_export_review_packet: lastTimelineExportReviewPacket,
    timeline_export_receipt_journal_summary: lastTimelineExportReceiptJournalSummary,
    repeat_run_index: lastExamSessionConsoleReceipt ? ((lastExamSessionConsoleReceipt.repeat_run_index || 1) + 1) : 1,
    previous_console_receipts: lastExamSessionConsoleReceipt ? [lastExamSessionConsoleReceipt] : [],
    public_safe: true
  };
}

function skillWorkspaceSessionConsolePayload(drilldown) {
  const payload = skillWorkspaceOperatorPayload(drilldown);
  payload.repeat_run_index = lastExamSessionConsoleReceipt ? ((lastExamSessionConsoleReceipt.repeat_run_index || 1) + 1) : 1;
  payload.previous_console_receipts = lastExamSessionConsoleReceipt ? [lastExamSessionConsoleReceipt] : [];
  payload.python_exam_local_cycle_operator_workspace_card = lastPythonExamLocalCycleWorkspaceCard;
  return payload;
}

function renderSkillToWorkspaceLiveFlow(drilldownOrFlow, operatorReport, sourceLabel) {
  const flowReport = drilldownOrFlow && drilldownOrFlow.artifact_type === "skill_to_workspace_live_flow" ? drilldownOrFlow : null;
  const drilldown = flowReport ? (flowReport.exam_skill_drilldown || {}) : drilldownOrFlow;
  const operator = flowReport ? (flowReport.operator_dry_run || {}) : operatorReport;
  const selected = drilldown.selected_skill || {};
  const live = drilldown.skill_to_workspace_live_flow || {};
  const action = drilldown.workspace_start_action || {};
  const summary = flowReport ? (flowReport.live_flow_summary || {}) : {};
  const receipt = operator.dry_run_receipt || (flowReport ? flowReport.dry_run_receipt : {}) || {};
  const confirmations = operator.operator_confirmation_matrix || (flowReport ? flowReport.operator_confirmation_matrix : {}) || {};
  const checkpoint = drilldown.notebook_checkpoint_template || {};
  const ledger = drilldown.help_ledger_preview_template || {};
  return [
    sourceLabel,
    flowReport ? `Live Flow: ${flowReport.status || "unknown"}` : "",
    `Drilldown: ${drilldown.status || "unknown"}`,
    `Flow: ${summary.status || live.status || "unknown"}`,
    `Skill: ${selected.skill_tag || "none"}`,
    `Action: ${action.status || "unknown"} -> ${action.endpoint || "none"}`,
    `Operator: ${operator.status || (flowReport ? flowReport.operator_run_status : "unknown")}`,
    `Receipt: ${receipt.status || "unknown"} (${receipt.receipt_id || "no-id"})`,
    `Help: ${receipt.effective_help_level || ledger.help_level || "A2"}`,
    `Checkpoint template: ${checkpoint.status || "unknown"}, task=${checkpoint.task_id || "none"}`,
    `Source cards: ${(selected.source_card_ids || []).join(", ") || "keine"}`,
    `Confirmations: ${confirmations.confirmed_count || 0}/${confirmations.write_step_count || 0}`,
    `Exam: ${(flowReport && flowReport.exam_deployment_status) || operator.exam_deployment_status || "not_cleared"}`,
    `Raw query returned: ${((flowReport && flowReport.raw_query_returned) || operator.raw_query_returned) ? "ja" : "nein"}`,
    `Raw text returned: ${((flowReport && flowReport.raw_text_returned) || operator.raw_text_returned) ? "ja" : "nein"}`,
    `Notebook code returned: ${((flowReport && flowReport.notebook_code_returned) || operator.notebook_code_returned) ? "ja" : "nein"}`,
    `Local paths returned: ${((flowReport && flowReport.local_paths_returned) || operator.local_paths_returned) ? "ja" : "nein"}`,
    `Grenze: ${(flowReport && flowReport.execution_boundary) || operator.execution_boundary || drilldown.execution_boundary || "dry-run only"}`,
    "",
    "Operator-Confirmations:",
    ...(Object.entries(confirmations.steps || {}).map(([key, step]) => (
      `- ${key}: ${step.confirmed ? "confirmed" : "dry-run"}; ${step.status || "unknown"}`
    ))),
    "",
    "Naechste Schritte:",
    ...(((flowReport && flowReport.next_actions) || operator.next_actions || drilldown.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].filter(Boolean).join("\n");
}

function renderSkillToWorkspaceSessionCarryover(report, sourceLabel) {
  const summary = report.carryover_summary || {};
  const packet = report.carryover_packet || {};
  const operator = packet.operator_receipt || {};
  const session = packet.session_receipt || {};
  const evidence = packet.evidence_preview || {};
  const handoff = packet.human_handoff || {};
  const confirmations = packet.operator_confirmation_status || {};
  const source = packet.source_anchor_metadata || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${summary.selected_skill_tag || packet.selected_skill_tag || "none"}`,
    `Operator receipt: ${operator.receipt_id || summary.operator_receipt_id || "missing"}`,
    `Session receipt: ${session.receipt_id || summary.session_receipt_id || "missing"}`,
    `Checkpoint hash: ${session.checkpoint_hash || summary.checkpoint_hash || "missing"}`,
    `Help: ${summary.help_status || evidence.help_status || "unknown"}`,
    `Source cards: ${(source.source_card_ids || []).join(", ") || "keine"}; anchors=${source.source_anchor_count || summary.source_anchor_count || 0}`,
    `Session: ${summary.session_status || "unknown"}`,
    `History: ${summary.run_history_status || "unknown"}; runs=${(packet.run_history || {}).run_count || 0}`,
    `Evidence: ${summary.evidence_preview_status || evidence.status || "unknown"} (${evidence.preview_receipt_id || "no-id"})`,
    `Handoff: ${summary.human_handoff_status || handoff.status || "unknown"} (${handoff.markdown_hash || "no-hash"})`,
    `Confirmations: open=${confirmations.open_operator_confirmation_count || summary.open_operator_confirmation_count || 0}, confirmed=${confirmations.confirmed_count || 0}/${confirmations.write_step_count || 0}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only carryover"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderExamSessionConsole(report, sourceLabel) {
  const consoleView = report.session_console || {};
  const selected = consoleView.selected_skill || {};
  const workspace = consoleView.workspace_status || {};
  const checkpoint = consoleView.notebook_checkpoint || {};
  const tutor = consoleView.tutor_state || {};
  const ledger = consoleView.help_ledger_preview || {};
  const localCycleWorkspaceCard = consoleView.local_cycle_operator_workspace_card || {};
  const exportReceipt = consoleView.export_receipt || {};
  const confirmations = consoleView.operator_confirmations || {};
  const repeat = consoleView.repeat_dry_run || {};
  const receipt = report.session_console_receipt || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Konsole: ${consoleView.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${selected.skill_tag || "none"} (${selected.start_point_status || "unknown"})`,
    `Workspace: ${workspace.workspace_run_status || "unknown"} / ${workspace.session_status || "unknown"}`,
    `Checkpoint: ${checkpoint.status || "unknown"} ${checkpoint.notebook_work_sha256 || ""}`,
    `Tutor: ${tutor.tutor_status || "unknown"}, Help=${tutor.effective_help_level || "A2"}, Receipt=${tutor.study_receipt_status || "unknown"}`,
    `Ledger: ${ledger.status || "unknown"}, general=${ledger.general_help_ledger_written ? "written" : "dry-run"}, exam=${ledger.exam_ledger_written ? "written" : "dry-run"}`,
    `Local Cycle Card: ${localCycleWorkspaceCard.status || "missing"}; ${localCycleWorkspaceCard.help_ledger_preview_status || "no-ledger"}; next=${localCycleWorkspaceCard.next_safe_action || "review_skill_readiness"}`,
    `Export: ${exportReceipt.status || "unknown"}, reviewable=${exportReceipt.human_reviewable_independence_evidence ? "ja" : "nein"}`,
    `Confirmations: ${confirmations.confirmed_count || 0}/${confirmations.write_step_count || 0}; offen=${(confirmations.open_steps || []).join(", ") || "keine"}`,
    `Repeat: #${repeat.repeat_run_index || receipt.repeat_run_index || 1}, supported=${repeat.supported ? "ja" : "nein"}`,
    `Receipt: ${receipt.receipt_id || "no-id"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "session console only"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderExamRunHistoryReview(report, sourceLabel) {
  const summary = report.history_summary || {};
  const pkg = report.export_review_package || {};
  const review = pkg.review_items || {};
  const receipt = report.export_review_receipt || {};
  const history = report.run_history || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Runs: ${summary.run_count || 0}`,
    `Skills: ${(summary.skill_tags || []).join(", ") || "keine"}`,
    `Checkpoint hashes: ${summary.checkpoint_hash_count || 0}`,
    `Help profile: ${JSON.stringify(summary.help_level_profile || {})}`,
    `Blockers: ${JSON.stringify(summary.blocker_profile || {})}`,
    `Workspace cards: ${JSON.stringify(summary.workspace_card_profile || {})}`,
    `Confirmations: confirmed=${summary.confirmed_operator_step_count || 0}, open=${summary.open_operator_step_count || 0}`,
    `Reflection: ${(review.reflection_statuses || []).join(", ") || "unknown"}`,
    `Export review: ${pkg.status || "unknown"}, receipt=${receipt.receipt_id || "no-id"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "history export review only"}`,
    "",
    "History:",
    ...(history.slice(0, 6).map((item) => (
      `- #${item.repeat_run_index || 1} ${item.skill_tag || "skill"}: checkpoint=${item.checkpoint_hash || "none"}; help=${item.help_level || "n/a"}; workspace=${(item.local_cycle_operator_workspace_card || {}).status || "missing"}; blockers=${(item.blockers || []).join(", ") || "keine"}`
    ))),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderCourseExamCoverageDashboard(report, sourceLabel) {
  const summary = report.dashboard_summary || {};
  const exportReview = report.export_review_summary || {};
  const skills = report.skill_dashboard || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skills: ${summary.skill_count || 0}, workspace-ready=${summary.workspace_ready_skill_count || 0}, mit Verlauf=${summary.skills_with_history_count || 0}`,
    `Anchors: ${summary.source_anchor_count || 0}, OCR=${summary.ocr_gap_count || 0}, Video=${summary.video_gap_count || 0}`,
    `Checkpoints: ${summary.checkpoint_hash_count || 0}`,
    `Help profile: ${JSON.stringify(summary.help_level_profile || {})}`,
    `Open confirmations: ${summary.open_operator_confirmation_count || 0}`,
    `Export review: ${exportReview.status || "unknown"}, reviewable=${exportReview.human_reviewable_independence_evidence ? "ja" : "nein"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "coverage dashboard only"}`,
    "",
    "Skills:",
    ...(skills.slice(0, 10).map((item) => (
      `- ${item.skill_tag}: ${item.workspace_readiness}; anchors=${item.source_anchor_count || 0}; notebook=${item.reviewed_notebook_anchor_count || 0}; checkpoints=${item.checkpoint_hash_count || 0}; open=${item.open_operator_confirmation_count || 0}; next=${item.next_safe_step || "review"}`
    ))),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPerSkillActionRouter(report, sourceLabel) {
  const selected = report.selected_skill || {};
  const route = report.selected_route || {};
  const summary = report.router_summary || {};
  const template = route.payload_template || {};
  const routes = report.skill_action_routes || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${selected.skill_tag || route.skill_tag || "none"} (${selected.workspace_readiness || "unknown"})`,
    `Route: ${route.route_id || "unknown"}`,
    `Action: ${route.action_label || "unknown"}`,
    `Endpoint: ${route.endpoint || "none"}`,
    `Reason: ${route.reason || "unknown"}`,
    `Dry-run: ${route.dry_run_by_default ? "ja" : "nein"}, Help=${route.requested_help_level || "A2"}`,
    `Confirmations: ${route.operator_confirmation_status || "unknown"} (${route.open_operator_confirmation_count || 0})`,
    `Routes: ${summary.route_count || 0}, session=${summary.ready_session_route_count || 0}, material=${summary.material_route_count || 0}, open=${summary.open_operator_confirmation_route_count || 0}`,
    `Payload: sourceCards=${(template.source_card_ids || []).length || 0}, checkpoints=${(template.checkpoint_hashes || []).length || 0}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "router only"}`,
    "",
    "Routen:",
    ...(routes.slice(0, 10).map((item) => (
      `- ${item.skill_tag}: ${item.route_id}; endpoint=${item.endpoint}; open=${item.open_operator_confirmation_count || 0}`
    ))),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderRoutedActionExecutor(report, sourceLabel) {
  const route = report.selected_route || {};
  const resultSummary = report.execution_result_summary || {};
  const receipt = report.executor_receipt || {};
  const confirmations = report.operator_confirmation_summary || {};
  const resultReceipt = resultSummary.receipt || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${(report.selected_skill || {}).skill_tag || route.skill_tag || "none"}`,
    `Route: ${route.route_id || "unknown"}`,
    `Endpoint: ${report.executed_endpoint || route.endpoint || "none"}`,
    `Result: ${resultSummary.artifact_type || "unknown"} / ${resultSummary.status || "unknown"}`,
    `Result receipt: ${resultReceipt.status || "unknown"} ${resultReceipt.receipt_id || ""}`,
    `Executor receipt: ${receipt.status || "unknown"} ${receipt.receipt_id || ""}`,
    `Confirmations: ${confirmations.confirmed_count || 0}; dry-run=${confirmations.dry_run_by_default ? "ja" : "nein"}`,
    `Local write started: ${resultSummary.local_write_started ? "ja" : "nein"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "routed executor only"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderExamRunPacket(report, sourceLabel) {
  const summary = report.packet_summary || {};
  const skill = report.selected_skill_packet || {};
  const trace = report.human_reviewable_independence_trace || {};
  const receipt = report.packet_receipt || {};
  const chain = report.local_cycle_chain_snapshot || {};
  const chainSummary = chain.chain_snapshot_summary || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${skill.skill_tag || "none"} (${skill.workspace_readiness || "unknown"})`,
    `Route: ${(skill.selected_route || {}).route_id || "unknown"}`,
    `Executed: ${summary.executed_artifact_type || "unknown"} / ${summary.executed_status || "unknown"}`,
    `Checkpoints: ${(skill.latest_checkpoint_hashes || []).length || 0}`,
    `Help profile: ${JSON.stringify(skill.help_level_profile || {})}`,
    `Open confirmations: ${skill.open_operator_confirmation_count || 0}`,
    `Trace: ${trace.trace_status || "unknown"}, no percent=${trace.no_percentage_claimed ? "ja" : "nein"}`,
    `Packet receipt: ${receipt.status || "unknown"} ${receipt.receipt_id || ""}`,
    `Local cycle chain: ${chain.status || "missing"}; steps=${chainSummary.chain_step_count || 0}; hash=${chainSummary.snapshot_hash || ""}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "exam run packet only"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderExamPacketTimeline(report, sourceLabel) {
  const summary = report.timeline_summary || {};
  const receipt = report.timeline_receipt || {};
  const review = report.export_review_preview || {};
  const events = report.timeline_events || [];
  const chain = report.local_cycle_chain_snapshot || {};
  const chainSummary = chain.chain_snapshot_summary || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Events: ${summary.event_count || 0}`,
    `Skills: ${(summary.skill_tags || []).join(", ") || "keine"}`,
    `Packet receipts: ${summary.packet_receipt_count || 0}`,
    `Checkpoint hashes: ${summary.checkpoint_hash_count || 0}`,
    `Help profile: ${JSON.stringify(summary.help_level_profile || {})}`,
    `Open confirmations: ${summary.open_operator_confirmation_count || 0}`,
    `Reflection: ${(summary.reflection_statuses || []).join(", ") || "unknown"}`,
    `Latest next action: ${summary.latest_next_safe_action || "review timeline"}`,
    `Export review: ${review.status || "unknown"}`,
    `Timeline receipt: ${receipt.status || "unknown"} ${receipt.receipt_id || ""}`,
    `Local cycle chain: ${chain.status || "missing"}; steps=${chainSummary.chain_step_count || 0}; hash=${chainSummary.snapshot_hash || ""}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "exam packet timeline only"}`,
    "",
    "Timeline:",
    ...(events.slice(0, 8).map((event) => (
      `- ${event.skill_tag || "skill"}: packet=${event.packet_receipt_status || "unknown"}; route=${event.route_id || "unknown"}; executed=${event.executed_artifact_type || "unknown"}; checkpoints=${event.checkpoint_hash_count || 0}; open=${event.open_operator_confirmation_count || 0}`
    ))),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderTimelineExportReviewPacket(report, sourceLabel) {
  const summary = report.export_review_summary || {};
  const receipt = report.local_export_receipt || {};
  const packets = report.skill_review_packets || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Timelines: ${summary.timeline_count || 0}, events=${summary.event_count || 0}`,
    `Skills: ${(summary.skill_tags || []).join(", ") || "keine"}`,
    `Packet receipts: ${summary.packet_receipt_count || 0}, timeline receipts=${summary.timeline_receipt_count || 0}`,
    `Checkpoint hashes: ${summary.checkpoint_hash_count || 0}`,
    `Help profile: ${JSON.stringify(summary.help_level_profile || {})}`,
    `Open confirmations: ${summary.open_operator_confirmation_count || 0}`,
    `Reflection: ${(summary.reflection_statuses || []).join(", ") || "unknown"}`,
    `Reviewer questions: ${summary.reviewer_question_count || 0}`,
    `Local export receipt: ${receipt.status || "unknown"} ${receipt.receipt_id || ""}`,
    `Local write started: ${receipt.local_write_started ? "ja" : "nein"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "timeline export review only"}`,
    "",
    "Skill Review:",
    ...(packets.slice(0, 8).map((packet) => (
      `- ${packet.skill_tag || "skill"}: events=${packet.event_count || 0}; checkpoints=${packet.checkpoint_hash_count || 0}; open=${packet.open_operator_confirmation_count || 0}; questions=${(packet.human_reviewer_questions || []).length || 0}`
    ))),
    "",
    "Review-Fragen:",
    ...((report.human_reviewer_questions || []).slice(0, 6).map((item) => `- ${item}`)),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderTimelineExportReceiptJournalAppend(report, sourceLabel) {
  const preview = report.write_preview || {};
  const record = report.stored_record || report.preview_record || {};
  const event = record.event || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Journal written: ${report.journal_written ? "ja" : "nein"}`,
    `Operator confirmed: ${report.operator_confirmed_timeline_export_receipt_journal_append ? "ja" : "nein"}`,
    `Preview: ${preview.status || "unknown"}, would append=${preview.would_append ? "ja" : "nein"}`,
    `Receipt: ${event.receipt_id || preview.receipt_id || "missing"}`,
    `Skills: ${(event.skill_tags || preview.skill_tags || []).join(", ") || "keine"}`,
    `Events: ${event.event_count || preview.event_count || 0}`,
    `Checkpoint hashes: ${event.checkpoint_hash_count || preview.checkpoint_hash_count || 0}`,
    `Reviewer questions: ${event.reviewer_question_count || preview.reviewer_question_count || 0}`,
    `Open confirmations: ${event.open_operator_confirmation_count || preview.open_operator_confirmation_count || 0}`,
    `Help profile: ${JSON.stringify(event.help_level_profile || {})}`,
    `Reflection: ${(event.reflection_statuses || []).join(", ") || "unknown"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.storage_policy || "receipt journal only"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderTimelineExportReceiptJournalSummary(summary, sourceLabel) {
  return [
    sourceLabel,
    `Status: ${summary.status || "unknown"}`,
    `Exam: ${summary.exam_deployment_status || "not_cleared"}`,
    `Records: ${summary.record_count || 0}, accepted=${summary.accepted_record_count || 0}, blocked=${summary.blocked_record_count || 0}`,
    `Skills: ${(summary.skill_tags || []).join(", ") || "keine"}`,
    `Events: ${summary.event_count || 0}`,
    `Checkpoint hashes: ${summary.checkpoint_hash_count || 0}`,
    `Reviewer questions: ${summary.reviewer_question_count || 0}`,
    `Open confirmations: ${summary.open_operator_confirmation_count || 0}`,
    `Help profile: ${JSON.stringify(summary.help_level_profile || {})}`,
    `Reflection: ${(summary.reflection_statuses || []).join(", ") || "unknown"}`,
    `Raw query returned: ${summary.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${summary.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${summary.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${summary.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${summary.gate_policy || "journal evidence only"}`
  ].join("\n");
}

function renderReviewChainIntegrityCheck(report, sourceLabel) {
  const summary = report.chain_integrity_summary || {};
  const context = report.chain_context || {};
  const counts = summary.counts || {};
  const receiptIds = summary.receipt_ids || {};
  const findings = report.findings || [];
  const attention = findings.filter((item) => item.status !== "pass");
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Links geprueft: ${summary.checked_link_count || 0}`,
    `Issues: ${summary.issue_count || 0}, missing=${summary.missing_count || 0}, contradiction=${summary.contradiction_count || 0}, duplicate=${summary.duplicate_count || 0}`,
    `Skills: ${(summary.skill_tags || []).join(", ") || "keine"}`,
    `Receipt IDs: packet=${receiptIds.packet_receipt_id || "missing"}, timeline=${receiptIds.timeline_receipt_id || "missing"}, review=${receiptIds.review_receipt_id || "missing"}, journal=${receiptIds.journal_receipt_id || "missing"}`,
    `Counts: events ${counts.timeline_event_count || 0}/${counts.review_event_count || 0}/${counts.journal_event_count || 0}; checkpoints ${counts.timeline_checkpoint_hash_count || 0}/${counts.review_checkpoint_hash_count || 0}/${counts.journal_checkpoint_hash_count || 0}; questions ${counts.reviewer_question_count || 0}/${counts.journal_reviewer_question_count || 0}`,
    `Help profile: ${JSON.stringify(summary.help_level_profiles || {})}`,
    `Open confirmations: ${JSON.stringify(summary.open_operator_confirmation_counts || {})}`,
    `Reflection: ${JSON.stringify(summary.reflection_statuses || {})}`,
    `Journal: ${JSON.stringify(summary.journal_status || {})}`,
    `Safety flags: ${JSON.stringify(context.safety_flags || {})}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Naechste sichere Aktion: ${summary.next_safe_action || "Review chain findings."}`,
    `Grenze: ${report.execution_boundary || "review chain integrity only"}`,
    "",
    "Findings:",
    ...((attention.length ? attention : findings).slice(0, 8).map((item) => (
      `- ${item.status || "unknown"} ${item.finding_type || "check"} ${item.item || "item"}: ${item.detail || ""}`
    ))),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamReadinessConsole(report, sourceLabel) {
  const summary = report.readiness_summary || {};
  const skill = report.selected_skill_readiness || {};
  const coverage = report.material_tutor_coverage || {};
  const checkpoint = report.notebook_checkpoint_status || {};
  const helpStatus = report.a0_a2_help_status || {};
  const confirmations = report.operator_confirmation_status || {};
  const chain = report.review_chain_status || {};
  const journal = report.receipt_journal_status || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${summary.selected_skill_tag || skill.skill_tag || "unknown"}`,
    `Workspace ready: ${summary.skill_ready_for_workspace ? "ja" : "nein"}`,
    `Source anchored: ${summary.source_anchored ? "ja" : "nein"}`,
    `Review chain: ${chain.status || "missing"}, issues=${chain.issue_count || 0}`,
    `Receipt journal: records=${journal.record_count || 0}, accepted=${journal.accepted_record_count || 0}`,
    `Latest checkpoint hash: ${summary.latest_notebook_checkpoint_hash || checkpoint.latest_notebook_checkpoint_hash || "missing"}`,
    `Material: anchors=${coverage.source_anchor_count || 0}, notebooks=${coverage.reviewed_notebook_anchor_count || 0}, course anchors=${coverage.course_source_anchor_count || 0}`,
    `Source Cards: ${(coverage.source_card_ids || []).join(", ") || "keine"}`,
    `A0-A2 help: ${helpStatus.status || "unknown"} ${JSON.stringify(helpStatus.observed_help_profile || {})}`,
    `Nonstandard help events: ${helpStatus.nonstandard_help_event_count || 0}`,
    `Open confirmations: ${summary.open_operator_confirmation_count || confirmations.open_operator_confirmation_count || 0}`,
    `Next safe action: ${summary.next_safe_action || "Readiness evidence pruefen."}`,
    `Reminder: ${report.real_world_clearance_reminder || "not_cleared"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "python exam readiness only"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamCockpitFlow(report, sourceLabel) {
  const summary = report.cockpit_summary || {};
  const confirmations = report.operator_confirmation_status || {};
  const receipts = report.evidence_receipts || {};
  const steps = report.step_bar || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${report.selected_skill_tag || "unknown"}`,
    `Steps: ${summary.complete_step_count || 0}/${summary.step_count || 0} complete, attention=${summary.attention_step_count || 0}, waiting=${summary.waiting_step_count || 0}`,
    `Current: ${summary.current_step_id || "unknown"}`,
    `Open confirmations: ${summary.open_operator_confirmation_count || confirmations.open_operator_confirmation_count || 0}`,
    `Confirmed local write steps: ${confirmations.confirmed_local_write_step_count || 0}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Cockpit writes executed: ${report.local_writes_executed_by_cockpit ? "ja" : "nein"}`,
    `Operator receipt: ${receipts.operator_receipt_id || "missing"}`,
    `Session receipt: ${receipts.session_receipt_id || "missing"}`,
    `Checkpoint hash: ${receipts.notebook_checkpoint_hash || "missing"}`,
    `Review chain: ${receipts.review_chain_status || summary.review_chain_status || "missing"}`,
    `Receipt journal: ${receipts.receipt_journal_accepted_record_count || 0}/${receipts.receipt_journal_record_count || 0}`,
    `Next safe action: ${report.next_safe_action || summary.next_safe_action || "Cockpit pruefen."}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "python exam cockpit only"}`,
    "",
    "Schrittleiste:",
    ...(steps.map((item, index) => (
      `${index + 1}. ${item.label || item.step_id}: ${item.status || "unknown"}; source=${item.source || "unknown"}; next=${item.next_safe_action || "review"}`
    ))),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamLiveControlSurface(report, sourceLabel) {
  const summary = report.control_summary || {};
  const lights = report.status_lights || {};
  const confirmations = report.operator_confirmation_status || {};
  const helpStatus = report.a0_a2_help_status || {};
  const receipts = report.evidence_receipts || {};
  const workspaceCard = report.local_cycle_operator_workspace_card || {};
  const actions = report.control_actions || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Actions: ${summary.enabled_action_count || 0}/${summary.action_count || 0} enabled; attention=${summary.attention_action_count || 0}; waiting=${summary.waiting_action_count || 0}`,
    `Current: ${summary.current_step_id || "unknown"}`,
    `Statusampel: overall=${lights.overall || "grey"}, readiness=${lights.readiness || "grey"}, A0-A2=${lights.a0_a2 || "grey"}, review=${lights.review_chain || "grey"}, receipts=${lights.receipt_journal || "grey"}, exam=${lights.exam_deployment || "grey"}`,
    `Open confirmations: ${summary.open_operator_confirmation_count || confirmations.open_operator_confirmation_count || 0}`,
    `Confirmed local write steps: ${confirmations.confirmed_local_write_step_count || 0}`,
    `A0-A2 help: ${helpStatus.status || "unknown"} (${helpStatus.effective_help_level || "A2"})`,
    `Workspace card: ${workspaceCard.status || "missing"}; ${workspaceCard.help_ledger_preview_status || "no-ledger"}; next=${workspaceCard.next_safe_action || summary.next_safe_action || "review_skill_readiness"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Surface writes executed: ${report.local_writes_executed_by_surface ? "ja" : "nein"}`,
    `Operator receipt: ${receipts.operator_receipt_id || "missing"}`,
    `Session receipt: ${receipts.session_receipt_id || "missing"}`,
    `Checkpoint hash: ${receipts.notebook_checkpoint_hash || "missing"}`,
    `Review chain: ${receipts.review_chain_status || "missing"}`,
    `Receipt journal: ${receipts.receipt_journal_accepted_record_count || 0}/${receipts.receipt_journal_record_count || 0}`,
    `Next safe action: ${report.next_safe_action || summary.next_safe_action || "Live Control pruefen."}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "python exam live control only"}`,
    "",
    "Sichere Aktionen:",
    ...(actions.map((item, index) => (
      `${index + 1}. [${item.light || "grey"}] ${item.label || item.safe_action_id}: ${item.method || "POST"} ${item.endpoint || "missing"}; status=${item.status || "unknown"}; confirm=${item.requires_operator_confirmation_for_local_writes ? (item.local_write_confirmation_keys || []).join(", ") || "required" : "nein"}; next=${item.next_safe_action || "review"}`
    ))),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamEvidenceExportPreview(report, sourceLabel) {
  const summary = report.preview_summary || {};
  const manifest = report.preview_manifest || {};
  const readiness = manifest.readiness_snapshot || {};
  const receipts = manifest.evidence_receipts || {};
  const helpProfile = manifest.help_level_profile || {};
  const confirmations = manifest.operator_confirmation_profile || {};
  const checkpoint = manifest.notebook_checkpoint || {};
  const reviewChain = manifest.review_chain_status || {};
  const journal = manifest.receipt_journal_summary || {};
  const human = report.human_review_packet || {};
  const receipt = report.preview_receipt || {};
  const steps = manifest.cockpit_steps || [];
  const actions = manifest.live_control_actions || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Readiness: ${summary.readiness_status || readiness.status || "missing"}; workspace=${summary.skill_ready_for_workspace ? "ja" : "nein"}`,
    `Cockpit steps: ${summary.cockpit_step_count || steps.length || 0}`,
    `Live actions: ${summary.live_control_action_count || actions.length || 0}`,
    `Help: ${summary.help_status || helpProfile.status || "missing"} ${JSON.stringify(helpProfile.profile || {})}`,
    `Open confirmations: ${summary.open_operator_confirmation_count || confirmations.open_operator_confirmation_count || 0}`,
    `Review chain: ${summary.review_chain_status || reviewChain.status || "missing"}, issues=${summary.review_chain_issue_count || reviewChain.issue_count || 0}`,
    `Checkpoint hash: ${checkpoint.notebook_checkpoint_hash || receipts.notebook_checkpoint_hash || "missing"}`,
    `Receipt journal: accepted=${summary.receipt_journal_accepted_record_count || journal.accepted_record_count || 0}, records=${journal.record_count || 0}`,
    `Evidence receipts: operator=${receipts.operator_receipt_id || "missing"}, session=${receipts.session_receipt_id || "missing"}, review=${receipts.review_receipt_id || "missing"}`,
    `Preview receipt: ${receipt.receipt_id || "missing"}`,
    `Human review: ${summary.human_review_status || human.status || "missing"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Export preview only: ${report.export_preview_only ? "ja" : "nein"}`,
    `Local export written: ${report.local_export_package_written ? "ja" : "nein"}`,
    `Next safe action: ${summary.next_safe_action || report.next_safe_action || "Preview pruefen."}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "python exam evidence export preview only"}`,
    "",
    "Review-Fragen:",
    ...((human.review_questions || []).slice(0, 8).map((item) => `- ${item}`)),
    "",
    "Sichere Aktionen im Preview:",
    ...(actions.slice(0, 9).map((item, index) => (
      `${index + 1}. ${item.label || item.safe_action_id}: ${item.status || "unknown"}; endpoint=${item.endpoint || "missing"}; confirm=${item.requires_operator_confirmation_for_local_writes ? (item.local_write_confirmation_keys || []).join(", ") || "required" : "nein"}`
    ))),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamTutorDrillPack(report, sourceLabel) {
  const summary = report.drill_pack_summary || {};
  const receipt = report.pack_receipt || {};
  const drills = report.skill_drills || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Drills: ${summary.ready_drill_count || 0}/${summary.skill_count || drills.length || 0}`,
    `Microtasks: ${summary.microtask_count || 0}; Retrieval-Fragen: ${summary.retrieval_question_count || 0}`,
    `Checkpoint templates: ${summary.checkpoint_template_count || 0}`,
    `Help: ${summary.help_status || "a0_a2_only"}`,
    `Carryover: ${summary.carryover_status || "missing"}`,
    `Receipt: ${receipt.receipt_id || "missing"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Solutions returned: ${report.solutions_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "source-grounded A0-A2 tutor drill pack only"}`,
    "",
    "Drills:",
    ...(drills.slice(0, 8).map((item) => (
      `- ${item.skill_tag}: ${item.status}; cards=${(((item.source_anchor_metadata || {}).source_card_ids || []).join(", ") || "keine")}; tasks=${(item.microtasks || []).length}; checkpoint=${(item.notebook_checkpoint_suggestions || {}).checkpoint_template_hash || "missing"}`
    ))),
    "",
    "Erster Drill im Detail:",
    ...(((drills[0] || {}).microtasks || []).slice(0, 3).map((item) => `- ${item.task_id}: ${item.prompt_summary}`)),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamDrillSessionRunner(report, sourceLabel) {
  const summary = report.drill_session_summary || {};
  const task = report.selected_microtask || {};
  const checkpoint = report.notebook_checkpoint_adapter_summary || {};
  const ledger = report.help_ledger_preview || {};
  const carryover = report.carryover_reference || {};
  const receipt = report.drill_session_receipt || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${report.selected_skill_tag || "unknown"}`,
    `Task: ${task.task_id || "missing"}`,
    `Task hash: ${task.task_hash || "missing"}`,
    `Checkpoint: ${checkpoint.status || "missing"}, hash=${checkpoint.notebook_work_sha256 || "missing"}`,
    `Study receipt: ${checkpoint.study_receipt_status || "missing"}`,
    `Help-Ledger preview: ${ledger.status || "missing"}, event=${ledger.event_hash || "missing"}`,
    `Carryover: ${carryover.status || "missing"}, session=${carryover.session_receipt_id || "missing"}`,
    `Receipt: ${receipt.receipt_id || "missing"}`,
    `Help: ${summary.help_status || "a0_a2_only"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Checkpoint write confirmed: ${(report.operator_confirmations || {}).checkpoint_store ? "ja" : "nein"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Raw cell returned: ${report.raw_cell_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Solutions returned: ${report.solutions_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "source-grounded A0-A2 drill session only"}`,
    "",
    "Microtask:",
    `- ${task.prompt_summary || "selected source-grounded task"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamDrillSessionReviewLoop(report, sourceLabel) {
  const summary = report.review_loop_summary || {};
  const evidence = report.session_evidence_summary || {};
  const next = report.next_step_recommendation || {};
  const receipt = report.review_loop_receipt || {};
  const reflection = report.reflection_status || {};
  const ledger = report.help_ledger_preview || {};
  const carryover = report.carryover_reference || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${report.selected_skill_tag || evidence.skill_tag || "unknown"}`,
    `Loop: ${summary.review_loop_index || 1}`,
    `Current task hash: ${evidence.microtask_hash || summary.current_task_hash || "missing"}`,
    `Checkpoint hash: ${evidence.checkpoint_hash || summary.checkpoint_hash || "missing"}`,
    `Reflection: ${reflection.status || "missing"}`,
    `Help-Ledger: ${ledger.status || "missing"}, event=${ledger.event_hash || "missing"}`,
    `Carryover session: ${carryover.session_receipt_id || "missing"}`,
    `Next: ${next.action || "missing"} (${next.status || "unknown"})`,
    `Next task hash: ${next.next_task_hash || "none"}`,
    `Receipt: ${receipt.receipt_id || "missing"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Percentage returned: ${report.percentage_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Solutions returned: ${report.solutions_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only review loop"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamDrillLoopControlPanel(report, sourceLabel) {
  const summary = report.control_panel_summary || {};
  const current = report.current_microtask || {};
  const evidence = report.session_evidence_summary || {};
  const next = report.next_step_recommendation || {};
  const receipt = report.control_panel_receipt || {};
  const cards = report.cycle_cards || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Current task hash: ${current.task_hash || summary.current_task_hash || "missing"}`,
    `Checkpoint hash: ${evidence.checkpoint_hash || summary.checkpoint_hash || "missing"}`,
    `Source cards: ${(evidence.source_card_ids || []).join(", ") || "keine"}`,
    `Help: ${summary.help_status || "a0_a2_only"}`,
    `Reflection: ${summary.reflection_status || evidence.reflection_status || "missing"}`,
    `Next: ${next.action || summary.next_step_action || "missing"} (${next.status || summary.next_step_status || "unknown"})`,
    `Next task hash: ${next.next_task_hash || summary.next_task_hash || "none"}`,
    `Receipt: ${receipt.receipt_id || "missing"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Percentage returned: ${report.percentage_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Solutions returned: ${report.solutions_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only drill loop control panel"}`,
    "",
    "Cycle:",
    ...(cards.map((item) => `- ${item.label || item.card_id}: ${item.status || "unknown"}; receipt=${item.receipt_id || "missing"}`)),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamDrillLoopProgressJournal(report, sourceLabel) {
  const summary = report.append_summary || {};
  const entry = report.journal_entry_preview || {};
  const resume = report.resume_state || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Journal written: ${report.journal_written ? "ja" : "nein"}`,
    `Operator confirmed: ${report.operator_confirmed_progress_journal_append ? "ja" : "nein"}`,
    `Skill: ${entry.skill_tag || summary.skill_tag || "unknown"}`,
    `Microtask hash: ${entry.microtask_hash || resume.last_safe_microtask_hash || "missing"}`,
    `Checkpoint hash: ${entry.checkpoint_hash || resume.last_checkpoint_hash || "missing"}`,
    `Source anchors: ${(entry.source_card_ids || []).join(", ") || "keine"}`,
    `Help: ${entry.help_level || "A2"}`,
    `Help-Ledger event: ${entry.help_ledger_event_hash || "missing"}`,
    `Carryover receipt: ${entry.carryover_session_receipt_id || "missing"}`,
    `Review receipt: ${entry.review_loop_receipt_id || "missing"}`,
    `Next: ${entry.next_step_action || resume.resume_action || "missing"} (${entry.next_step_status || "unknown"})`,
    `Next task hash: ${entry.next_task_hash || resume.next_microtask_hash || "none"}`,
    `Open repeat: ${resume.open_repeat_task_hash || "none"}`,
    `Accepted records: ${resume.accepted_record_count || 0}/${resume.record_count || 0}`,
    `Reflection: ${entry.reflection_status || resume.reflection_status || "missing"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only progress journal"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamResumeLauncher(report, sourceLabel) {
  const decision = report.resume_decision || {};
  const prefill = report.control_panel_prefill || {};
  const resume = report.resume_state || {};
  const latest = report.latest_progress_entry || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Action: ${decision.action || "start_first_microtask"}`,
    `Route: ${decision.route || "control_panel"}`,
    `Endpoint: ${prefill.endpoint || "missing"}`,
    `Skill: ${decision.selected_skill_tag || latest.skill_tag || "unknown"}`,
    `Selected task hash: ${decision.selected_task_hash || prefill.selected_task_hash || "none"}`,
    `Checkpoint hash: ${decision.checkpoint_hash || resume.last_checkpoint_hash || "none"}`,
    `Help: ${decision.help_level || prefill.requested_help_level || "A2"}`,
    `Source anchors: ${(prefill.source_card_ids || latest.source_card_ids || []).join(", ") || "keine"}`,
    `Prefill hash: ${prefill.prefill_hash || "missing"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only resume launcher"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamActiveStudyLoopDashboard(report, sourceLabel) {
  const summary = report.active_study_summary || {};
  const rows = report.skill_loop_dashboard || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Selected skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Skills: ${summary.skill_count || 0}, ready=${summary.workspace_ready_skill_count || 0}`,
    `Resume action: ${summary.active_resume_action || "unknown"}`,
    `Next safe action: ${summary.next_safe_action || "review"}`,
    `Open repeats: ${summary.open_repeat_count || 0}`,
    `Completed loops: ${summary.completed_skill_loop_count || 0}`,
    `Source anchors: ${summary.source_anchor_count || 0}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only active study loop"}`,
    "",
    "Skill-Loops:",
    ...(rows.slice(0, 8).map((item) => (
      `- ${item.skill_tag}: ready=${item.workspace_readiness || "unknown"}; task=${item.last_safe_microtask_hash || item.next_microtask_hash || item.open_repeat_task_hash || "none"}; next=${item.next_safe_action || "review"}; anchors=${item.source_anchor_count || 0}; help=${item.help_level || "A2"}; checkpoint=${item.checkpoint_hash || "none"}`
    ))),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamActiveStudyGuidedRunner(report, sourceLabel) {
  const summary = report.guided_runner_summary || {};
  const card = report.guided_action_card || {};
  const prefill = report.control_panel_prefill || report.dashboard_return_prefill || {};
  const receipt = report.guided_runner_receipt || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${summary.selected_skill_tag || card.selected_skill_tag || "unknown"}`,
    `Action: ${summary.action || card.action || "review_skill_readiness"}`,
    `Route: ${summary.route || card.route || "skill_dashboard"}`,
    `Endpoint: ${summary.endpoint || card.endpoint || prefill.endpoint || "missing"}`,
    `Selected task hash: ${summary.selected_task_hash || card.selected_task_hash || "none"}`,
    `Checkpoint hash: ${summary.checkpoint_hash || card.checkpoint_hash || "none"}`,
    `Help: ${summary.help_level || card.help_level || "A2"}`,
    `Source anchors: ${(card.source_card_ids || prefill.source_card_ids || []).join(", ") || "keine"}`,
    `Prefill hash: ${(prefill || {}).prefill_hash || "missing"}`,
    `Receipt: ${receipt.receipt_id || "missing"}`,
    `Ready: ${card.ready ? "ja" : "nein"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Operator confirmations: ${(card.operator_confirmations_required || []).join(", ") || "keine"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only guided runner"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamGuidedActionExecutionBridge(report, sourceLabel) {
  const summary = report.execution_bridge_summary || {};
  const preview = report.control_panel_cycle_preview || report.dashboard_return_preview || {};
  const matrix = report.operator_confirmation_matrix || {};
  const receipt = report.execution_bridge_receipt || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${summary.selected_skill_tag || preview.selected_skill_tag || "unknown"}`,
    `Action: ${summary.action || preview.action || "review_skill_readiness"}`,
    `Route: ${summary.route || preview.route || "skill_dashboard"}`,
    `Endpoint: ${summary.endpoint || preview.endpoint || "missing"}`,
    `Preview: ${summary.preview_status || preview.status || "missing"}`,
    `Selected task hash: ${summary.selected_task_hash || preview.selected_task_hash || "none"}`,
    `Checkpoint hash: ${summary.checkpoint_hash || preview.checkpoint_hash || "none"}`,
    `Help: ${summary.help_level || preview.help_level || "A2"}`,
    `Source anchors: ${(preview.source_card_ids || []).join(", ") || "keine"}`,
    `Progress preview: ${preview.progress_journal_preview_status || "missing"}`,
    `Confirmations: ${matrix.confirmed_count || 0}; status=${matrix.status || "all_steps_dry_run"}`,
    `Receipt: ${receipt.receipt_id || "missing"}`,
    `Ready: ${summary.ready ? "ja" : "nein"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only execution bridge"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamSafeCycleConsole(report, sourceLabel) {
  const summary = report.safe_cycle_summary || {};
  const view = report.current_cycle_view || {};
  const preview = view.preview || {};
  const receipts = view.receipts || {};
  const matrix = view.operator_confirmation_matrix || {};
  const receipt = report.safe_cycle_receipt || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Cycle: ${summary.cycle_status || "safe_cycle_attention"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Next action: ${summary.next_safe_action || preview.action || "review_skill_readiness"}`,
    `Route: ${summary.route || preview.route || "missing"}`,
    `Endpoint: ${summary.endpoint || preview.endpoint || "missing"}`,
    `Preview: ${summary.preview_status || preview.status || "missing"}`,
    `Task hash: ${summary.selected_task_hash || preview.selected_task_hash || "none"}`,
    `Checkpoint hash: ${summary.checkpoint_hash || preview.checkpoint_hash || "none"}`,
    `Help: ${summary.help_level || preview.help_level || "A2"}`,
    `Source anchors: ${(preview.source_card_ids || []).join(", ") || "keine"}`,
    `Help ledger: ${receipts.help_ledger_event_hash || "missing"}`,
    `Review receipt: ${receipts.review_loop_receipt_id || "missing"}`,
    `Progress entry: ${receipts.progress_entry_hash || "missing"}`,
    `Confirmations: ${matrix.confirmed_count || 0}; status=${matrix.status || "all_steps_dry_run"}`,
    `Receipt: ${receipt.receipt_id || "missing"}`,
    `Ready: ${summary.ready ? "ja" : "nein"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only safe cycle console"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamSafeCycleOperatorGate(report, sourceLabel) {
  const summary = report.operator_gate_summary || {};
  const matrix = report.operator_confirmation_matrix || {};
  const receipt = report.operator_gate_receipt || {};
  const cards = report.confirmation_cards || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Gate: ${summary.gate_status || "operator_gate_attention"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Next action: ${summary.next_safe_action || "review_skill_readiness"}`,
    `Route: ${summary.route || "missing"}`,
    `Task hash: ${summary.selected_task_hash || "none"}`,
    `Checkpoint hash: ${summary.checkpoint_hash || "none"}`,
    `Help: ${summary.help_level || "A2"}`,
    `Cards: ${summary.confirmation_card_count || cards.length}; confirmed=${summary.confirmed_count || 0}`,
    `Confirmations: ${matrix.status || "all_steps_waiting_for_operator_confirmation"}`,
    `Receipt: ${receipt.receipt_id || "missing"}`,
    `Ready: ${summary.ready ? "ja" : "nein"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    "",
    "Confirmation Cards:",
    ...(cards.slice(0, 8).map((card) => (
      `- ${card.step_id}: confirmed=${card.operator_confirmed ? "ja" : "nein"}; write=${card.write_started ? "ja" : "nein"}; help=${card.help_level || "A2"}; hash=${card.card_hash || "missing"}`
    ))),
    "",
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only operator gate"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamOperatorGateDecisionReceipt(report, sourceLabel) {
  const summary = report.decision_receipt_summary || {};
  const next = report.next_allowed_local_action || {};
  const receipt = report.operator_decision_receipt || {};
  const unconfirmed = report.unconfirmed_steps || [];
  const confirmed = report.confirmed_step_hash_metadata || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Decision: ${summary.decision_status || "decision_receipt_attention"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Cards: ${summary.card_count || 0}; confirmed=${summary.confirmed_count || 0}; open=${summary.unconfirmed_count || 0}`,
    `Next confirmable: ${summary.next_confirmable_step_id || next.step_id || "none"}`,
    `Next allowed action: ${summary.next_allowed_local_action || next.action || "review_operator_gate_cards"}`,
    `Execution started: ${summary.local_action_execution_started ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Receipt: ${receipt.receipt_id || "missing"}`,
    "",
    "Unconfirmed:",
    ...(unconfirmed.slice(0, 8).map((item) => (
      `- ${item.step_id}: next=${item.next_confirmable ? "ja" : "nein"}; hash=${item.card_hash || "missing"}`
    ))),
    "",
    "Confirmed hash metadata:",
    ...(confirmed.slice(0, 8).map((item) => `- ${item.step_id}: hash=${item.card_hash || "missing"}`)),
    "",
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only decision receipt"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamLocalCycleStartPacket(report, sourceLabel) {
  const summary = report.local_cycle_start_summary || {};
  const packet = report.start_packet || {};
  const receipt = report.local_cycle_start_receipt || {};
  const open = packet.open_confirmations || [];
  const confirmed = packet.confirmed_hash_metadata || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Start: ${summary.start_status || packet.start_status || "blocked_for_confirmation"}`,
    `Blocked reason: ${summary.blocked_reason || packet.blocked_reason || "operator_confirmations_open"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Next action: ${summary.next_safe_action || packet.next_safe_action || "review_skill_readiness"}`,
    `Next user action: ${summary.next_safe_user_action || packet.next_safe_user_action || "review_next_operator_confirmation"}`,
    `Task hash: ${summary.selected_task_hash || packet.task_hash || "none"}`,
    `Checkpoint hash: ${summary.checkpoint_hash || packet.checkpoint_hash || "none"}`,
    `Help: ${summary.help_level || packet.help_level || "A2"}`,
    `Open confirmations: ${summary.open_confirmation_count || open.length}`,
    `Confirmed hash metadata: ${summary.confirmed_count || confirmed.length}`,
    `Gate receipt: ${packet.gate_receipt_id || "missing"}`,
    `Decision receipt: ${packet.decision_receipt_id || "missing"}`,
    `Packet receipt: ${receipt.receipt_id || "missing"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    "",
    "Open confirmations:",
    ...(open.slice(0, 8).map((item) => `- ${item.step_id}: hash=${item.card_hash || "missing"}`)),
    "",
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only local cycle start packet"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamLocalCycleReadinessReview(report, sourceLabel) {
  const summary = report.readiness_review_summary || {};
  const packet = report.local_cycle_start_packet || {};
  const receipt = report.readiness_review_receipt || {};
  const open = packet.open_confirmations || [];
  const confirmed = packet.confirmed_hash_metadata || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Recommendation: ${summary.recommendation || "keep_blocked"}`,
    `Reason: ${summary.recommendation_reason || "missing_start_packet"}`,
    `Cycle state: ${summary.start_status || packet.start_status || "missing"}`,
    `Blocked: ${summary.blocked_for_confirmation ? "ja" : "nein"}`,
    `Open confirmations: ${summary.open_confirmation_count || open.length}`,
    `Confirmed hash metadata: ${summary.confirmed_count || confirmed.length}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Next action: ${summary.next_safe_action || packet.next_safe_action || "review_skill_readiness"}`,
    `Next user action: ${summary.next_safe_user_action || packet.next_safe_user_action || "review_confirmed_start_packet"}`,
    `Task hash: ${summary.task_hash || packet.task_hash || "none"}`,
    `Checkpoint hash: ${summary.checkpoint_hash || packet.checkpoint_hash || "none"}`,
    `Help: ${summary.help_level || packet.help_level || "A2"}`,
    `Source anchors: ${(summary.source_card_ids || packet.source_card_ids || []).join(", ") || "keine"}`,
    `Gate receipt: ${summary.gate_receipt_id || packet.gate_receipt_id || "missing"}`,
    `Decision receipt: ${summary.decision_receipt_id || packet.decision_receipt_id || "missing"}`,
    `Start receipt: ${summary.start_receipt_id || packet.start_receipt_id || receipt.receipt_id || "missing"}`,
    `Ready for manual local cycle review: ${summary.ready_for_manual_local_cycle_review ? "ja" : "nein"}`,
    `Request missing confirmation review: ${summary.request_missing_confirmation_review ? "ja" : "nein"}`,
    `Keep blocked: ${summary.keep_blocked ? "ja" : "nein"}`,
    `Receipt: ${receipt.receipt_id || "missing"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only readiness review"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamLocalCycleReadinessHandoff(report, sourceLabel) {
  const summary = report.handoff_summary || {};
  const prefill = report.operator_run_prefill || {};
  const manual = report.manual_local_cycle_handoff || {};
  const packet = report.local_cycle_start_packet || {};
  const receipt = report.handoff_receipt || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Recommendation: ${summary.recommendation || "keep_blocked"}`,
    `Reason: ${summary.recommendation_reason || "missing_start_packet"}`,
    `Handoff ready: ${summary.ready_for_operator_prefill ? "ja" : "nein"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Review status: ${summary.readiness_review_status || report.readiness_review_status || "missing"}`,
    `Start status: ${summary.start_packet_status || report.local_cycle_start_packet_status || packet.start_status || "missing"}`,
    `Next action: ${summary.next_safe_action || manual.next_operator_action || "resolve_readiness_review_attention_items"}`,
    `Operator endpoint: ${summary.operator_run_endpoint || prefill.endpoint || "missing"}`,
    `Operator method: ${summary.operator_run_method || prefill.method || "POST"}`,
    `Prefill status: ${prefill.status || "missing"}`,
    `Prefill hash: ${prefill.prefill_hash || "missing"}`,
    `Manual handoff status: ${manual.status || "missing"}`,
    `Manual next operator action: ${manual.next_operator_action || "missing"}`,
    `Task hash: ${summary.task_hash || prefill.task_hash || manual.task_hash || "none"}`,
    `Checkpoint hash: ${summary.checkpoint_hash || prefill.checkpoint_hash || manual.checkpoint_hash || "none"}`,
    `Help: ${summary.help_level || prefill.requested_help_level || manual.help_level || "A2"}`,
    `Source anchors: ${(prefill.source_card_ids || manual.source_card_ids || packet.source_card_ids || []).join(", ") || "keine"}`,
    `Open confirmations: ${summary.open_confirmation_count || manual.open_confirmation_count || 0}`,
    `Confirmed hash metadata: ${summary.confirmed_count || manual.confirmed_count || 0}`,
    `Receipt: ${receipt.receipt_id || "missing"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only readiness handoff"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamLocalCycleOperatorWorkspaceCard(report, sourceLabel) {
  const summary = report.workspace_card_summary || {};
  const review = report.readiness_review || {};
  const handoff = report.readiness_handoff || {};
  const ledger = report.help_ledger_preview || {};
  const prefill = report.operator_run_prefill || {};
  const manual = report.manual_local_cycle_handoff || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Recommendation: ${summary.recommendation || review.recommendation || "keep_blocked"}`,
    `Reason: ${summary.recommendation_reason || review.recommendation_reason || "missing_start_packet"}`,
    `Next safe action: ${summary.next_safe_action || review.next_safe_action || "review_skill_readiness"}`,
    `Next user action: ${summary.next_safe_user_action || review.next_safe_user_action || "review_confirmed_start_packet"}`,
    `Workspace ready: ${summary.ready_for_operator_prefill ? "ja" : "nein"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Review: ${summary.readiness_review_status || review.status || "missing"}`,
    `Handoff: ${summary.readiness_handoff_status || handoff.status || "missing"}`,
    `Help-Ledger Preview: ${summary.help_ledger_preview_status || ledger.status || "missing"} (${summary.help_ledger_preview_hash || ledger.preview_hash || "no-hash"})`,
    `Help: ${summary.help_level || ledger.help_level || "A2"}`,
    `Task hash: ${summary.task_hash || report.task_hash || "none"}`,
    `Checkpoint hash: ${summary.checkpoint_hash || report.checkpoint_hash || "none"}`,
    `Source cards: ${(summary.source_card_ids || report.source_card_ids || []).join(", ") || "keine"}`,
    `Open confirmations: ${summary.open_confirmation_count || 0}`,
    `Confirmed hash metadata: ${summary.confirmed_count || 0}`,
    `Operator endpoint: ${summary.operator_run_endpoint || handoff.operator_run_endpoint || prefill.endpoint || "missing"}`,
    `Operator method: ${summary.operator_run_method || handoff.operator_run_method || prefill.method || "POST"}`,
    `Prefill hash: ${prefill.prefill_hash || handoff.prefill_hash || "missing"}`,
    `Manual next operator action: ${manual.next_operator_action || handoff.manual_next_operator_action || "missing"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only operator workspace card"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamLocalCycleChainSnapshot(report, sourceLabel) {
  const summary = report.chain_snapshot_summary || {};
  const receipt = report.chain_snapshot_receipt || {};
  const steps = report.chain_steps || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Chain present: ${summary.chain_present ? "ja" : "nein"}`,
    `Chain hash complete: ${summary.chain_hash_complete ? "ja" : "nein"}`,
    `Ready for manual local cycle review: ${summary.chain_ready_for_manual_local_cycle_review ? "ja" : "nein"}`,
    `Review recommendation: ${summary.review_recommendation || "keep_blocked"}`,
    `Ready for operator prefill: ${summary.ready_for_operator_prefill ? "ja" : "nein"}`,
    `Task hash: ${summary.task_hash || "none"}`,
    `Checkpoint hash: ${summary.checkpoint_hash || "none"}`,
    `Source cards: ${(summary.source_card_ids || []).join(", ") || "keine"}`,
    `Help: ${summary.help_level || "A2"}`,
    `Open confirmations: ${summary.open_confirmation_count || 0}`,
    `Confirmed hash metadata: ${summary.confirmed_count || 0}`,
    `Snapshot hash: ${summary.snapshot_hash || report.snapshot_hash || "missing"}`,
    `Receipt: ${receipt.receipt_id || "missing"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    "",
    "Chain steps:",
    ...(steps.slice(0, 6).map((item) => `- ${item.step_id}: ${item.status}; receipt=${item.receipt_hash || "missing"}`)),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamManualConfirmationConsole(report, sourceLabel) {
  const summary = report.console_summary || {};
  const matrix = report.confirmation_matrix || {};
  const metadata = report.source_checkpoint_metadata || {};
  const receipt = report.manual_confirmation_console_receipt || {};
  const open = report.open_confirmation_cards || [];
  const confirmed = report.confirmed_hash_metadata_cards || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Next manual action: ${summary.next_manual_confirmation_action || report.next_manual_confirmation_action || "refresh_start_packet_review"}`,
    `Reason: ${summary.next_manual_confirmation_reason || "missing_start_packet_or_chain_hash_metadata"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Review: ${summary.readiness_review_status || "missing"}; recommendation=${summary.readiness_recommendation || "keep_blocked"}`,
    `Handoff: ${summary.handoff_status || "missing"}`,
    `Workspace: ${summary.operator_workspace_card_status || "missing"}`,
    `Chain: ${summary.chain_snapshot_status || "missing"}; hash complete=${summary.chain_hash_complete ? "ja" : "nein"}`,
    `Start: ${summary.start_status || "missing"}`,
    `Open confirmations: ${matrix.open_count || 0}`,
    `Confirmed hash metadata: ${matrix.confirmed_count || 0}`,
    `Task hash: ${metadata.task_hash || summary.task_hash || "none"}`,
    `Checkpoint hash: ${metadata.checkpoint_hash || summary.checkpoint_hash || "none"}`,
    `Source cards: ${(metadata.source_card_ids || summary.source_card_ids || []).join(", ") || "keine"}`,
    `Help: ${metadata.help_level || summary.help_level || "A2"}`,
    `Receipt: ${receipt.receipt_id || "missing"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    "",
    "Open confirmation cards:",
    ...(open.slice(0, 8).map((item) => `- ${item.step_id}: action=${item.action || "review"}; hash=${item.card_hash || "missing"}`)),
    "",
    "Confirmed hash metadata cards:",
    ...(confirmed.slice(0, 8).map((item) => `- ${item.step_id}: action=${item.action || "confirmed"}; hash=${item.card_hash || "missing"}`)),
    "",
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only manual confirmation console"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamManualCycleLaunchReceipt(report, sourceLabel) {
  const summary = report.launch_receipt_summary || {};
  const metadata = report.launch_metadata || {};
  const confirmation = report.confirmation_review || {};
  const prefill = report.operator_run_prefill || {};
  const receipt = report.manual_cycle_launch_receipt || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Launch decision: ${summary.launch_decision || report.launch_decision || "refresh_manual_console"}`,
    `Reason: ${summary.launch_decision_reason || "manual_confirmation_console_needs_refresh"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Manual console: ${summary.manual_confirmation_console_status || confirmation.manual_confirmation_console_status || "missing"}`,
    `Manual action: ${summary.manual_confirmation_action || confirmation.manual_confirmation_action || "refresh_start_packet_review"}`,
    `Chain: ${summary.chain_snapshot_status || "missing"}`,
    `Workspace: ${summary.operator_workspace_card_status || "missing"}`,
    `Handoff: ${summary.handoff_status || "missing"}`,
    `Prefill: ${summary.operator_prefill_status || prefill.status || "missing"}`,
    `Open confirmations: ${summary.open_confirmation_count || confirmation.open_confirmation_count || 0}`,
    `Confirmed hash metadata: ${summary.confirmed_count || confirmation.confirmed_count || 0}`,
    `Task hash: ${metadata.task_hash || summary.task_hash || "none"}`,
    `Checkpoint hash: ${metadata.checkpoint_hash || summary.checkpoint_hash || "none"}`,
    `Source cards: ${(metadata.source_card_ids || summary.source_card_ids || []).join(", ") || "keine"}`,
    `Help: ${metadata.help_level || summary.help_level || "A2"}`,
    `Operator endpoint: ${metadata.operator_run_endpoint || prefill.endpoint || "missing"}`,
    `Operator prefill hash: ${metadata.operator_run_prefill_hash || prefill.prefill_hash || "missing"}`,
    `Console receipt hash: ${metadata.manual_confirmation_console_receipt_hash || confirmation.manual_confirmation_console_receipt_hash || "missing"}`,
    `Chain snapshot hash: ${metadata.chain_snapshot_hash || "missing"}`,
    `Receipt: ${receipt.receipt_id || "missing"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only manual cycle launch receipt"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamManualCycleEvidenceBinder(report, sourceLabel) {
  const summary = report.binder_summary || {};
  const evidence = report.manual_cycle_evidence || {};
  const receipt = report.manual_cycle_evidence_binder_receipt || {};
  const windowInfo = report.cycle_review_window || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Next safe review action: ${summary.next_safe_review_action || report.next_safe_review_action || "refresh_launch_receipt"}`,
    `Reason: ${summary.next_safe_review_reason || "launch_receipt_missing_or_unhashed"}`,
    `Launch decision: ${summary.launch_decision || evidence.launch_decision || "refresh_manual_console"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Required hashes present: ${summary.required_hashes_present ? "ja" : "nein"}`,
    `Open confirmations: ${summary.open_confirmation_count || evidence.open_confirmation_count || 0}`,
    `Confirmed hash metadata: ${summary.confirmed_count || evidence.confirmed_count || 0}`,
    `Task hash: ${summary.task_hash || evidence.task_hash || "none"}`,
    `Checkpoint hash: ${summary.checkpoint_hash || evidence.checkpoint_hash || "none"}`,
    `Source cards: ${(summary.source_card_ids || evidence.source_card_ids || []).join(", ") || "keine"}`,
    `Help: ${summary.help_level || evidence.help_level || "A2"}`,
    `Help ledger preview hash: ${summary.help_ledger_preview_hash || evidence.help_ledger_preview_hash || "missing"}`,
    `Gate receipt hash: ${summary.gate_receipt_hash || evidence.gate_receipt_hash || "missing"}`,
    `Decision receipt hash: ${summary.decision_receipt_hash || evidence.decision_receipt_hash || "missing"}`,
    `Start receipt hash: ${summary.start_receipt_hash || evidence.start_receipt_hash || "missing"}`,
    `Chain snapshot hash: ${summary.chain_snapshot_hash || evidence.chain_snapshot_hash || "missing"}`,
    `Launch receipt hash: ${summary.launch_receipt_hash || evidence.launch_receipt_hash || "missing"}`,
    `Binder receipt: ${receipt.receipt_id || "missing"}`,
    `Pre-cycle bound: ${windowInfo.pre_cycle_chain_bound ? "ja" : "nein"}`,
    `Post-cycle execution claimed: ${windowInfo.post_cycle_execution_claimed ? "ja" : "nein"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only manual cycle evidence binder"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamManualPostCycleReceiptIntake(report, sourceLabel) {
  const summary = report.post_cycle_intake_summary || {};
  const metadata = report.post_cycle_hash_metadata || {};
  const pre = report.pre_cycle_evidence || {};
  const receipt = report.manual_post_cycle_receipt_intake || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Recommendation: ${summary.post_cycle_review_recommendation || report.post_cycle_review_recommendation || "keep_post_cycle_review_open"}`,
    `Reason: ${summary.post_cycle_review_reason || "pre_cycle_stop_go_chain_not_ready_for_post_cycle_intake"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Binder action: ${summary.binder_next_safe_review_action || pre.binder_next_safe_review_action || "refresh_launch_receipt"}`,
    `Launch decision: ${summary.launch_decision || pre.launch_decision || "refresh_manual_console"}`,
    `Metadata: ${summary.metadata_status || metadata.status || "post_cycle_hash_metadata_missing"}`,
    `Missing hashes: ${(summary.missing_required_hashes || metadata.missing_required_hashes || []).join(", ") || "keine"}`,
    `Forbidden metadata keys: ${(summary.forbidden_metadata_keys || metadata.forbidden_metadata_keys || []).join(", ") || "keine"}`,
    `Task hash: ${summary.task_hash || metadata.task_hash || "none"}`,
    `Notebook checkpoint hash: ${summary.notebook_checkpoint_hash || metadata.notebook_checkpoint_hash || "missing"}`,
    `Help ledger entry hash: ${summary.help_ledger_entry_hash || metadata.help_ledger_entry_hash || "missing"}`,
    `Operator reflection hash: ${summary.operator_reflection_hash || metadata.operator_reflection_hash || "missing"}`,
    `Source cards: ${(summary.source_card_ids || metadata.source_card_ids || []).join(", ") || "keine"}`,
    `Source anchor hash count: ${summary.source_anchor_hash_count || (metadata.source_anchor_hashes || []).length || 0}`,
    `Binder receipt hash: ${summary.binder_receipt_hash || pre.binder_receipt_hash || "missing"}`,
    `Launch receipt hash: ${summary.launch_receipt_hash || pre.launch_receipt_hash || "missing"}`,
    `Post-cycle receipt hash: ${summary.post_cycle_receipt_hash || metadata.post_cycle_receipt_hash || "missing"}`,
    `Human confirmation hash: ${summary.human_confirmation_hash || metadata.human_confirmation_hash || "missing"}`,
    `Intake receipt: ${receipt.receipt_id || "missing"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only manual post-cycle receipt intake"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamManualCycleClosureLedger(report, sourceLabel) {
  const summary = report.closure_summary || {};
  const receipt = report.manual_cycle_closure_ledger_receipt || {};
  const entries = report.closure_ledger_entries || [];
  const accepted = summary.accepted_post_cycle_hashes || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Ledger decision: ${summary.closure_ledger_decision || report.closure_ledger_decision || "keep_cycle_open"}`,
    `Reason: ${summary.closure_ledger_reason || "post_cycle_intake_missing_or_open"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Post-cycle recommendation: ${summary.post_cycle_review_recommendation || "keep_post_cycle_review_open"}`,
    `Pre-cycle action: ${summary.pre_cycle_stop_go_action || "missing"}`,
    `Launch decision: ${summary.launch_decision || "refresh_manual_console"}`,
    `Manual action: ${summary.manual_confirmation_action || "missing"}`,
    `Open confirmations: ${summary.open_confirmation_count || 0}`,
    `Confirmed hash metadata: ${summary.confirmed_count || 0}`,
    `Missing hashes: ${(summary.missing_required_hashes || []).join(", ") || "keine"}`,
    `Forbidden metadata keys: ${(summary.forbidden_metadata_keys || []).join(", ") || "keine"}`,
    `Task hash: ${summary.task_hash || "none"}`,
    `Checkpoint hash: ${summary.checkpoint_hash || "missing"}`,
    `Notebook checkpoint hash: ${summary.notebook_checkpoint_hash || "missing"}`,
    `Help ledger hash: ${summary.help_ledger_hash || "missing"}`,
    `Operator reflection hash: ${summary.operator_reflection_hash || "missing"}`,
    `Accepted post-cycle notebook hash: ${accepted.notebook_checkpoint_hash || "missing"}`,
    `Source cards: ${(summary.source_card_ids || []).join(", ") || "keine"}`,
    `Source anchor hash count: ${summary.source_anchor_hash_count || 0}`,
    `Binder receipt hash: ${summary.binder_receipt_hash || "missing"}`,
    `Launch receipt hash: ${summary.launch_receipt_hash || "missing"}`,
    `Post-cycle receipt hash: ${summary.post_cycle_receipt_hash || "missing"}`,
    `Intake receipt hash: ${summary.intake_receipt_hash || "missing"}`,
    `Closure receipt: ${receipt.receipt_id || "missing"}`,
    `Next safe review action: ${summary.next_safe_review_action || "continue_manual_cycle_review"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only manual cycle closure ledger"}`,
    "",
    "Ledger entries:",
    ...(entries.slice(0, 6).map((item) => `- ${item.entry_id}: ${item.status}; hash=${item.entry_hash || "missing"}`)),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamManualCycleReviewTimeline(report, sourceLabel) {
  const summary = report.timeline_summary || {};
  const receipt = report.manual_cycle_review_timeline_receipt || {};
  const events = report.timeline_events || [];
  const accepted = summary.accepted_post_cycle_hashes || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Timeline recommendation: ${summary.timeline_review_recommendation || report.timeline_review_recommendation || "continue_cycle_review"}`,
    `Reason: ${summary.timeline_review_reason || "cycle_still_open_for_review"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Closure decision: ${summary.closure_ledger_decision || "keep_cycle_open"}`,
    `Post-cycle recommendation: ${summary.post_cycle_review_recommendation || "keep_post_cycle_review_open"}`,
    `Next safe review action: ${summary.next_safe_review_action || "continue_manual_cycle_review"}`,
    `Missing hashes: ${(summary.missing_required_hashes || []).join(", ") || "keine"}`,
    `Task hash: ${summary.task_hash || "none"}`,
    `Checkpoint hash: ${summary.checkpoint_hash || "missing"}`,
    `Notebook checkpoint hash: ${summary.notebook_checkpoint_hash || "missing"}`,
    `Help ledger hash: ${summary.help_ledger_hash || "missing"}`,
    `Operator reflection hash: ${summary.operator_reflection_hash || "missing"}`,
    `Accepted post-cycle notebook hash: ${accepted.notebook_checkpoint_hash || "missing"}`,
    `Source cards: ${(summary.source_card_ids || []).join(", ") || "keine"}`,
    `Source anchor hash count: ${summary.source_anchor_hash_count || 0}`,
    `Binder receipt hash: ${summary.binder_receipt_hash || "missing"}`,
    `Launch receipt hash: ${summary.launch_receipt_hash || "missing"}`,
    `Post-cycle receipt hash: ${summary.post_cycle_receipt_hash || "missing"}`,
    `Intake receipt hash: ${summary.intake_receipt_hash || "missing"}`,
    `Closure receipt hash: ${summary.closure_receipt_hash || "missing"}`,
    `Timeline receipt: ${receipt.receipt_id || "missing"}`,
    `Timeline events: ${summary.timeline_event_count || events.length || 0}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only manual cycle review timeline"}`,
    "",
    "Timeline:",
    ...(events.slice(0, 8).map((item) => `- ${item.sequence_index}. ${item.event_id}: ${item.review_state || item.status}; hash=${item.event_hash || "missing"}`)),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamManualCycleReviewPacket(report, sourceLabel) {
  const summary = report.review_packet_summary || {};
  const body = report.review_packet_body || {};
  const receipt = report.manual_cycle_review_packet_receipt || {};
  const accepted = summary.accepted_post_cycle_hashes || body.accepted_post_cycle_hashes || {};
  const receipts = summary.receipt_hashes || body.receipt_hashes || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Packet recommendation: ${summary.packet_recommendation || report.packet_recommendation || "keep_review_packet_open"}`,
    `Reason: ${summary.packet_recommendation_reason || "timeline_review_still_open"}`,
    `Timeline recommendation: ${summary.timeline_recommendation || body.timeline_recommendation || "continue_cycle_review"}`,
    `Closure decision: ${summary.closure_decision || body.closure_decision || "keep_cycle_open"}`,
    `Post-cycle recommendation: ${summary.post_cycle_recommendation || body.post_cycle_recommendation || "missing"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Missing hashes: ${(summary.missing_required_hashes || body.missing_required_hashes || []).join(", ") || "keine"}`,
    `Task hash: ${summary.task_hash || body.task_hash || "none"}`,
    `Checkpoint hash: ${summary.checkpoint_hash || body.checkpoint_hash || "missing"}`,
    `Notebook checkpoint hash: ${summary.notebook_checkpoint_hash || body.notebook_checkpoint_hash || "missing"}`,
    `Help ledger hash: ${summary.help_ledger_hash || body.help_ledger_hash || "missing"}`,
    `Operator reflection hash: ${summary.operator_reflection_hash || body.operator_reflection_hash || "missing"}`,
    `Accepted post-cycle notebook hash: ${accepted.notebook_checkpoint_hash || "missing"}`,
    `Source cards: ${(summary.source_card_ids || body.source_card_ids || []).join(", ") || "keine"}`,
    `Source anchor hash count: ${summary.source_anchor_hash_count || body.source_anchor_hash_count || 0}`,
    `Binder receipt hash: ${receipts.binder_receipt_hash || "missing"}`,
    `Launch receipt hash: ${receipts.launch_receipt_hash || "missing"}`,
    `Post-cycle receipt hash: ${receipts.post_cycle_receipt_hash || "missing"}`,
    `Intake receipt hash: ${receipts.intake_receipt_hash || "missing"}`,
    `Closure receipt hash: ${receipts.closure_receipt_hash || "missing"}`,
    `Timeline receipt hash: ${receipts.timeline_receipt_hash || "missing"}`,
    `Timeline events: ${summary.timeline_event_count || body.timeline_event_count || 0}`,
    `Timeline event hashes: ${(summary.timeline_event_hashes || body.timeline_event_hashes || []).length || 0}`,
    `Next safe review action: ${summary.next_safe_review_action || body.next_safe_review_action || "continue_manual_cycle_review"}`,
    `Packet receipt: ${receipt.receipt_id || "missing"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only manual cycle review packet"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamManualReviewExportPreview(report, sourceLabel) {
  const summary = report.export_preview_summary || {};
  const manifest = report.export_manifest_preview || {};
  const receipt = report.manual_review_export_preview_receipt || {};
  const accepted = summary.accepted_post_cycle_hashes || manifest.accepted_post_cycle_hashes || {};
  const receipts = summary.receipt_hashes || manifest.receipt_hashes || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Export preview recommendation: ${summary.export_preview_recommendation || report.export_preview_recommendation || "keep_export_preview_open"}`,
    `Reason: ${summary.export_preview_reason || "review_packet_still_open"}`,
    `Packet recommendation: ${summary.packet_recommendation || manifest.packet_recommendation || "keep_review_packet_open"}`,
    `Timeline recommendation: ${summary.timeline_recommendation || manifest.timeline_recommendation || "continue_cycle_review"}`,
    `Closure decision: ${summary.closure_decision || manifest.closure_decision || "keep_cycle_open"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Export manifest hash: ${summary.export_manifest_hash || manifest.export_manifest_hash || "missing"}`,
    `Export created: ${report.export_created ? "ja" : "nein"}`,
    `Missing hashes: ${(summary.missing_required_hashes || manifest.missing_required_hashes || []).join(", ") || "keine"}`,
    `Task hash: ${summary.task_hash || manifest.task_hash || "none"}`,
    `Checkpoint hash: ${summary.checkpoint_hash || manifest.checkpoint_hash || "missing"}`,
    `Notebook checkpoint hash: ${summary.notebook_checkpoint_hash || manifest.notebook_checkpoint_hash || "missing"}`,
    `Help ledger hash: ${summary.help_ledger_hash || manifest.help_ledger_hash || "missing"}`,
    `Operator reflection hash: ${summary.operator_reflection_hash || manifest.operator_reflection_hash || "missing"}`,
    `Accepted post-cycle notebook hash: ${accepted.notebook_checkpoint_hash || "missing"}`,
    `Source cards: ${(summary.source_card_ids || manifest.source_card_ids || []).join(", ") || "keine"}`,
    `Source anchor hash count: ${summary.source_anchor_hash_count || manifest.source_anchor_hash_count || 0}`,
    `Binder receipt hash: ${receipts.binder_receipt_hash || "missing"}`,
    `Launch receipt hash: ${receipts.launch_receipt_hash || "missing"}`,
    `Post-cycle receipt hash: ${receipts.post_cycle_receipt_hash || "missing"}`,
    `Intake receipt hash: ${receipts.intake_receipt_hash || "missing"}`,
    `Closure receipt hash: ${receipts.closure_receipt_hash || "missing"}`,
    `Timeline receipt hash: ${receipts.timeline_receipt_hash || "missing"}`,
    `Packet receipt hash: ${receipts.packet_receipt_hash || "missing"}`,
    `Timeline events: ${summary.timeline_event_count || manifest.timeline_event_count || 0}`,
    `Timeline event hashes: ${(summary.timeline_event_hashes || manifest.timeline_event_hashes || []).length || 0}`,
    `Next safe review action: ${summary.next_safe_review_action || manifest.next_safe_review_action || "continue_manual_cycle_review"}`,
    `Preview receipt: ${receipt.receipt_id || "missing"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only manual review export preview"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamManualReviewExportAuthorizationGate(report, sourceLabel) {
  const summary = report.authorization_gate_summary || {};
  const receipt = report.manual_review_export_authorization_gate_receipt || {};
  const accepted = summary.accepted_post_cycle_hashes || {};
  const receipts = summary.receipt_hashes || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Authorization gate decision: ${summary.authorization_gate_decision || report.authorization_gate_decision || "keep_export_blocked"}`,
    `Reason: ${summary.authorization_gate_reason || "export_preview_still_open"}`,
    `Export preview recommendation: ${summary.export_preview_recommendation || "keep_export_preview_open"}`,
    `Packet recommendation: ${summary.packet_recommendation || "keep_review_packet_open"}`,
    `Timeline recommendation: ${summary.timeline_recommendation || "continue_cycle_review"}`,
    `Closure decision: ${summary.closure_decision || "keep_cycle_open"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Export manifest hash: ${summary.export_manifest_hash || "missing"}`,
    `Authorization gate hash: ${summary.authorization_gate_hash || "missing"}`,
    `Export created: ${report.export_created ? "ja" : "nein"}`,
    `Export authorized: ${report.export_authorized ? "ja" : "nein"}`,
    `Missing hashes: ${(summary.missing_required_hashes || []).join(", ") || "keine"}`,
    `Accepted post-cycle notebook hash: ${accepted.notebook_checkpoint_hash || "missing"}`,
    `Binder receipt hash: ${receipts.binder_receipt_hash || "missing"}`,
    `Launch receipt hash: ${receipts.launch_receipt_hash || "missing"}`,
    `Post-cycle receipt hash: ${receipts.post_cycle_receipt_hash || "missing"}`,
    `Intake receipt hash: ${receipts.intake_receipt_hash || "missing"}`,
    `Closure receipt hash: ${receipts.closure_receipt_hash || "missing"}`,
    `Timeline receipt hash: ${receipts.timeline_receipt_hash || "missing"}`,
    `Packet receipt hash: ${receipts.packet_receipt_hash || "missing"}`,
    `Preview receipt hash: ${receipts.preview_receipt_hash || "missing"}`,
    `Timeline events: ${summary.timeline_event_count || 0}`,
    `Timeline event hashes: ${(summary.timeline_event_hashes || []).length || 0}`,
    `Next safe review action: ${summary.next_safe_review_action || "keep_export_blocked_and_continue_manual_review"}`,
    `Gate receipt: ${receipt.receipt_id || "missing"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only manual review export authorization gate"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamManualExportReviewQueue(report, sourceLabel) {
  const summary = report.queue_summary || {};
  const receipt = report.manual_export_review_queue_receipt || {};
  const candidates = report.queue_candidates || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Queue recommendation: ${summary.queue_recommendation || report.queue_recommendation || "keep_queue_open"}`,
    `Reason: ${summary.queue_reason || "queue_entries_still_blocked_or_open"}`,
    `Queue hash: ${summary.queue_hash || "missing"}`,
    `Candidates: ${summary.candidate_count || candidates.length || 0}`,
    `Ready: ${summary.ready_candidate_count || 0}`,
    `Blocked/open: ${summary.blocked_candidate_count || 0}`,
    `Missing-hash: ${summary.missing_hash_candidate_count || 0}`,
    `Rejected: ${summary.rejected_candidate_count || 0}`,
    `Export created: ${report.export_created ? "ja" : "nein"}`,
    `Export authorized: ${report.export_authorized ? "ja" : "nein"}`,
    `Next safe review action: ${summary.next_safe_review_action || "keep_queue_open_and_continue_manual_review"}`,
    `Queue receipt: ${receipt.receipt_id || "missing"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    "",
    "Queue candidates:",
    ...(candidates.slice(0, 6).map((candidate, index) => (
      `- ${index + 1}. ${candidate.candidate_id || "candidate"}: ${candidate.queue_entry_recommendation || "keep_queue_open"}; gate=${candidate.authorization_gate_decision || "keep_export_blocked"}; skill=${candidate.selected_skill_tag || "unknown"}; manifest=${candidate.export_manifest_hash || "missing"}; gate_hash=${candidate.authorization_gate_hash || "missing"}; missing=${(candidate.missing_required_hashes || []).join(", ") || "keine"}; next=${candidate.next_safe_review_action || "continue_review"}`
    ))),
    `Grenze: ${report.execution_boundary || "metadata-only manual export review queue"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamManualExportReviewerPacket(report, sourceLabel) {
  const summary = report.reviewer_packet_summary || {};
  const body = report.reviewer_packet_body || {};
  const receipt = report.manual_export_reviewer_packet_receipt || {};
  const accepted = summary.accepted_post_cycle_hashes || body.accepted_post_cycle_hashes || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Reviewer packet recommendation: ${summary.reviewer_packet_recommendation || report.reviewer_packet_recommendation || "keep_reviewer_packet_open"}`,
    `Reason: ${summary.reviewer_packet_reason || "queue_still_open_or_blocked"}`,
    `Queue recommendation: ${summary.queue_recommendation || body.queue_recommendation || "keep_queue_open"}`,
    `Queue hash: ${summary.queue_hash || body.queue_hash || "missing"}`,
    `Reviewer packet hash: ${summary.reviewer_packet_hash || body.reviewer_packet_hash || "missing"}`,
    `Candidate count: ${summary.candidate_count || body.candidate_count || 0}`,
    `Candidate hashes: ${(summary.candidate_hashes || body.candidate_hashes || []).length || 0}`,
    `Gate decisions: ${(summary.gate_decisions || body.gate_decisions || []).join(", ") || "keine"}`,
    `Export manifest hash: ${summary.export_manifest_hash || body.export_manifest_hash || "missing"}`,
    `Authorization gate hash: ${summary.authorization_gate_hash || body.authorization_gate_hash || "missing"}`,
    `Preview receipt hash: ${summary.preview_receipt_hash || body.preview_receipt_hash || "missing"}`,
    `Packet receipt hash: ${summary.packet_receipt_hash || body.packet_receipt_hash || "missing"}`,
    `Timeline receipt hash: ${summary.timeline_receipt_hash || body.timeline_receipt_hash || "missing"}`,
    `Authorization gate receipt hash: ${summary.authorization_gate_receipt_hash || body.authorization_gate_receipt_hash || "missing"}`,
    `Queue receipt hash: ${summary.queue_receipt_hash || body.queue_receipt_hash || "missing"}`,
    `Missing hashes: ${(summary.missing_required_hashes || body.missing_required_hashes || []).join(", ") || "keine"}`,
    `Accepted post-cycle notebook hash: ${accepted.notebook_checkpoint_hash || "missing"}`,
    `Skill: ${summary.selected_skill_tag || body.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Help level: ${summary.help_level || body.help_level || "A2"}`,
    `Source cards: ${(summary.source_card_ids || body.source_card_ids || []).join(", ") || "keine"}`,
    `Source anchor hash count: ${summary.source_anchor_hash_count || body.source_anchor_hash_count || 0}`,
    `Timeline events: ${summary.timeline_event_count || body.timeline_event_count || 0}`,
    `Timeline event hashes: ${(summary.timeline_event_hashes || body.timeline_event_hashes || []).length || 0}`,
    `Next safe review action: ${summary.next_safe_review_action || body.next_safe_review_action || "continue_review"}`,
    `Packet receipt: ${receipt.receipt_id || "missing"}`,
    `Export created: ${report.export_created ? "ja" : "nein"}`,
    `Export authorized: ${report.export_authorized ? "ja" : "nein"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only manual export reviewer packet"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamManualArchiveDecisionDraft(report, sourceLabel) {
  const summary = report.archive_decision_draft_summary || {};
  const body = report.archive_decision_draft_body || {};
  const receipt = report.manual_archive_decision_draft_receipt || {};
  const accepted = summary.accepted_post_cycle_hashes || body.accepted_post_cycle_hashes || {};
  const receipts = summary.receipt_hashes || body.receipt_hashes || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Draft recommendation: ${summary.archive_decision_draft_recommendation || report.archive_decision_draft_recommendation || "keep_archive_decision_draft_open"}`,
    `Reason: ${summary.archive_decision_draft_reason || "reviewer_packet_still_open"}`,
    `Reviewer packet recommendation: ${summary.reviewer_packet_recommendation || body.reviewer_packet_recommendation || "keep_reviewer_packet_open"}`,
    `Queue recommendation: ${summary.queue_recommendation || body.queue_recommendation || "keep_queue_open"}`,
    `Archive decision draft hash: ${summary.archive_decision_draft_hash || body.archive_decision_draft_hash || "missing"}`,
    `Reviewer packet hash: ${summary.reviewer_packet_hash || body.reviewer_packet_hash || "missing"}`,
    `Queue hash: ${summary.queue_hash || body.queue_hash || "missing"}`,
    `Export manifest hash: ${summary.export_manifest_hash || body.export_manifest_hash || "missing"}`,
    `Authorization gate hash: ${summary.authorization_gate_hash || body.authorization_gate_hash || "missing"}`,
    `Candidate hashes: ${(summary.candidate_hashes || body.candidate_hashes || []).length || 0}`,
    `Gate decisions: ${(summary.gate_decisions || body.gate_decisions || []).join(", ") || "keine"}`,
    `Receipt hashes: ${Object.keys(receipts).length || 0}`,
    `Missing hashes: ${(summary.missing_required_hashes || body.missing_required_hashes || []).join(", ") || "keine"}`,
    `Accepted post-cycle notebook hash: ${accepted.notebook_checkpoint_hash || "missing"}`,
    `Skill: ${summary.selected_skill_tag || body.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Help level: ${summary.help_level || body.help_level || "A2"}`,
    `Source cards: ${(summary.source_card_ids || body.source_card_ids || []).join(", ") || "keine"}`,
    `Source anchor hash count: ${summary.source_anchor_hash_count || body.source_anchor_hash_count || 0}`,
    `Timeline events: ${summary.timeline_event_count || body.timeline_event_count || 0}`,
    `Timeline event hashes: ${(summary.timeline_event_hashes || body.timeline_event_hashes || []).length || 0}`,
    `Next safe decision action: ${summary.next_safe_decision_action || body.next_safe_decision_action || "continue_review"}`,
    `Draft receipt: ${receipt.receipt_id || "missing"}`,
    `Export created: ${report.export_created ? "ja" : "nein"}`,
    `Export authorized: ${report.export_authorized ? "ja" : "nein"}`,
    `Archive created: ${report.archive_created ? "ja" : "nein"}`,
    `Submission started: ${report.submission_started ? "ja" : "nein"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only manual archive decision draft"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamManualFinalReviewHandoff(report, sourceLabel) {
  const summary = report.final_review_handoff_summary || {};
  const body = report.final_review_handoff_body || {};
  const receipt = report.manual_final_review_handoff_receipt || {};
  const accepted = summary.accepted_post_cycle_hashes || body.accepted_post_cycle_hashes || {};
  const receipts = summary.receipt_hashes || body.receipt_hashes || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Final handoff recommendation: ${summary.final_review_handoff_recommendation || report.final_review_handoff_recommendation || "keep_final_handoff_open"}`,
    `Reason: ${summary.final_review_handoff_reason || "archive_decision_draft_still_open"}`,
    `Archive draft recommendation: ${summary.archive_decision_draft_recommendation || body.archive_decision_draft_recommendation || "keep_archive_decision_draft_open"}`,
    `Reviewer packet recommendation: ${summary.reviewer_packet_recommendation || body.reviewer_packet_recommendation || "keep_reviewer_packet_open"}`,
    `Queue recommendation: ${summary.queue_recommendation || body.queue_recommendation || "keep_queue_open"}`,
    `Final handoff hash: ${summary.final_review_handoff_hash || body.final_review_handoff_hash || "missing"}`,
    `Archive draft hash: ${summary.archive_decision_draft_hash || body.archive_decision_draft_hash || "missing"}`,
    `Reviewer packet hash: ${summary.reviewer_packet_hash || body.reviewer_packet_hash || "missing"}`,
    `Queue hash: ${summary.queue_hash || body.queue_hash || "missing"}`,
    `Export manifest hash: ${summary.export_manifest_hash || body.export_manifest_hash || "missing"}`,
    `Authorization gate hash: ${summary.authorization_gate_hash || body.authorization_gate_hash || "missing"}`,
    `Candidate hashes: ${(summary.candidate_hashes || body.candidate_hashes || []).length || 0}`,
    `Gate decisions: ${(summary.gate_decisions || body.gate_decisions || []).join(", ") || "keine"}`,
    `Receipt hashes: ${Object.keys(receipts).length || 0}`,
    `Missing hashes: ${(summary.missing_required_hashes || body.missing_required_hashes || []).join(", ") || "keine"}`,
    `Accepted post-cycle notebook hash: ${accepted.notebook_checkpoint_hash || "missing"}`,
    `Skill: ${summary.selected_skill_tag || body.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Help level: ${summary.help_level || body.help_level || "A2"}`,
    `Source cards: ${(summary.source_card_ids || body.source_card_ids || []).join(", ") || "keine"}`,
    `Source anchor hash count: ${summary.source_anchor_hash_count || body.source_anchor_hash_count || 0}`,
    `Timeline events: ${summary.timeline_event_count || body.timeline_event_count || 0}`,
    `Timeline event hashes: ${(summary.timeline_event_hashes || body.timeline_event_hashes || []).length || 0}`,
    `Next safe human review action: ${summary.next_safe_human_review_action || body.next_safe_human_review_action || "continue_review"}`,
    `Handoff receipt: ${receipt.receipt_id || "missing"}`,
    `Export created: ${report.export_created ? "ja" : "nein"}`,
    `Export authorized: ${report.export_authorized ? "ja" : "nein"}`,
    `Archive created: ${report.archive_created ? "ja" : "nein"}`,
    `Submission started: ${report.submission_started ? "ja" : "nein"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only manual final review handoff"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamManualFinalReviewReceiptLedger(report, sourceLabel) {
  const summary = report.final_review_receipt_ledger_summary || {};
  const body = report.final_review_receipt_ledger_body || {};
  const receipt = report.manual_final_review_receipt_ledger_receipt || {};
  const accepted = summary.accepted_post_cycle_hashes || body.accepted_post_cycle_hashes || {};
  const receipts = summary.receipt_hashes || body.receipt_hashes || {};
  const events = summary.ledger_event_hashes || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Final ledger recommendation: ${summary.final_review_receipt_ledger_recommendation || report.final_review_receipt_ledger_recommendation || "keep_final_ledger_open"}`,
    `Reason: ${summary.final_review_receipt_ledger_reason || "final_review_handoff_still_open"}`,
    `Final handoff recommendation: ${summary.final_review_handoff_recommendation || body.final_review_handoff_recommendation || "keep_final_handoff_open"}`,
    `Archive draft recommendation: ${summary.archive_decision_draft_recommendation || body.archive_decision_draft_recommendation || "keep_archive_decision_draft_open"}`,
    `Reviewer packet recommendation: ${summary.reviewer_packet_recommendation || body.reviewer_packet_recommendation || "keep_reviewer_packet_open"}`,
    `Queue recommendation: ${summary.queue_recommendation || body.queue_recommendation || "keep_queue_open"}`,
    `Final ledger hash: ${summary.final_review_receipt_ledger_hash || body.final_review_receipt_ledger_hash || "missing"}`,
    `Final handoff hash: ${summary.final_review_handoff_hash || body.final_review_handoff_hash || "missing"}`,
    `Archive draft hash: ${summary.archive_decision_draft_hash || body.archive_decision_draft_hash || "missing"}`,
    `Reviewer packet hash: ${summary.reviewer_packet_hash || body.reviewer_packet_hash || "missing"}`,
    `Queue hash: ${summary.queue_hash || body.queue_hash || "missing"}`,
    `Export manifest hash: ${summary.export_manifest_hash || body.export_manifest_hash || "missing"}`,
    `Authorization gate hash: ${summary.authorization_gate_hash || body.authorization_gate_hash || "missing"}`,
    `Candidate hashes: ${(summary.candidate_hashes || body.candidate_hashes || []).length || 0}`,
    `Gate decisions: ${(summary.gate_decisions || body.gate_decisions || []).join(", ") || "keine"}`,
    `Receipt hashes: ${Object.keys(receipts).length || 0}`,
    `Missing hashes: ${(summary.missing_required_hashes || body.missing_required_hashes || []).join(", ") || "keine"}`,
    `Accepted post-cycle notebook hash: ${accepted.notebook_checkpoint_hash || "missing"}`,
    `Skill: ${summary.selected_skill_tag || body.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Help level: ${summary.help_level || body.help_level || "A2"}`,
    `Source cards: ${(summary.source_card_ids || body.source_card_ids || []).join(", ") || "keine"}`,
    `Source anchor hash count: ${summary.source_anchor_hash_count || body.source_anchor_hash_count || 0}`,
    `Timeline events: ${summary.timeline_event_count || body.timeline_event_count || 0}`,
    `Ledger events: ${summary.ledger_event_count || events.length || 0}`,
    `Ledger event hashes: ${events.length || 0}`,
    `Next safe human review action: ${summary.next_safe_human_review_action || body.next_safe_human_review_action || "continue_review"}`,
    `Ledger receipt: ${receipt.receipt_id || "missing"}`,
    `Export created: ${report.export_created ? "ja" : "nein"}`,
    `Export authorized: ${report.export_authorized ? "ja" : "nein"}`,
    `Archive created: ${report.archive_created ? "ja" : "nein"}`,
    `Submission started: ${report.submission_started ? "ja" : "nein"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only manual final review receipt ledger"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamFinalReviewLedgerIntegrityGate(report, sourceLabel) {
  const summary = report.final_review_ledger_integrity_gate_summary || {};
  const body = report.final_review_ledger_integrity_gate_body || {};
  const receipt = report.final_review_ledger_integrity_gate_receipt || {};
  const sourceHashes = summary.source_hashes || body.source_hashes || {};
  const ledgerHashes = summary.ledger_hashes || body.ledger_hashes || {};
  const receipts = summary.receipt_hashes || body.receipt_hashes || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Integrity gate recommendation: ${summary.final_review_ledger_integrity_gate_recommendation || report.final_review_ledger_integrity_gate_recommendation || "keep_integrity_gate_open"}`,
    `Reason: ${summary.final_review_ledger_integrity_gate_reason || "final_review_ledger_still_open"}`,
    `Final ledger recommendation: ${summary.final_review_receipt_ledger_recommendation || body.final_review_receipt_ledger_recommendation || "keep_final_ledger_open"}`,
    `Final handoff recommendation: ${summary.final_review_handoff_recommendation || body.final_review_handoff_recommendation || "keep_final_handoff_open"}`,
    `Archive draft recommendation: ${summary.archive_decision_draft_recommendation || body.archive_decision_draft_recommendation || "keep_archive_decision_draft_open"}`,
    `Reviewer packet recommendation: ${summary.reviewer_packet_recommendation || body.reviewer_packet_recommendation || "keep_reviewer_packet_open"}`,
    `Queue recommendation: ${summary.queue_recommendation || body.queue_recommendation || "keep_queue_open"}`,
    `Integrity gate hash: ${summary.final_review_ledger_integrity_gate_hash || body.final_review_ledger_integrity_gate_hash || "missing"}`,
    `Source handoff hash: ${sourceHashes.final_review_handoff_hash || "missing"}`,
    `Ledger handoff hash: ${ledgerHashes.final_review_handoff_hash || "missing"}`,
    `Source draft hash: ${sourceHashes.archive_decision_draft_hash || "missing"}`,
    `Ledger draft hash: ${ledgerHashes.archive_decision_draft_hash || "missing"}`,
    `Source reviewer hash: ${sourceHashes.reviewer_packet_hash || "missing"}`,
    `Ledger reviewer hash: ${ledgerHashes.reviewer_packet_hash || "missing"}`,
    `Source queue hash: ${sourceHashes.queue_hash || "missing"}`,
    `Ledger queue hash: ${ledgerHashes.queue_hash || "missing"}`,
    `Mismatched hashes: ${(summary.mismatched_hashes || body.mismatched_hashes || []).join(", ") || "keine"}`,
    `Missing hashes: ${(summary.missing_required_hashes || body.missing_required_hashes || []).join(", ") || "keine"}`,
    `Chain issues: ${summary.chain_issue_count || body.chain_issue_count || 0}`,
    `Candidate hashes: ${(summary.candidate_hashes || body.candidate_hashes || []).length || 0}`,
    `Gate decisions: ${(summary.gate_decisions || body.gate_decisions || []).join(", ") || "keine"}`,
    `Receipt hashes: ${Object.keys(receipts).length || 0}`,
    `Skill: ${summary.selected_skill_tag || body.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Skill consistent: ${(summary.skill_tag_consistent || body.skill_tag_consistent) ? "ja" : "nein"}`,
    `Help level: ${summary.help_level || body.help_level || "A2"}`,
    `Help consistent: ${(summary.help_level_consistent || body.help_level_consistent) ? "ja" : "nein"}`,
    `Source cards: ${(summary.source_card_ids || body.source_card_ids || []).join(", ") || "keine"}`,
    `Source anchor hash count: ${summary.source_anchor_hash_count || body.source_anchor_hash_count || 0}`,
    `Timeline event hashes: ${(summary.timeline_event_hashes || body.timeline_event_hashes || []).length || 0}`,
    `Ledger event hashes: ${(summary.ledger_event_hashes || body.ledger_event_hashes || []).length || 0}`,
    `Next safe human review action: ${summary.next_safe_human_review_action || body.next_safe_human_review_action || "continue_review"}`,
    `Gate receipt: ${receipt.receipt_id || "missing"}`,
    `Export created: ${report.export_created ? "ja" : "nein"}`,
    `Export authorized: ${report.export_authorized ? "ja" : "nein"}`,
    `Archive created: ${report.archive_created ? "ja" : "nein"}`,
    `Submission started: ${report.submission_started ? "ja" : "nein"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only final review ledger integrity gate"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamFinalManualReviewConsole(report, sourceLabel) {
  const summary = report.final_manual_review_console_summary || {};
  const body = report.final_manual_review_console_body || {};
  const receipt = report.final_manual_review_console_receipt || {};
  const accepted = summary.accepted_post_cycle_hashes || body.accepted_post_cycle_hashes || {};
  const receiptHashes = summary.receipt_hashes || body.receipt_hashes || {};
  const timelineHashes = summary.timeline_event_hashes || body.timeline_event_hashes || [];
  const ledgerHashes = summary.ledger_event_hashes || body.ledger_event_hashes || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Console recommendation: ${summary.final_manual_review_console_recommendation || report.final_manual_review_console_recommendation || "keep_final_console_open"}`,
    `Reason: ${summary.final_manual_review_console_reason || "integrity_gate_still_open"}`,
    `Integrity gate recommendation: ${summary.final_review_ledger_integrity_gate_recommendation || body.final_review_ledger_integrity_gate_recommendation || "keep_integrity_gate_open"}`,
    `Final ledger recommendation: ${summary.final_review_receipt_ledger_recommendation || body.final_review_receipt_ledger_recommendation || "keep_final_ledger_open"}`,
    `Final handoff recommendation: ${summary.final_review_handoff_recommendation || body.final_review_handoff_recommendation || "keep_final_handoff_open"}`,
    `Archive draft recommendation: ${summary.archive_decision_draft_recommendation || body.archive_decision_draft_recommendation || "keep_archive_decision_draft_open"}`,
    `Reviewer packet recommendation: ${summary.reviewer_packet_recommendation || body.reviewer_packet_recommendation || "keep_reviewer_packet_open"}`,
    `Queue recommendation: ${summary.queue_recommendation || body.queue_recommendation || "keep_queue_open"}`,
    `Integrity issues: ${summary.integrity_issue_count || body.integrity_issue_count || 0}`,
    `Missing hashes: ${(summary.missing_required_hashes || body.missing_required_hashes || []).join(", ") || "keine"}`,
    `Mismatched hashes: ${(summary.mismatched_hashes || body.mismatched_hashes || []).join(", ") || "keine"}`,
    `Accepted notebook hash: ${accepted.notebook_checkpoint_hash || "missing"}`,
    `Skill: ${summary.selected_skill_tag || body.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Help level: ${summary.help_level || body.help_level || "A2"}`,
    `Source cards: ${(summary.source_card_ids || body.source_card_ids || []).join(", ") || "keine"}`,
    `Source anchor hash count: ${summary.source_anchor_hash_count || body.source_anchor_hash_count || 0}`,
    `Receipt hashes: ${Object.keys(receiptHashes).length || 0}`,
    `Timeline events: ${summary.timeline_event_count || body.timeline_event_count || 0}`,
    `Timeline event hashes: ${timelineHashes.length || 0}`,
    `Ledger events: ${summary.ledger_event_count || body.ledger_event_count || 0}`,
    `Ledger event hashes: ${ledgerHashes.length || 0}`,
    `Next safe human review action: ${summary.next_safe_human_review_action || body.next_safe_human_review_action || "keep_final_console_open_and_continue_manual_review"}`,
    `Console hash: ${summary.final_manual_review_console_hash || body.final_manual_review_console_hash || "missing"}`,
    `Console receipt: ${receipt.receipt_id || "missing"}`,
    `Export created: ${report.export_created ? "ja" : "nein"}`,
    `Export authorized: ${report.export_authorized ? "ja" : "nein"}`,
    `Archive created: ${report.archive_created ? "ja" : "nein"}`,
    `Submission started: ${report.submission_started ? "ja" : "nein"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only final manual review console"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamFinalManualReviewActionLock(report, sourceLabel) {
  const summary = report.final_manual_review_action_lock_summary || {};
  const body = report.final_manual_review_action_lock_body || {};
  const receipt = report.final_manual_review_action_lock_receipt || {};
  const receiptHashes = summary.receipt_hashes || body.receipt_hashes || {};
  const timelineHashes = summary.timeline_event_hashes || body.timeline_event_hashes || [];
  const ledgerHashes = summary.ledger_event_hashes || body.ledger_event_hashes || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Action lock recommendation: ${summary.final_manual_review_action_lock_recommendation || report.final_manual_review_action_lock_recommendation || "keep_action_locked"}`,
    `Reason: ${summary.final_manual_review_action_lock_reason || "final_action_path_still_locked"}`,
    `Console recommendation: ${summary.final_manual_review_console_recommendation || body.final_manual_review_console_recommendation || "keep_final_console_open"}`,
    `Integrity gate recommendation: ${summary.final_review_ledger_integrity_gate_recommendation || body.final_review_ledger_integrity_gate_recommendation || "keep_integrity_gate_open"}`,
    `Final ledger recommendation: ${summary.final_review_receipt_ledger_recommendation || body.final_review_receipt_ledger_recommendation || "keep_final_ledger_open"}`,
    `Integrity issues: ${summary.integrity_issue_count || body.integrity_issue_count || 0}`,
    `Missing hashes: ${(summary.missing_required_hashes || body.missing_required_hashes || []).join(", ") || "keine"}`,
    `Mismatched hashes: ${(summary.mismatched_hashes || body.mismatched_hashes || []).join(", ") || "keine"}`,
    `Skill: ${summary.selected_skill_tag || body.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Help level: ${summary.help_level || body.help_level || "A2"}`,
    `Source cards: ${(summary.source_card_ids || body.source_card_ids || []).join(", ") || "keine"}`,
    `Source anchor hash count: ${summary.source_anchor_hash_count || body.source_anchor_hash_count || 0}`,
    `Receipt hashes: ${summary.receipt_hash_count || body.receipt_hash_count || Object.keys(receiptHashes).length || 0}`,
    `Timeline events: ${summary.timeline_event_count || body.timeline_event_count || 0}`,
    `Timeline event hashes: ${timelineHashes.length || 0}`,
    `Ledger events: ${summary.ledger_event_count || body.ledger_event_count || 0}`,
    `Ledger event hashes: ${ledgerHashes.length || 0}`,
    `Console hash: ${summary.final_manual_review_console_hash || body.final_manual_review_console_hash || "missing"}`,
    `Integrity gate hash: ${summary.final_review_ledger_integrity_gate_hash || body.final_review_ledger_integrity_gate_hash || "missing"}`,
    `Final ledger hash: ${summary.final_review_receipt_ledger_hash || body.final_review_receipt_ledger_hash || "missing"}`,
    `Action lock hash: ${summary.final_manual_review_action_lock_hash || body.final_manual_review_action_lock_hash || "missing"}`,
    `Next safe human review action: ${summary.next_safe_human_review_action || body.next_safe_human_review_action || "keep_action_locked_and_continue_manual_review"}`,
    `Action lock receipt: ${receipt.receipt_id || "missing"}`,
    `Export created: ${report.export_created ? "ja" : "nein"}`,
    `Export authorized: ${report.export_authorized ? "ja" : "nein"}`,
    `Archive created: ${report.archive_created ? "ja" : "nein"}`,
    `Submission started: ${report.submission_started ? "ja" : "nein"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only final manual review action lock"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamLockedFinalReviewBoard(report, sourceLabel) {
  const summary = report.locked_final_review_board_summary || {};
  const body = report.locked_final_review_board_body || {};
  const receipt = report.locked_final_review_board_receipt || {};
  const receiptHashes = summary.receipt_hashes || body.receipt_hashes || {};
  const timelineHashes = summary.timeline_event_hashes || body.timeline_event_hashes || [];
  const ledgerHashes = summary.ledger_event_hashes || body.ledger_event_hashes || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Board recommendation: ${summary.locked_final_review_board_recommendation || report.locked_final_review_board_recommendation || "keep_final_board_open"}`,
    `Reason: ${summary.locked_final_review_board_reason || "final_board_still_open"}`,
    `Action lock recommendation: ${summary.final_manual_review_action_lock_recommendation || body.final_manual_review_action_lock_recommendation || "keep_action_locked"}`,
    `Console recommendation: ${summary.final_manual_review_console_recommendation || body.final_manual_review_console_recommendation || "keep_final_console_open"}`,
    `Integrity gate recommendation: ${summary.final_review_ledger_integrity_gate_recommendation || body.final_review_ledger_integrity_gate_recommendation || "keep_integrity_gate_open"}`,
    `Final ledger recommendation: ${summary.final_review_receipt_ledger_recommendation || body.final_review_receipt_ledger_recommendation || "keep_final_ledger_open"}`,
    `Draft review: ${summary.draft_review_status || body.draft_review_status || "missing"}`,
    `Human handoff: ${summary.human_handoff_status || body.human_handoff_status || "missing"}`,
    `Full rehearsal: ${summary.full_local_rehearsal_status || body.full_local_rehearsal_status || "missing"}`,
    `Integrity issues: ${summary.integrity_issue_count || body.integrity_issue_count || 0}`,
    `Missing hashes: ${(summary.missing_required_hashes || body.missing_required_hashes || []).join(", ") || "keine"}`,
    `Mismatched hashes: ${(summary.mismatched_hashes || body.mismatched_hashes || []).join(", ") || "keine"}`,
    `Skill: ${summary.selected_skill_tag || body.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Help level: ${summary.help_level || body.help_level || "A2"}`,
    `Source cards: ${(summary.source_card_ids || body.source_card_ids || []).join(", ") || "keine"}`,
    `Source anchor hash count: ${summary.source_anchor_hash_count || body.source_anchor_hash_count || 0}`,
    `Receipt hashes: ${summary.receipt_hash_count || body.receipt_hash_count || Object.keys(receiptHashes).length || 0}`,
    `Timeline events: ${summary.timeline_event_count || body.timeline_event_count || 0}`,
    `Timeline event hashes: ${timelineHashes.length || 0}`,
    `Ledger events: ${summary.ledger_event_count || body.ledger_event_count || 0}`,
    `Ledger event hashes: ${ledgerHashes.length || 0}`,
    `Action lock hash: ${summary.final_manual_review_action_lock_hash || body.final_manual_review_action_lock_hash || "missing"}`,
    `Console hash: ${summary.final_manual_review_console_hash || body.final_manual_review_console_hash || "missing"}`,
    `Integrity gate hash: ${summary.final_review_ledger_integrity_gate_hash || body.final_review_ledger_integrity_gate_hash || "missing"}`,
    `Final ledger hash: ${summary.final_review_receipt_ledger_hash || body.final_review_receipt_ledger_hash || "missing"}`,
    `Draft package hash: ${summary.draft_package_hash || body.draft_package_hash || "missing"}`,
    `Human handoff hash: ${summary.human_handoff_markdown_hash || body.human_handoff_markdown_hash || "missing"}`,
    `Board hash: ${summary.locked_final_review_board_hash || body.locked_final_review_board_hash || "missing"}`,
    `Next safe human review action: ${summary.next_safe_human_review_action || body.next_safe_human_review_action || "keep_final_board_open_and_continue_manual_review"}`,
    `Board receipt: ${receipt.receipt_id || "missing"}`,
    `Export created: ${report.export_created ? "ja" : "nein"}`,
    `Export authorized: ${report.export_authorized ? "ja" : "nein"}`,
    `Archive created: ${report.archive_created ? "ja" : "nein"}`,
    `Submission started: ${report.submission_started ? "ja" : "nein"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only locked final review board"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamLockedFinalReviewGapResolver(report, sourceLabel) {
  const summary = report.locked_final_review_gap_resolver_summary || {};
  const body = report.locked_final_review_gap_resolver_body || {};
  const receipt = report.locked_final_review_gap_resolver_receipt || {};
  const card = report.prioritized_repair_card || summary.prioritized_repair_card || body.prioritized_repair_card || {};
  const receiptHashes = summary.receipt_hashes || body.receipt_hashes || {};
  const timelineHashes = summary.timeline_event_hashes || body.timeline_event_hashes || [];
  const ledgerHashes = summary.ledger_event_hashes || body.ledger_event_hashes || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Resolver recommendation: ${summary.locked_final_review_gap_resolver_recommendation || report.locked_final_review_gap_resolver_recommendation || "keep_gap_resolver_open"}`,
    `Reason: ${summary.locked_final_review_gap_resolver_reason || "gap_resolver_still_open"}`,
    `Board recommendation: ${summary.locked_final_review_board_recommendation || body.locked_final_review_board_recommendation || "keep_final_board_open"}`,
    `Action lock recommendation: ${summary.final_manual_review_action_lock_recommendation || body.final_manual_review_action_lock_recommendation || "keep_action_locked"}`,
    `Rehearsal: ${summary.full_local_rehearsal_status || body.full_local_rehearsal_status || "missing"}`,
    `Gap coach: ${summary.gap_coach_status || body.gap_coach_status || "missing"}`,
    `Guided loop: ${summary.guided_loop_control_status || body.guided_loop_control_status || "missing"}`,
    `Affected layer: ${summary.affected_review_layer || body.affected_review_layer || card.affected_review_layer || "manual_review"}`,
    `Integrity issues: ${summary.integrity_issue_count || body.integrity_issue_count || 0}`,
    `Missing hashes: ${(summary.missing_required_hashes || body.missing_required_hashes || []).join(", ") || "keine"}`,
    `Mismatched hashes: ${(summary.mismatched_hashes || body.mismatched_hashes || []).join(", ") || "keine"}`,
    `Skill: ${summary.selected_skill_tag || body.selected_skill_tag || report.selected_skill_tag || "unknown"}`,
    `Help level: ${summary.help_level || body.help_level || "A2"}`,
    `Source cards: ${(summary.source_card_ids || body.source_card_ids || []).join(", ") || "keine"}`,
    `Source anchor hash count: ${summary.source_anchor_hash_count || body.source_anchor_hash_count || 0}`,
    `Receipt hashes: ${summary.receipt_hash_count || body.receipt_hash_count || Object.keys(receiptHashes).length || 0}`,
    `Timeline events: ${summary.timeline_event_count || body.timeline_event_count || 0}`,
    `Timeline event hashes: ${timelineHashes.length || 0}`,
    `Ledger events: ${summary.ledger_event_count || body.ledger_event_count || 0}`,
    `Ledger event hashes: ${ledgerHashes.length || 0}`,
    `Repair action: ${card.repair_action || "continue_manual_final_review"}`,
    `Repair rationale: ${card.rationale || "board_open_with_hash_issues"}`,
    `Gap coach action: ${summary.gap_coach_next_safe_action_key || body.gap_coach_next_safe_action_key || card.gap_coach_action_key || "missing"}`,
    `Guided click: ${summary.guided_loop_next_safe_click || body.guided_loop_next_safe_click || card.guided_loop_next_safe_click || "missing"}`,
    `Board hash: ${summary.locked_final_review_board_hash || body.locked_final_review_board_hash || "missing"}`,
    `Action lock hash: ${summary.final_manual_review_action_lock_hash || body.final_manual_review_action_lock_hash || "missing"}`,
    `Resolver hash: ${summary.locked_final_review_gap_resolver_hash || body.locked_final_review_gap_resolver_hash || "missing"}`,
    `Next safe human review action: ${summary.next_safe_human_review_action || body.next_safe_human_review_action || card.next_safe_human_review_action || "continue_manual_final_review"}`,
    `Resolver receipt: ${receipt.receipt_id || "missing"}`,
    `Export created: ${report.export_created ? "ja" : "nein"}`,
    `Export authorized: ${report.export_authorized ? "ja" : "nein"}`,
    `Archive created: ${report.archive_created ? "ja" : "nein"}`,
    `Submission started: ${report.submission_started ? "ja" : "nein"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Score returned: ${report.score_returned ? "ja" : "nein"}`,
    `Grade returned: ${report.grade_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "metadata-only locked final review gap resolver"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamConfirmedLocalExportDraft(report, sourceLabel) {
  const summary = report.draft_summary || {};
  const preview = report.write_preview || {};
  const receipt = report.draft_receipt || {};
  const files = report.draft_file_manifest || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${summary.selected_skill_tag || receipt.selected_skill_tag || "unknown"}`,
    `Source preview: ${summary.source_preview_status || "missing"}`,
    `Draft package: ${summary.draft_package_id || receipt.draft_package_id || "missing"}`,
    `Package hash: ${summary.draft_package_hash || receipt.draft_package_hash || "missing"}`,
    `Files: ${report.draft_file_count || summary.draft_file_count || 0}; write preview files=${preview.file_count || 0}`,
    `Operator confirmed write: ${report.operator_confirmed_local_export_draft_write ? "ja" : "nein"}`,
    `Local draft written: ${report.local_export_draft_written ? "ja" : "nein"}`,
    `Dry-run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Export dir returned: ${report.export_draft_dir_returned ? "ja" : "nein"}`,
    `Next safe action: ${summary.next_safe_action || "Export-Draft pruefen."}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Values returned: ${report.values_returned ? "ja" : "nein"}`,
    `Solutions returned: ${report.solutions_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "python exam local export draft only"}`,
    "",
    "File manifest:",
    ...(files.map((item) => (
      `- ${item.file_name || "file"}: ${item.artifact_type || "artifact"}; sha=${item.sha256 || "missing"}`
    ))),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamDraftPackageReviewConsole(report, sourceLabel) {
  const summary = report.review_summary || {};
  const integrity = report.package_integrity || {};
  const manifest = report.manifest_status || {};
  const receipt = report.not_cleared_receipt_status || {};
  const process = report.process_log_status || {};
  const helpProfile = report.help_level_profile || {};
  const confirmations = report.operator_confirmation_status || {};
  const chain = report.review_chain_status || {};
  const journal = report.receipt_journal_status || {};
  const questions = report.review_questions || [];
  const sections = report.console_sections || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Draft: ${summary.draft_present_status || report.draft_present_status || "unknown"}`,
    `Package ID: ${summary.draft_package_id || integrity.draft_package_id || "missing"}`,
    `Package hash: ${summary.draft_package_hash || integrity.draft_package_hash || "missing"}`,
    `File integrity: ${summary.file_hash_integrity_status || integrity.status || "missing"}; files=${integrity.file_count || 0}`,
    `Manifest: ${summary.manifest_status || manifest.status || "missing"}`,
    `not_cleared receipt: ${summary.not_cleared_receipt_status || receipt.status || "missing"}`,
    `Process log: ${summary.process_log_status || process.status || "missing"}`,
    `A0-A2: ${summary.help_status || helpProfile.status || "missing"} ${JSON.stringify(helpProfile.profile || {})}`,
    `Review chain: ${summary.review_chain_status || chain.status || "missing"}, issues=${chain.issue_count || 0}`,
    `Receipt journal: ${summary.receipt_journal_status || journal.status || "missing"}, accepted=${journal.accepted_record_count || 0}`,
    `Open confirmations: ${summary.open_operator_confirmation_count || confirmations.open_operator_confirmation_count || 0}`,
    `Questions: ${summary.review_question_count || questions.length || 0}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Next safe action: ${summary.next_safe_action || "Draft Review Console pruefen."}`,
    `Grenze: ${report.execution_boundary || "python exam draft review console only"}`,
    "",
    "Sections:",
    ...(sections.map((item) => `- ${item.title || "Section"}: ${item.status || "unknown"}; ${(item.lines || []).join("; ")}`)),
    "",
    "Review-Fragen:",
    ...(questions.slice(0, 8).map((item) => `- ${item}`)),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamHumanHandoffPacket(report, sourceLabel) {
  const summary = report.handoff_summary || {};
  const packet = report.handoff_packet || {};
  const packageInfo = packet.package || {};
  const checkpoint = packet.notebook_checkpoint || {};
  const journal = packet.receipt_journal_summary || {};
  const chain = packet.review_chain_status || {};
  const confirmations = packet.operator_confirmations || {};
  const copyView = report.copy_export_view || {};
  const questions = packet.review_questions || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Draft: ${summary.draft_present_status || packet.draft_present_status || "unknown"}`,
    `Package ID: ${summary.draft_package_id || packageInfo.draft_package_id || "missing"}`,
    `File integrity: ${summary.file_hash_integrity_status || packageInfo.file_hash_integrity_status || "missing"}`,
    `File hashes: ${summary.file_hash_count || Object.keys(packageInfo.file_hashes || {}).length || 0}`,
    `Help: ${summary.help_status || "missing"}`,
    `Review chain: ${summary.review_chain_status || chain.status || "missing"}, issues=${chain.issue_count || 0}`,
    `Receipt journal: ${summary.receipt_journal_status || journal.status || "missing"}, accepted=${summary.receipt_journal_accepted_record_count || journal.accepted_record_count || 0}`,
    `Checkpoint hash: ${checkpoint.notebook_checkpoint_hash || "missing"}`,
    `Open confirmations: ${summary.open_operator_confirmation_count || confirmations.open_operator_confirmation_count || 0}`,
    `Review questions: ${summary.review_question_count || questions.length || 0}`,
    `Copy view: ${copyView.status || "missing"}, hash=${copyView.markdown_hash || "missing"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Next safe action: ${summary.next_safe_action || "Human Handoff pruefen."}`,
    `Grenze: ${report.execution_boundary || "python exam human handoff only"}`,
    "",
    "Review-Fragen:",
    ...(questions.slice(0, 8).map((item) => `- ${item}`)),
    "",
    "Copy Preview:",
    `${(copyView.markdown || "").slice(0, 1800)}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamFullLocalRehearsalPack(report, sourceLabel) {
  const summary = report.rehearsal_summary || {};
  const source = report.source_anchor_metadata || {};
  const confirmations = report.operator_confirmation_status || {};
  const helpStatus = report.a0_a2_help_status || {};
  const chain = report.evidence_chain || {};
  const statuses = report.artifact_statuses || {};
  const steps = report.rehearsal_steps || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "none"}`,
    `Steps: ${summary.ready_step_count || 0}/${summary.step_count || steps.length || 0} ready; attention=${summary.attention_step_count || 0}; missing=${summary.missing_step_count || 0}`,
    `Local cycle chain: ${summary.local_cycle_chain_snapshot_status || statuses.local_chain || "missing"}; hash=${summary.local_cycle_chain_snapshot_hash || chain.local_cycle_chain_snapshot_hash || "missing"}`,
    `Operator: ${summary.operator_run_status || statuses.operator || "missing"}`,
    `Session: ${summary.session_console_status || statuses.session || "missing"}`,
    `Exam packet: ${summary.exam_run_packet_status || statuses.packet || "missing"}; timeline=${summary.exam_packet_timeline_status || statuses.timeline || "missing"}`,
    `Evidence: ${summary.evidence_preview_status || statuses.evidence || "missing"}; handoff=${summary.human_handoff_status || statuses.human_handoff || "missing"}`,
    `Source cards: ${(source.source_card_ids || []).join(", ") || "keine"}; anchors=${source.source_anchor_count || 0}`,
    `Help: ${helpStatus.status || "missing"} ${JSON.stringify(helpStatus.profile || {})}`,
    `Confirmations: open=${confirmations.open_operator_confirmation_count || 0}, confirmed=${confirmations.confirmed_count || 0}/${confirmations.write_step_count || 0}`,
    `Packet receipt: ${chain.exam_run_packet_receipt_id || "missing"}`,
    `Timeline receipt: ${chain.exam_packet_timeline_receipt_id || "missing"}`,
    `Evidence receipt: ${chain.evidence_preview_receipt_id || "missing"}`,
    `Handoff hash: ${chain.human_handoff_markdown_hash || "missing"}`,
    `Dry run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes by pack: ${report.local_writes_executed_by_rehearsal_pack ? "ja" : "nein"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Next safe action: ${summary.next_safe_action || "Full Local Rehearsal pruefen."}`,
    `Grenze: ${report.execution_boundary || "full local rehearsal metadata-only"}`,
    "",
    "Rehearsal Steps:",
    ...(steps.map((item) => `- ${item.step_id}: ${item.step_status}; ${item.status || "missing"}; hash=${item.artifact_hash || "missing"}`)),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamRehearsalPlaybackGapCoach(report, sourceLabel) {
  const summary = report.playback_summary || {};
  const gaps = report.gap_profile || {};
  const source = report.source_anchor_metadata || {};
  const confirmations = report.operator_confirmation_status || {};
  const helpStatus = report.a0_a2_help_status || {};
  const checkpoint = report.notebook_checkpoint_metadata || {};
  const evidence = report.evidence_playback || {};
  const steps = report.playback_steps || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "none"}`,
    `Action: ${report.next_safe_action_key || "review"} - ${report.next_safe_action || "Playback pruefen."}`,
    `Last rehearsal: ${summary.last_rehearsal_status || "missing"}`,
    `Steps: ${summary.ready_step_count || 0}/${summary.step_count || steps.length || 0} ready; attention=${summary.attention_step_count || 0}; missing=${summary.missing_step_count || 0}`,
    `Gaps: missing=${gaps.missing_or_attention_count || 0}; source=${gaps.source_gap ? "ja" : "nein"}; checkpoint=${gaps.notebook_checkpoint_gap ? "ja" : "nein"}; confirmations=${gaps.operator_confirmation_gap ? "ja" : "nein"}; help=${gaps.a0_a2_profile_gap ? "ja" : "nein"}`,
    `Source cards: ${(source.source_card_ids || []).join(", ") || "keine"}; anchors=${source.source_anchor_count || 0}`,
    `Confirmations: open=${confirmations.open_operator_confirmation_count || 0}, confirmed=${confirmations.confirmed_count || 0}/${confirmations.write_step_count || 0}`,
    `Help: ${helpStatus.status || "missing"} ${JSON.stringify(helpStatus.profile || {})}`,
    `Checkpoint: ${checkpoint.status || "missing"}; count=${checkpoint.checkpoint_hash_count || 0}; latest=${checkpoint.latest_notebook_checkpoint_hash || "missing"}`,
    `Evidence: preview=${evidence.evidence_preview_status || "missing"}; receipt=${evidence.evidence_preview_receipt_id || "missing"}`,
    `Human handoff: ${evidence.human_handoff_status || "missing"}; hash=${evidence.human_handoff_markdown_hash || "missing"}`,
    `Dry run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes by coach: ${report.local_writes_executed_by_gap_coach ? "ja" : "nein"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "rehearsal playback metadata-only"}`,
    "",
    "Attention Steps:",
    ...((gaps.missing_artifact_step_ids || []).map((item) => `- missing: ${item}`)),
    ...((gaps.attention_step_ids || []).map((item) => `- attention: ${item}`)),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamGapCoachGuidedLoop(report, sourceLabel) {
  const summary = report.guided_loop_summary || {};
  const step = report.guided_step || {};
  const prefill = report.safe_prefill || {};
  const confirmations = report.operator_confirmation_review_cards || [];
  const sourceCards = report.source_checkpoint_review_cards || [];
  const missingCards = report.missing_artifact_request_cards || [];
  const drill = report.a0_a2_drill_card || {};
  const handoff = report.human_review_packet_card || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "none"}`,
    `Action: ${summary.next_safe_action_key || report.requested_action_key || "review"} - ${summary.next_safe_action || "Guided Loop pruefen."}`,
    `Route: ${summary.route || step.route || "missing"}`,
    `Endpoint: ${summary.endpoint || step.endpoint || "missing"}`,
    `Step: ${summary.guided_step_status || step.status || "missing"}; ready=${summary.ready ? "ja" : "nein"}`,
    `Source anchors: ${summary.source_anchor_count || 0}; checkpoint hashes=${summary.checkpoint_hash_count || 0}`,
    `Open confirmations: ${summary.open_operator_confirmation_count || 0}; help=${summary.help_status || "missing"}`,
    `Prefill: ${prefill.status || "missing"}; hash=${prefill.prefill_hash || "missing"}`,
    `Dry run default: ${report.dry_run_default ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Local execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "guided rehearsal loop metadata-only"}`,
    "",
    "Operator Confirmations:",
    ...(confirmations.slice(0, 6).map((item) => `- ${item.card_id || item.step_id}: ${item.step_id || "review"}; confirmed=${item.operator_confirmed ? "ja" : "nein"}; hash=${item.artifact_hash || "missing"}`)),
    "",
    "Source/Checkpoint:",
    ...(sourceCards.slice(0, 4).map((item) => `- ${item.card_id}: ${item.status || "unknown"}; anchors=${item.source_anchor_count || 0}; checkpoints=${item.checkpoint_hash_count || 0}`)),
    "",
    "Missing Artifacts:",
    ...(missingCards.slice(0, 6).map((item) => `- ${item.step_id}: ${item.current_status || "missing"}; endpoint=${item.endpoint || "missing"}`)),
    "",
    `A0-A2 Drill: ${drill.card_id || "none"}; help=${drill.requested_help_level || "A2"}`,
    `Human Review: ${handoff.human_handoff_status || "none"}; hash=${handoff.human_handoff_markdown_hash || "missing"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderPythonExamGuidedLoopControlSurface(report, sourceLabel) {
  const summary = report.control_summary || {};
  const step = report.current_guided_step_card || {};
  const source = report.source_anchor_status || {};
  const checkpoint = report.notebook_checkpoint_status || {};
  const confirmations = report.operator_confirmation_status || {};
  const helpStatus = report.a0_a2_help_status || {};
  const evidence = report.evidence_status || {};
  const clicks = report.control_clicks || [];
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Skill: ${summary.selected_skill_tag || report.selected_skill_tag || "none"}`,
    `Next click: ${summary.next_safe_click || "review_visible_metadata"}`,
    `Action: ${summary.action_key || "review"}; route=${summary.route || "missing"}`,
    `Endpoint: ${summary.endpoint || "missing"}`,
    `Step: ${summary.guided_step_status || step.status || "missing"}; ready=${summary.ready ? "ja" : "nein"}`,
    `Prefill hash: ${summary.prefill_hash || step.prefill_hash || "missing"}`,
    `Source cards: ${(source.source_card_ids || []).join(", ") || "keine"}; anchors=${source.source_anchor_count || 0}`,
    `Checkpoint: ${checkpoint.status || "missing"}; count=${checkpoint.checkpoint_hash_count || 0}; latest=${checkpoint.latest_notebook_checkpoint_hash || "missing"}`,
    `Confirmations: ${confirmations.status || "missing"}; open=${confirmations.open_operator_confirmation_count || 0}; cards=${confirmations.review_card_count || 0}`,
    `Help: ${helpStatus.status || "missing"} ${JSON.stringify(helpStatus.profile || {})}`,
    `Evidence: ${evidence.evidence_preview_status || "missing"}; receipt=${evidence.evidence_preview_receipt_id || "missing"}`,
    `Human handoff: ${evidence.human_handoff_status || "missing"}; hash=${evidence.human_handoff_markdown_hash || "missing"}`,
    `Dry-run request: ${summary.dry_run_request_status || "prepared_not_executed"}`,
    `Dry run executed by surface: ${report.dry_run_request_executed_by_surface ? "ja" : "nein"}`,
    `Local writes requested: ${report.local_writes_requested ? "ja" : "nein"}`,
    `Local execution started: ${report.local_execution_started ? "ja" : "nein"}`,
    `Raw query returned: ${report.raw_query_returned ? "ja" : "nein"}`,
    `Raw text returned: ${report.raw_text_returned ? "ja" : "nein"}`,
    `Notebook code returned: ${report.notebook_code_returned ? "ja" : "nein"}`,
    `Local paths returned: ${report.local_paths_returned ? "ja" : "nein"}`,
    `Grenze: ${report.execution_boundary || "guided loop control metadata-only"}`,
    "",
    "Control Clicks:",
    ...(clicks.map((item) => `- ${item.click_id || "click"}: ${item.label || ""}; enabled=${item.enabled ? "ja" : "nein"}; endpoint=${item.endpoint || "none"}; prefill=${item.prefill_hash || "missing"}`)),
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 5).map((item) => `- ${item}`))
  ].join("\n");
}

function renderStudySessionPlan(plan, sourceLabel) {
  const coverage = plan.coverage_summary || {};
  const tasks = plan.tasks || [];
  return [
    sourceLabel,
    `Status: ${plan.status || "unknown"}`,
    `Exam: ${plan.exam_deployment_status || "not_cleared"}`,
    `Tasks: ${tasks.length}, bereit: ${plan.ready_task_count || 0}`,
    `Coverage: ${coverage.current_ready_skill_count || 0} -> ${coverage.projected_ready_skill_count || 0}`,
    `Grenze: ${plan.execution_boundary || "study plan only"}`,
    "",
    "Session:",
    ...(tasks.slice(0, 5).map((item, index) => (
      `${index + 1}. ${item.skill_tag}: ${item.retrieval_prompt}\n   Notebook: ${item.notebook_microtask}`
    ))),
    "",
    "Spacing:",
    ...((plan.spacing_plan || []).slice(0, 5).map((item) => `- ${item.review_window}: ${item.skill_tag}`))
  ].join("\n");
}

function renderStudyReceiptValidation(validation, sourceLabel) {
  const evidence = validation.evidence || {};
  return [
    sourceLabel,
    `Status: ${validation.status || "unknown"}`,
    `Exam: ${validation.exam_deployment_status || "not_cleared"}`,
    `Task: ${validation.task_id || "missing"}`,
    `Skill: ${validation.skill_tag || "missing"}`,
    `Help: ${validation.help_level || "A0"}`,
    `Repeat required: ${validation.repeat_task_required ? "ja" : "nein"}`,
    `Evidence: prediction=${evidence.prediction_present ? "ja" : "nein"}, retrieval=${evidence.retrieval_response_present ? "ja" : "nein"}, notebook=${evidence.notebook_action_present ? "ja" : "nein"}, source=${evidence.source_anchor_present ? "ja" : "nein"}, reflection=${evidence.reflection_present ? "ja" : "nein"}`,
    `Issues: ${(validation.issues || []).join(", ") || "keine"}`,
    `Grenze: ${validation.assessment_policy || "no grade"}`
  ].join("\n");
}

function renderStudyReviewReport(report, sourceLabel) {
  const summary = report.receipt_summary || {};
  const evidence = report.evidence_profile || {};
  return [
    sourceLabel,
    `Status: ${report.status || "unknown"}`,
    `Exam: ${report.exam_deployment_status || "not_cleared"}`,
    `Plan tasks: ${report.planned_task_count || 0}`,
    `Receipts: ${summary.valid_receipt_count || 0}/${summary.submitted_receipt_count || 0}, repeat=${summary.repeat_task_required_count || 0}`,
    `Evidence: prediction=${evidence.prediction_present_count || 0}, notebook=${evidence.notebook_action_present_count || 0}, reflection=${evidence.reflection_present_count || 0}`,
    `Grenze: ${report.execution_boundary || "review only"}`,
    "",
    "Naechste Schritte:",
    ...((report.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderClearanceBoard(board, sourceLabel) {
  const lanes = board.scope_lanes || [];
  return [
    sourceLabel,
    `Status: ${board.status || "unknown"}`,
    `Exam: ${board.exam_deployment_status || "not_cleared"}`,
    `Scopes: ${lanes.length}`,
    `Grenze: ${board.decision_boundary || "not approval"}`,
    "",
    "Lanes:",
    ...lanes.map((lane) => (
      `- ${lane.clearance_scope}: ${lane.current_status}; Rollen: ${(lane.required_reviewer_roles || []).join(", ")}`
    )),
    "",
    "Naechste Schritte:",
    ...((board.next_actions || []).slice(0, 3).map((item) => `- ${item}`))
  ].join("\n");
}

function renderSubmissionBundle(bundle, sourceLabel) {
  const summary = bundle.combined_evidence_summary || {};
  const lanes = bundle.decision_lanes || [];
  return [
    sourceLabel,
    `Status: ${bundle.status || "unknown"}`,
    `Exam: ${bundle.exam_deployment_status || "not_cleared"}`,
    `Decision Lanes: ${lanes.length}`,
    `Jobs: ${summary.extraction_job_count || 0} (OCR ${summary.ocr_job_count || 0}, Transkription ${summary.transcription_job_count || 0})`,
    `Grenze: ${bundle.submission_boundary || "not sent, not approval"}`,
    "",
    "Lanes:",
    ...lanes.map((lane) => `- ${lane.lane_id}: ${lane.status}; Validator: ${lane.validator_endpoint}`),
    "",
    "Naechste Schritte:",
    ...((bundle.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderDecisionRequest(packet, sourceLabel) {
  const receipt = packet.receipt_template || {};
  const evidence = packet.evidence_manifest || [];
  return [
    sourceLabel,
    `Status: ${packet.status || "unknown"}`,
    `Lane: ${packet.lane_id || "missing"}`,
    `Request ID: ${packet.request_id || "missing"}`,
    `Exam: ${packet.exam_deployment_status || "not_cleared"}`,
    `Receipt: ${receipt.manual_submission_status || "missing"}, Tool sendet: ${receipt.tool_sent_message ? "ja" : "nein"}`,
    `Evidence: ${evidence.length}`,
    `Grenze: ${packet.request_boundary || "not sent, not approval"}`,
    "",
    "Checkliste:",
    ...((packet.human_review_checklist || []).slice(0, 6).map((item) => `- ${item}`)),
    "",
    "Naechste Schritte:",
    ...((packet.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderDecisionJournal(summary, sourceLabel) {
  return [
    sourceLabel,
    `Status: ${summary.status || "unknown"}`,
    `Events: ${summary.event_count || 0}`,
    `Blocked: ${summary.blocked_record_count || 0}`,
    `Sent Receipts: ${summary.sent_receipt_count || 0}`,
    `Draft Receipts: ${summary.draft_receipt_count || 0}`,
    "",
    "By Lane:",
    ...Object.entries(summary.by_lane || {}).map(([lane, count]) => `- ${lane}: ${count}`),
    "",
    `Grenze: ${summary.gate_policy || "journal entries do not authorize gates"}`
  ].join("\n");
}

function renderDecisionRecordJournal(summary, sourceLabel) {
  const gates = summary.gate_summary || {};
  const deferral = summary.extraction_deferral_summary || {};
  return [
    sourceLabel,
    `Status: ${summary.status || "unknown"}`,
    `Records: ${summary.record_count || 0}`,
    `Accepted: ${summary.accepted_record_count || 0}, blocked: ${summary.blocked_record_count || 0}`,
    `Exam Record: ${gates.exam_clearance_record_valid ? "validiert" : "offen"}`,
    `Extraction Deferral: ${gates.extraction_deferral_record_valid ? "validiert" : "offen"}`,
    `Manual Go: ${gates.manual_deployment_go_recorded ? "recorded" : "not recorded"}`,
    `Exam Deployment: ${gates.exam_deployment_status || "not_cleared"}`,
    `Deferral Types: ${(deferral.deferred_job_types || []).join(", ") || "none"}`,
    "",
    "By Record Type:",
    ...Object.entries(summary.by_record_type || {}).map(([recordType, count]) => `- ${recordType}: ${count}`),
    "",
    `Grenze: ${summary.gate_policy || "journal entries are review evidence only"}`
  ].join("\n");
}

function renderDecisionState(state, sourceLabel) {
  const extraction = state.local_extraction_decision || {};
  const exam = state.exam_authority_decision || {};
  const gates = state.gate_summary || {};
  return [
    sourceLabel,
    `Status: ${state.status || "unknown"}`,
    `Exam Deployment: ${state.exam_deployment_status || "not_cleared"}`,
    `Extraktion: ${extraction.status || "missing"} (${gates.local_extraction_can_start ? "startbereit" : "offen"})`,
    `Exam Record: ${exam.status || "missing"} (${gates.exam_clearance_record_valid ? "validiert" : "offen"})`,
    `Deployment Go: ${exam.deployment_switch_status || "not_requested"}`,
    `Grenze: ${state.decision_boundary || "no silent deployment"}`,
    "",
    "Naechste Schritte:",
    ...((state.next_actions || []).slice(0, 4).map((item) => `- ${item}`))
  ].join("\n");
}

function renderContextPacket(packet, sourceLabel) {
  const contract = packet.handoff_contract || {};
  return [
    sourceLabel,
    `Rolle: ${(packet.role || {}).role_id || "unknown"} - ${(packet.role || {}).label || ""}`,
    `Mission: ${(packet.role || {}).mission || ""}`,
    `Exam Gate: ${(packet.mode_gates || {}).exam_controlled_gateway || "not_cleared"}`,
    "",
    "Handoff-Felder:",
    ...((contract.required_fields || []).map((field) => `- ${field}`)),
    "",
    `Harness: ${packet.required_harness || "test or smoke required"}`
  ].join("\n");
}

function buildDemoFeedback() {
  return {
    scenario_id: feedbackScenario.value,
    outcome: feedbackOutcome.value,
    severity: feedbackSeverity.value,
    what_i_tried: feedbackTried.value,
    expected: feedbackExpected.value,
    what_happened: feedbackHappened.value,
    button_or_endpoint: feedbackEndpoint.value,
    public_safe_text: feedbackPublicText.value,
    private_data_removed: feedbackPrivateRemoved.checked
  };
}

function validateFeedbackLocally(feedback) {
  const issues = [];
  ["scenario_id", "what_i_tried", "expected", "what_happened", "button_or_endpoint"].forEach((field) => {
    if (!feedback[field]) issues.push(`missing_${field}`);
  });
  if (!feedback.private_data_removed) issues.push("private_data_not_confirmed_removed");
  const flags = classifyLocally([
    feedback.what_i_tried,
    feedback.expected,
    feedback.what_happened,
    feedback.button_or_endpoint,
    feedback.public_safe_text
  ].join("\n"));
  if (flags.length) issues.push("feedback_not_public_safe");
  return {
    status: issues.length ? "blocked" : "ok",
    issues,
    findings: flags
  };
}

function renderFeedbackValidation(validation, sourceLabel) {
  return [
    sourceLabel,
    `Status: ${validation.status}`,
    `Issues: ${(validation.issues || []).join(", ") || "none"}`,
    `Findings: ${(validation.findings || []).map((item) => item.type || item).join(", ") || "none"}`,
    validation.feedback_id ? `Feedback-ID: ${validation.feedback_id}` : ""
  ].filter(Boolean).join("\n");
}

document.querySelector("#selection").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.id) return;
  const response = await chrome.tabs.sendMessage(tab.id, { type: "UNIBOT_GET_SELECTION" });
  external.value = response.selectedText || external.value;
});

document.querySelector("#prompt").addEventListener("click", async () => {
  const apiCard = await callUniBot("/api/unibot/prompt-card", {
    task: task.value,
    tool: "colab_gemini",
    mode: "practice_overlay"
  });
  const card = apiCard ? apiCard.copyable_prompt : promptCard();
  await navigator.clipboard.writeText(card);
  result.value = `${apiCard ? "Lokale UniBot-API genutzt." : "Offline-Fallback genutzt."}\n\nPromptkarte kopiert:\n\n${card}`;
});

document.querySelector("#review").addEventListener("click", async () => {
  const apiReview = await callUniBot("/api/unibot/review-output", {
    external_output: external.value,
    requested_help_level: helpLevel(),
    mode: "practice_overlay"
  });
  if (apiReview) {
    result.value = [
      "Lokale UniBot-API genutzt.",
      `Hilfestufe: ${apiReview.requested_help_level}`,
      `Status: ${apiReview.status}`,
      `Flags: ${(apiReview.categories || []).join(", ") || "none"}`,
      apiReview.allowed_socratic_hint
    ].join("\n");
    return;
  }

  const flags = classifyLocally(external.value);
  const blocked = flags.length > 0;
  const hint = blocked
    ? "Blockiert: Nutze nur eine Rueckfrage. Welcher Teil ist dein eigener naechster Schritt?"
    : "Erlaubt als sokratische Hilfe: keine Loesung uebernehmen, Reflexion ins Ledger schreiben.";
  result.value = [
    "Offline-Fallback genutzt.",
    `Hilfestufe: ${helpLevel()}`,
    `Status: ${blocked ? "blocked" : "allowed"}`,
    `Flags: ${flags.join(", ") || "none"}`,
    hint
  ].join("\n");
});

document.querySelector("#ledger").addEventListener("click", async () => {
  const flow = await callUniBot("/api/unibot/practice-flow", {
    task: task.value,
    external_output: external.value,
    requested_help_level: helpLevel(),
    mode: "practice_overlay",
    tool: "colab_gemini",
    student_reflection: reflection.value
  });
  if (!flow) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  const stored = await callUniBot("/api/unibot/ledger/append", {
    event: flow.guardian_event
  });
  result.value = [
    stored ? "Ledger lokal gespeichert." : "Flow geprueft, Ledger konnte nicht gespeichert werden.",
    `Status: ${flow.postfilter.status}`,
    `Hilfestufe: ${flow.formative_score.help_levels.join(", ")}`,
    `Score: ${flow.formative_score.score} privat/formativ`,
    flow.postfilter.allowed_socratic_hint
  ].join("\n");
});

document.querySelector("#adaptive").addEventListener("click", async () => {
  const apiPlan = await callUniBot("/api/unibot/tasks/adaptive-plan", {
    skill_state: localSkillState(),
    max_tasks: 3,
    public_safe: true
  });
  if (apiPlan) {
    result.value = renderAdaptivePlan(apiPlan, "Lokale UniBot-API genutzt.");
    return;
  }
  result.value = renderAdaptivePlan(offlineAdaptivePlan(), "Offline-Fallback genutzt.");
});

document.querySelector("#commandCenter").addEventListener("click", async () => {
  const center = await callUniBot("/api/unibot/orchestration/command-center", {
    public_safe: true
  });
  if (!center) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderCommandCenter(center, "Lokale UniBot-API genutzt.");
});

document.querySelector("#compilerPlan").addEventListener("click", async () => {
  const plan = await callUniBot("/api/unibot/course/compiler-plan", {
    review_policy: "staged",
    public_safe: true
  });
  if (!plan) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderCompilerPlan(plan, "Lokale UniBot-API genutzt.");
});

document.querySelector("#extractionQueue").addEventListener("click", async () => {
  const queue = await callUniBot("/api/unibot/course/extraction-queue", {
    review_policy: "staged",
    public_safe: true
  });
  if (!queue) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderExtractionQueue(queue, "Lokale UniBot-API genutzt.");
});

document.querySelector("#decisionPacket").addEventListener("click", async () => {
  const packet = await callUniBot("/api/unibot/course/extraction-decision-packet", {
    review_policy: "staged",
    public_safe: true
  });
  if (!packet) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderDecisionPacket(packet, "Lokale UniBot-API genutzt.");
});

document.querySelector("#localDecisionIntake").addEventListener("click", async () => {
  const packet = await callUniBot("/api/unibot/course/extraction-decision/local-intake", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    job_types: ["ocr"],
    batch_size: 12,
    public_safe: true
  });
  if (!packet) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderLocalDecisionIntake(packet, "Lokale UniBot-API genutzt. Decision-Intake ist hash-only und startet keine Extraktion.");
});

document.querySelector("#localDecisionWorkspace").addEventListener("click", async () => {
  const packet = await callUniBot("/api/unibot/course/extraction-decision/workspace/prepare", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_output_dir: "~/.unibot_guardian/private_extractions",
    job_types: ["ocr"],
    batch_size: 12,
    public_safe: true
  });
  if (!packet) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderLocalDecisionWorkspace(packet, "Lokale UniBot-API genutzt. Workspace schreibt Template/Manifest lokal und startet keine Extraktion.");
});

document.querySelector("#operatorPacket").addEventListener("click", async () => {
  const packet = await callUniBot("/api/unibot/course/extraction-operator-packet", {
    review_policy: "staged",
    public_safe: true
  });
  if (!packet) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderOperatorPacket(packet, "Lokale UniBot-API genutzt.");
});

document.querySelector("#privateExtractionRun").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/course/private-extraction/run-batch", {
    review_policy: "staged",
    max_jobs: 4,
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderPrivateExtractionRun(report, "Lokale UniBot-API genutzt. Ohne valide Entscheidung blockiert dieser Harness und schreibt keine Extraktion.");
});

document.querySelector("#privateExtractionRunOcr").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/course/private-extraction/run-batch", {
    review_policy: "staged",
    max_jobs: 12,
    job_types: ["ocr"],
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderPrivateExtractionRun(report, "Lokale UniBot-API genutzt. OCR-first nutzt einen lokalen Decision-Record aus dem Journal, schreibt nur Hash-Receipts und blockiert ohne valide Entscheidung.");
});

document.querySelector("#ocrFirstOperatorRun").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/course/ocr-first/operator-run", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_output_dir: "~/.unibot_guardian/private_extractions",
    batch_size: 12,
    operator_confirmed_dry_run: false,
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderOcrFirstOperatorRun(report, "Lokale UniBot-API genutzt. Operator-Run prueft Dry-run und startet ohne Confirmation keine OCR.");
});

document.querySelector("#videoTranscriptionRun").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/course/video-transcription/run-batch", {
    review_policy: "staged",
    max_jobs: 4,
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderVideoTranscriptionRun(report, "Lokale UniBot-API genutzt. Ohne valide Entscheidung blockiert dieser Harness und schreibt keine Transkription.");
});

document.querySelector("#extractionProgress").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/course/extraction-progress-report", {
    review_policy: "staged",
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderExtractionProgress(report, "Lokale UniBot-API genutzt.");
});

document.querySelector("#extractionReceiptJournal").addEventListener("click", async () => {
  const summary = await callUniBot("/api/unibot/course/extraction-receipts/summary", {});
  if (!summary) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderExtractionReceiptJournal(summary, "Lokale UniBot-API genutzt.");
});

document.querySelector("#extractionHumanReviewPlan").addEventListener("click", async () => {
  const plan = await callUniBot("/api/unibot/course/extraction-review/apply-plan", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    review_journal_path: "~/.unibot_guardian/extraction_human_reviews.jsonl",
    review_decisions: [],
    public_safe: true
  });
  if (!plan) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderExtractionHumanReviewPlan(plan, "Lokale UniBot-API genutzt. Ohne Review-Entscheidungen schreibt dieser Plan nichts.");
});

document.querySelector("#privateManifestApplyDryRun").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/course/extraction-manifest/apply-dry-run", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    operator_confirmed_manifest_apply: false,
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderPrivateManifestApplyDryRun(report, "Lokale UniBot-API genutzt. Sidepanel prueft nur Dry-Run und schreibt kein Manifest.");
});

document.querySelector("#privateTutorIndexDryRun").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/course/tutor-index/dry-run", {
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    operator_confirmed_tutor_index_build: false,
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderPrivateTutorIndexDryRun(report, "Lokale UniBot-API genutzt. Standard ist Dry-Run; der Index wird nur mit Operator-Confirmation gebaut.");
});

document.querySelector("#privateIndexTutorResponse").addEventListener("click", async () => {
  const response = await callUniBot("/api/unibot/course/tutor-index/respond-dry-run", {
    query: task.value,
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    mode: "exam_controlled_gateway",
    requested_help_level: helpLevel(),
    exam_status: "strict",
    public_safe: true
  });
  if (!response) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderPrivateIndexTutorResponse(response, "Lokale UniBot-API genutzt. Antwort nutzt nur den hash-only Tutor-Index und gibt die Frage nicht roh zurueck.");
});

document.querySelector("#privateTutorUseFlow").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/course/private-tutor-use-flow/dry-run", {
    query: task.value,
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    ledger_path: "~/.unibot_guardian/help_ledger.jsonl",
    requested_help_level: helpLevel(),
    mode: "exam_controlled_gateway",
    exam_status: "strict",
    operator_confirmed_manifest_apply: false,
    operator_confirmed_tutor_index_build: false,
    operator_confirmed_help_ledger_append: false,
    study_receipt: {
      prediction_present: Boolean(task.value.trim()),
      notebook_action_present: true,
      reflection_present: Boolean(reflection.value.trim()),
    },
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderPrivateTutorUseFlow(report, "Lokale UniBot-API genutzt. Flow ist standardmaessig Dry-Run; Apply/Index/Ledger schreiben nur mit Operator-Confirmation.");
});

document.querySelector("#notebookCheckpointAdapter").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/exam-workspace/notebook-checkpoint/adapt", {
    task_id: "sidepanel-local-checkpoint",
    skill_tag: (skillTags([task.value, notebookCell.value].join("\n"))[0] || "general_python"),
    source_card_ids: ["dfg-gwp"],
    cell_source: notebookCell.value,
    cell_index: 0,
    cell_type: "code",
    requested_help_level: helpLevel(),
    prediction_present: Boolean(task.value.trim()),
    retrieval_response_present: true,
    notebook_action_present: Boolean(notebookCell.value.trim()),
    reflection_present: Boolean(reflection.value.trim()),
    student_reflection: reflection.value,
    checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
    operator_confirmed_checkpoint_store: false,
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastNotebookCheckpointAdapter = report;
  result.value = renderNotebookCheckpointAdapter(report, "Lokale UniBot-API genutzt. Lokale Zelle wird nur als Hash-Checkpoint ausgewertet.");
});

document.querySelector("#examWorkspaceRun").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/exam-workspace/run-dry-run", {
    query: task.value,
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    ledger_path: "~/.unibot_guardian/help_ledger.jsonl",
    requested_help_level: helpLevel(),
    exam_status: "strict",
    cell_index: 0,
    cell_type: "code",
    cell_source: notebookCell.value,
    student_reflection: reflection.value,
    operator_confirmed_exam_workspace_run: false,
    operator_confirmed_manifest_apply: false,
    operator_confirmed_tutor_index_build: false,
    operator_confirmed_help_ledger_append: false,
    operator_confirmed_exam_ledger_append: false,
    study_receipt: {
      prediction_present: Boolean(task.value.trim()),
      notebook_action_present: true,
      reflection_present: Boolean(reflection.value.trim()),
    },
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderExamWorkspaceRun(report, "Lokale UniBot-API genutzt. Exam-Workspace bleibt Dry-Run, koppelt Notebook, Tutor, Ledger und Export, und bleibt not_cleared.");
});

function syntheticExtractionDeferral() {
  return {
    deferral_scope: "course_material_extraction",
    decision_status: "approved_deferral",
    deferred_job_types: ["ocr", "transcription"],
    deferral_reason: "synthetic sidepanel schema check for current public draft planning",
    reviewer_roles: ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
    decision_reference: "synthetic sidepanel deferral reference",
    human_review_before_future_tutor_use: true,
    raw_text_public_release_allowed: false,
    exam_deployment_status: "not_cleared"
  };
}

document.querySelector("#extractionDeferralValidate").addEventListener("click", async () => {
  const validation = await callUniBot("/api/unibot/course/extraction-deferral/validate", {
    deferral_record: syntheticExtractionDeferral(),
    public_safe: true
  });
  if (!validation) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderExtractionDeferralValidation(validation, "Lokale UniBot-API genutzt. Synthetischer Schema-Check, keine echte Freigabe.");
});

document.querySelector("#extractionCompletionReport").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/course/extraction-completion-report", {
    review_policy: "staged",
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderExtractionCompletionReport(report, "Lokale UniBot-API genutzt.");
});

document.querySelector("#extractionBatchPlan").addEventListener("click", async () => {
  const plan = await callUniBot("/api/unibot/course/extraction-batch-plan", {
    review_policy: "staged",
    batch_size: 12,
    public_safe: true
  });
  if (!plan) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderExtractionBatchPlan(plan, "Lokale UniBot-API genutzt.");
});

document.querySelector("#extractionBatchPlanOcr").addEventListener("click", async () => {
  const plan = await callUniBot("/api/unibot/course/extraction-batch-plan", {
    review_policy: "staged",
    batch_size: 12,
    job_types: ["ocr"],
    public_safe: true
  });
  if (!plan) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderExtractionBatchPlan(plan, "Lokale UniBot-API genutzt. OCR-first trennt Textcontainer von Video-Transkription.");
});

document.querySelector("#batchReceiptPacket").addEventListener("click", async () => {
  const packet = await callUniBot("/api/unibot/course/extraction-batch-receipt-packet", {
    review_policy: "staged",
    batch_size: 12,
    batch_index: 1,
    public_safe: true
  });
  if (!packet) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderBatchReceiptPacket(packet, "Lokale UniBot-API genutzt.");
});

document.querySelector("#batchReceiptPacketOcr").addEventListener("click", async () => {
  const packet = await callUniBot("/api/unibot/course/extraction-batch-receipt-packet", {
    review_policy: "staged",
    batch_size: 12,
    batch_index: 1,
    job_types: ["ocr"],
    public_safe: true
  });
  if (!packet) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderBatchReceiptPacket(packet, "Lokale UniBot-API genutzt. OCR-first Receipt-Paket ohne Videojobs.");
});

document.querySelector("#manifestUpdatePlan").addEventListener("click", async () => {
  const plan = await callUniBot("/api/unibot/course/extraction-manifest-update-plan", {
    review_policy: "staged",
    public_safe: true
  });
  if (!plan) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderManifestUpdatePlan(plan, "Lokale UniBot-API genutzt.");
});

document.querySelector("#tutorCoveragePlan").addEventListener("click", async () => {
  const plan = await callUniBot("/api/unibot/course/tutor-coverage-plan", {
    review_policy: "staged",
    public_safe: true
  });
  if (!plan) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderTutorCoveragePlan(plan, "Lokale UniBot-API genutzt.");
});

document.querySelector("#materialCoverageRun").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/course/material-coverage/run", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    focus_query: task.value,
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderMaterialCoverageRun(report, "Lokale UniBot-API genutzt. Coverage-Run verdichtet Material, Receipts, Manifest, Index und naechsten Exam-Workspace-Startpunkt.");
});

document.querySelector("#examSkillDrilldown").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/course/exam-skill-drilldown", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    focus_query: task.value,
    selected_skill_tag: task.value,
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastExamSkillDrilldown = report;
  result.value = renderExamSkillDrilldown(report, "Lokale UniBot-API genutzt. Exam-Skill-Drilldown erstellt.");
});

document.querySelector("#skillToWorkspaceRun").addEventListener("click", async () => {
  const flowReport = await callUniBot("/api/unibot/course/skill-to-workspace-live-flow", skillWorkspaceLiveFlowPayload());
  if (!flowReport) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastExamSkillDrilldown = flowReport.exam_skill_drilldown || null;
  lastExamWorkspaceOperatorRun = flowReport.operator_dry_run || null;
  lastSkillToWorkspaceLiveFlow = flowReport;
  result.value = renderSkillToWorkspaceLiveFlow(flowReport, null, "Skill-to-Workspace Live Flow: Drilldown vorausgefuellt und Operator-Dry-Run ausgefuehrt.");
});

document.querySelector("#skillToWorkspaceSessionCarryover").addEventListener("click", async () => {
  const carryover = await callUniBot("/api/unibot/course/skill-to-workspace-session-carryover", skillWorkspaceSessionCarryoverPayload());
  if (!carryover) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  const artifacts = carryover.carryover_artifacts || {};
  lastSkillToWorkspaceSessionCarryover = carryover;
  if (artifacts.session_console) {
    lastExamSessionConsoleReceipt = artifacts.session_console.session_console_receipt || null;
    examSessionConsoleReports = [...examSessionConsoleReports, artifacts.session_console].slice(-12);
  }
  if (artifacts.python_exam_evidence_export_preview) {
    lastPythonExamEvidenceExportPreview = artifacts.python_exam_evidence_export_preview;
  }
  if (artifacts.python_exam_human_handoff_packet) {
    lastPythonExamHumanHandoffPacket = artifacts.python_exam_human_handoff_packet;
  }
  result.value = renderSkillToWorkspaceSessionCarryover(carryover, "Skill-to-Workspace Session Carryover: Dry-Run-Receipt bis Evidence/Handoff weitergereicht.");
});

document.querySelector("#examSessionConsole").addEventListener("click", async () => {
  const drilldown = await callUniBot("/api/unibot/course/exam-skill-drilldown", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    focus_query: task.value,
    selected_skill_tag: task.value,
    public_safe: true
  });
  if (!drilldown) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastExamSkillDrilldown = drilldown;
  const liveFlow = drilldown.skill_to_workspace_live_flow || {};
  if (liveFlow.status !== "ready_to_execute_operator_dry_run") {
    result.value = renderExamSkillDrilldown(drilldown, "Skill ist noch nicht workspace-ready. Session-Konsole wartet auf Material-/Index-Readiness.");
    return;
  }
  const report = await callUniBot("/api/unibot/exam-workspace/session-console", skillWorkspaceSessionConsolePayload(drilldown));
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastExamSessionConsoleReceipt = report.session_console_receipt || null;
  examSessionConsoleReports = [...examSessionConsoleReports, report].slice(-12);
  result.value = renderExamSessionConsole(report, "Exam Workspace Session Console: Skill vorausgefuellt und Console-Dry-Run erstellt.");
});

document.querySelector("#examRunHistoryReview").addEventListener("click", async () => {
  let reports = examSessionConsoleReports;
  if (!reports.length) {
    const drilldown = await callUniBot("/api/unibot/course/exam-skill-drilldown", {
      review_policy: "staged",
      decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
      receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
      private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
      manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
      tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
      tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
      focus_query: task.value,
      selected_skill_tag: task.value,
      public_safe: true
    });
    if (!drilldown || (drilldown.skill_to_workspace_live_flow || {}).status !== "ready_to_execute_operator_dry_run") {
      result.value = drilldown
        ? renderExamSkillDrilldown(drilldown, "Skill ist noch nicht workspace-ready. History Review wartet auf Session-Console-Receipt.")
        : "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    const consoleReport = await callUniBot("/api/unibot/exam-workspace/session-console", skillWorkspaceSessionConsolePayload(drilldown));
    if (!consoleReport) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastExamSessionConsoleReceipt = consoleReport.session_console_receipt || null;
    examSessionConsoleReports = [...examSessionConsoleReports, consoleReport].slice(-12);
    reports = examSessionConsoleReports;
  }
  const review = await callUniBot("/api/unibot/exam-workspace/run-history-export-review", {
    console_reports: reports,
    console_receipts: lastExamSessionConsoleReceipt ? [lastExamSessionConsoleReceipt] : [],
    build_current_console: false,
    public_safe: true
  });
  if (!review) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastExamRunHistoryExportReview = review;
  result.value = renderExamRunHistoryReview(review, "Run-History Export Review: hash-only Verlauf und Review-Paket erstellt.");
});

document.querySelector("#courseExamCoverageDashboard").addEventListener("click", async () => {
  let reports = examSessionConsoleReports;
  if (!reports.length) {
    const drilldown = await callUniBot("/api/unibot/course/exam-skill-drilldown", {
      review_policy: "staged",
      decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
      receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
      private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
      manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
      tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
      tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
      focus_query: task.value,
      selected_skill_tag: task.value,
      public_safe: true
    });
    if (drilldown && (drilldown.skill_to_workspace_live_flow || {}).status === "ready_to_execute_operator_dry_run") {
      const consoleReport = await callUniBot("/api/unibot/exam-workspace/session-console", skillWorkspaceSessionConsolePayload(drilldown));
      if (consoleReport) {
        lastExamSkillDrilldown = drilldown;
        lastExamSessionConsoleReceipt = consoleReport.session_console_receipt || null;
        examSessionConsoleReports = [...examSessionConsoleReports, consoleReport].slice(-12);
        reports = examSessionConsoleReports;
      }
    }
  }
  const dashboard = await callUniBot("/api/unibot/course/exam-coverage-dashboard", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    focus_query: task.value,
    selected_skill_tag: task.value,
    console_reports: reports,
    console_receipts: lastExamSessionConsoleReceipt ? [lastExamSessionConsoleReceipt] : [],
    build_current_console: false,
    public_safe: true
  });
  if (!dashboard) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastCourseExamCoverageDashboard = dashboard;
  result.value = renderCourseExamCoverageDashboard(dashboard, "Course Exam Coverage Dashboard: Material, Skill-Readiness, Session Console und Run-History kompakt zusammengezogen.");
});

document.querySelector("#perSkillActionRouter").addEventListener("click", async () => {
  const router = await callUniBot("/api/unibot/course/per-skill-action-router", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    focus_query: task.value,
    selected_skill_tag: task.value,
    console_reports: examSessionConsoleReports,
    console_receipts: lastExamSessionConsoleReceipt ? [lastExamSessionConsoleReceipt] : [],
    build_current_console: false,
    public_safe: true
  });
  if (!router) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPerSkillActionRouter = router;
  result.value = renderPerSkillActionRouter(router, "Per-Skill Action Router: naechste sichere Route fuer den ausgewaehlten Python-Skill erstellt.");
});

document.querySelector("#executeRoutedAction").addEventListener("click", async () => {
  let router = lastPerSkillActionRouter;
  if (!router) {
    router = await callUniBot("/api/unibot/course/per-skill-action-router", {
      review_policy: "staged",
      decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
      receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
      private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
      manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
      tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
      tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
      focus_query: task.value,
      selected_skill_tag: task.value,
      console_reports: examSessionConsoleReports,
      console_receipts: lastExamSessionConsoleReceipt ? [lastExamSessionConsoleReceipt] : [],
      build_current_console: false,
      public_safe: true
    });
    if (!router) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastPerSkillActionRouter = router;
  }
  const report = await callUniBot("/api/unibot/course/routed-action-executor", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    ledger_path: "~/.unibot_guardian/help_ledger.jsonl",
    checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
    router_report: router,
    selected_route: router.selected_route || {},
    focus_query: task.value,
    selected_skill_tag: (router.selected_skill || {}).skill_tag || task.value,
    query: task.value,
    requested_help_level: helpLevel() === "A0" || helpLevel() === "A1" ? helpLevel() : "A2",
    exam_status: "strict",
    student_reflection: reflection.value,
    cell_source: notebookCell.value,
    cell_index: 0,
    cell_type: "code",
    console_reports: examSessionConsoleReports,
    console_receipts: lastExamSessionConsoleReceipt ? [lastExamSessionConsoleReceipt] : [],
    operator_confirmed_checkpoint_store: confirmCheckpointStore.checked,
    operator_confirmed_exam_workspace_run: confirmExamWorkspaceRun.checked,
    operator_confirmed_manifest_apply: confirmManifestApply.checked,
    operator_confirmed_tutor_index_build: confirmTutorIndexBuild.checked,
    operator_confirmed_help_ledger_append: confirmHelpLedgerAppend.checked,
    operator_confirmed_exam_ledger_append: confirmExamLedgerAppend.checked,
    operator_confirmed_private_extraction_run: false,
    operator_confirmed_video_transcription_run: false,
    study_receipt: {
      prediction_present: Boolean(task.value.trim()),
      notebook_action_present: Boolean(notebookCell.value.trim()),
      reflection_present: Boolean(reflection.value.trim()),
    },
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastRoutedActionExecutor = report;
  result.value = renderRoutedActionExecutor(report, "Routed Action Executor: ausgewaehlte Route kontrolliert als Dry-run ausgefuehrt.");
});

document.querySelector("#examRunPacket").addEventListener("click", async () => {
  let router = lastPerSkillActionRouter;
  if (!router) {
    router = await callUniBot("/api/unibot/course/per-skill-action-router", {
      review_policy: "staged",
      decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
      receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
      private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
      manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
      tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
      tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
      focus_query: task.value,
      selected_skill_tag: task.value,
      console_reports: examSessionConsoleReports,
      console_receipts: lastExamSessionConsoleReceipt ? [lastExamSessionConsoleReceipt] : [],
      build_current_console: false,
      public_safe: true
    });
    if (!router) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastPerSkillActionRouter = router;
  }
  let executor = lastRoutedActionExecutor;
  if (!executor) {
    executor = await callUniBot("/api/unibot/course/routed-action-executor", {
      review_policy: "staged",
      decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
      receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
      private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
      manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
      tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
      tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
      ledger_path: "~/.unibot_guardian/help_ledger.jsonl",
      checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
      router_report: router,
      selected_route: router.selected_route || {},
      focus_query: task.value,
      selected_skill_tag: (router.selected_skill || {}).skill_tag || task.value,
      query: task.value,
      requested_help_level: helpLevel() === "A0" || helpLevel() === "A1" ? helpLevel() : "A2",
      exam_status: "strict",
      student_reflection: reflection.value,
      cell_source: notebookCell.value,
      cell_index: 0,
      cell_type: "code",
      console_reports: examSessionConsoleReports,
      console_receipts: lastExamSessionConsoleReceipt ? [lastExamSessionConsoleReceipt] : [],
      study_receipt: {
        prediction_present: Boolean(task.value.trim()),
        notebook_action_present: Boolean(notebookCell.value.trim()),
        reflection_present: Boolean(reflection.value.trim()),
      },
      public_safe: true
    });
    if (!executor) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastRoutedActionExecutor = executor;
  }
  const packet = await callUniBot("/api/unibot/course/exam-run-packet", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    ledger_path: "~/.unibot_guardian/help_ledger.jsonl",
    checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
    router_report: router,
    executor_report: executor,
    focus_query: task.value,
    selected_skill_tag: (router.selected_skill || {}).skill_tag || task.value,
    python_exam_local_cycle_readiness_review: lastPythonExamLocalCycleReadinessReview,
    python_exam_local_cycle_readiness_handoff: lastPythonExamLocalCycleReadinessHandoff,
    python_exam_local_cycle_operator_workspace_card: lastPythonExamLocalCycleWorkspaceCard,
    console_reports: examSessionConsoleReports,
    console_receipts: lastExamSessionConsoleReceipt ? [lastExamSessionConsoleReceipt] : [],
    query: task.value,
    requested_help_level: helpLevel() === "A0" || helpLevel() === "A1" ? helpLevel() : "A2",
    exam_status: "strict",
    student_reflection: reflection.value,
    cell_source: notebookCell.value,
    cell_index: 0,
    cell_type: "code",
    study_receipt: {
      prediction_present: Boolean(task.value.trim()),
      notebook_action_present: Boolean(notebookCell.value.trim()),
      reflection_present: Boolean(reflection.value.trim()),
    },
    public_safe: true
  });
  if (!packet) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastExamRunPacket = packet;
  result.value = renderExamRunPacket(packet, "Exam Run Packet: Dashboard, Router, Executor und History als pruefbare Spur zusammengezogen.");
});

document.querySelector("#examPacketTimeline").addEventListener("click", async () => {
  let packet = lastExamRunPacket;
  if (!packet) {
    packet = await callUniBot("/api/unibot/course/exam-run-packet", {
      review_policy: "staged",
      decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
      receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
      private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
      manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
      tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
      tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
      ledger_path: "~/.unibot_guardian/help_ledger.jsonl",
      checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
      router_report: lastPerSkillActionRouter,
      executor_report: lastRoutedActionExecutor,
      focus_query: task.value,
      selected_skill_tag: (lastPerSkillActionRouter || {}).selected_skill ? (lastPerSkillActionRouter.selected_skill || {}).skill_tag : task.value,
      console_reports: examSessionConsoleReports,
      console_receipts: lastExamSessionConsoleReceipt ? [lastExamSessionConsoleReceipt] : [],
      query: task.value,
      requested_help_level: helpLevel() === "A0" || helpLevel() === "A1" ? helpLevel() : "A2",
      exam_status: "strict",
      student_reflection: reflection.value,
      cell_source: notebookCell.value,
      cell_index: 0,
      cell_type: "code",
      study_receipt: {
        prediction_present: Boolean(task.value.trim()),
        notebook_action_present: Boolean(notebookCell.value.trim()),
        reflection_present: Boolean(reflection.value.trim()),
      },
      public_safe: true
    });
    if (!packet) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastExamRunPacket = packet;
  }
  const timeline = await callUniBot("/api/unibot/course/exam-packet-timeline", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    ledger_path: "~/.unibot_guardian/help_ledger.jsonl",
    checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
    exam_run_packets: [packet],
    exam_run_packet: packet,
    router_report: lastPerSkillActionRouter,
    executor_report: lastRoutedActionExecutor,
    focus_query: task.value,
    selected_skill_tag: (packet.selected_skill_packet || {}).skill_tag || task.value,
    python_exam_local_cycle_readiness_review: lastPythonExamLocalCycleReadinessReview,
    python_exam_local_cycle_readiness_handoff: lastPythonExamLocalCycleReadinessHandoff,
    python_exam_local_cycle_operator_workspace_card: lastPythonExamLocalCycleWorkspaceCard,
    console_reports: examSessionConsoleReports,
    console_receipts: lastExamSessionConsoleReceipt ? [lastExamSessionConsoleReceipt] : [],
    public_safe: true
  });
  if (!timeline) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastExamPacketTimeline = timeline;
  result.value = renderExamPacketTimeline(timeline, "Exam Packet Timeline: Packet-Receipt, Route, Dry-run, Checkpoints und Review-Spur als metadata-only Verlauf.");
});

document.querySelector("#timelineExportReviewPacket").addEventListener("click", async () => {
  let timeline = lastExamPacketTimeline;
  let packet = lastExamRunPacket;
  if (!timeline) {
    if (!packet) {
      packet = await callUniBot("/api/unibot/course/exam-run-packet", {
        review_policy: "staged",
        decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
        receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
        private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
        manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
        tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
        tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
        ledger_path: "~/.unibot_guardian/help_ledger.jsonl",
        checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
        router_report: lastPerSkillActionRouter,
        executor_report: lastRoutedActionExecutor,
        focus_query: task.value,
        selected_skill_tag: (lastPerSkillActionRouter || {}).selected_skill ? (lastPerSkillActionRouter.selected_skill || {}).skill_tag : task.value,
        python_exam_local_cycle_readiness_review: lastPythonExamLocalCycleReadinessReview,
        python_exam_local_cycle_readiness_handoff: lastPythonExamLocalCycleReadinessHandoff,
        python_exam_local_cycle_operator_workspace_card: lastPythonExamLocalCycleWorkspaceCard,
        console_reports: examSessionConsoleReports,
        console_receipts: lastExamSessionConsoleReceipt ? [lastExamSessionConsoleReceipt] : [],
        query: task.value,
        requested_help_level: helpLevel() === "A0" || helpLevel() === "A1" ? helpLevel() : "A2",
        exam_status: "strict",
        student_reflection: reflection.value,
        cell_source: notebookCell.value,
        cell_index: 0,
        cell_type: "code",
        study_receipt: {
          prediction_present: Boolean(task.value.trim()),
          notebook_action_present: Boolean(notebookCell.value.trim()),
          reflection_present: Boolean(reflection.value.trim()),
        },
        public_safe: true
      });
      if (!packet) {
        result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
        return;
      }
      lastExamRunPacket = packet;
    }
    timeline = await callUniBot("/api/unibot/course/exam-packet-timeline", {
      review_policy: "staged",
      decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
      receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
      private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
      manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
      tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
      tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
      ledger_path: "~/.unibot_guardian/help_ledger.jsonl",
      checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
      exam_run_packets: [packet],
      exam_run_packet: packet,
      router_report: lastPerSkillActionRouter,
      executor_report: lastRoutedActionExecutor,
      focus_query: task.value,
      selected_skill_tag: (packet.selected_skill_packet || {}).skill_tag || task.value,
      python_exam_local_cycle_readiness_review: lastPythonExamLocalCycleReadinessReview,
      python_exam_local_cycle_readiness_handoff: lastPythonExamLocalCycleReadinessHandoff,
      python_exam_local_cycle_operator_workspace_card: lastPythonExamLocalCycleWorkspaceCard,
      console_reports: examSessionConsoleReports,
      console_receipts: lastExamSessionConsoleReceipt ? [lastExamSessionConsoleReceipt] : [],
      public_safe: true
    });
    if (!timeline) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastExamPacketTimeline = timeline;
  }
  const reviewPacket = await callUniBot("/api/unibot/course/timeline-export-review-packet", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    ledger_path: "~/.unibot_guardian/help_ledger.jsonl",
    checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
    exam_packet_timelines: [timeline],
    exam_packet_timeline: timeline,
    exam_run_packet: packet,
    exam_run_packets: packet ? [packet] : [],
    focus_query: task.value,
    selected_skill_tag: (timeline.timeline_summary || {}).skill_tags ? ((timeline.timeline_summary || {}).skill_tags[0] || task.value) : task.value,
    operator_confirmed_local_export_receipt: false,
    public_safe: true
  });
  if (!reviewPacket) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastTimelineExportReviewPacket = reviewPacket;
  result.value = renderTimelineExportReviewPacket(reviewPacket, "Timeline Export Review Packet: menschlich pruefbares Review-Paket aus Timeline, Receipts, Hashes und Review-Fragen.");
});

document.querySelector("#timelineExportReceiptJournalAppend").addEventListener("click", async () => {
  let reviewPacket = lastTimelineExportReviewPacket;
  if (!reviewPacket) {
    reviewPacket = await callUniBot("/api/unibot/course/timeline-export-review-packet", {
      review_policy: "staged",
      timeline_export_receipt_journal_path: "~/.unibot_guardian/timeline_export_receipts.jsonl",
      exam_packet_timeline: lastExamPacketTimeline,
      exam_packet_timelines: lastExamPacketTimeline ? [lastExamPacketTimeline] : [],
      exam_run_packet: lastExamRunPacket,
      exam_run_packets: lastExamRunPacket ? [lastExamRunPacket] : [],
      focus_query: task.value,
      selected_skill_tag: (lastExamPacketTimeline && lastExamPacketTimeline.timeline_summary) ? ((lastExamPacketTimeline.timeline_summary.skill_tags || [])[0] || task.value) : task.value,
      operator_confirmed_local_export_receipt: false,
      public_safe: true
    });
    if (!reviewPacket) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastTimelineExportReviewPacket = reviewPacket;
  }
  const journal = await callUniBot("/api/unibot/course/timeline-export-receipt-journal/append", {
    timeline_export_receipt_journal_path: "~/.unibot_guardian/timeline_export_receipts.jsonl",
    review_packet: reviewPacket,
    operator_confirmed_timeline_export_receipt_journal_append: confirmTimelineExportReceiptJournalAppend.checked,
    public_safe: true
  });
  if (!journal) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastTimelineExportReceiptJournalAppend = journal;
  result.value = renderTimelineExportReceiptJournalAppend(journal, "Timeline Receipt-Journal: Preview oder Append aus dem Review-Paket erzeugt.");
});

document.querySelector("#timelineExportReceiptJournalSummary").addEventListener("click", async () => {
  const summary = await callUniBot("/api/unibot/course/timeline-export-receipt-journal/summary", {
    timeline_export_receipt_journal_path: "~/.unibot_guardian/timeline_export_receipts.jsonl"
  });
  if (!summary) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastTimelineExportReceiptJournalSummary = summary;
  result.value = renderTimelineExportReceiptJournalSummary(summary, "Timeline Receipt-Journal Summary: lokale Review-Receipts metadata-only zusammengefasst.");
});

document.querySelector("#reviewChainIntegrityCheck").addEventListener("click", async () => {
  let journalAppend = lastTimelineExportReceiptJournalAppend;
  if (!journalAppend && lastTimelineExportReviewPacket) {
    journalAppend = await callUniBot("/api/unibot/course/timeline-export-receipt-journal/append", {
      timeline_export_receipt_journal_path: "~/.unibot_guardian/timeline_export_receipts.jsonl",
      review_packet: lastTimelineExportReviewPacket,
      operator_confirmed_timeline_export_receipt_journal_append: false,
      public_safe: true
    });
    if (!journalAppend) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastTimelineExportReceiptJournalAppend = journalAppend;
  }
  let journalSummary = lastTimelineExportReceiptJournalSummary;
  if (!journalSummary) {
    journalSummary = await callUniBot("/api/unibot/course/timeline-export-receipt-journal/summary", {
      timeline_export_receipt_journal_path: "~/.unibot_guardian/timeline_export_receipts.jsonl"
    });
    if (!journalSummary) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastTimelineExportReceiptJournalSummary = journalSummary;
  }
  const report = await callUniBot("/api/unibot/course/review-chain-integrity-check", {
    exam_run_packet: lastExamRunPacket,
    exam_packet_timeline: lastExamPacketTimeline,
    timeline_export_review_packet: lastTimelineExportReviewPacket,
    timeline_export_receipt_journal_append: journalAppend,
    timeline_export_receipt_journal_summary: journalSummary,
    timeline_export_receipt_journal_path: "~/.unibot_guardian/timeline_export_receipts.jsonl",
    selected_skill_tag: (lastExamPacketTimeline && lastExamPacketTimeline.timeline_summary)
      ? ((lastExamPacketTimeline.timeline_summary.skill_tags || [])[0] || task.value)
      : task.value,
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastReviewChainIntegrityCheck = report;
  result.value = renderReviewChainIntegrityCheck(report, "Review Chain Integrity: Exam Packet -> Timeline -> Export Review -> Receipt Journal metadata-only geprueft.");
});

document.querySelector("#pythonExamReadinessConsole").addEventListener("click", async () => {
  let drilldown = lastExamSkillDrilldown;
  if (!drilldown) {
    drilldown = await callUniBot("/api/unibot/course/exam-skill-drilldown", {
      review_policy: "staged",
      decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
      receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
      private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
      manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
      tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
      tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
      focus_query: task.value,
      selected_skill_tag: task.value,
      public_safe: true
    });
    if (!drilldown) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastExamSkillDrilldown = drilldown;
  }
  let dashboard = lastCourseExamCoverageDashboard;
  if (!dashboard) {
    dashboard = await callUniBot("/api/unibot/course/exam-coverage-dashboard", {
      review_policy: "staged",
      decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
      receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
      private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
      manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
      tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
      tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
      focus_query: task.value,
      selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
      console_reports: examSessionConsoleReports,
      console_receipts: lastExamSessionConsoleReceipt ? [lastExamSessionConsoleReceipt] : [],
      build_current_console: false,
      public_safe: true
    });
    if (!dashboard) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastCourseExamCoverageDashboard = dashboard;
  }
  let journalSummary = lastTimelineExportReceiptJournalSummary;
  if (!journalSummary) {
    journalSummary = await callUniBot("/api/unibot/course/timeline-export-receipt-journal/summary", {
      timeline_export_receipt_journal_path: "~/.unibot_guardian/timeline_export_receipts.jsonl"
    });
    if (!journalSummary) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastTimelineExportReceiptJournalSummary = journalSummary;
  }
  let chain = lastReviewChainIntegrityCheck;
  if (!chain) {
    chain = await callUniBot("/api/unibot/course/review-chain-integrity-check", {
      exam_run_packet: lastExamRunPacket,
      exam_packet_timeline: lastExamPacketTimeline,
      timeline_export_review_packet: lastTimelineExportReviewPacket,
      timeline_export_receipt_journal_append: lastTimelineExportReceiptJournalAppend,
      timeline_export_receipt_journal_summary: journalSummary,
      timeline_export_receipt_journal_path: "~/.unibot_guardian/timeline_export_receipts.jsonl",
      selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
      public_safe: true
    });
    if (!chain) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastReviewChainIntegrityCheck = chain;
  }
  const consoleReport = await callUniBot("/api/unibot/course/python-exam-readiness-console", {
    course_exam_coverage_dashboard: dashboard,
    exam_skill_drilldown: drilldown,
    review_chain_integrity_check: chain,
    timeline_export_receipt_journal_summary: journalSummary,
    selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
    public_safe: true
  });
  if (!consoleReport) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamReadinessConsole = consoleReport;
  result.value = renderPythonExamReadinessConsole(consoleReport, "Python Exam Readiness Console: Coverage, Drilldown, Review Chain und Receipt Journal als pruefungsnahe Skill-Konsole.");
});

document.querySelector("#pythonExamCockpitFlow").addEventListener("click", async () => {
  let drilldown = lastExamSkillDrilldown;
  if (!drilldown) {
    drilldown = await callUniBot("/api/unibot/course/exam-skill-drilldown", {
      review_policy: "staged",
      decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
      receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
      private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
      manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
      tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
      tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
      focus_query: task.value,
      selected_skill_tag: task.value,
      public_safe: true
    });
    if (!drilldown) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastExamSkillDrilldown = drilldown;
  }
  let operatorReport = lastExamWorkspaceOperatorRun;
  if (!operatorReport && (drilldown.skill_to_workspace_live_flow || {}).status === "ready_to_execute_operator_dry_run") {
    operatorReport = await callUniBot("/api/unibot/exam-workspace/operator-run", skillWorkspaceOperatorPayload(drilldown));
    if (operatorReport) lastExamWorkspaceOperatorRun = operatorReport;
  }
  let sessionReport = examSessionConsoleReports[examSessionConsoleReports.length - 1] || null;
  if (!sessionReport && (drilldown.skill_to_workspace_live_flow || {}).status === "ready_to_execute_operator_dry_run") {
    sessionReport = await callUniBot("/api/unibot/exam-workspace/session-console", skillWorkspaceSessionConsolePayload(drilldown));
    if (sessionReport) {
      lastExamSessionConsoleReceipt = sessionReport.session_console_receipt || null;
      examSessionConsoleReports = [...examSessionConsoleReports, sessionReport].slice(-12);
    }
  }
  let readiness = lastPythonExamReadinessConsole;
  if (!readiness) {
    readiness = await callUniBot("/api/unibot/course/python-exam-readiness-console", {
      course_exam_coverage_dashboard: lastCourseExamCoverageDashboard,
      exam_skill_drilldown: drilldown,
      review_chain_integrity_check: lastReviewChainIntegrityCheck,
      timeline_export_receipt_journal_summary: lastTimelineExportReceiptJournalSummary,
      selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
      public_safe: true
    });
    if (readiness) lastPythonExamReadinessConsole = readiness;
  }
  const cockpit = await callUniBot("/api/unibot/course/python-exam-cockpit-flow", {
    python_exam_readiness_console: readiness,
    exam_skill_drilldown: drilldown,
    exam_workspace_operator_run: operatorReport,
    exam_workspace_session_console: sessionReport,
    notebook_checkpoint: lastNotebookCheckpointAdapter,
    review_chain_integrity_check: lastReviewChainIntegrityCheck,
    timeline_export_review_packet: lastTimelineExportReviewPacket,
    timeline_export_receipt_journal_summary: lastTimelineExportReceiptJournalSummary,
    selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
    public_safe: true
  });
  if (!cockpit) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamCockpitFlow = cockpit;
  result.value = renderPythonExamCockpitFlow(cockpit, "Python Exam Cockpit Flow: gefuehrte Schrittleiste von Readiness bis Review-/Receipt-Evidence.");
});

document.querySelector("#pythonExamLiveControlSurface").addEventListener("click", async () => {
  let drilldown = lastExamSkillDrilldown;
  if (!drilldown) {
    drilldown = await callUniBot("/api/unibot/course/exam-skill-drilldown", {
      review_policy: "staged",
      decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
      receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
      private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
      manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
      tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
      tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
      focus_query: task.value,
      selected_skill_tag: task.value,
      public_safe: true
    });
    if (!drilldown) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastExamSkillDrilldown = drilldown;
  }
  let readiness = lastPythonExamReadinessConsole;
  if (!readiness) {
    readiness = await callUniBot("/api/unibot/course/python-exam-readiness-console", {
      course_exam_coverage_dashboard: lastCourseExamCoverageDashboard,
      exam_skill_drilldown: drilldown,
      review_chain_integrity_check: lastReviewChainIntegrityCheck,
      timeline_export_receipt_journal_summary: lastTimelineExportReceiptJournalSummary,
      selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
      public_safe: true
    });
    if (readiness) lastPythonExamReadinessConsole = readiness;
  }
  let cockpit = lastPythonExamCockpitFlow;
  if (!cockpit) {
    cockpit = await callUniBot("/api/unibot/course/python-exam-cockpit-flow", {
      python_exam_readiness_console: readiness,
      exam_skill_drilldown: drilldown,
      exam_workspace_operator_run: lastExamWorkspaceOperatorRun,
      exam_workspace_session_console: examSessionConsoleReports[examSessionConsoleReports.length - 1] || null,
      notebook_checkpoint: lastNotebookCheckpointAdapter,
      review_chain_integrity_check: lastReviewChainIntegrityCheck,
      timeline_export_review_packet: lastTimelineExportReviewPacket,
      timeline_export_receipt_journal_summary: lastTimelineExportReceiptJournalSummary,
      selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
      public_safe: true
    });
    if (cockpit) lastPythonExamCockpitFlow = cockpit;
  }
  const surface = await callUniBot("/api/unibot/course/python-exam-live-control-surface", {
    selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
    python_exam_cockpit_flow: cockpit,
    python_exam_readiness_console: readiness,
    exam_skill_drilldown: drilldown,
    python_exam_local_cycle_operator_workspace_card: lastPythonExamLocalCycleWorkspaceCard,
    exam_workspace_operator_run: lastExamWorkspaceOperatorRun,
    exam_workspace_session_console: examSessionConsoleReports[examSessionConsoleReports.length - 1] || null,
    notebook_checkpoint: lastNotebookCheckpointAdapter,
    review_chain_integrity_check: lastReviewChainIntegrityCheck,
    timeline_export_review_packet: lastTimelineExportReviewPacket,
    timeline_export_receipt_journal_summary: lastTimelineExportReceiptJournalSummary,
    public_safe: true
  });
  if (!surface) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamLiveControlSurface = surface;
  result.value = renderPythonExamLiveControlSurface(surface, "Python Exam Live Control Surface: sidepanel-first sichere Aktionen, Statusampel, Evidence-Receipts und Operator-Confirmations.");
});

document.querySelector("#pythonExamEvidenceExportPreview").addEventListener("click", async () => {
  let drilldown = lastExamSkillDrilldown;
  if (!drilldown) {
    drilldown = await callUniBot("/api/unibot/course/exam-skill-drilldown", {
      review_policy: "staged",
      decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
      receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
      private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
      manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
      tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
      tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
      focus_query: task.value,
      selected_skill_tag: task.value,
      public_safe: true
    });
    if (!drilldown) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastExamSkillDrilldown = drilldown;
  }
  let readiness = lastPythonExamReadinessConsole;
  if (!readiness) {
    readiness = await callUniBot("/api/unibot/course/python-exam-readiness-console", {
      course_exam_coverage_dashboard: lastCourseExamCoverageDashboard,
      exam_skill_drilldown: drilldown,
      review_chain_integrity_check: lastReviewChainIntegrityCheck,
      timeline_export_receipt_journal_summary: lastTimelineExportReceiptJournalSummary,
      selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
      public_safe: true
    });
    if (readiness) lastPythonExamReadinessConsole = readiness;
  }
  let cockpit = lastPythonExamCockpitFlow;
  if (!cockpit) {
    cockpit = await callUniBot("/api/unibot/course/python-exam-cockpit-flow", {
      python_exam_readiness_console: readiness,
      exam_skill_drilldown: drilldown,
      exam_workspace_operator_run: lastExamWorkspaceOperatorRun,
      exam_workspace_session_console: examSessionConsoleReports[examSessionConsoleReports.length - 1] || null,
      notebook_checkpoint: lastNotebookCheckpointAdapter,
      review_chain_integrity_check: lastReviewChainIntegrityCheck,
      timeline_export_review_packet: lastTimelineExportReviewPacket,
      timeline_export_receipt_journal_summary: lastTimelineExportReceiptJournalSummary,
      selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
      public_safe: true
    });
    if (cockpit) lastPythonExamCockpitFlow = cockpit;
  }
  let liveControl = lastPythonExamLiveControlSurface;
  if (!liveControl) {
    liveControl = await callUniBot("/api/unibot/course/python-exam-live-control-surface", {
      selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
      python_exam_cockpit_flow: cockpit,
      python_exam_readiness_console: readiness,
      exam_skill_drilldown: drilldown,
      exam_workspace_operator_run: lastExamWorkspaceOperatorRun,
      exam_workspace_session_console: examSessionConsoleReports[examSessionConsoleReports.length - 1] || null,
      notebook_checkpoint: lastNotebookCheckpointAdapter,
      review_chain_integrity_check: lastReviewChainIntegrityCheck,
      timeline_export_review_packet: lastTimelineExportReviewPacket,
      timeline_export_receipt_journal_summary: lastTimelineExportReceiptJournalSummary,
      public_safe: true
    });
    if (liveControl) lastPythonExamLiveControlSurface = liveControl;
  }
  const preview = await callUniBot("/api/unibot/course/python-exam-evidence-export-preview", {
    selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
    python_exam_live_control_surface: liveControl,
    python_exam_cockpit_flow: cockpit,
    python_exam_readiness_console: readiness,
    exam_skill_drilldown: drilldown,
    exam_workspace_operator_run: lastExamWorkspaceOperatorRun,
    exam_workspace_session_console: examSessionConsoleReports[examSessionConsoleReports.length - 1] || null,
    notebook_checkpoint: lastNotebookCheckpointAdapter,
    review_chain_integrity_check: lastReviewChainIntegrityCheck,
    timeline_export_review_packet: lastTimelineExportReviewPacket,
    timeline_export_receipt_journal_summary: lastTimelineExportReceiptJournalSummary,
    public_safe: true
  });
  if (!preview) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamEvidenceExportPreview = preview;
  result.value = renderPythonExamEvidenceExportPreview(preview, "Python Exam Evidence Export Preview: pruefbares Manifest fuer Human Review, Preview-only und not_cleared.");
});

document.querySelector("#pythonExamTutorDrillPack").addEventListener("click", async () => {
  let drilldown = lastExamSkillDrilldown;
  if (!drilldown) {
    drilldown = await callUniBot("/api/unibot/course/exam-skill-drilldown", {
      review_policy: "staged",
      decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
      receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
      private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
      manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
      tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
      tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
      focus_query: task.value,
      selected_skill_tag: task.value,
      public_safe: true
    });
    if (!drilldown) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastExamSkillDrilldown = drilldown;
  }
  let dashboard = lastCourseExamCoverageDashboard;
  if (!dashboard) {
    dashboard = await callUniBot("/api/unibot/course/exam-coverage-dashboard", {
      exam_skill_drilldown: drilldown,
      selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
      build_current_console: false,
      public_safe: true
    });
    if (!dashboard) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastCourseExamCoverageDashboard = dashboard;
  }
  let carryover = lastSkillToWorkspaceSessionCarryover;
  if (!carryover) {
    carryover = await callUniBot("/api/unibot/course/skill-to-workspace-session-carryover", skillWorkspaceSessionCarryoverPayload());
    if (!carryover) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    const artifacts = carryover.carryover_artifacts || {};
    lastSkillToWorkspaceSessionCarryover = carryover;
    if (artifacts.session_console) {
      lastExamSessionConsoleReceipt = artifacts.session_console.session_console_receipt || null;
      examSessionConsoleReports = [...examSessionConsoleReports, artifacts.session_console].slice(-12);
    }
    if (artifacts.python_exam_evidence_export_preview) {
      lastPythonExamEvidenceExportPreview = artifacts.python_exam_evidence_export_preview;
    }
    if (artifacts.python_exam_human_handoff_packet) {
      lastPythonExamHumanHandoffPacket = artifacts.python_exam_human_handoff_packet;
    }
  }
  const pack = await callUniBot("/api/unibot/course/python-exam-source-grounded-tutor-drill-pack", {
    selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
    course_exam_coverage_dashboard: dashboard,
    exam_skill_drilldown: drilldown,
    skill_to_workspace_session_carryover: carryover,
    public_safe: true
  });
  if (!pack) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamTutorDrillPack = pack;
  result.value = renderPythonExamTutorDrillPack(pack, "Python Exam Tutor Drill Pack: source-grounded A0-A2 Drills ohne Loesungen.");
});

document.querySelector("#pythonExamDrillSessionRunner").addEventListener("click", async () => {
  let pack = lastPythonExamTutorDrillPack;
  if (!pack) {
    let drilldown = lastExamSkillDrilldown;
    if (!drilldown) {
      drilldown = await callUniBot("/api/unibot/course/exam-skill-drilldown", {
        review_policy: "staged",
        decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
        receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
        private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
        manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
        tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
        tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
        focus_query: task.value,
        selected_skill_tag: task.value,
        public_safe: true
      });
      if (!drilldown) {
        result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
        return;
      }
      lastExamSkillDrilldown = drilldown;
    }
    let dashboard = lastCourseExamCoverageDashboard;
    if (!dashboard) {
      dashboard = await callUniBot("/api/unibot/course/exam-coverage-dashboard", {
        exam_skill_drilldown: drilldown,
        selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
        build_current_console: false,
        public_safe: true
      });
      if (!dashboard) {
        result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
        return;
      }
      lastCourseExamCoverageDashboard = dashboard;
    }
    let carryover = lastSkillToWorkspaceSessionCarryover;
    if (!carryover) {
      carryover = await callUniBot("/api/unibot/course/skill-to-workspace-session-carryover", skillWorkspaceSessionCarryoverPayload());
      if (!carryover) {
        result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
        return;
      }
      lastSkillToWorkspaceSessionCarryover = carryover;
    }
    pack = await callUniBot("/api/unibot/course/python-exam-source-grounded-tutor-drill-pack", {
      selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
      course_exam_coverage_dashboard: dashboard,
      exam_skill_drilldown: drilldown,
      skill_to_workspace_session_carryover: carryover,
      public_safe: true
    });
    if (!pack) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastPythonExamTutorDrillPack = pack;
  }
  const drill = (pack.skill_drills || [])[0] || {};
  const microtask = (drill.microtasks || [])[0] || {};
  const session = await callUniBot("/api/unibot/course/python-exam-drill-session-runner", {
    python_exam_tutor_drill_pack: pack,
    skill_to_workspace_session_carryover: lastSkillToWorkspaceSessionCarryover,
    selected_skill_tag: pack.selected_skill_tag || drill.skill_tag || task.value,
    selected_task_id: microtask.task_id || "",
    selected_task_hash: microtask.task_hash || "",
    cell_source: notebookCell.value,
    cell_index: 0,
    cell_type: "code",
    student_reflection: reflection.value,
    checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
    operator_confirmed_checkpoint_store: confirmCheckpointStore.checked,
    public_safe: true
  });
  if (!session) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamDrillSessionRunner = session;
  result.value = renderPythonExamDrillSessionRunner(session, "Python Exam Drill Session: Microtask in hash-only Notebook-Checkpoint und Help-Ledger-Preview ueberfuehrt.");
});

document.querySelector("#pythonExamDrillSessionReviewLoop").addEventListener("click", async () => {
  let session = lastPythonExamDrillSessionRunner;
  if (!session) {
    let pack = lastPythonExamTutorDrillPack;
    if (!pack) {
      result.value = "Bitte zuerst Python Exam Tutor Drill Pack oder Python Exam Drill Session erzeugen.";
      return;
    }
    const drill = (pack.skill_drills || [])[0] || {};
    const microtask = (drill.microtasks || [])[0] || {};
    session = await callUniBot("/api/unibot/course/python-exam-drill-session-runner", {
      python_exam_tutor_drill_pack: pack,
      skill_to_workspace_session_carryover: lastSkillToWorkspaceSessionCarryover,
      selected_skill_tag: pack.selected_skill_tag || drill.skill_tag || task.value,
      selected_task_id: microtask.task_id || "",
      selected_task_hash: microtask.task_hash || "",
      cell_source: notebookCell.value,
      cell_index: 0,
      cell_type: "code",
      student_reflection: reflection.value,
      checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
      operator_confirmed_checkpoint_store: confirmCheckpointStore.checked,
      public_safe: true
    });
    if (!session) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastPythonExamDrillSessionRunner = session;
  }
  const review = await callUniBot("/api/unibot/course/python-exam-drill-session-review-loop", {
    python_exam_drill_session_runner: session,
    python_exam_tutor_drill_pack: lastPythonExamTutorDrillPack,
    previous_review_loops: lastPythonExamDrillSessionReviewLoop ? [lastPythonExamDrillSessionReviewLoop] : [],
    selected_skill_tag: session.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!review) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamDrillSessionReviewLoop = review;
  result.value = renderPythonExamDrillSessionReviewLoop(review, "Python Exam Drill Review Loop: Next-Step ohne Score, Note, Ranking oder Loesung.");
});

document.querySelector("#pythonExamDrillLoopControlPanel").addEventListener("click", async () => {
  let pack = lastPythonExamTutorDrillPack;
  if (!pack) {
    let drilldown = lastExamSkillDrilldown;
    if (!drilldown) {
      drilldown = await callUniBot("/api/unibot/course/exam-skill-drilldown", {
        review_policy: "staged",
        decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
        receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
        private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
        manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
        tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
        tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
        focus_query: task.value,
        selected_skill_tag: task.value,
        public_safe: true
      });
      if (!drilldown) {
        result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
        return;
      }
      lastExamSkillDrilldown = drilldown;
    }
    let dashboard = lastCourseExamCoverageDashboard;
    if (!dashboard) {
      dashboard = await callUniBot("/api/unibot/course/exam-coverage-dashboard", {
        exam_skill_drilldown: drilldown,
        selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
        build_current_console: false,
        public_safe: true
      });
      if (!dashboard) {
        result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
        return;
      }
      lastCourseExamCoverageDashboard = dashboard;
    }
    let carryover = lastSkillToWorkspaceSessionCarryover;
    if (!carryover) {
      carryover = await callUniBot("/api/unibot/course/skill-to-workspace-session-carryover", skillWorkspaceSessionCarryoverPayload());
      if (!carryover) {
        result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
        return;
      }
      lastSkillToWorkspaceSessionCarryover = carryover;
    }
    pack = await callUniBot("/api/unibot/course/python-exam-source-grounded-tutor-drill-pack", {
      selected_skill_tag: (drilldown.selected_skill || {}).skill_tag || task.value,
      course_exam_coverage_dashboard: dashboard,
      exam_skill_drilldown: drilldown,
      skill_to_workspace_session_carryover: carryover,
      public_safe: true
    });
    if (!pack) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastPythonExamTutorDrillPack = pack;
  }
  const previousReview = lastPythonExamDrillSessionReviewLoop || null;
  const nextHash = ((previousReview || {}).next_step_recommendation || {}).next_task_hash || "";
  const panel = await callUniBot("/api/unibot/course/python-exam-drill-loop-control-panel", {
    python_exam_tutor_drill_pack: pack,
    skill_to_workspace_session_carryover: lastSkillToWorkspaceSessionCarryover,
    previous_review_loops: previousReview ? [previousReview] : [],
    selected_skill_tag: pack.selected_skill_tag || task.value,
    selected_task_hash: nextHash,
    cell_source: notebookCell.value,
    cell_index: 0,
    cell_type: "code",
    student_reflection: reflection.value,
    checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
    operator_confirmed_checkpoint_store: confirmCheckpointStore.checked,
    public_safe: true
  });
  if (!panel) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  const artifacts = panel.control_panel_artifacts || {};
  lastPythonExamDrillLoopControlPanel = panel;
  if (artifacts.drill_session_runner) lastPythonExamDrillSessionRunner = artifacts.drill_session_runner;
  if (artifacts.drill_session_review_loop) lastPythonExamDrillSessionReviewLoop = artifacts.drill_session_review_loop;
  result.value = renderPythonExamDrillLoopControlPanel(panel, "Python Exam Drill Control Panel: Pack, Session und Review als ein sicherer Arbeitszyklus.");
});

document.querySelector("#pythonExamDrillLoopProgressJournal").addEventListener("click", async () => {
  let panel = lastPythonExamDrillLoopControlPanel;
  if (!panel) {
    result.value = "Bitte zuerst Python Exam Drill Control Panel erzeugen.";
    return;
  }
  const journal = await callUniBot("/api/unibot/course/python-exam-drill-loop-progress-journal", {
    python_exam_drill_loop_control_panel: panel,
    progress_journal_path: "~/.unibot_guardian/python_exam_drill_loop_progress.jsonl",
    operator_confirmed_progress_journal_append: confirmDrillLoopProgressJournalAppend.checked,
    public_safe: true
  });
  if (!journal) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamDrillLoopProgressJournal = journal;
  result.value = renderPythonExamDrillLoopProgressJournal(journal, "Python Exam Drill Progress Journal: sicherer Resume-/Recovery-Record.");
});

document.querySelector("#pythonExamResumeLauncher").addEventListener("click", async () => {
  const journal = lastPythonExamDrillLoopProgressJournal;
  if (!journal) {
    result.value = "Bitte zuerst Python Exam Drill Progress Journal erzeugen.";
    return;
  }
  const launcher = await callUniBot("/api/unibot/course/python-exam-resume-launcher", {
    python_exam_drill_loop_progress_journal: journal,
    progress_journal_path: "~/.unibot_guardian/python_exam_drill_loop_progress.jsonl",
    selected_skill_tag: ((journal.journal_entry_preview || {}).skill_tag) || task.value,
    public_safe: true
  });
  if (!launcher) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamResumeLauncher = launcher;
  result.value = renderPythonExamResumeLauncher(launcher, "Python Exam Resume Launcher: naechsten sicheren Drill-Start vorausgefuellt.");
});

document.querySelector("#pythonExamActiveStudyLoopDashboard").addEventListener("click", async () => {
  const dashboard = await callUniBot("/api/unibot/course/python-exam-active-study-loop-dashboard", {
    course_exam_coverage_dashboard: lastCourseExamCoverageDashboard,
    python_exam_tutor_drill_pack: lastPythonExamTutorDrillPack,
    python_exam_drill_loop_control_panel: lastPythonExamDrillLoopControlPanel,
    python_exam_drill_loop_progress_journal: lastPythonExamDrillLoopProgressJournal,
    python_exam_resume_launcher: lastPythonExamResumeLauncher,
    selected_skill_tag: ((lastPythonExamResumeLauncher || {}).resume_decision || {}).selected_skill_tag || task.value,
    public_safe: true
  });
  if (!dashboard) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamActiveStudyLoopDashboard = dashboard;
  result.value = renderPythonExamActiveStudyLoopDashboard(dashboard, "Python Exam Active Study Loop: Coverage, Drills, Resume und Progress als sichere Skill-Uebersicht.");
});

document.querySelector("#pythonExamActiveStudyGuidedRunner").addEventListener("click", async () => {
  const dashboard = lastPythonExamActiveStudyLoopDashboard;
  if (!dashboard) {
    result.value = "Bitte zuerst Python Exam Active Study Loop erzeugen.";
    return;
  }
  const guided = await callUniBot("/api/unibot/course/python-exam-active-study-guided-runner", {
    python_exam_active_study_loop_dashboard: dashboard,
    python_exam_resume_launcher: lastPythonExamResumeLauncher,
    python_exam_drill_loop_control_panel: lastPythonExamDrillLoopControlPanel,
    selected_skill_tag: ((dashboard.active_study_summary || {}).selected_skill_tag) || task.value,
    requested_action: ((dashboard.active_study_summary || {}).next_safe_action) || "",
    public_safe: true
  });
  if (!guided) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamActiveStudyGuidedRunner = guided;
  result.value = renderPythonExamActiveStudyGuidedRunner(guided, "Python Exam Guided Runner: naechste sichere Action Card aus dem Active Study Loop.");
});

document.querySelector("#pythonExamGuidedActionExecutionBridge").addEventListener("click", async () => {
  const guided = lastPythonExamActiveStudyGuidedRunner;
  if (!guided) {
    result.value = "Bitte zuerst Python Exam Guided Runner erzeugen.";
    return;
  }
  const bridge = await callUniBot("/api/unibot/course/python-exam-guided-action-execution-bridge", {
    python_exam_active_study_guided_runner: guided,
    python_exam_drill_loop_control_panel: lastPythonExamDrillLoopControlPanel,
    python_exam_drill_loop_progress_journal: lastPythonExamDrillLoopProgressJournal,
    selected_skill_tag: ((guided.guided_runner_summary || {}).selected_skill_tag) || task.value,
    public_safe: true
  });
  if (!bridge) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamGuidedActionExecutionBridge = bridge;
  result.value = renderPythonExamGuidedActionExecutionBridge(bridge, "Python Exam Execution Bridge: Action Card als naechster sicherer Arbeitszyklus.");
});

document.querySelector("#pythonExamSafeCycleConsole").addEventListener("click", async () => {
  const bridge = lastPythonExamGuidedActionExecutionBridge;
  if (!bridge) {
    result.value = "Bitte zuerst Python Exam Execution Bridge erzeugen.";
    return;
  }
  const consoleReport = await callUniBot("/api/unibot/course/python-exam-safe-cycle-console", {
    python_exam_active_study_loop_dashboard: lastPythonExamActiveStudyLoopDashboard,
    python_exam_active_study_guided_runner: lastPythonExamActiveStudyGuidedRunner,
    python_exam_guided_action_execution_bridge: bridge,
    python_exam_drill_loop_control_panel: lastPythonExamDrillLoopControlPanel,
    python_exam_drill_loop_progress_journal: lastPythonExamDrillLoopProgressJournal,
    selected_skill_tag: ((bridge.execution_bridge_summary || {}).selected_skill_tag) || task.value,
    public_safe: true
  });
  if (!consoleReport) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamSafeCycleConsole = consoleReport;
  result.value = renderPythonExamSafeCycleConsole(consoleReport, "Python Exam Safe Cycle Console: aktueller sicherer Arbeitszyklus.");
});

document.querySelector("#pythonExamSafeCycleOperatorGate").addEventListener("click", async () => {
  const consoleReport = lastPythonExamSafeCycleConsole;
  if (!consoleReport) {
    result.value = "Bitte zuerst Python Exam Safe Cycle Console erzeugen.";
    return;
  }
  const gate = await callUniBot("/api/unibot/course/python-exam-safe-cycle-operator-gate", {
    python_exam_safe_cycle_console: consoleReport,
    selected_skill_tag: ((consoleReport.safe_cycle_summary || {}).selected_skill_tag) || task.value,
    public_safe: true
  });
  if (!gate) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamSafeCycleOperatorGate = gate;
  result.value = renderPythonExamSafeCycleOperatorGate(gate, "Python Exam Operator Gate: menschliche Bestaetigungskarten vor dem Arbeitszyklus.");
});

document.querySelector("#pythonExamOperatorGateDecisionReceipt").addEventListener("click", async () => {
  const gate = lastPythonExamSafeCycleOperatorGate;
  if (!gate) {
    result.value = "Bitte zuerst Python Exam Operator Gate erzeugen.";
    return;
  }
  const receipt = await callUniBot("/api/unibot/course/python-exam-operator-gate-decision-receipt", {
    python_exam_safe_cycle_operator_gate: gate,
    confirmed_step_ids: [],
    selected_skill_tag: ((gate.operator_gate_summary || {}).selected_skill_tag) || task.value,
    public_safe: true
  });
  if (!receipt) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamOperatorGateDecisionReceipt = receipt;
  result.value = renderPythonExamOperatorGateDecisionReceipt(receipt, "Python Exam Gate Decision Receipt: offener Bestaetigungsstand ohne Ausfuehrung.");
});

document.querySelector("#pythonExamLocalCycleStartPacket").addEventListener("click", async () => {
  const receipt = lastPythonExamOperatorGateDecisionReceipt;
  if (!receipt) {
    result.value = "Bitte zuerst Python Exam Gate Decision Receipt erzeugen.";
    return;
  }
  const packet = await callUniBot("/api/unibot/course/python-exam-local-cycle-start-packet", {
    python_exam_safe_cycle_console: lastPythonExamSafeCycleConsole,
    python_exam_safe_cycle_operator_gate: lastPythonExamSafeCycleOperatorGate,
    python_exam_operator_gate_decision_receipt: receipt,
    selected_skill_tag: ((receipt.decision_receipt_summary || {}).selected_skill_tag) || task.value,
    public_safe: true
  });
  if (!packet) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamLocalCycleStartPacket = packet;
  result.value = renderPythonExamLocalCycleStartPacket(packet, "Python Exam Local Cycle Start Packet: finaler Startstatus ohne Ausfuehrung.");
});

document.querySelector("#pythonExamLocalCycleReadinessReview").addEventListener("click", async () => {
  const packet = lastPythonExamLocalCycleStartPacket;
  if (!packet) {
    result.value = "Bitte zuerst Python Exam Local Cycle Start Packet erzeugen.";
    return;
  }
  const review = await callUniBot("/api/unibot/course/python-exam-local-cycle-readiness-review", {
    python_exam_local_cycle_start_packet: packet,
    selected_skill_tag:
      ((packet.local_cycle_start_packet || {}).selected_skill_tag) || packet.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!review) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamLocalCycleReadinessReview = review;
  result.value = renderPythonExamLocalCycleReadinessReview(review, "Python Exam Local Cycle Readiness Review: nur Empfehlung, keine Ausfuehrung.");
});

document.querySelector("#pythonExamLocalCycleReadinessHandoff").addEventListener("click", async () => {
  const review = lastPythonExamLocalCycleReadinessReview;
  const packet = lastPythonExamLocalCycleStartPacket;
  if (!review || !packet) {
    result.value = "Bitte zuerst Python Exam Local Cycle Start Packet und Readiness Review erzeugen.";
    return;
  }
  const handoff = await callUniBot("/api/unibot/course/python-exam-local-cycle-readiness-handoff", {
    python_exam_local_cycle_readiness_review: review,
    python_exam_local_cycle_start_packet: packet,
    selected_skill_tag: ((review.readiness_review_summary || {}).selected_skill_tag) || packet.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!handoff) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamLocalCycleReadinessHandoff = handoff;
  result.value = renderPythonExamLocalCycleReadinessHandoff(handoff, "Python Exam Local Cycle Handoff: Operator-Run-Prefill und manueller Handoff ohne Ausfuehrung.");
});

document.querySelector("#pythonExamLocalCycleWorkspaceCard").addEventListener("click", async () => {
  const review = lastPythonExamLocalCycleReadinessReview;
  const handoff = lastPythonExamLocalCycleReadinessHandoff;
  const packet = lastPythonExamLocalCycleStartPacket;
  if (!review || !handoff || !packet) {
    result.value = "Bitte zuerst Python Exam Local Cycle Start Packet, Readiness Review und Handoff erzeugen.";
    return;
  }
  const workspaceCard = await callUniBot("/api/unibot/course/python-exam-local-cycle-operator-workspace-card", {
    python_exam_local_cycle_readiness_review: review,
    python_exam_local_cycle_readiness_handoff: handoff,
    python_exam_local_cycle_start_packet: packet,
    selected_skill_tag: ((handoff.readiness_review_status ? handoff.selected_skill_tag : "") || ((review.readiness_review_summary || {}).selected_skill_tag) || packet.selected_skill_tag || task.value),
    public_safe: true
  });
  if (!workspaceCard) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamLocalCycleWorkspaceCard = workspaceCard;
  result.value = renderPythonExamLocalCycleOperatorWorkspaceCard(workspaceCard, "Python Exam Local Cycle Workspace: Readiness Review, Handoff und Help-Ledger-Preview kompakt.");
});

document.querySelector("#pythonExamLocalCycleChainSnapshot").addEventListener("click", async () => {
  const review = lastPythonExamLocalCycleReadinessReview;
  const handoff = lastPythonExamLocalCycleReadinessHandoff;
  const workspaceCard = lastPythonExamLocalCycleWorkspaceCard;
  if (!review || !handoff || !workspaceCard) {
    result.value = "Bitte zuerst Python Exam Local Cycle Readiness Review, Handoff und Workspace erzeugen.";
    return;
  }
  const snapshot = await callUniBot("/api/unibot/course/python-exam-local-cycle-chain-snapshot", {
    python_exam_local_cycle_readiness_review: review,
    python_exam_local_cycle_readiness_handoff: handoff,
    python_exam_local_cycle_operator_workspace_card: workspaceCard,
    selected_skill_tag: ((workspaceCard.workspace_card_summary || {}).selected_skill_tag) || workspaceCard.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!snapshot) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamLocalCycleChainSnapshot = snapshot;
  result.value = renderPythonExamLocalCycleChainSnapshot(snapshot, "Python Exam Local Cycle Chain Snapshot: hash-only Evidence Chain vor manueller Confirmation.");
});

document.querySelector("#pythonExamManualConfirmationConsole").addEventListener("click", async () => {
  const review = lastPythonExamLocalCycleReadinessReview;
  const handoff = lastPythonExamLocalCycleReadinessHandoff;
  const workspaceCard = lastPythonExamLocalCycleWorkspaceCard;
  if (!review || !handoff || !workspaceCard) {
    result.value = "Bitte zuerst Python Exam Local Cycle Readiness Review, Handoff und Workspace erzeugen.";
    return;
  }
  let snapshot = lastPythonExamLocalCycleChainSnapshot;
  if (!snapshot) {
    snapshot = await callUniBot("/api/unibot/course/python-exam-local-cycle-chain-snapshot", {
      python_exam_local_cycle_readiness_review: review,
      python_exam_local_cycle_readiness_handoff: handoff,
      python_exam_local_cycle_operator_workspace_card: workspaceCard,
      selected_skill_tag: ((workspaceCard.workspace_card_summary || {}).selected_skill_tag) || workspaceCard.selected_skill_tag || task.value,
      public_safe: true
    });
    if (!snapshot) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastPythonExamLocalCycleChainSnapshot = snapshot;
  }
  const consoleReport = await callUniBot("/api/unibot/course/python-exam-local-cycle-manual-confirmation-console", {
    python_exam_local_cycle_readiness_review: review,
    python_exam_local_cycle_readiness_handoff: handoff,
    python_exam_local_cycle_operator_workspace_card: workspaceCard,
    python_exam_local_cycle_chain_snapshot: snapshot,
    selected_skill_tag: ((snapshot.chain_snapshot_summary || {}).selected_skill_tag) || snapshot.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!consoleReport) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamManualConfirmationConsole = consoleReport;
  result.value = renderPythonExamManualConfirmationConsole(consoleReport, "Python Exam Manual Confirmation Console: offene und bestaetigte Hash-Confirmations nebeneinander.");
});

document.querySelector("#pythonExamManualCycleLaunchReceipt").addEventListener("click", async () => {
  const review = lastPythonExamLocalCycleReadinessReview;
  const handoff = lastPythonExamLocalCycleReadinessHandoff;
  const workspaceCard = lastPythonExamLocalCycleWorkspaceCard;
  if (!review || !handoff || !workspaceCard) {
    result.value = "Bitte zuerst Python Exam Local Cycle Readiness Review, Handoff und Workspace erzeugen.";
    return;
  }
  let snapshot = lastPythonExamLocalCycleChainSnapshot;
  if (!snapshot) {
    snapshot = await callUniBot("/api/unibot/course/python-exam-local-cycle-chain-snapshot", {
      python_exam_local_cycle_readiness_review: review,
      python_exam_local_cycle_readiness_handoff: handoff,
      python_exam_local_cycle_operator_workspace_card: workspaceCard,
      selected_skill_tag: ((workspaceCard.workspace_card_summary || {}).selected_skill_tag) || workspaceCard.selected_skill_tag || task.value,
      public_safe: true
    });
    if (!snapshot) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastPythonExamLocalCycleChainSnapshot = snapshot;
  }
  let consoleReport = lastPythonExamManualConfirmationConsole;
  if (!consoleReport) {
    consoleReport = await callUniBot("/api/unibot/course/python-exam-local-cycle-manual-confirmation-console", {
      python_exam_local_cycle_readiness_review: review,
      python_exam_local_cycle_readiness_handoff: handoff,
      python_exam_local_cycle_operator_workspace_card: workspaceCard,
      python_exam_local_cycle_chain_snapshot: snapshot,
      selected_skill_tag: ((snapshot.chain_snapshot_summary || {}).selected_skill_tag) || snapshot.selected_skill_tag || task.value,
      public_safe: true
    });
    if (!consoleReport) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastPythonExamManualConfirmationConsole = consoleReport;
  }
  const receipt = await callUniBot("/api/unibot/course/python-exam-manual-cycle-launch-receipt", {
    python_exam_manual_confirmation_console: consoleReport,
    python_exam_local_cycle_chain_snapshot: snapshot,
    python_exam_local_cycle_operator_workspace_card: workspaceCard,
    python_exam_local_cycle_readiness_handoff: handoff,
    selected_skill_tag: ((consoleReport.console_summary || {}).selected_skill_tag) || consoleReport.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!receipt) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamManualCycleLaunchReceipt = receipt;
  result.value = renderPythonExamManualCycleLaunchReceipt(receipt, "Python Exam Manual Cycle Launch Receipt: letzte hash-only Launch-Quittung ohne Ausfuehrung.");
});

document.querySelector("#pythonExamManualCycleEvidenceBinder").addEventListener("click", async () => {
  const review = lastPythonExamLocalCycleReadinessReview;
  const workspaceCard = lastPythonExamLocalCycleWorkspaceCard;
  const snapshot = lastPythonExamLocalCycleChainSnapshot;
  const consoleReport = lastPythonExamManualConfirmationConsole;
  let launchReceipt = lastPythonExamManualCycleLaunchReceipt;
  if (!review || !workspaceCard || !snapshot || !consoleReport) {
    result.value = "Bitte zuerst Local Cycle Readiness Review, Workspace, Chain Snapshot und Manual Confirmation Console erzeugen.";
    return;
  }
  if (!launchReceipt) {
    launchReceipt = await callUniBot("/api/unibot/course/python-exam-manual-cycle-launch-receipt", {
      python_exam_manual_confirmation_console: consoleReport,
      python_exam_local_cycle_chain_snapshot: snapshot,
      python_exam_local_cycle_operator_workspace_card: workspaceCard,
      python_exam_local_cycle_readiness_handoff: lastPythonExamLocalCycleReadinessHandoff,
      selected_skill_tag: ((consoleReport.console_summary || {}).selected_skill_tag) || consoleReport.selected_skill_tag || task.value,
      public_safe: true
    });
    if (!launchReceipt) {
      result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
      return;
    }
    lastPythonExamManualCycleLaunchReceipt = launchReceipt;
  }
  const binder = await callUniBot("/api/unibot/course/python-exam-manual-cycle-evidence-binder", {
    python_exam_manual_cycle_launch_receipt: launchReceipt,
    python_exam_manual_confirmation_console: consoleReport,
    python_exam_local_cycle_chain_snapshot: snapshot,
    python_exam_local_cycle_operator_workspace_card: workspaceCard,
    python_exam_local_cycle_readiness_review: review,
    selected_skill_tag: ((launchReceipt.launch_receipt_summary || {}).selected_skill_tag) || launchReceipt.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!binder) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamManualCycleEvidenceBinder = binder;
  result.value = renderPythonExamManualCycleEvidenceBinder(binder, "Python Exam Manual Cycle Evidence Binder: hash-only Stop-Go-Kette vor/nach manueller lokaler Review.");
});

document.querySelector("#pythonExamManualPostCycleReceiptIntake").addEventListener("click", async () => {
  const binder = lastPythonExamManualCycleEvidenceBinder;
  const launchReceipt = lastPythonExamManualCycleLaunchReceipt;
  const consoleReport = lastPythonExamManualConfirmationConsole;
  if (!binder || !launchReceipt || !consoleReport) {
    result.value = "Bitte zuerst Manual Cycle Evidence Binder, Launch Receipt und Manual Confirmation Console erzeugen.";
    return;
  }
  const intake = await callUniBot("/api/unibot/course/python-exam-manual-post-cycle-receipt-intake", {
    python_exam_manual_cycle_evidence_binder: binder,
    python_exam_manual_cycle_launch_receipt: launchReceipt,
    python_exam_manual_confirmation_console: consoleReport,
    selected_skill_tag: ((binder.binder_summary || {}).selected_skill_tag) || binder.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!intake) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamManualPostCycleReceiptIntake = intake;
  result.value = renderPythonExamManualPostCycleReceiptIntake(intake, "Python Exam Manual Post-Cycle Receipt Intake: hash-only Nachweisaufnahme nach menschlicher lokaler Aktion.");
});

document.querySelector("#pythonExamManualCycleClosureLedger").addEventListener("click", async () => {
  const intake = lastPythonExamManualPostCycleReceiptIntake;
  const binder = lastPythonExamManualCycleEvidenceBinder;
  const launchReceipt = lastPythonExamManualCycleLaunchReceipt;
  const consoleReport = lastPythonExamManualConfirmationConsole;
  if (!intake || !binder || !launchReceipt || !consoleReport) {
    result.value = "Bitte zuerst Post-Cycle Receipt Intake, Evidence Binder, Launch Receipt und Manual Confirmation Console erzeugen.";
    return;
  }
  const ledger = await callUniBot("/api/unibot/course/python-exam-manual-cycle-closure-ledger", {
    python_exam_manual_post_cycle_receipt_intake: intake,
    python_exam_manual_cycle_evidence_binder: binder,
    python_exam_manual_cycle_launch_receipt: launchReceipt,
    python_exam_manual_confirmation_console: consoleReport,
    selected_skill_tag: ((intake.post_cycle_intake_summary || {}).selected_skill_tag) || intake.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!ledger) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamManualCycleClosureLedger = ledger;
  result.value = renderPythonExamManualCycleClosureLedger(ledger, "Python Exam Manual Cycle Closure Ledger: hash-only Zyklusabschluss fuer menschliche Review.");
});

document.querySelector("#pythonExamManualCycleReviewTimeline").addEventListener("click", async () => {
  const ledger = lastPythonExamManualCycleClosureLedger;
  const intake = lastPythonExamManualPostCycleReceiptIntake;
  const binder = lastPythonExamManualCycleEvidenceBinder;
  const launchReceipt = lastPythonExamManualCycleLaunchReceipt;
  const consoleReport = lastPythonExamManualConfirmationConsole;
  if (!ledger || !intake || !binder || !launchReceipt || !consoleReport) {
    result.value = "Bitte zuerst Closure Ledger, Post-Cycle Intake, Evidence Binder, Launch Receipt und Manual Confirmation Console erzeugen.";
    return;
  }
  const timeline = await callUniBot("/api/unibot/course/python-exam-manual-cycle-review-timeline", {
    python_exam_manual_cycle_closure_ledger: ledger,
    python_exam_manual_post_cycle_receipt_intake: intake,
    python_exam_manual_cycle_evidence_binder: binder,
    python_exam_manual_cycle_launch_receipt: launchReceipt,
    python_exam_manual_confirmation_console: consoleReport,
    selected_skill_tag: ((ledger.closure_summary || {}).selected_skill_tag) || ledger.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!timeline) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamManualCycleReviewTimeline = timeline;
  result.value = renderPythonExamManualCycleReviewTimeline(timeline, "Python Exam Manual Cycle Review Timeline: chronologische hash-only Review-Kette.");
});

document.querySelector("#pythonExamManualCycleReviewPacket").addEventListener("click", async () => {
  const timeline = lastPythonExamManualCycleReviewTimeline;
  const ledger = lastPythonExamManualCycleClosureLedger;
  const intake = lastPythonExamManualPostCycleReceiptIntake;
  const binder = lastPythonExamManualCycleEvidenceBinder;
  const launchReceipt = lastPythonExamManualCycleLaunchReceipt;
  const consoleReport = lastPythonExamManualConfirmationConsole;
  if (!timeline || !ledger || !intake || !binder || !launchReceipt || !consoleReport) {
    result.value = "Bitte zuerst Review Timeline, Closure Ledger, Post-Cycle Intake, Evidence Binder, Launch Receipt und Manual Confirmation Console erzeugen.";
    return;
  }
  const packet = await callUniBot("/api/unibot/course/python-exam-manual-cycle-review-packet", {
    python_exam_manual_cycle_review_timeline: timeline,
    python_exam_manual_cycle_closure_ledger: ledger,
    python_exam_manual_post_cycle_receipt_intake: intake,
    python_exam_manual_cycle_evidence_binder: binder,
    python_exam_manual_cycle_launch_receipt: launchReceipt,
    python_exam_manual_confirmation_console: consoleReport,
    selected_skill_tag: ((timeline.timeline_summary || {}).selected_skill_tag) || timeline.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!packet) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamManualCycleReviewPacket = packet;
  result.value = renderPythonExamManualCycleReviewPacket(packet, "Python Exam Manual Cycle Review Packet: kompaktes hash-only Pruefpaket.");
});

document.querySelector("#pythonExamManualReviewExportPreview").addEventListener("click", async () => {
  const packet = lastPythonExamManualCycleReviewPacket;
  const timeline = lastPythonExamManualCycleReviewTimeline;
  const ledger = lastPythonExamManualCycleClosureLedger;
  const intake = lastPythonExamManualPostCycleReceiptIntake;
  const binder = lastPythonExamManualCycleEvidenceBinder;
  const launchReceipt = lastPythonExamManualCycleLaunchReceipt;
  const consoleReport = lastPythonExamManualConfirmationConsole;
  if (!packet || !timeline || !ledger || !intake || !binder || !launchReceipt || !consoleReport) {
    result.value = "Bitte zuerst Review Packet, Review Timeline, Closure Ledger, Post-Cycle Intake, Evidence Binder, Launch Receipt und Manual Confirmation Console erzeugen.";
    return;
  }
  const preview = await callUniBot("/api/unibot/course/python-exam-manual-review-export-preview", {
    python_exam_manual_cycle_review_packet: packet,
    python_exam_manual_cycle_review_timeline: timeline,
    python_exam_manual_cycle_closure_ledger: ledger,
    python_exam_manual_post_cycle_receipt_intake: intake,
    python_exam_manual_cycle_evidence_binder: binder,
    python_exam_manual_cycle_launch_receipt: launchReceipt,
    python_exam_manual_confirmation_console: consoleReport,
    selected_skill_tag: ((packet.review_packet_summary || {}).selected_skill_tag) || packet.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!preview) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamManualReviewExportPreview = preview;
  result.value = renderPythonExamManualReviewExportPreview(preview, "Python Exam Manual Review Export Preview: hash-only Exportvorschau ohne Export.");
});

document.querySelector("#pythonExamManualReviewExportAuthorizationGate").addEventListener("click", async () => {
  const preview = lastPythonExamManualReviewExportPreview;
  const packet = lastPythonExamManualCycleReviewPacket;
  const timeline = lastPythonExamManualCycleReviewTimeline;
  const ledger = lastPythonExamManualCycleClosureLedger;
  if (!preview || !packet || !timeline || !ledger) {
    result.value = "Bitte zuerst Manual Review Export Preview, Review Packet, Review Timeline und Closure Ledger erzeugen.";
    return;
  }
  const gate = await callUniBot("/api/unibot/course/python-exam-manual-review-export-authorization-gate", {
    python_exam_manual_review_export_preview: preview,
    python_exam_manual_cycle_review_packet: packet,
    python_exam_manual_cycle_review_timeline: timeline,
    python_exam_manual_cycle_closure_ledger: ledger,
    selected_skill_tag: ((preview.export_preview_summary || {}).selected_skill_tag) || preview.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!gate) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamManualReviewExportAuthorizationGate = gate;
  result.value = renderPythonExamManualReviewExportAuthorizationGate(gate, "Python Exam Export Authorization Gate: hash-only Gate vor menschlicher Export-Autorisierung.");
});

document.querySelector("#pythonExamManualExportReviewQueue").addEventListener("click", async () => {
  const gate = lastPythonExamManualReviewExportAuthorizationGate;
  const preview = lastPythonExamManualReviewExportPreview;
  const packet = lastPythonExamManualCycleReviewPacket;
  const timeline = lastPythonExamManualCycleReviewTimeline;
  if (!gate || !preview || !packet || !timeline) {
    result.value = "Bitte zuerst Export Authorization Gate, Export Preview, Review Packet und Review Timeline erzeugen.";
    return;
  }
  const queue = await callUniBot("/api/unibot/course/python-exam-manual-export-review-queue", {
    python_exam_manual_review_export_authorization_gate: gate,
    python_exam_manual_review_export_preview: preview,
    python_exam_manual_cycle_review_packet: packet,
    python_exam_manual_cycle_review_timeline: timeline,
    selected_skill_tag: ((gate.authorization_gate_summary || {}).selected_skill_tag) || gate.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!queue) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamManualExportReviewQueue = queue;
  result.value = renderPythonExamManualExportReviewQueue(queue, "Python Exam Export Review Queue: hash-only Review-Kandidaten ohne Export.");
});

document.querySelector("#pythonExamManualExportReviewerPacket").addEventListener("click", async () => {
  const queue = lastPythonExamManualExportReviewQueue;
  const gate = lastPythonExamManualReviewExportAuthorizationGate;
  const preview = lastPythonExamManualReviewExportPreview;
  const packet = lastPythonExamManualCycleReviewPacket;
  const timeline = lastPythonExamManualCycleReviewTimeline;
  if (!queue || !gate || !preview || !packet || !timeline) {
    result.value = "Bitte zuerst Export Review Queue, Export Authorization Gate, Export Preview, Review Packet und Review Timeline erzeugen.";
    return;
  }
  const reviewer = await callUniBot("/api/unibot/course/python-exam-manual-export-reviewer-packet", {
    python_exam_manual_export_review_queue: queue,
    python_exam_manual_review_export_authorization_gate: gate,
    python_exam_manual_review_export_preview: preview,
    python_exam_manual_cycle_review_packet: packet,
    python_exam_manual_cycle_review_timeline: timeline,
    selected_skill_tag: ((queue.queue_summary || {}).selected_skill_tag) || queue.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!reviewer) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamManualExportReviewerPacket = reviewer;
  result.value = renderPythonExamManualExportReviewerPacket(reviewer, "Python Exam Export Reviewer Packet: hash-only Pruefpaket ohne Export.");
});

document.querySelector("#pythonExamManualArchiveDecisionDraft").addEventListener("click", async () => {
  const reviewer = lastPythonExamManualExportReviewerPacket;
  const queue = lastPythonExamManualExportReviewQueue;
  const gate = lastPythonExamManualReviewExportAuthorizationGate;
  const preview = lastPythonExamManualReviewExportPreview;
  if (!reviewer || !queue || !gate || !preview) {
    result.value = "Bitte zuerst Export Reviewer Packet, Export Review Queue, Export Authorization Gate und Export Preview erzeugen.";
    return;
  }
  const draft = await callUniBot("/api/unibot/course/python-exam-manual-archive-decision-draft", {
    python_exam_manual_export_reviewer_packet: reviewer,
    python_exam_manual_export_review_queue: queue,
    python_exam_manual_review_export_authorization_gate: gate,
    python_exam_manual_review_export_preview: preview,
    selected_skill_tag: ((reviewer.reviewer_packet_summary || {}).selected_skill_tag) || reviewer.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!draft) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamManualArchiveDecisionDraft = draft;
  result.value = renderPythonExamManualArchiveDecisionDraft(draft, "Python Exam Archive Decision Draft: hash-only Entscheidungsentwurf ohne Archivierung oder Einreichung.");
});

document.querySelector("#pythonExamManualFinalReviewHandoff").addEventListener("click", async () => {
  const draft = lastPythonExamManualArchiveDecisionDraft;
  const reviewer = lastPythonExamManualExportReviewerPacket;
  const queue = lastPythonExamManualExportReviewQueue;
  const gate = lastPythonExamManualReviewExportAuthorizationGate;
  if (!draft || !reviewer || !queue || !gate) {
    result.value = "Bitte zuerst Archive Decision Draft, Export Reviewer Packet, Export Review Queue und Export Authorization Gate erzeugen.";
    return;
  }
  const handoff = await callUniBot("/api/unibot/course/python-exam-manual-final-review-handoff", {
    python_exam_manual_archive_decision_draft: draft,
    python_exam_manual_export_reviewer_packet: reviewer,
    python_exam_manual_export_review_queue: queue,
    python_exam_manual_review_export_authorization_gate: gate,
    selected_skill_tag: ((draft.archive_decision_draft_summary || {}).selected_skill_tag) || draft.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!handoff) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamManualFinalReviewHandoff = handoff;
  result.value = renderPythonExamManualFinalReviewHandoff(handoff, "Python Exam Final Review Handoff: finale hash-only Pruefansicht ohne Handlung.");
});

document.querySelector("#pythonExamManualFinalReviewReceiptLedger").addEventListener("click", async () => {
  const handoff = lastPythonExamManualFinalReviewHandoff;
  const draft = lastPythonExamManualArchiveDecisionDraft;
  const reviewer = lastPythonExamManualExportReviewerPacket;
  const queue = lastPythonExamManualExportReviewQueue;
  if (!handoff || !draft || !reviewer || !queue) {
    result.value = "Bitte zuerst Final Review Handoff, Archive Decision Draft, Export Reviewer Packet und Export Review Queue erzeugen.";
    return;
  }
  const ledger = await callUniBot("/api/unibot/course/python-exam-manual-final-review-receipt-ledger", {
    python_exam_manual_final_review_handoff: handoff,
    python_exam_manual_archive_decision_draft: draft,
    python_exam_manual_export_reviewer_packet: reviewer,
    python_exam_manual_export_review_queue: queue,
    selected_skill_tag: ((handoff.final_review_handoff_summary || {}).selected_skill_tag) || handoff.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!ledger) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamManualFinalReviewReceiptLedger = ledger;
  result.value = renderPythonExamManualFinalReviewReceiptLedger(ledger, "Python Exam Final Review Receipt Ledger: chronologische hash-only Pruefkette ohne Handlung.");
});

document.querySelector("#pythonExamFinalReviewLedgerIntegrityGate").addEventListener("click", async () => {
  const ledger = lastPythonExamManualFinalReviewReceiptLedger;
  const handoff = lastPythonExamManualFinalReviewHandoff;
  const draft = lastPythonExamManualArchiveDecisionDraft;
  const reviewer = lastPythonExamManualExportReviewerPacket;
  const queue = lastPythonExamManualExportReviewQueue;
  if (!ledger || !handoff || !draft || !reviewer || !queue) {
    result.value = "Bitte zuerst Final Review Receipt Ledger, Final Review Handoff, Archive Decision Draft, Export Reviewer Packet und Export Review Queue erzeugen.";
    return;
  }
  const gate = await callUniBot("/api/unibot/course/python-exam-final-review-ledger-integrity-gate", {
    python_exam_manual_final_review_receipt_ledger: ledger,
    python_exam_manual_final_review_handoff: handoff,
    python_exam_manual_archive_decision_draft: draft,
    python_exam_manual_export_reviewer_packet: reviewer,
    python_exam_manual_export_review_queue: queue,
    selected_skill_tag: ((ledger.final_review_receipt_ledger_summary || {}).selected_skill_tag) || ledger.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!gate) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamFinalReviewLedgerIntegrityGate = gate;
  result.value = renderPythonExamFinalReviewLedgerIntegrityGate(gate, "Python Exam Final Review Ledger Integrity Gate: hash-only Konsistenzpruefung ohne Handlung.");
});

document.querySelector("#pythonExamFinalManualReviewConsole").addEventListener("click", async () => {
  const gate = lastPythonExamFinalReviewLedgerIntegrityGate;
  const ledger = lastPythonExamManualFinalReviewReceiptLedger;
  const handoff = lastPythonExamManualFinalReviewHandoff;
  const draft = lastPythonExamManualArchiveDecisionDraft;
  const reviewer = lastPythonExamManualExportReviewerPacket;
  const queue = lastPythonExamManualExportReviewQueue;
  if (!gate || !ledger || !handoff || !draft || !reviewer || !queue) {
    result.value = "Bitte zuerst Final Integrity Gate, Final Review Receipt Ledger, Final Review Handoff, Archive Decision Draft, Export Reviewer Packet und Export Review Queue erzeugen.";
    return;
  }
  const consoleReport = await callUniBot("/api/unibot/course/python-exam-final-manual-review-console", {
    python_exam_final_review_ledger_integrity_gate: gate,
    python_exam_manual_final_review_receipt_ledger: ledger,
    python_exam_manual_final_review_handoff: handoff,
    python_exam_manual_archive_decision_draft: draft,
    python_exam_manual_export_reviewer_packet: reviewer,
    python_exam_manual_export_review_queue: queue,
    selected_skill_tag: ((gate.final_review_ledger_integrity_gate_summary || {}).selected_skill_tag) || gate.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!consoleReport) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamFinalManualReviewConsole = consoleReport;
  result.value = renderPythonExamFinalManualReviewConsole(consoleReport, "Python Exam Final Review Console: finale hash-only menschliche Pruefansicht ohne Handlung.");
});

document.querySelector("#pythonExamFinalManualReviewActionLock").addEventListener("click", async () => {
  const consoleReport = lastPythonExamFinalManualReviewConsole;
  const gate = lastPythonExamFinalReviewLedgerIntegrityGate;
  const ledger = lastPythonExamManualFinalReviewReceiptLedger;
  if (!consoleReport || !gate || !ledger) {
    result.value = "Bitte zuerst Final Review Console, Final Integrity Gate und Final Review Receipt Ledger erzeugen.";
    return;
  }
  const lock = await callUniBot("/api/unibot/course/python-exam-final-manual-review-action-lock", {
    python_exam_final_manual_review_console: consoleReport,
    python_exam_final_review_ledger_integrity_gate: gate,
    python_exam_manual_final_review_receipt_ledger: ledger,
    selected_skill_tag: ((consoleReport.final_manual_review_console_summary || {}).selected_skill_tag) || consoleReport.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!lock) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamFinalManualReviewActionLock = lock;
  result.value = renderPythonExamFinalManualReviewActionLock(lock, "Python Exam Final Action Lock: hash-only Sperre vor Export, Archivierung oder Einreichungsnaehe.");
});

document.querySelector("#pythonExamLockedFinalReviewBoard").addEventListener("click", async () => {
  const lock = lastPythonExamFinalManualReviewActionLock;
  const consoleReport = lastPythonExamFinalManualReviewConsole;
  const gate = lastPythonExamFinalReviewLedgerIntegrityGate;
  const ledger = lastPythonExamManualFinalReviewReceiptLedger;
  const draftConsole = lastPythonExamDraftPackageReviewConsole;
  const handoff = lastPythonExamHumanHandoffPacket;
  const rehearsal = lastPythonExamFullLocalRehearsalPack;
  if (!lock || !consoleReport || !gate || !ledger || !draftConsole || !handoff || !rehearsal) {
    result.value = "Bitte zuerst Final Action Lock, Final Review Console, Final Integrity Gate, Final Review Receipt Ledger, Draft Review Console, Human Handoff und Full Local Rehearsal erzeugen.";
    return;
  }
  const board = await callUniBot("/api/unibot/course/python-exam-locked-final-review-board", {
    python_exam_final_manual_review_action_lock: lock,
    python_exam_final_manual_review_console: consoleReport,
    python_exam_final_review_ledger_integrity_gate: gate,
    python_exam_manual_final_review_receipt_ledger: ledger,
    python_exam_draft_package_review_console: draftConsole,
    python_exam_human_handoff_packet: handoff,
    python_exam_full_local_rehearsal_pack: rehearsal,
    selected_skill_tag: ((lock.final_manual_review_action_lock_summary || {}).selected_skill_tag) || lock.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!board) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamLockedFinalReviewBoard = board;
  result.value = renderPythonExamLockedFinalReviewBoard(board, "Python Exam Locked Final Review Board: finale hash-only Abschluss-Review-Tafel ohne Handlung.");
});

document.querySelector("#pythonExamConfirmedLocalExportDraft").addEventListener("click", async () => {
  let preview = lastPythonExamEvidenceExportPreview;
  if (!preview) {
    result.value = "Bitte zuerst Python Exam Evidence Export Preview erzeugen.";
    return;
  }
  const draft = await callUniBot("/api/unibot/course/python-exam-confirmed-local-export-draft", {
    python_exam_evidence_export_preview: preview,
    operator_confirmed_local_export_draft_write: confirmLocalExportDraftWrite.checked,
    public_safe: true
  });
  if (!draft) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamConfirmedLocalExportDraft = draft;
  result.value = renderPythonExamConfirmedLocalExportDraft(draft, "Python Exam Confirmed Local Export Draft: Preview oder bestaetigter lokaler Hash-Draft, ohne Pfadrueckgabe.");
});

document.querySelector("#pythonExamDraftPackageReviewConsole").addEventListener("click", async () => {
  let preview = lastPythonExamEvidenceExportPreview;
  if (!preview) {
    result.value = "Bitte zuerst Python Exam Evidence Export Preview erzeugen.";
    return;
  }
  let draft = lastPythonExamConfirmedLocalExportDraft;
  if (!draft) {
    draft = await callUniBot("/api/unibot/course/python-exam-confirmed-local-export-draft", {
      python_exam_evidence_export_preview: preview,
      operator_confirmed_local_export_draft_write: confirmLocalExportDraftWrite.checked,
      public_safe: true
    });
    if (draft) lastPythonExamConfirmedLocalExportDraft = draft;
  }
  const consoleReport = await callUniBot("/api/unibot/course/python-exam-draft-package-review-console", {
    python_exam_confirmed_local_export_draft: draft,
    python_exam_evidence_export_preview: preview,
    public_safe: true
  });
  if (!consoleReport) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamDraftPackageReviewConsole = consoleReport;
  result.value = renderPythonExamDraftPackageReviewConsole(consoleReport, "Python Exam Draft Package Review Console: Hash-Integritaet, not_cleared-Receipt, A0-A2 und Review Chain.");
});

document.querySelector("#pythonExamHumanHandoffPacket").addEventListener("click", async () => {
  let preview = lastPythonExamEvidenceExportPreview;
  if (!preview) {
    result.value = "Bitte zuerst Python Exam Evidence Export Preview erzeugen.";
    return;
  }
  let draft = lastPythonExamConfirmedLocalExportDraft;
  if (!draft) {
    draft = await callUniBot("/api/unibot/course/python-exam-confirmed-local-export-draft", {
      python_exam_evidence_export_preview: preview,
      operator_confirmed_local_export_draft_write: false,
      public_safe: true
    });
    if (draft) lastPythonExamConfirmedLocalExportDraft = draft;
  }
  let consoleReport = lastPythonExamDraftPackageReviewConsole;
  if (!consoleReport) {
    consoleReport = await callUniBot("/api/unibot/course/python-exam-draft-package-review-console", {
      python_exam_confirmed_local_export_draft: draft,
      python_exam_evidence_export_preview: preview,
      public_safe: true
    });
    if (consoleReport) lastPythonExamDraftPackageReviewConsole = consoleReport;
  }
  const handoff = await callUniBot("/api/unibot/course/python-exam-human-handoff-packet", {
    python_exam_draft_package_review_console: consoleReport,
    python_exam_evidence_export_preview: preview,
    python_exam_confirmed_local_export_draft: draft,
    public_safe: true
  });
  if (!handoff) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamHumanHandoffPacket = handoff;
  await navigator.clipboard.writeText((handoff.copy_export_view || {}).markdown || "");
  result.value = renderPythonExamHumanHandoffPacket(handoff, "Python Exam Human Handoff Packet: sichere Copy-Ansicht fuer menschliche Pruefung wurde kopiert.");
});

document.querySelector("#pythonExamFullLocalRehearsalPack").addEventListener("click", async () => {
  const pack = await callUniBot("/api/unibot/course/python-exam-full-local-rehearsal-pack", {
    selected_skill_tag: task.value,
    exam_skill_drilldown: lastExamSkillDrilldown,
    python_exam_local_cycle_readiness_review: lastPythonExamLocalCycleReadinessReview,
    python_exam_local_cycle_readiness_handoff: lastPythonExamLocalCycleReadinessHandoff,
    python_exam_local_cycle_operator_workspace_card: lastPythonExamLocalCycleWorkspaceCard,
    exam_workspace_operator_run: lastExamWorkspaceOperatorRun,
    exam_workspace_session_console: examSessionConsoleReports[examSessionConsoleReports.length - 1] || null,
    exam_workspace_run_history_export_review: lastExamRunHistoryExportReview,
    course_exam_coverage_dashboard: lastCourseExamCoverageDashboard,
    course_per_skill_action_router: lastPerSkillActionRouter,
    routed_action_executor: lastRoutedActionExecutor,
    exam_run_packet: lastExamRunPacket,
    exam_packet_timeline: lastExamPacketTimeline,
    timeline_export_review_packet: lastTimelineExportReviewPacket,
    timeline_export_receipt_journal_summary: lastTimelineExportReceiptJournalSummary,
    review_chain_integrity_check: lastReviewChainIntegrityCheck,
    python_exam_readiness_console: lastPythonExamReadinessConsole,
    python_exam_cockpit_flow: lastPythonExamCockpitFlow,
    python_exam_live_control_surface: lastPythonExamLiveControlSurface,
    python_exam_evidence_export_preview: lastPythonExamEvidenceExportPreview,
    python_exam_confirmed_local_export_draft: lastPythonExamConfirmedLocalExportDraft,
    python_exam_draft_package_review_console: lastPythonExamDraftPackageReviewConsole,
    python_exam_human_handoff_packet: lastPythonExamHumanHandoffPacket,
    public_safe: true
  });
  if (!pack) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamFullLocalRehearsalPack = pack;
  if (pack.python_exam_evidence_export_preview) lastPythonExamEvidenceExportPreview = pack.python_exam_evidence_export_preview;
  if (pack.python_exam_human_handoff_packet) lastPythonExamHumanHandoffPacket = pack.python_exam_human_handoff_packet;
  result.value = renderPythonExamFullLocalRehearsalPack(pack, "Python Exam Full Local Rehearsal: kompletter lokaler Trockenlauf als hash-only Review-Pack.");
});

document.querySelector("#pythonExamRehearsalPlaybackGapCoach").addEventListener("click", async () => {
  let pack = lastPythonExamFullLocalRehearsalPack;
  if (!pack) {
    pack = await callUniBot("/api/unibot/course/python-exam-full-local-rehearsal-pack", {
      selected_skill_tag: task.value,
      exam_skill_drilldown: lastExamSkillDrilldown,
      python_exam_local_cycle_readiness_review: lastPythonExamLocalCycleReadinessReview,
      python_exam_local_cycle_readiness_handoff: lastPythonExamLocalCycleReadinessHandoff,
      python_exam_local_cycle_operator_workspace_card: lastPythonExamLocalCycleWorkspaceCard,
      exam_workspace_operator_run: lastExamWorkspaceOperatorRun,
      exam_workspace_session_console: examSessionConsoleReports[examSessionConsoleReports.length - 1] || null,
      exam_workspace_run_history_export_review: lastExamRunHistoryExportReview,
      course_exam_coverage_dashboard: lastCourseExamCoverageDashboard,
      course_per_skill_action_router: lastPerSkillActionRouter,
      routed_action_executor: lastRoutedActionExecutor,
      exam_run_packet: lastExamRunPacket,
      exam_packet_timeline: lastExamPacketTimeline,
      timeline_export_review_packet: lastTimelineExportReviewPacket,
      timeline_export_receipt_journal_summary: lastTimelineExportReceiptJournalSummary,
      review_chain_integrity_check: lastReviewChainIntegrityCheck,
      python_exam_readiness_console: lastPythonExamReadinessConsole,
      python_exam_cockpit_flow: lastPythonExamCockpitFlow,
      python_exam_live_control_surface: lastPythonExamLiveControlSurface,
      python_exam_evidence_export_preview: lastPythonExamEvidenceExportPreview,
      python_exam_confirmed_local_export_draft: lastPythonExamConfirmedLocalExportDraft,
      python_exam_draft_package_review_console: lastPythonExamDraftPackageReviewConsole,
      python_exam_human_handoff_packet: lastPythonExamHumanHandoffPacket,
      public_safe: true
    });
    if (pack) lastPythonExamFullLocalRehearsalPack = pack;
  }
  const coach = await callUniBot("/api/unibot/course/python-exam-rehearsal-playback-gap-coach", {
    selected_skill_tag: task.value,
    python_exam_full_local_rehearsal_pack: pack,
    public_safe: true
  });
  if (!coach) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamRehearsalPlaybackGapCoach = coach;
  result.value = renderPythonExamRehearsalPlaybackGapCoach(coach, "Python Exam Gap Coach: Playback, Luecken und naechste sichere Aktion.");
});

document.querySelector("#pythonExamGapCoachGuidedLoop").addEventListener("click", async () => {
  let coach = lastPythonExamRehearsalPlaybackGapCoach;
  if (!coach) {
    let pack = lastPythonExamFullLocalRehearsalPack;
    if (!pack) {
      result.value = "Bitte zuerst Python Exam Full Local Rehearsal oder Gap Coach erzeugen.";
      return;
    }
    coach = await callUniBot("/api/unibot/course/python-exam-rehearsal-playback-gap-coach", {
      selected_skill_tag: task.value,
      python_exam_full_local_rehearsal_pack: pack,
      public_safe: true
    });
    if (coach) lastPythonExamRehearsalPlaybackGapCoach = coach;
  }
  const loop = await callUniBot("/api/unibot/course/python-exam-gap-coach-guided-rehearsal-loop", {
    selected_skill_tag: task.value,
    python_exam_rehearsal_playback_gap_coach: coach,
    requested_action_key: (coach || {}).next_safe_action_key || "",
    public_safe: true
  });
  if (!loop) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamGapCoachGuidedLoop = loop;
  result.value = renderPythonExamGapCoachGuidedLoop(loop, "Python Exam Guided Loop: naechste sichere Gap-Coach-Aktion als Review-Karte.");
});

document.querySelector("#pythonExamGuidedLoopControlSurface").addEventListener("click", async () => {
  let loop = lastPythonExamGapCoachGuidedLoop;
  let coach = lastPythonExamRehearsalPlaybackGapCoach;
  if (!loop) {
    if (!coach) {
      result.value = "Bitte zuerst Python Exam Gap Coach oder Guided Loop erzeugen.";
      return;
    }
    loop = await callUniBot("/api/unibot/course/python-exam-gap-coach-guided-rehearsal-loop", {
      selected_skill_tag: task.value,
      python_exam_rehearsal_playback_gap_coach: coach,
      requested_action_key: (coach || {}).next_safe_action_key || "",
      public_safe: true
    });
    if (loop) lastPythonExamGapCoachGuidedLoop = loop;
  }
  const surface = await callUniBot("/api/unibot/course/python-exam-guided-loop-control-surface", {
    selected_skill_tag: task.value,
    python_exam_gap_coach_guided_rehearsal_loop: loop,
    python_exam_rehearsal_playback_gap_coach: coach,
    operator_confirmed_dry_run_request: false,
    public_safe: true
  });
  if (!surface) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamGuidedLoopControlSurface = surface;
  result.value = renderPythonExamGuidedLoopControlSurface(surface, "Python Exam Loop Control: aktueller Guided-Step als sichere Kontrolloberflaeche.");
});

document.querySelector("#pythonExamLockedFinalReviewGapResolver").addEventListener("click", async () => {
  const board = lastPythonExamLockedFinalReviewBoard;
  const lock = lastPythonExamFinalManualReviewActionLock;
  const rehearsal = lastPythonExamFullLocalRehearsalPack;
  const coach = lastPythonExamRehearsalPlaybackGapCoach;
  const surface = lastPythonExamGuidedLoopControlSurface;
  if (!board || !lock || !rehearsal || !coach || !surface) {
    result.value = "Bitte zuerst Locked Final Review Board, Final Action Lock, Full Local Rehearsal, Gap Coach und Loop Control erzeugen.";
    return;
  }
  const resolver = await callUniBot("/api/unibot/course/python-exam-locked-final-review-gap-resolver", {
    python_exam_locked_final_review_board: board,
    python_exam_final_manual_review_action_lock: lock,
    python_exam_full_local_rehearsal_pack: rehearsal,
    python_exam_rehearsal_playback_gap_coach: coach,
    python_exam_guided_loop_control_surface: surface,
    selected_skill_tag: ((board.locked_final_review_board_summary || {}).selected_skill_tag) || board.selected_skill_tag || task.value,
    public_safe: true
  });
  if (!resolver) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastPythonExamLockedFinalReviewGapResolver = resolver;
  result.value = renderPythonExamLockedFinalReviewGapResolver(resolver, "Python Exam Final Gap Resolver: hash-only Reparaturkarte fuer die naechste sichere menschliche Review-Handlung.");
});

document.querySelector("#examWorkspaceOperatorRun").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/exam-workspace/operator-run", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    ledger_path: "~/.unibot_guardian/help_ledger.jsonl",
    checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
    focus_query: task.value,
    query: task.value,
    requested_help_level: helpLevel(),
    exam_status: "strict",
    student_reflection: reflection.value,
    cell_source: notebookCell.value,
    cell_index: 0,
    cell_type: "code",
    operator_confirmed_checkpoint_store: confirmCheckpointStore.checked,
    operator_confirmed_exam_workspace_run: confirmExamWorkspaceRun.checked,
    operator_confirmed_manifest_apply: confirmManifestApply.checked,
    operator_confirmed_tutor_index_build: confirmTutorIndexBuild.checked,
    operator_confirmed_help_ledger_append: confirmHelpLedgerAppend.checked,
    operator_confirmed_exam_ledger_append: confirmExamLedgerAppend.checked,
    study_receipt: {
      prediction_present: Boolean(task.value.trim()),
      notebook_action_present: Boolean(notebookCell.value.trim()),
      reflection_present: Boolean(reflection.value.trim()),
    },
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  lastExamWorkspaceOperatorRun = report;
  result.value = renderExamWorkspaceOperatorRun(report, "Lokale UniBot-API genutzt. Start Exam Workspace Receipt erstellt.");
});

document.querySelector("#examWorkspaceLaunchFlow").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/exam-workspace/launch-flow/dry-run", {
    review_policy: "staged",
    decision_record_journal_path: "~/.unibot_guardian/external_decision_records.jsonl",
    receipt_journal_path: "~/.unibot_guardian/extraction_receipts.jsonl",
    private_manifest_path: "~/.unibot_guardian/private_course_material_manifest.json",
    manifest_apply_journal_path: "~/.unibot_guardian/private_manifest_apply_journal.jsonl",
    tutor_index_path: "~/.unibot_guardian/private_tutor_index.hash_only.json",
    tutor_index_journal_path: "~/.unibot_guardian/private_tutor_index_journal.jsonl",
    ledger_path: "~/.unibot_guardian/help_ledger.jsonl",
    checkpoint_journal_path: "~/.unibot_guardian/notebook_checkpoints.jsonl",
    focus_query: task.value,
    query: task.value,
    requested_help_level: helpLevel(),
    exam_status: "strict",
    student_reflection: reflection.value,
    cell_source: notebookCell.value,
    cell_index: 0,
    cell_type: "code",
    operator_confirmed_exam_workspace_run: false,
    operator_confirmed_manifest_apply: false,
    operator_confirmed_tutor_index_build: false,
    operator_confirmed_help_ledger_append: false,
    operator_confirmed_exam_ledger_append: false,
    operator_confirmed_checkpoint_store: false,
    study_receipt: {
      prediction_present: Boolean(task.value.trim()),
      notebook_action_present: true,
      reflection_present: Boolean(reflection.value.trim()),
    },
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderExamWorkspaceLaunchFlow(report, "Lokale UniBot-API genutzt. Coverage-Startpunkt wird als A2 Exam-Workspace-Dry-Run vorbereitet.");
});

document.querySelector("#studySessionPlan").addEventListener("click", async () => {
  const plan = await callUniBot("/api/unibot/course/study-session-plan", {
    review_policy: "staged",
    focus_query: task.value,
    max_items: 5,
    public_safe: true
  });
  if (!plan) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderStudySessionPlan(plan, "Lokale UniBot-API genutzt.");
});

function syntheticStudyReceipt() {
  return {
    task_id: "sidepanel-study-task",
    skill_tag: "pandas",
    source_anchor_id: "sidepanel-source-anchor",
    retrieval_response_present: true,
    prediction_present: Boolean(task.value.trim()),
    notebook_action_present: true,
    reflection: reflection.value || "Ich pruefe meinen kleinsten naechsten Schritt.",
    help_level: "A2"
  };
}

document.querySelector("#studyReceiptValidate").addEventListener("click", async () => {
  const validation = await callUniBot("/api/unibot/course/study-session-receipt/validate", {
    receipt: syntheticStudyReceipt(),
    public_safe: true
  });
  if (!validation) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderStudyReceiptValidation(validation, "Lokale UniBot-API genutzt.");
});

document.querySelector("#studyReviewReport").addEventListener("click", async () => {
  const report = await callUniBot("/api/unibot/course/study-session-review-report", {
    review_policy: "staged",
    focus_query: task.value,
    study_receipts: [syntheticStudyReceipt()],
    public_safe: true
  });
  if (!report) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderStudyReviewReport(report, "Lokale UniBot-API genutzt.");
});

document.querySelector("#clearanceBoard").addEventListener("click", async () => {
  const board = await callUniBot("/api/unibot/institutional-clearance/board", {
    public_safe: true
  });
  if (!board) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderClearanceBoard(board, "Lokale UniBot-API genutzt.");
});

document.querySelector("#submissionBundle").addEventListener("click", async () => {
  const bundle = await callUniBot("/api/unibot/stakeholder/submission-bundle", {
    review_policy: "staged",
    public_safe: true
  });
  if (!bundle) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderSubmissionBundle(bundle, "Lokale UniBot-API genutzt.");
});

document.querySelector("#decisionRequest").addEventListener("click", async () => {
  const packet = await callUniBot("/api/unibot/stakeholder/decision-request", {
    lane_id: "rights_privacy_local_extraction",
    review_policy: "staged",
    public_safe: true
  });
  if (!packet) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderDecisionRequest(packet, "Lokale UniBot-API genutzt.");
});

document.querySelector("#decisionRequestMarkdown").addEventListener("click", async () => {
  const response = await callUniBot("/api/unibot/stakeholder/decision-request-markdown", {
    lane_id: "rights_privacy_local_extraction",
    review_policy: "staged"
  });
  if (!response) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  await navigator.clipboard.writeText(response.markdown || "");
  result.value = `Decision-Request Markdown kopiert.\n\n${(response.markdown || "").slice(0, 1800)}`;
});

document.querySelector("#decisionJournal").addEventListener("click", async () => {
  const summary = await callUniBot("/api/unibot/stakeholder/decision-journal/summary", {});
  if (!summary) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderDecisionJournal(summary, "Lokale UniBot-API genutzt.");
});

document.querySelector("#decisionRecordJournal").addEventListener("click", async () => {
  const summary = await callUniBot("/api/unibot/stakeholder/decision-record-journal/summary", {});
  if (!summary) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderDecisionRecordJournal(summary, "Lokale UniBot-API genutzt.");
});

document.querySelector("#decisionState").addEventListener("click", async () => {
  const state = await callUniBot("/api/unibot/stakeholder/decision-state", {
    public_safe: true
  });
  if (!state) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  result.value = renderDecisionState(state, "Lokale UniBot-API genutzt.");
});

document.querySelector("#contextPacket").addEventListener("click", async () => {
  const packet = await callUniBot("/api/unibot/orchestration/context-packet", {
    role_id: "qa_redteam"
  });
  if (!packet) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  const text = renderContextPacket(packet, "Lokale UniBot-API genutzt.");
  await navigator.clipboard.writeText(JSON.stringify(packet, null, 2));
  result.value = `${text}\n\nContext Packet JSON kopiert.`;
});

document.querySelector("#feedbackValidate").addEventListener("click", async () => {
  const feedback = buildDemoFeedback();
  const validation = await callUniBot("/api/unibot/demo-feedback/validate", { feedback });
  if (validation) {
    result.value = renderFeedbackValidation(validation, "Lokale UniBot-API genutzt.");
    return;
  }
  result.value = renderFeedbackValidation(validateFeedbackLocally(feedback), "Offline-Fallback genutzt.");
});

document.querySelector("#feedbackSave").addEventListener("click", async () => {
  const feedback = buildDemoFeedback();
  const stored = await callUniBot("/api/unibot/demo-feedback/append", { feedback });
  if (!stored) {
    result.value = "Lokale UniBot-API nicht erreichbar. Feedback kann offline nicht gespeichert werden.";
    return;
  }
  if (stored.status === "stored") {
    result.value = [
      "Feedback lokal gespeichert.",
      `Feedback-ID: ${stored.record.feedback.feedback_id}`,
      `Szenario: ${stored.record.feedback.scenario_id}`,
      "Freitext wurde nicht in die Public Summary uebernommen."
    ].join("\n");
    return;
  }
  result.value = renderFeedbackValidation(stored.validation || stored, "Feedback nicht gespeichert.");
});

document.querySelector("#notebook").addEventListener("click", async () => {
  const template = await callUniBot("/api/unibot/notebook-template", {
    task: task.value,
    mode: "practice_overlay",
    source_card_ids: ["google-colab-gemini", "uoc-ki-lehre", "vanlehn-2011"]
  });
  if (!template) {
    result.value = "Lokale UniBot-API nicht erreichbar. Starte: python3 -m unibot.server";
    return;
  }
  await navigator.clipboard.writeText(JSON.stringify(template.notebook, null, 2));
  result.value = [
    "Notebook-JSON kopiert.",
    `Audit: ${template.audit.status}`,
    `Zellen: ${template.audit.cell_count}`,
    "Als .ipynb speichern und in Colab/Jupyter oeffnen."
  ].join("\n");
});
