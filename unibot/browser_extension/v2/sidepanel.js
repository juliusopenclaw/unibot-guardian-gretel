const NATIVE_HOST = "de.gretel.unibot_companion";

const state = {
  port: null,
  pending: new Map(),
  requestCounter: 0,
  contract: null,
  notebookId: "",
  selectedCell: null,
  lastReview: null
};

const elements = {
  connectionStatus: document.querySelector("#connectionStatus"),
  pseudonym: document.querySelector("#pseudonym"),
  courseId: document.querySelector("#courseId"),
  maxHelpLevel: document.querySelector("#maxHelpLevel"),
  fixedHelpLevel: document.querySelector("#fixedHelpLevel"),
  startSession: document.querySelector("#startSession"),
  sessionOutput: document.querySelector("#sessionOutput"),
  notebookSource: document.querySelector("#notebookSource"),
  importNotebook: document.querySelector("#importNotebook"),
  openGateway: document.querySelector("#openGateway"),
  notebookOutput: document.querySelector("#notebookOutput"),
  capture: document.querySelector("#capture"),
  cellMeta: document.querySelector("#cellMeta"),
  task: document.querySelector("#task"),
  attempt: document.querySelector("#attempt"),
  confirmEscalation: document.querySelector("#confirmEscalation"),
  ask: document.querySelector("#ask"),
  helpOutput: document.querySelector("#helpOutput"),
  refreshReview: document.querySelector("#refreshReview"),
  exportReview: document.querySelector("#exportReview"),
  reviewOutput: document.querySelector("#reviewOutput")
};

function setConnection(text, status) {
  elements.connectionStatus.textContent = text;
  elements.connectionStatus.dataset.state = status;
}

function selectedHelpLevel() {
  return document.querySelector("input[name='helpLevel']:checked").value;
}

function selectedAssistanceMode() {
  return document.querySelector("input[name='assistanceMode']:checked").value;
}

function connectCompanion() {
  if (!chrome.runtime?.connectNative) {
    setConnection("Begleiter fehlt", "error");
    elements.sessionOutput.textContent = "UniBot Companion ist nicht installiert.";
    return;
  }
  state.port = chrome.runtime.connectNative(NATIVE_HOST);
  state.port.onMessage.addListener((message) => {
    const request = state.pending.get(message.request_id);
    if (!request) return;
    clearTimeout(request.timeout);
    state.pending.delete(message.request_id);
    if (message.error) request.reject(new Error(message.error));
    else request.resolve(message);
  });
  state.port.onDisconnect.addListener(() => {
    const message = chrome.runtime.lastError?.message || "Lokaler Begleiter wurde getrennt.";
    for (const request of state.pending.values()) {
      clearTimeout(request.timeout);
      request.reject(new Error(message));
    }
    state.pending.clear();
    state.port = null;
    state.contract = null;
    setConnection("Begleiter getrennt", "error");
  });
  nativeRequest("companion.status").then(() => {
    setConnection("Lokal bereit", "ready");
    elements.sessionOutput.textContent = "Begleiter bereit. Lernsitzung starten.";
  }).catch((error) => {
    setConnection("Begleiter fehlt", "error");
    elements.sessionOutput.textContent = error.message;
  });
}

function nativeRequest(type, payload = {}) {
  if (!state.port) return Promise.reject(new Error("UniBot Companion ist nicht verbunden."));
  const requestId = `unibot-${Date.now()}-${++state.requestCounter}`;
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      state.pending.delete(requestId);
      reject(new Error("Der lokale Begleiter antwortet nicht."));
    }, 10000);
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
  const mode = selectedAssistanceMode();
  const response = await nativeRequest("session.start", {
    pseudonym: elements.pseudonym.value.trim() || "Lernende Person",
    course_id: elements.courseId.value.trim() || "python-practice",
    assistance_mode: mode,
    fixed_help_level: elements.fixedHelpLevel.value,
    max_help_level: elements.maxHelpLevel.value,
    planned_task_count: 1
  });
  state.contract = response.contract;
  setConnection("Sitzung aktiv", "ready");
  elements.sessionOutput.textContent = [
    `${mode === "fixed" ? "Feste" : "Adaptive"} Hilfe`,
    `Maximum: ${response.contract.max_help_level}`,
    "Hilfen werden lokal verarbeitet."
  ].join("\n");
}

async function captureCell() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) throw new Error("Kein aktiver Notebook-Tab");
  const response = await chrome.tabs.sendMessage(tab.id, { type: "UNIBOT_GET_SELECTION" });
  state.selectedCell = response.selectedCell || null;
  if (!state.selectedCell?.source || state.selectedCell.confidence === "low") {
    throw new Error("Zelle nicht eindeutig erkannt. Bitte Quelltext markieren und erneut erfassen.");
  }
  elements.cellMeta.textContent = [
    state.selectedCell.adapter,
    state.selectedCell.cellType,
    state.selectedCell.cellIndex >= 0 ? `Zelle ${state.selectedCell.cellIndex}` : "Auswahl",
    `Sicherheit ${state.selectedCell.confidence}`
  ].join(" | ");
  if (!elements.task.value.trim()) elements.task.value = response.title || "Notebook-Aufgabe";
}

async function importNotebook() {
  const response = await nativeRequest("notebook.import", {
    source: elements.notebookSource.value.trim()
  });
  state.notebookId = response.notebook_id;
  elements.openGateway.disabled = false;
  elements.notebookOutput.textContent = [
    "Bereinigtes Notebook bereit",
    `Zellen: ${response.manifest.cell_count}`,
    `Entfernte Ausgaben: ${response.manifest.outputs_removed}`,
    `Hash: ${response.manifest.sanitized_sha256.slice(0, 16)}`
  ].join("\n");
}

async function openGateway() {
  if (!state.notebookId) throw new Error("Notebook zuerst importieren");
  const response = await nativeRequest("gateway.launch", { notebook_id: state.notebookId });
  elements.notebookOutput.textContent = [
    "Lokales Jupyter gestartet",
    `Notebook: ${response.gateway.artifact_name}`,
    "Terminal deaktiviert. Pruefungseinsatz nicht freigegeben."
  ].join("\n");
}

function renderTurn(turn) {
  const sources = (turn.source_anchors || []).map((source) => source.label).join(", ");
  const boundary = (turn.blocked_reasons || []).length ? `\nGrenze: ${turn.blocked_reasons.join(", ")}` : "";
  return [
    `${turn.effective_help_level} | ${turn.hint_markdown}`,
    sources ? `Quelle: ${sources}` : "",
    `Hilfebudget dieser Aufgabe: ${turn.assistance_points_for_task} Punkte (+${turn.assistance_points_delta})`,
    `Naechste erlaubte Stufe: ${turn.next_allowed_help_level}${boundary}`
  ].filter(Boolean).join("\n");
}

async function requestHelp() {
  if (!state.contract) throw new Error("Lernsitzung zuerst starten");
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
    requested_help_level: selectedHelpLevel(),
    confirm_escalation: elements.confirmEscalation.checked
  });
  elements.helpOutput.textContent = renderTurn(response.turn);
  elements.confirmEscalation.checked = false;
}

function renderReview(report) {
  return [
    `Ereignisse: ${report.event_count || 0}`,
    `Eigene Versuche: ${report.own_attempt_count || 0}`,
    `Hilfestufen: ${JSON.stringify(report.by_help_level || {})}`,
    `Hilfebudget genutzt: ${report.assistance_points_used || 0} Punkte`,
    "Keine automatische Note oder KI-Erkennung",
    "Pruefungseinsatz: nicht freigegeben"
  ].join("\n");
}

async function refreshReview() {
  if (!state.contract) throw new Error("Lernsitzung zuerst starten");
  const response = await nativeRequest("session.report");
  state.lastReview = response.report;
  elements.reviewOutput.textContent = renderReview(state.lastReview);
}

function exportReview() {
  if (!state.lastReview) throw new Error("Rueckblick zuerst aktualisieren");
  const blob = new Blob([JSON.stringify(state.lastReview, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "unibot-lernbericht-metadaten.json";
  link.click();
  URL.revokeObjectURL(url);
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

document.querySelectorAll("nav button[data-tab]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("nav button[data-tab]").forEach((item) => {
      item.setAttribute("aria-selected", String(item === button));
    });
    document.querySelectorAll("[data-panel]").forEach((panel) => {
      panel.hidden = panel.id !== button.dataset.tab;
    });
  });
});

elements.startSession.addEventListener("click", guarded(startSession, elements.sessionOutput));
elements.importNotebook.addEventListener("click", guarded(importNotebook, elements.notebookOutput));
elements.openGateway.addEventListener("click", guarded(openGateway, elements.notebookOutput));
elements.capture.addEventListener("click", guarded(captureCell, elements.helpOutput));
elements.ask.addEventListener("click", guarded(requestHelp, elements.helpOutput));
elements.refreshReview.addEventListener("click", guarded(refreshReview, elements.reviewOutput));
elements.exportReview.addEventListener("click", guarded(exportReview, elements.reviewOutput));

connectCompanion();
