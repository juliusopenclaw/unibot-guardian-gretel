from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "unibot" / "browser_extension"


class BrowserExtensionV2Tests(unittest.TestCase):
    def test_manifest_loads_focused_v2_sidepanel(self) -> None:
        manifest = json.loads((EXTENSION / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "0.3.0")
        self.assertEqual(manifest["side_panel"]["default_path"], "v2/sidepanel.html")
        self.assertIn("nativeMessaging", manifest["permissions"])
        self.assertEqual(len(manifest["key"]), 392)
        self.assertNotIn("<all_urls>", json.dumps(manifest))

    def test_v2_sidepanel_has_three_workflows_native_transport_and_a0_a4(self) -> None:
        html = (EXTENSION / "v2" / "sidepanel.html").read_text(encoding="utf-8")
        script = (EXTENSION / "v2" / "sidepanel.js").read_text(encoding="utf-8")
        self.assertEqual(html.count("data-tab="), 3)
        self.assertIn("Lernsitzung", html)
        self.assertIn("Sokratische Hilfe", html)
        self.assertIn("Sitzungsrueckblick", html)
        self.assertIn('value="A0"', html)
        self.assertIn('value="A1"', html)
        self.assertIn('value="A2"', html)
        self.assertIn('value="A3"', html)
        self.assertIn('value="A4"', html)
        self.assertNotIn('value="A6"', html)
        self.assertIn("chrome.runtime.connectNative", script)
        self.assertIn('nativeRequest("session.start"', script)
        self.assertIn('nativeRequest("notebook.import"', script)
        self.assertIn('nativeRequest("notebook.upload.start"', script)
        self.assertIn('nativeRequest("notebook.upload.chunk"', script)
        self.assertIn('nativeRequest("notebook.upload.finish"', script)
        self.assertIn('nativeRequest("gateway.launch"', script)
        self.assertIn('nativeRequest("gateway.status"', script)
        self.assertIn('nativeRequest("gateway.stop"', script)
        self.assertIn('nativeRequest("tutor.turn"', script)
        self.assertIn('nativeRequest("session.report"', script)
        self.assertIn('nativeRequest("session.resume"', script)
        self.assertIn('nativeRequest("session.delete"', script)
        self.assertIn("deleteSession", html)
        self.assertIn("stopGateway", html)
        self.assertIn('id="notebookFile"', html)
        self.assertIn('accept=".ipynb,application/x-ipynb+json"', html)
        self.assertIn('id="showExportPreview"', html)
        self.assertIn('id="confirmExport"', html)
        self.assertIn("Weitergabe: freiwillig", script)
        self.assertIn('id="accessibilitySupport"', html)
        self.assertIn("kostenneutral", html)
        self.assertIn('data-accessibility="enhanced"', html)
        self.assertIn("Größere Bedienelemente", html)
        self.assertIn("accessibility_used", script)
        self.assertIn("applyAccessibilityMode", script)
        self.assertNotIn("127.0.0.1:8765", script)

    def test_content_script_extracts_active_notebook_cell_not_output(self) -> None:
        content = (EXTENSION / "content.js").read_text(encoding="utf-8")
        self.assertIn("activeNotebookCell", content)
        self.assertIn("jupyterAdapter", content)
        self.assertIn("colabAdapter", content)
        self.assertIn("selectionAdapter", content)
        self.assertIn(".jp-Notebook-cell.jp-mod-active", content)
        self.assertIn("colab-code-cell.focused", content)
        self.assertIn(".cm-content", content)
        self.assertIn("selectedCell", content)
        self.assertNotIn(".output_area", content)

    def test_gitleaks_exception_is_narrowly_bound_to_public_manifest_key(self) -> None:
        policy = (ROOT / ".gitleaks.toml").read_text(encoding="utf-8")
        self.assertIn('id = "generic-api-key"', policy)
        self.assertIn("[[rules.allowlists]]", policy)
        self.assertIn("unibot/browser_extension/manifest", policy)
        self.assertIn("MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A", policy)
        self.assertIn('condition = "AND"', policy)


if __name__ == "__main__":
    unittest.main()
