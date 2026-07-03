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
      required_manifest_permissions: ["activeTab", "storage", "sidePanel"],
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
    banner.textContent = "UniBot Guardian Practice Overlay aktiv - externe KI-Hilfe erst im Side Panel pruefen.";
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

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (!message || message.type !== "UNIBOT_GET_SELECTION") {
      return false;
    }
    sendResponse({
      selectedText: collectVisibleSelection(),
      location: window.location.href,
      title: document.title
    });
    return true;
  });

  ensureBanner();
})();
