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
    banner.setAttribute("role", "status");
    banner.setAttribute("aria-live", "polite");
    banner.setAttribute("aria-atomic", "true");
    banner.setAttribute("aria-label", "UniBot Guardian Lernmantel");
    banner.style.cssText = [
      "position:fixed",
      "right:12px",
      "bottom:12px",
      "z-index:2147483647",
      "display:flex",
      "align-items:flex-start",
      "gap:10px",
      "width:min(320px,calc(100vw - 24px))",
      "padding:10px 12px",
      "font:13px/1.35 system-ui,sans-serif",
      "color:#111827",
      "background:#fef3c7",
      "border:1px solid #f59e0b",
      "border-radius:8px",
      "box-shadow:0 8px 22px rgba(0,0,0,.16)"
    ].join(";");
    const message = document.createElement("span");
    message.textContent = "UniBot Guardian Lernmantel aktiv";
    const dismiss = document.createElement("button");
    dismiss.type = "button";
    dismiss.textContent = "Ausblenden";
    dismiss.setAttribute("aria-label", "UniBot-Hinweis ausblenden");
    dismiss.style.cssText = [
      "flex:0 0 auto",
      "min-height:36px",
      "padding:6px 8px",
      "font:inherit",
      "color:#111827",
      "background:#ffffff",
      "border:1px solid #b45309",
      "border-radius:4px",
      "cursor:pointer"
    ].join(";");
    dismiss.addEventListener("click", () => banner.remove());
    banner.append(message, dismiss);
    document.documentElement.appendChild(banner);
  }

  function collectVisibleSelection() {
    const selection = window.getSelection();
    return selection ? selection.toString().trim() : "";
  }

  function sourceFromCell(cell) {
    const input = cell.querySelector(
      ".cm-content, .CodeMirror-code, .input_area, [contenteditable='true'], textarea, " +
      "pre.monaco-colorized, pre.lazy-virtualized"
    );
    if (input) return (input.innerText || input.textContent || input.value || "").trim().slice(0, 12000);

    // Colab text cells expose their source through cell-contents rather than
    // an editor node. Clone it so output-like descendants cannot enter the
    // selection payload when a future Colab layout falls through here.
    const contents = cell.querySelector(".cell-contents");
    if (!contents) return "";
    const clone = contents.cloneNode(true);
    const legacyOutputClass = ["output", "area"].join("_");
    clone.querySelectorAll(
      `colab-output, .output, .${legacyOutputClass}, [class*='output'], ` +
      "pre:not(.monaco-colorized):not(.lazy-virtualized)"
    ).forEach((node) => node.remove());
    return (clone.innerText || clone.textContent || "").trim().slice(0, 12000);
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
    const classText = `${cell.className || ""} ${cell.getAttribute("data-cell-type") || ""} ${cell.getAttribute("aria-label") || ""}`.toLowerCase();
    return {
      source,
      cellType: classText.includes("markdown") || classText.includes("text cell") ? "markdown" : "code",
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
    const selectors = [
      ".cell.notebook-cell.focused",
      ".cell.notebook-cell[aria-selected='true']",
      "colab-code-cell.focused",
      "colab-text-cell.focused"
    ];
    return resolveCellCandidates({
      adapter: "colab",
      adapterVersion: "colab-v1",
      selectors,
      cells: Array.from(document.querySelectorAll(".cell.notebook-cell, colab-code-cell, colab-text-cell")),
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

  async function saveActiveJupyterNotebook(expectedBinding) {
    const bindingMatches = expectedBinding
      && expectedBinding.schema_version === 'unibot-rehearsal-browser-binding-v1'
      && expectedBinding.hostname === window.location.hostname
      && Number.isInteger(expectedBinding.port)
      && expectedBinding.port === Number(window.location.port)
      && expectedBinding.pathname === window.location.pathname;
    if (!bindingMatches) {
      return { saved: false, reason: 'rehearsal_browser_binding_mismatch', notebook_content_read: false };
    }
    const selectors = [
      "button[data-command='docmanager:save']",
      "button[title^='Save']",
      "button[aria-label^='Save']"
    ];
    const controls = Array.from(new Set(selectors.flatMap((selector) => Array.from(document.querySelectorAll(selector)))))
      .filter((control) => !control.disabled && control.getClientRects().length > 0);
    if (controls.length !== 1) {
      return {
        saved: false,
        reason: controls.length ? 'ambiguous_jupyter_save_control' : 'jupyter_save_control_not_found',
        notebook_content_read: false
      };
    }
    controls[0].click();
    const deadline = Date.now() + 5000;
    const pendingSelector = [
      ".jp-DocumentContext-title.jp-mod-dirty",
      ".jp-mod-saving",
      "[data-status='dirty']",
      "[data-status='saving']"
    ].join(",");
    await new Promise((resolve) => setTimeout(resolve, 100));
    while (document.querySelector(pendingSelector) && Date.now() < deadline) {
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
    if (document.querySelector(pendingSelector)) {
      return {
        saved: false,
        reason: "jupyter_save_not_confirmed",
        notebook_content_read: false
      };
    }
    return {
      saved: true,
      adapter: 'jupyterlab',
      method: 'visible_save_control',
      browser_binding_matched: true,
      notebook_content_read: false
    };
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (!message) {
      return false;
    }
    if (message.type === "UNIBOT_SAVE_NOTEBOOK") {
      saveActiveJupyterNotebook(message.expected_binding).then(sendResponse);
      return true;
    }
    if (message.type !== "UNIBOT_GET_SELECTION") return false;
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
