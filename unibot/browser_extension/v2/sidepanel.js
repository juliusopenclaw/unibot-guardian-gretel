const NATIVE_HOST = "de.gretel.unibot_companion";
const MAX_NOTEBOOK_BYTES = 10 * 1024 * 1024;
const UPLOAD_CHUNK_BYTES = 32 * 1024;
const HELP_LEVELS = ["A0", "A1", "A2", "A3", "A4"];
const ACCESSIBILITY_PREFERENCE_KEY = "unibot.accessibility.display.v1";

const state = {
  port: null,
  pending: new Map(),
  requestCounter: 0,
  contract: null,
  sessionActive: false,
  mode: "practice",
  rehearsalId: "",
  rehearsalStatus: "",
  rehearsalBrowserBinding: null,
  notebookId: "",
  notebookSourceSha256: "",
  gatewayActive: false,
  selectedCell: null,
  lastReview: null,
  transferTask: null,
  reconnectTimer: null,
  reconnectAttempt: 0,
  connecting: false
};

const elements = {
  connectionStatus: document.querySelector("#connectionStatus"),
  releaseStatus: document.querySelector("#releaseStatus"),
  sessionMode: document.querySelector("#sessionMode"),
  pseudonym: document.querySelector("#pseudonym"),
  courseId: document.querySelector("#courseId"),
  maxHelpLevel: document.querySelector("#maxHelpLevel"),
  fixedHelpLevel: document.querySelector("#fixedHelpLevel"),
  practiceBoundary: document.querySelector("#practiceBoundary"),
  boundaryLabel: document.querySelector("#boundaryLabel"),
  practiceBoundaryNote: document.querySelector("#practiceBoundaryNote"),
  startSession: document.querySelector("#startSession"),
  stopSession: document.querySelector("#stopSession"),
  finishRehearsal: document.querySelector("#finishRehearsal"),
  sessionOutput: document.querySelector("#sessionOutput"),
  notebookSource: document.querySelector("#notebookSource"),
  notebookFile: document.querySelector("#notebookFile"),
  importNotebook: document.querySelector("#importNotebook"),
  openGateway: document.querySelector("#openGateway"),
  stopGateway: document.querySelector("#stopGateway"),
  notebookOutput: document.querySelector("#notebookOutput"),
  capture: document.querySelector("#capture"),
  cellMeta: document.querySelector("#cellMeta"),
  task: document.querySelector("#task"),
  attempt: document.querySelector("#attempt"),
  confirmEscalation: document.querySelector("#confirmEscalation"),
  accessibilitySupport: document.querySelector("#accessibilitySupport"),
  ask: document.querySelector("#ask"),
  helpOutput: document.querySelector("#helpOutput"),
  refreshReview: document.querySelector("#refreshReview"),
  showTransferTask: document.querySelector("#showTransferTask"),
  transferPrompt: document.querySelector("#transferPrompt"),
  transferAnswerLabel: document.querySelector("#transferAnswerLabel"),
  transferAnswer: document.querySelector("#transferAnswer"),
  recordTransfer: document.querySelector("#recordTransfer"),
  exportReview: document.querySelector("#exportReview"),
  deleteSession: document.querySelector("#deleteSession"),
  reviewOutput: document.querySelector("#reviewOutput"),
  showExportPreview: document.querySelector("#showExportPreview"),
  exportPreview: document.querySelector("#exportPreview"),
  exportConfirmRow: document.querySelector("#exportConfirmRow"),
  confirmExport: document.querySelector("#confirmExport"),
  scopeBoundary: document.querySelector("#scopeBoundary")
};

function setConnection(text, status) {
  elements.connectionStatus.textContent = text;
  elements.connectionStatus.dataset.state = status;
}

function renderCompanionReleaseStatus(status) {
  const localStatus = {
    ready_for_local_practice: "Lokaler Uebungsbetrieb: bereit",
    attention: "Lokaler Uebungsbetrieb: Diagnose erforderlich",
    not_installed: "Lokaler Uebungsbetrieb: Companion fehlt"
  }[status.local_practice_status] || "Lokaler Uebungsbetrieb: Status unbekannt";
  const distributionStatus = {
    blocked_human_release_gates: "Allgemeine Verteilung: noch nicht freigegeben",
    ready_for_distribution: "Allgemeine Verteilung: menschliche Freigabe liegt vor"
  }[status.distribution_status] || "Allgemeine Verteilung: Status unbekannt";
  const rehearsalStatus = {
    ready_for_offline_preflight: "Künstliche Simulation: JupyterLab bereit; Offline-Prüfung folgt beim Start",
    jupyterlab_missing: "Künstliche Simulation: JupyterLab fehlt",
    prerequisites_missing: "Künstliche Simulation: Voraussetzungen fehlen"
  }[status.controlled_rehearsal_status] || "Künstliche Simulation: Status beim Start geprüft";
  elements.releaseStatus.textContent = `${localStatus}. ${distributionStatus}. ${rehearsalStatus}.`;
  elements.releaseStatus.dataset.state = status.local_practice_status === "ready_for_local_practice"
    && status.distribution_status === "blocked_human_release_gates" ? "ready" : "attention";
}

function selectedHelpLevel() {
  return document.querySelector("input[name='helpLevel']:checked")?.value || "A0";
}

function selectedAssistanceMode() {
  return document.querySelector("input[name='assistanceMode']:checked").value;
}

function applyAccessibilityMode() {
  document.documentElement.dataset.accessibility = elements.accessibilitySupport.checked ? "enhanced" : "default";
}

function restoreAccessibilityPreference() {
  try {
    elements.accessibilitySupport.checked = window.localStorage.getItem(ACCESSIBILITY_PREFERENCE_KEY) === "enhanced";
  } catch {
    // Some browser test and restricted file contexts do not expose local storage.
  }
  applyAccessibilityMode();
}

function persistAccessibilityPreference() {
  try {
    window.localStorage.setItem(
      ACCESSIBILITY_PREFERENCE_KEY,
      elements.accessibilitySupport.checked ? "enhanced" : "default"
    );
  } catch {
    // The preference remains session-local when browser storage is unavailable.
  }
}

function syncSessionControls() {
  const hasContract = Boolean(state.contract);
  const active = hasContract && state.sessionActive;
  const rehearsal = state.mode === "rehearsal";
  const syntheticFixtureReady = state.notebookSourceSha256 === "f65a9b818bd0247cd1026d2750352597aaf47c672796374965d33379286c2b50";
  elements.startSession.disabled = active || (hasContract && !state.sessionActive) || (rehearsal && !syntheticFixtureReady);
  elements.stopSession.disabled = !active || rehearsal;
  elements.stopSession.hidden = rehearsal;
  elements.finishRehearsal.hidden = !rehearsal;
  elements.finishRehearsal.disabled = !rehearsal || !["active", "frozen"].includes(state.rehearsalStatus);
  elements.capture.disabled = !active;
  elements.ask.disabled = !active;
  elements.refreshReview.disabled = !hasContract;
  elements.showExportPreview.disabled = !state.lastReview;
  elements.deleteSession.disabled = !hasContract;
  const transferReport = state.lastReview?.transfer_tasks?.[0];
  const transferRecorded = transferReport?.status === "recorded";
  const transferVisible = Boolean(!rehearsal && hasContract && !active && !transferRecorded);
  elements.showTransferTask.disabled = !transferVisible;
  elements.recordTransfer.hidden = !state.transferTask || transferRecorded;
  elements.transferAnswerLabel.hidden = !state.transferTask || transferRecorded;
  elements.transferAnswer.hidden = !state.transferTask || transferRecorded;
  elements.recordTransfer.disabled = !state.transferTask || transferRecorded || !elements.transferAnswer.value.trim();

  elements.sessionMode.disabled = hasContract;
  [elements.pseudonym, elements.courseId, elements.maxHelpLevel, elements.fixedHelpLevel]
    .forEach((control) => { control.disabled = hasContract || rehearsal; });
  elements.practiceBoundary.disabled = hasContract;
  document.querySelectorAll("input[name='assistanceMode']").forEach((control) => {
    control.disabled = hasContract || rehearsal;
  });

  document.querySelectorAll("input[name='helpLevel']").forEach((control) => {
    const levelIndex = HELP_LEVELS.indexOf(control.value);
    const maximumIndex = HELP_LEVELS.indexOf(state.contract?.max_help_level || (rehearsal ? "A2" : "A4"));
    const fixedLevel = state.contract?.fixed_help_level || elements.fixedHelpLevel.value;
    const allowed = (!hasContract && (!rehearsal || levelIndex <= HELP_LEVELS.indexOf("A2")))
      || (state.sessionActive && (state.contract.assistance_mode === "fixed"
        ? control.value === fixedLevel
        : levelIndex >= 0 && levelIndex <= maximumIndex));
    control.disabled = !allowed;
  });

  if (active && state.contract.assistance_mode === "fixed") {
    const fixedLevel = state.contract.fixed_help_level || elements.fixedHelpLevel.value;
    const fixedControl = document.querySelector(`input[name='helpLevel'][value='${fixedLevel}']`);
    if (fixedControl) fixedControl.checked = true;
  } else if (active) {
    const maximumIndex = HELP_LEVELS.indexOf(state.contract.max_help_level || "A4");
    const current = document.querySelector("input[name='helpLevel']:checked");
    if (!current || HELP_LEVELS.indexOf(current.value) > maximumIndex) {
      const fallback = document.querySelector(`input[name='helpLevel'][value='${HELP_LEVELS[Math.max(0, maximumIndex)]}']`);
      if (fallback) fallback.checked = true;
    }
  }
  elements.openGateway.disabled = rehearsal || !state.notebookId || state.gatewayActive;
  elements.stopGateway.disabled = !state.gatewayActive;
}

function syncModePresentation() {
  state.mode = elements.sessionMode.value === "rehearsal" ? "rehearsal" : "practice";
  const rehearsal = state.mode === "rehearsal";
  elements.boundaryLabel.textContent = rehearsal
    ? "Künstliche Prüfungssimulation und Status nicht freigegeben bestätigen"
    : "Freiwillige Übung bestätigen";
  elements.practiceBoundaryNote.textContent = rehearsal
    ? "Nur das veröffentlichte künstliche Notebook; A0-A2, lokaler Offline-Betrieb, keine echte Klausur oder automatische Abgabe."
    : "Diese Sitzung ist kein Prüfungseinsatz. Hilfe und Rückblick bleiben lokal; es gibt keine automatische Note oder KI-Erkennung.";
  elements.startSession.textContent = rehearsal ? "Simulation starten" : "Sitzung starten";
  elements.scopeBoundary.textContent = rehearsal
    ? "A0-A2. Künstliche Simulation. Keine Note, Überwachung, automatische Abgabe oder Prüfungsfreigabe."
    : "A0-A4. Lernbetrieb. Keine Note, KI-Erkennung oder Pruefungsfreigabe.";
  if (rehearsal) {
    elements.maxHelpLevel.value = "A2";
    document.querySelector("input[name='assistanceMode'][value='adaptive']").checked = true;
    const a2 = document.querySelector("input[name='helpLevel'][value='A2']");
    if (a2) a2.checked = true;
  }
  syncSessionControls();
}

function scheduleReconnect() {
  if (state.reconnectTimer || state.port || state.connecting || !globalThis.chrome?.runtime?.connectNative) return;
  const delay = Math.min(5000, 500 * (2 ** Math.min(state.reconnectAttempt, 3)));
  state.reconnectAttempt += 1;
  state.reconnectTimer = setTimeout(() => {
    state.reconnectTimer = null;
    connectCompanion();
  }, delay);
}

function connectCompanion() {
  if (state.port || state.connecting) return;
  if (!globalThis.chrome?.runtime?.connectNative) {
    setConnection("Begleiter fehlt", "error");
    renderCompanionReleaseStatus({ local_practice_status: "not_installed", distribution_status: "blocked_human_release_gates" });
    elements.sessionOutput.textContent = "UniBot Companion ist nicht installiert.";
    return;
  }
  state.connecting = true;
  let port;
  try {
    port = globalThis.chrome.runtime.connectNative(NATIVE_HOST);
  } catch (error) {
    state.connecting = false;
    setConnection("Begleiter fehlt", "error");
    renderCompanionReleaseStatus({ local_practice_status: "not_installed", distribution_status: "blocked_human_release_gates" });
    elements.sessionOutput.textContent = error.message;
    scheduleReconnect();
    return;
  }
  state.port = port;
  state.port.onMessage.addListener((message) => {
    const request = state.pending.get(message.request_id);
    if (!request) return;
    clearTimeout(request.timeout);
    state.pending.delete(message.request_id);
    if (message.error) request.reject(new Error(message.error));
    else request.resolve(message);
  });
  state.port.onDisconnect.addListener(() => {
    const message = globalThis.chrome?.runtime?.lastError?.message || "Lokaler Begleiter wurde getrennt.";
    for (const request of state.pending.values()) {
      clearTimeout(request.timeout);
      request.reject(new Error(message));
    }
    state.pending.clear();
    state.port = null;
    state.connecting = false;
    setConnection("Begleiter getrennt", "error");
    scheduleReconnect();
  });
  nativeRequest("companion.status").then(async (status) => {
    if (status.status !== "ready") throw new Error(status.error || "Lokaler Begleiter ist blockiert.");
    renderCompanionReleaseStatus(status);
    setConnection("Lokal bereit", "ready");
    state.reconnectAttempt = 0;
    state.connecting = false;
    if (status.rehearsal_resume_available) {
      const resumed = await nativeRequest("rehearsal.status", {
        rehearsal_id: status.active_rehearsal_metadata?.rehearsal_id || ""
      });
      state.mode = "rehearsal";
      state.rehearsalId = resumed.rehearsal.rehearsal_id;
      state.rehearsalStatus = resumed.rehearsal.status;
      state.rehearsalBrowserBinding = resumed.rehearsal.browser_binding || null;
      state.contract = resumed.contract;
      state.sessionActive = resumed.rehearsal.status === "active";
      state.notebookId = resumed.rehearsal.notebook_id || "";
      elements.sessionMode.value = "rehearsal";
      elements.practiceBoundary.checked = true;
      state.lastReview = resumed.report;
      syncModePresentation();
      setConnection("Simulation fortgesetzt", "ready");
      elements.sessionOutput.textContent = "Vorhandene künstliche Prüfungssimulation wurde lokal fortgesetzt.";
      elements.reviewOutput.textContent = renderReview(state.lastReview);
    } else if (status.resume_available) {
      const resumed = await nativeRequest("session.resume", {
        session_id: status.active_session_metadata?.session_id || ""
      });
      state.contract = resumed.contract;
      state.sessionActive = true;
      elements.practiceBoundary.checked = resumed.contract.practice_scope === "practice_only";
      state.lastReview = resumed.report;
      setConnection("Sitzung fortgesetzt", "ready");
      elements.sessionOutput.textContent = "Vorhandene Lernsitzung wurde lokal fortgesetzt.";
      elements.reviewOutput.textContent = renderReview(state.lastReview);
    } else {
      state.sessionActive = false;
      elements.sessionOutput.textContent = "Begleiter bereit. Lernsitzung starten.";
    }
    const gateway = await nativeRequest("gateway.status");
    state.gatewayActive = gateway.status === "active"
      && gateway.gateway?.mode !== "synthetic_exam_rehearsal";
    if (state.gatewayActive) {
      elements.notebookOutput.textContent = "Lokales Jupyter-Gateway ist aktiv.";
    }
    syncSessionControls();
  }).catch((error) => {
    state.connecting = false;
    setConnection("Begleiter fehlt", "error");
    renderCompanionReleaseStatus({ local_practice_status: "attention", distribution_status: "blocked_human_release_gates" });
    elements.sessionOutput.textContent = error.message;
    syncSessionControls();
    if (state.port) {
      state.port.disconnect?.();
    }
    scheduleReconnect();
  });
}

function nativeRequest(type, payload = {}, timeoutMs = 10000) {
  if (!state.port) return Promise.reject(new Error("UniBot Companion ist nicht verbunden."));
  const requestId = `unibot-${Date.now()}-${++state.requestCounter}`;
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      state.pending.delete(requestId);
      reject(new Error("Der lokale Begleiter antwortet nicht."));
    }, timeoutMs);
    state.pending.set(requestId, { resolve, reject, timeout });
    state.port.postMessage({
      schema_version: "unibot-companion-message-v1",
      request_id: requestId,
      type,
      payload
    });
  });
}

async function startSession() {
  if (state.contract) throw new Error("Vor einer neuen Sitzung die beendete Sitzung löschen.");
  if (!elements.practiceBoundary.checked) {
    throw new Error(state.mode === "rehearsal"
      ? "Bitte zuerst die künstliche Simulation und den Status nicht freigegeben bestätigen."
      : "Bitte zuerst bestätigen: Diese Sitzung ist freiwillige Übung, keine Prüfung.");
  }
  if (state.mode === "rehearsal") {
    if (!state.notebookId) throw new Error("Zuerst das veröffentlichte künstliche Notebook importieren.");
    const response = await nativeRequest("rehearsal.start", { notebook_id: state.notebookId }, 30000);
    state.contract = response.contract;
    state.rehearsalId = response.rehearsal_contract.rehearsal_id;
    state.rehearsalStatus = "active";
    state.rehearsalBrowserBinding = response.rehearsal.browser_binding;
    state.sessionActive = true;
    state.lastReview = null;
    setConnection("Simulation aktiv", "ready");
    elements.sessionOutput.textContent = [
      "Künstliche Prüfungssimulation aktiv",
      "Hilfestufen: A0-A2",
      "Netz: lokal gesperrt und überwacht",
      "Prüfungseinsatz: nicht freigegeben"
    ].join("\n");
    syncSessionControls();
    return;
  }
  const mode = selectedAssistanceMode();
  const response = await nativeRequest("session.start", {
    pseudonym: elements.pseudonym.value.trim() || "Lernende Person",
    course_id: elements.courseId.value.trim() || "python-practice",
    assistance_mode: mode,
    fixed_help_level: elements.fixedHelpLevel.value,
    max_help_level: elements.maxHelpLevel.value,
    practice_scope: "practice_only",
    practice_scope_confirmed: true,
    planned_task_count: 1
  });
  state.contract = response.contract;
  state.sessionActive = true;
  elements.practiceBoundary.checked = response.contract.practice_scope === "practice_only";
  state.lastReview = null;
  setConnection("Sitzung aktiv", "ready");
  elements.sessionOutput.textContent = [
    `${mode === "fixed" ? "Feste" : "Adaptive"} Hilfe`,
    `Maximum: ${response.contract.max_help_level}`,
    "Hilfen werden lokal verarbeitet."
  ].join("\n");
  syncSessionControls();
}

async function captureCell() {
  if (!state.sessionActive) throw new Error("Lernsitzung zuerst starten");
  const tabs = globalThis.chrome?.tabs;
  if (!tabs) throw new Error("Browser-Zellwahl ist nicht verfügbar.");
  const [tab] = await tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) throw new Error("Kein aktiver Notebook-Tab");
  const response = await tabs.sendMessage(tab.id, { type: "UNIBOT_GET_SELECTION" });
  state.selectedCell = response.selectedCell || null;
  if (!state.selectedCell?.source || state.selectedCell.confidence === "low") {
    throw new Error("Zelle nicht eindeutig erkannt. Bitte Quelltext markieren und erneut erfassen.");
  }
  elements.cellMeta.textContent = [
    state.selectedCell.adapter,
    state.selectedCell.adapterVersion || "adapter-v1",
    state.selectedCell.cellType,
    state.selectedCell.cellIndex >= 0 ? `Zelle ${state.selectedCell.cellIndex}` : "Auswahl",
    `Sicherheit ${state.selectedCell.confidence}`
  ].join(" | ");
  if (!elements.task.value.trim()) elements.task.value = response.title || "Notebook-Aufgabe";
}

async function importNotebook() {
  const source = elements.notebookSource.value.trim();
  const file = elements.notebookFile.files?.[0];
  if (source && file) throw new Error("Bitte URL oder lokale Datei auswählen, nicht beides.");
  let response;
  if (file) {
    if (!file.name.toLowerCase().endsWith(".ipynb")) throw new Error("Nur .ipynb-Dateien sind erlaubt.");
    if (file.size <= 0 || file.size > MAX_NOTEBOOK_BYTES) throw new Error("Das Notebook ist zu groß oder leer.");
    const buffer = await file.arrayBuffer();
    const uploadId = Array.from(crypto.getRandomValues(new Uint8Array(16)), (value) => value.toString(16).padStart(2, "0")).join("");
    const digest = await crypto.subtle.digest("SHA-256", buffer);
    const sourceSha256 = Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, "0")).join("");
    const totalChunks = Math.ceil(file.size / UPLOAD_CHUNK_BYTES);
    let uploadStarted = false;
    try {
      await nativeRequest("notebook.upload.start", {
        upload_id: uploadId,
        source_label: file.name,
        source_sha256: sourceSha256,
        total_bytes: file.size,
        total_chunks: totalChunks
      });
      uploadStarted = true;
      const bytes = new Uint8Array(buffer);
      for (let index = 0; index < totalChunks; index += 1) {
        const chunk = bytes.slice(index * UPLOAD_CHUNK_BYTES, Math.min(bytes.length, (index + 1) * UPLOAD_CHUNK_BYTES));
        let binary = "";
        for (let offset = 0; offset < chunk.length; offset += 1) binary += String.fromCharCode(chunk[offset]);
        await nativeRequest("notebook.upload.chunk", {
          upload_id: uploadId,
          chunk_index: index,
          data: btoa(binary)
        });
      }
      response = await nativeRequest("notebook.upload.finish", { upload_id: uploadId });
    } catch (error) {
      if (uploadStarted) await nativeRequest("notebook.upload.abort", { upload_id: uploadId }).catch(() => {});
      throw error;
    }
  } else {
    if (!source) throw new Error("Bitte eine öffentliche URL oder eine lokale .ipynb-Datei auswählen.");
    response = await nativeRequest("notebook.import", { source });
  }
  state.notebookId = response.notebook_id;
  state.notebookSourceSha256 = response.manifest.source_sha256 || "";
  elements.openGateway.disabled = state.mode === "rehearsal";
  elements.notebookOutput.textContent = [
    "Bereinigtes Notebook bereit",
    `Zellen: ${response.manifest.cell_count}`,
    `Entfernte Ausgaben: ${response.manifest.outputs_removed}`,
    `Hash: ${response.manifest.sanitized_sha256.slice(0, 16)}`
  ].join("\n");
  syncSessionControls();
}

async function openGateway() {
  if (!state.notebookId) throw new Error("Notebook zuerst importieren");
  const response = await nativeRequest("gateway.launch", { notebook_id: state.notebookId });
  state.gatewayActive = true;
  elements.notebookOutput.textContent = [
    "Lokales Jupyter gestartet",
    `Notebook: ${response.gateway.artifact_name}`,
    "Terminal deaktiviert. Pruefungseinsatz nicht freigegeben."
  ].join("\n");
  syncSessionControls();
}

async function stopGateway() {
  const response = await nativeRequest("gateway.stop");
  state.gatewayActive = false;
  elements.notebookOutput.textContent = response.status === "stopped"
    ? "Lokales Jupyter-Gateway wurde gestoppt."
    : "Kein lokales Jupyter-Gateway aktiv.";
  syncSessionControls();
}

function renderTurn(turn) {
  const sources = (turn.source_anchors || []).map((source) => source.label).join(", ");
  const boundary = (turn.blocked_reasons || []).length ? `\nGrenze: ${turn.blocked_reasons.join(", ")}` : "";
  return [
    `${turn.effective_help_level} | ${turn.hint_markdown}`,
    sources ? `Quelle: ${sources}` : "",
    `Hilfebudget dieser Aufgabe: ${turn.assistance_points_for_task} Punkte (+${turn.assistance_points_delta})`,
    `Naechste erlaubte Stufe: ${turn.next_allowed_help_level}${boundary}`,
    turn.accessibility_used ? "Barrierearme Darstellung aktiviert: größere Bedienelemente und Abstände (kostenneutral)" : ""
  ].filter(Boolean).join("\n");
}

async function requestHelp() {
  if (!state.contract || !state.sessionActive) throw new Error("Lernsitzung zuerst starten");
  if (!elements.task.value.trim() || !elements.attempt.value.trim()) {
    throw new Error("Lernziel und eigener Schritt sind erforderlich");
  }
  const response = await nativeRequest("tutor.turn", {
    session_id: state.contract.session_id,
    task: elements.task.value.trim().slice(0, 4000),
    learner_attempt: elements.attempt.value.trim().slice(0, 4000),
    cell_context: (state.selectedCell?.source || "").slice(0, 12000),
    cell_type: state.selectedCell?.cellType || "none",
    cell_index: state.selectedCell?.cellIndex ?? -1,
    adapter: state.selectedCell?.adapter || "none",
    adapter_version: state.selectedCell?.adapterVersion || "adapter-v1",
    requested_help_level: selectedHelpLevel(),
    confirm_escalation: elements.confirmEscalation.checked,
    accessibility_used: elements.accessibilitySupport.checked
  });
  elements.helpOutput.textContent = renderTurn(response.turn);
  elements.confirmEscalation.checked = false;
}

function renderReview(report) {
  const transfer = report.transfer_tasks?.[0];
  const transferStatus = transfer?.status === "recorded"
    ? "auf Hashbasis erfasst (nicht bewertet)"
    : transfer?.status === "locked_until_session_stop"
      ? "nach Sitzungsende verfügbar"
      : "freiwillig noch nicht beantwortet";
  return [
    `Ereignisse: ${report.event_count || 0}`,
    `Eigene Versuche: ${report.own_attempt_count || 0}`,
    `Hilfestufen: ${JSON.stringify(report.by_help_level || {})}`,
    `Hilfebudget genutzt: ${report.assistance_points_used || 0} Punkte`,
    "Barrierearme Darstellung: lokal und kostenneutral; Nutzung wird nicht protokolliert",
    `Transferaufgabe ohne Hilfe: ${transferStatus}`,
    "Keine automatische Note oder KI-Erkennung",
    "Pruefungseinsatz: nicht freigegeben"
  ].join("\n");
}

async function showTransferTask() {
  if (!state.contract || state.sessionActive) throw new Error("Transferaufgabe erst nach Sitzungsende verfügbar");
  const response = await nativeRequest("session.transfer.prompt");
  state.transferTask = response.transfer;
  elements.transferPrompt.textContent = response.transfer.prompt;
  elements.transferPrompt.hidden = false;
  elements.transferAnswer.value = "";
  elements.transferAnswer.focus();
  syncSessionControls();
}

async function recordTransfer() {
  if (!state.transferTask) throw new Error("Transferaufgabe zuerst anzeigen");
  const answer = elements.transferAnswer.value.trim();
  if (!answer) throw new Error("Bitte zuerst einen eigenen Transfer-Versuch eintragen");
  const response = await nativeRequest("session.transfer.record", {
    task_id: state.transferTask.task_id,
    answer: answer.slice(0, 4000)
  });
  state.lastReview = response.report;
  state.transferTask = null;
  elements.transferPrompt.textContent = "Transfer-Versuch wurde nur als Hash gespeichert und nicht bewertet.";
  elements.transferAnswer.value = "";
  elements.reviewOutput.textContent = renderReview(state.lastReview);
  syncSessionControls();
}

async function refreshReview() {
  if (!state.contract) throw new Error("Lernsitzung zuerst starten");
  const response = await nativeRequest("session.report");
  state.lastReview = response.report;
  resetExportPreview();
  elements.reviewOutput.textContent = renderReview(state.lastReview);
  syncSessionControls();
}

async function stopSession() {
  if (!state.contract || !state.sessionActive) throw new Error("Keine aktive Lernsitzung ausgewählt");
  const response = await nativeRequest("session.stop");
  state.sessionActive = false;
  state.lastReview = response.report;
  elements.sessionOutput.textContent = "Lernsitzung beendet. Der Rückblick bleibt bis zur Löschung lokal verfügbar.";
  elements.helpOutput.textContent = "Lernsitzung beendet. Für weitere Hilfe eine neue Sitzung starten.";
  elements.reviewOutput.textContent = renderReview(state.lastReview);
  resetExportPreview();
  setConnection("Sitzung beendet", "ready");
  syncSessionControls();
}

async function finishRehearsal() {
  if (state.mode !== "rehearsal" || !state.rehearsalId || !["active", "frozen"].includes(state.rehearsalStatus)) {
    throw new Error("Keine abschließbare künstliche Prüfungssimulation.");
  }
  if (state.rehearsalStatus === "active") {
    const tabs = globalThis.chrome?.tabs;
    if (!tabs) throw new Error("Lokales Jupyter-Speichern ist nicht verfügbar.");
    const [tab] = await tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) throw new Error("Kein aktiver lokaler Jupyter-Tab.");
    const saved = await tabs.sendMessage(tab.id, {
      type: "UNIBOT_SAVE_NOTEBOOK",
      expected_binding: state.rehearsalBrowserBinding
    });
    if (!saved?.saved || saved.browser_binding_matched !== true || saved.notebook_content_read !== false) {
      throw new Error("Jupyter konnte den aktuellen Stand nicht eindeutig speichern. Die Simulation bleibt aktiv.");
    }
  }
  const response = await nativeRequest(
    "rehearsal.finish",
    {
      rehearsal_id: state.rehearsalId,
      browser_save_confirmed: true,
      browser_binding: state.rehearsalBrowserBinding
    },
    130000
  );
  state.sessionActive = false;
  state.rehearsalStatus = "exported";
  state.lastReview = response.report;
  setConnection("Simulation abgeschlossen", "ready");
  elements.sessionOutput.textContent = [
    "Simulation abgeschlossen und lokal gespeichert",
    `Abschlussbeleg: ${response.receipt.receipt_hash.slice(0, 16)}`,
    "Automatische Abgabe: nein",
    "Prüfungseinsatz: nicht freigegeben"
  ].join("\n");
  elements.reviewOutput.textContent = renderReview(state.lastReview);
  resetExportPreview();
  syncSessionControls();
}

function resetExportPreview() {
  elements.exportPreview.hidden = true;
  elements.exportConfirmRow.hidden = true;
  elements.confirmExport.checked = false;
  elements.exportReview.disabled = true;
  elements.exportPreview.textContent = "Noch keine Exportvorschau.";
}

function showExportPreview() {
  if (!state.lastReview) throw new Error("Rueckblick zuerst aktualisieren");
  elements.exportPreview.textContent = [
    "Exportvorschau: Es werden nur Metadaten und Hashes exportiert:",
    "Enthalten: Hilfestufen, eigene Versuchsanzahl, Quellen-IDs, Zeitpunkte, Pseudonym, Kurskennung und Vertrags-/Berichtshash.",
    "Nicht enthalten: Zelltext, eigener Versuchstext, Transferantwort, Tutortranskript, lokale Pfade, Tokens, Note, KI-Erkennung oder die Nutzung der barrierearmen Darstellung.",
    "Aufbewahrung: lokale Sitzungsmetadaten bis zu 7 Tage; eine von dir gespeicherte Exportdatei loescht UniBot nicht automatisch.",
    "Weitergabe: freiwillig und erst nach deiner eigenen Pruefung."
  ].join("\n");
  elements.exportPreview.hidden = false;
  elements.exportConfirmRow.hidden = false;
  elements.confirmExport.checked = false;
  elements.exportReview.disabled = true;
}

function exportReview() {
  if (!state.lastReview || elements.exportPreview.hidden || !elements.confirmExport.checked) {
    throw new Error("Exportvorschau anzeigen und freiwillig bestaetigen");
  }
  const blob = new Blob([JSON.stringify(state.lastReview, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "unibot-lernbericht-metadaten.json";
  link.click();
  URL.revokeObjectURL(url);
  elements.reviewOutput.textContent = "Export erstellt. Weitergabe bleibt freiwillig und menschlich kontrolliert.";
}

async function deleteSession() {
  if (!state.contract) throw new Error("Keine Lernsitzung ausgewählt");
  if (!window.confirm("Lernsitzung und lokale Metadaten sofort löschen?")) return;
  if (state.mode === "rehearsal") {
    await nativeRequest("rehearsal.delete", { rehearsal_id: state.rehearsalId });
  } else {
    await nativeRequest("session.delete", { session_id: state.contract.session_id });
  }
  state.contract = null;
  state.sessionActive = false;
  state.rehearsalId = "";
  state.rehearsalStatus = "";
  state.rehearsalBrowserBinding = null;
  state.notebookId = "";
  state.notebookSourceSha256 = "";
  state.mode = "practice";
  elements.sessionMode.value = "practice";
  elements.practiceBoundary.checked = false;
  state.lastReview = null;
  state.transferTask = null;
  state.selectedCell = null;
  elements.transferPrompt.hidden = true;
  elements.transferAnswer.value = "";
  elements.sessionOutput.textContent = "Lernsitzung und lokale Metadaten wurden gelöscht.";
  elements.reviewOutput.textContent = "Keine Sitzungsdaten.";
  elements.helpOutput.textContent = "Noch keine Anfrage.";
  resetExportPreview();
  syncModePresentation();
  setConnection("Lokal bereit", "ready");
  syncSessionControls();
}

function guarded(action, output) {
  return async () => {
    try {
      await action();
    } catch (error) {
      output.textContent = error.message;
    }
  };
}

const tabButtons = Array.from(document.querySelectorAll("nav button[data-tab]"));

function selectTab(button) {
    tabButtons.forEach((item) => {
      item.setAttribute("aria-selected", String(item === button));
      item.setAttribute("tabindex", item === button ? "0" : "-1");
    });
    button.focus();
    document.querySelectorAll("[data-panel]").forEach((panel) => {
      panel.hidden = panel.id !== button.dataset.tab;
    });
}

tabButtons.forEach((button, index) => {
  button.addEventListener("click", () => selectTab(button));
  button.addEventListener("keydown", (event) => {
    const movement = {
      ArrowRight: 1,
      ArrowDown: 1,
      ArrowLeft: -1,
      ArrowUp: -1
    }[event.key];
    let nextIndex = index;
    if (movement) nextIndex = (index + movement + tabButtons.length) % tabButtons.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = tabButtons.length - 1;
    if (nextIndex === index) return;
    event.preventDefault();
    selectTab(tabButtons[nextIndex]);
  });
});

elements.startSession.addEventListener("click", guarded(startSession, elements.sessionOutput));
elements.stopSession.addEventListener("click", guarded(stopSession, elements.sessionOutput));
elements.finishRehearsal.addEventListener("click", guarded(finishRehearsal, elements.sessionOutput));
elements.sessionMode.addEventListener("change", () => {
  elements.practiceBoundary.checked = false;
  syncModePresentation();
});
elements.importNotebook.addEventListener("click", guarded(importNotebook, elements.notebookOutput));
elements.openGateway.addEventListener("click", guarded(openGateway, elements.notebookOutput));
elements.stopGateway.addEventListener("click", guarded(stopGateway, elements.notebookOutput));
elements.capture.addEventListener("click", guarded(captureCell, elements.helpOutput));
elements.ask.addEventListener("click", guarded(requestHelp, elements.helpOutput));
elements.refreshReview.addEventListener("click", guarded(refreshReview, elements.reviewOutput));
elements.showTransferTask.addEventListener("click", guarded(showTransferTask, elements.transferPrompt));
elements.transferAnswer.addEventListener("input", syncSessionControls);
elements.recordTransfer.addEventListener("click", guarded(recordTransfer, elements.reviewOutput));
elements.showExportPreview.addEventListener("click", guarded(showExportPreview, elements.exportPreview));
elements.confirmExport.addEventListener("change", () => {
  elements.exportReview.disabled = !elements.confirmExport.checked || elements.exportPreview.hidden;
});
elements.accessibilitySupport.addEventListener("change", () => {
  applyAccessibilityMode();
  persistAccessibilityPreference();
});
elements.exportReview.addEventListener("click", guarded(exportReview, elements.reviewOutput));
elements.deleteSession.addEventListener("click", guarded(deleteSession, elements.reviewOutput));

connectCompanion();
resetExportPreview();
restoreAccessibilityPreference();
syncModePresentation();
