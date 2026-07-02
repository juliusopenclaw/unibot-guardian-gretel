chrome.runtime.onInstalled.addListener(() => {
  if (!chrome.sidePanel || !chrome.sidePanel.setPanelBehavior) {
    return;
  }
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {
    // Older Chromium builds may not support click-to-open side panels.
  });
});
