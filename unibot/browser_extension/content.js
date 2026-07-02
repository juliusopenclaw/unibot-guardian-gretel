(() => {
  const ROOT_ID = "unibot-guardian-banner";

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
