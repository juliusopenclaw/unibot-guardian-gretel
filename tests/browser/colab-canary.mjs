import { chromium } from "playwright";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const extensionRoot = path.join(root, "unibot", "browser_extension");
const expectedId = "cmbjhndgjhgpopcflkjoalmpfjhoiana";
const sourceCommit = execFileSync("git", ["-C", root, "rev-parse", "HEAD"], { encoding: "utf-8" }).trim();
const defaultUrl = "https://colab.research.google.com/notebooks/intro.ipynb";
const canaryUrl = process.env.UNIBOT_LIVE_COLAB_URL || defaultUrl;
const parsedUrl = new URL(canaryUrl);
if (parsedUrl.protocol !== "https:" || parsedUrl.hostname !== "colab.research.google.com") {
  throw new Error("Live Colab canary accepts only the official public Colab host");
}

const launchOptions = {
  // Chromium's headless mode can render Colab but omit extension service
  // workers. The live canary must exercise the actual MV3 content script.
  headless: false,
  args: []
};
if (process.env.UNIBOT_CHROME_EXECUTABLE) {
  launchOptions.executablePath = process.env.UNIBOT_CHROME_EXECUTABLE;
  launchOptions.args.push("--enable-unsafe-extension-debugging");
  launchOptions.ignoreDefaultArgs = [
    "--disable-extensions",
    "--disable-component-extensions-with-background-pages"
  ];
} else {
  launchOptions.args.push(
    `--disable-extensions-except=${extensionRoot}`,
    `--load-extension=${extensionRoot}`
  );
}

const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "unibot-live-colab-"));
let context;

function safeCellMetadata(selectedCell) {
  const cell = selectedCell && typeof selectedCell === "object" ? selectedCell : {};
  return {
    adapter: typeof cell.adapter === "string" ? cell.adapter : "none",
    adapter_version: typeof cell.adapterVersion === "string" ? cell.adapterVersion : "none",
    confidence: typeof cell.confidence === "string" ? cell.confidence : "none",
    cell_type: typeof cell.cellType === "string" ? cell.cellType : "none",
    cell_index: Number.isInteger(cell.cellIndex) ? cell.cellIndex : -1,
    ambiguity: typeof cell.ambiguity === "string" ? cell.ambiguity : "",
    source_text_omitted: true
  };
}

async function extensionWorker() {
  const deadline = Date.now() + 15_000;
  while (Date.now() < deadline) {
    for (const worker of context.serviceWorkers()) {
      try {
        const manifest = await worker.evaluate(() => chrome.runtime.getManifest());
        if (manifest.name === "UniBot Guardian Mantel") return worker;
      } catch {
        // Browser-owned workers can disappear while Chrome starts.
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  return null;
}

try {
  context = await chromium.launchPersistentContext(userDataDir, launchOptions);
  let extensionId = expectedId;
  if (process.env.UNIBOT_CHROME_EXECUTABLE) {
    const cdp = await context.browser().newBrowserCDPSession();
    const loaded = await cdp.send("Extensions.loadUnpacked", { path: extensionRoot });
    extensionId = loaded.id;
  }
  if (extensionId !== expectedId) throw new Error("Live Colab canary loaded an unexpected extension ID");

  const page = await context.newPage();
  await page.goto(canaryUrl, { waitUntil: "domcontentloaded", timeout: 60_000 });
  await page.waitForTimeout(8_000);
  const publicSurfaceReady = await page.locator("colab-notebook-toolbar").count() > 0;
  const worker = await extensionWorker();
  let capture = { status: "blocked", reason: "extension_worker_unavailable", selectedCell: null };
  if (worker) {
    capture = await worker.evaluate(async () => {
      const tabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
      if (!tabs[0]?.id) return { status: "blocked", reason: "active_tab_missing", selectedCell: null };
      try {
        const response = await chrome.tabs.sendMessage(tabs[0].id, { type: "UNIBOT_GET_SELECTION" });
        return { status: "ok", selectedCell: response?.selectedCell || null };
      } catch (error) {
        return { status: "blocked", reason: String(error), selectedCell: null };
      }
    });
  }
  const cell = safeCellMetadata(capture.selectedCell);
  const payload = {
    schema_version: "UniBotLiveColabCanaryV1",
    source_commit: sourceCommit,
    status: publicSurfaceReady && capture.status === "ok" ? "pass" : "blocked",
    public_surface_ready: publicSurfaceReady,
    capture_status: cell.confidence === "low" ? "manual_selection_required" : "adapter_metadata_available",
    ...cell,
    notebook_output_read: false,
    provider_calls: 0,
    raw_cell_text_persisted: false,
    source_url_kind: "official_public_colab_notebook"
  };
  const output = JSON.stringify(payload);
  if (process.env.UNIBOT_COLAB_CANARY_OUTPUT) {
    fs.writeFileSync(process.env.UNIBOT_COLAB_CANARY_OUTPUT, `${output}\n`, { encoding: "utf-8", mode: 0o600 });
  }
  process.stdout.write(`${output}\n`);
} finally {
  if (context) await context.close();
  fs.rmSync(userDataDir, { recursive: true, force: true });
}
