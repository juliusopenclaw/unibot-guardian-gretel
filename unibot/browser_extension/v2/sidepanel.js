const NATIVE_HOST = "de.gretel.unibot_companion";
const MAX_NOTEBOOK_BYTES = 10 * 1024 * 1024;
const UPLOAD_CHUNK_BYTES = 32 * 1024;

const state = {
  port: null,
  pending: new Map(),
  requestCounter: 0,
  contract: null,
  notebookId: "",
  selectedCell: null,
  lastReview: null,
  reconnectTimer: null,
  reconnectAttempt: 0,
  connecting: false
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
  ask: document.querySelector("#ask"),
  helpOutput: document.querySelector("#helpOutput"),
  refreshReview: document.querySelector("#refreshReview"),
  exportReview: document.querySelector("#exportReview"),
  deleteSession: document.querySelector("#deleteSession"),
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

function scheduleReconnect() {
  if (state.reconnectTimer || state.port || state.connecting || !chrome.runtime?.connectNative) return;
  const delay = Math.min(5000, 500 * (2 ** Math.min(state.reconnectAttempt, 3)));
  state.reconnectAttempt += 1;
  state.reconnectTimer = setTimeout(() => {
    state.reconnectTimer = null;
    connectCompanion();
  }, delay);
}

function connectCompanion() {
  if (state.port || state.connecting) return;
  if (!chrome.runtime?.connectNative) {
    setConnection("Begleiter fehlt", "error");
    elements.sessionOutput.textContent = "UniBot Companion ist nicht installiert.";
    return;
  }
  state.connecting = true;
  let port;
  try {
    port = chrome.runtime.connectNative(NATIVE_HOST);
  } catch (error) {
    state.connecting = false;
    setConnection("Begleiter fehlt", "error");
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
    const message = chrome.runtime.lastError?.message || "Lokaler Begleiter wurde getrennt.";
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
    setConnection("Lokal bereit", "ready");
    state.reconnectAttempt = 0;
    state.connecting = false;
    if (status.resume_available) {
      const resumed = await nativeRequest("session.resume", {
        session_id: status.active_session_metadata?.session_id || ""
      });
      state.contract = resumed.contract;
      state.lastReview = resumed.report;
      setConnection("Sitzung fortgesetzt", "ready");
      elements.sessionOutput.textContent = "Vorhandene Lernsitzung wurde lokal fortgesetzt.";
      elements.reviewOutput.textContent = renderReview(state.lastReview);
    } else {
      elements.sessionOutput.textContent = "Begleiter bereit. Lernsitzung starten.";
    }
    const gateway = await nativeRequest("gateway.status");
    if (gateway.status === "active") {
      elements.stopGateway.disabled = false;
      elements.notebookOutput.textContent = "Lokales Jupyter-Gateway ist aktiv.";
    }
  }).catch((error) => {
    state.connecting = false;
    setConnection("Begleiter fehlt", "error");
    elements.sessionOutput.textContent = error.message;
    if (state.port) {
      state.port.disconnect?.();
    }
    scheduleReconnect();
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
  elements.stopGateway.disabled = false;
  elements.notebookOutput.textContent = [
    "Lokales Jupyter gestartet",
    `Notebook: ${response.gateway.artifact_name}`,
    "Terminal deaktiviert. Pruefungseinsatz nicht freigegeben."
  ].join("\n");
}

async function stopGateway() {
  const response = await nativeRequest("gateway.stop");
  elements.stopGateway.disabled = true;
  elements.notebookOutput.textContent = response.status === "stopped"
    ? "Lokales Jupyter-Gateway wurde gestoppt."
    : "Kein lokales Jupyter-Gateway aktiv.";
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

async function deleteSession() {
  if (!state.contract) throw new Error("Keine Lernsitzung ausgewählt");
  if (!window.confirm("Lernsitzung und lokale Metadaten sofort löschen?")) return;
  await nativeRequest("session.delete", { session_id: state.contract.session_id });
  state.contract = null;
  state.lastReview = null;
  state.selectedCell = null;
  elements.sessionOutput.textContent = "Lernsitzung und lokale Metadaten wurden gelöscht.";
  elements.reviewOutput.textContent = "Keine Sitzungsdaten.";
  elements.helpOutput.textContent = "Noch keine Anfrage.";
  setConnection("Lokal bereit", "ready");
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
      item.setAttribute("tabindex", item === button ? "0" : "-1");
    });
    button.focus();
    document.querySelectorAll("[data-panel]").forEach((panel) => {
      panel.hidden = panel.id !== button.dataset.tab;
    });
  });
});

elements.startSession.addEventListener("click", guarded(startSession, elements.sessionOutput));
elements.importNotebook.addEventListener("click", guarded(importNotebook, elements.notebookOutput));
elements.openGateway.addEventListener("click", guarded(openGateway, elements.notebookOutput));
elements.stopGateway.addEventListener("click", guarded(stopGateway, elements.notebookOutput));
elements.capture.addEventListener("click", guarded(captureCell, elements.helpOutput));
elements.ask.addEventListener("click", guarded(requestHelp, elements.helpOutput));
elements.refreshReview.addEventListener("click", guarded(refreshReview, elements.reviewOutput));
elements.exportReview.addEventListener("click", guarded(exportReview, elements.reviewOutput));
elements.deleteSession.addEventListener("click", guarded(deleteSession, elements.reviewOutput));

connectCompanion();
