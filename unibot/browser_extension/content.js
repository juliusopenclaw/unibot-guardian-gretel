(() => {
  const ROOT_ID = "unibot-guardian-banner";
  const contentScriptBoundaryClaimAlignment = Object.freeze({
    schema_version: "unibot-browser-manifest-content-boundary-claim-alignment-v1",
    status: "ready",
    practice_overlay_only: true,
    content_script_scope: "visible selection and practice banner only",
    sidepanel_handoff_required: true,
    no_exam_security_claim: true,
    manual_publication_claim_contract: {
      expected_schema_version: "unibot-browser-manifest-content-boundary-claim-alignment-v1",
      required_sidepanel_claim_schema_version: "unibot-browser-extension-release-review-board-claim-alignment-v1",
      required_local_demo_claim_schema_version: "unibot-local-demo-release-review-board-claim-alignment-v1",
      required_readiness_check_ids: [
        "browser_manifest_content_boundary",
        "browser_extension_demo_handoff",
        "local_demo_run",
        "demo_feedback_contract",
        "publication_package",
        "public_safety"
      ],
      required_human_gates: [
        "human_review_before_github_create",
        "human_submission_review_required",
        "public_safety_required"
      ],
      required_manifest_permissions: ["activeTab", "nativeMessaging", "sidePanel"],
      required_host_permission_policy: "Colab, localhost, and loopback practice surfaces only",
      use: "Content-script and manifest boundary remains practice-only, delegates decisions to the sidepanel, and never claims exam security."
    },
    blocked_claims: ["exam clearance", "official grading", "proctoring", "KI-detection evidence"],
    public_language: "Practice overlay only - sidepanel review required before public or institutional claims."
  });

  function ensureBanner() {
    if (document.getElementById(ROOT_ID)) {
      return;
    }
    const banner = document.createElement("aside");
    banner.id = ROOT_ID;
    banner.textContent = "UniBot Guardian Lernmantel aktiv";
    banner.style.cssText = [
      "position:fixed",
      "right:12px",
      "bottom:12px",
      "z-index:2147483647",
      "max-width:320px",
      "padding:10px 12px",
      "font:13px/1.35 system-ui,sans-serif",
      "color:#111827",
      "background:#fef3c7",
      "border:1px solid #f59e0b",
      "border-radius:8px",
      "box-shadow:0 8px 22px rgba(0,0,0,.16)"
    ].join(";");
    document.documentElement.appendChild(banner);
  }

  function collectVisibleSelection() {
    const selection = window.getSelection();
    return selection ? selection.toString().trim() : "";
  }

  function sourceFromCell(cell) {
    const input = cell.querySelector(
      ".cm-content, .CodeMirror-code, .input_area, [contenteditable='true'], textarea, pre"
    );
    return input ? (input.innerText || input.textContent || input.value || "").trim().slice(0, 12000) : "";
  }

  function candidateCells(selectors) {
    const byCell = new Map();
    for (const selector of selectors) {
      for (const cell of document.querySelectorAll(selector)) {
        const existing = byCell.get(cell);
        if (existing) {
          existing.selectors.push(selector);
        } else {
          byCell.set(cell, { cell, selectors: [selector] });
        }
      }
    }
    return Array.from(byCell.values());
  }

  function cellPayload(candidate, { adapter, adapterVersion, cells, confidence }) {
    const cell = candidate.cell;
    const source = sourceFromCell(cell);
    const cellIndex = cells.indexOf(cell);
    const classText = `${cell.className || ""} ${cell.getAttribute("data-cell-type") || ""}`.toLowerCase();
    return {
      source,
      cellType: classText.includes("markdown") ? "markdown" : "code",
      cellIndex,
      adapter,
      adapterVersion,
      selector: candidate.selectors.join(","),
      confidence: source && cellIndex >= 0 ? confidence : "low"
    };
  }

  function ambiguousPayload(adapter, adapterVersion, candidates) {
    return {
      source: "",
      cellType: "unknown",
      cellIndex: -1,
      adapter,
      adapterVersion,
      selector: candidates.map((candidate) => candidate.selectors.join(",")).join(" | "),
      confidence: "low",
      ambiguity: "multiple_active_cells"
    };
  }

  function resolveCellCandidates({ adapter, adapterVersion, selectors, cells, confidence }) {
    const candidates = candidateCells(selectors);
    if (candidates.length === 0) return null;
    if (candidates.length !== 1) return ambiguousPayload(adapter, adapterVersion, candidates);
    return cellPayload(candidates[0], { adapter, adapterVersion, cells, confidence });
  }

  function jupyterAdapter() {
    const selectors = [".jp-Notebook-cell.jp-mod-active", ".jp-CodeCell.jp-mod-active", ".cell.selected"];
    return resolveCellCandidates({
      adapter: "jupyterlab",
      adapterVersion: "jupyterlab-v1",
      selectors,
      cells: Array.from(document.querySelectorAll(".jp-Notebook-cell, .cell")),
      confidence: "high"
    });
  }

  function colabAdapter() {
    const selectors = ["colab-code-cell.focused", "colab-text-cell.focused", "[role='listitem'][aria-selected='true']"];
    return resolveCellCandidates({
      adapter: "colab",
      adapterVersion: "colab-v1",
      selectors,
      cells: Array.from(document.querySelectorAll("colab-code-cell, colab-text-cell")),
      confidence: "high"
    });
  }

  function selectionAdapter() {
    const source = collectVisibleSelection().slice(0, 12000);
    return {
      source,
      cellType: "selection",
      cellIndex: -1,
      adapter: "manual_selection",
      adapterVersion: "manual-v1",
      selector: "",
      confidence: source ? "medium" : "low"
    };
  }

  function activeNotebookCell() {
    return colabAdapter() || jupyterAdapter() || selectionAdapter();
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (!message || message.type !== "UNIBOT_GET_SELECTION") {
      return false;
    }
    const cell = activeNotebookCell();
    sendResponse({
      selectedText: collectVisibleSelection(),
      selectedCell: cell,
      location: window.location.href,
      title: document.title
    });
    return true;
  });

  ensureBanner();
})();
