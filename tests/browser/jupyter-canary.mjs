import { chromium } from "playwright";
import { spawn } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const extensionRoot = path.join(root, "unibot", "browser_extension");
const fixture = path.join(root, "fixtures", "public", "synthetic_python_practice.ipynb");
const expectedExtensionId = "cmbjhndgjhgpopcflkjoalmpfjhoiana";
const chromeExecutable = process.env.UNIBOT_CHROME_EXECUTABLE;
const jupyterPython = process.env.UNIBOT_JUPYTER_PYTHON
  || path.join(os.homedir(), "Library", "Application Support", "UniBotAutonomy", "jupyter-canary-venv", "bin", "python");

if (!chromeExecutable) {
  throw new Error("Live Jupyter canary requires UNIBOT_CHROME_EXECUTABLE");
}
if (!fs.statSync(jupyterPython, { throwIfNoEntry: false })?.isFile()) {
  throw new Error("Live Jupyter canary requires an isolated JupyterLab Python environment");
}
if (!fs.statSync(fixture, { throwIfNoEntry: false })?.isFile()) {
  throw new Error("Public synthetic notebook fixture is missing");
}

const canaryRoot = fs.mkdtempSync(path.join(os.tmpdir(), "unibot-jupyter-canary-"));
const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "unibot-jupyter-chrome-"));
const notebookName = "synthetic_python_practice.ipynb";
fs.copyFileSync(fixture, path.join(canaryRoot, notebookName));

const token = crypto.randomBytes(24).toString("hex");
const requestedPort = await findFreePort();
const server = spawn(
  jupyterPython,
  [
    "-m", "jupyter", "lab", "--no-browser", "--ip=127.0.0.1", `--port=${requestedPort}`,
    `--ServerApp.token=${token}`,
    `--ServerApp.root_dir=${canaryRoot}`
  ],
  { stdio: ["ignore", "pipe", "pipe"] }
);

let serverOutput = "";
let serverUrl = "";
const serverReady = new Promise((resolve, reject) => {
  const consume = (chunk) => {
    serverOutput += chunk.toString();
    const match = serverOutput.match(/http:\/\/127\.0\.0\.1:(\d+)\/lab/);
    if (match && Number(match[1]) > 0 && !serverUrl) {
      serverUrl = `http://127.0.0.1:${match[1]}/lab/tree/${notebookName}?token=${token}`;
      resolve(serverUrl);
    }
  };
  server.stdout.on("data", consume);
  server.stderr.on("data", consume);
  server.on("error", reject);
  server.on("exit", (code) => {
    if (!serverUrl) reject(new Error(`JupyterLab exited before startup (${code ?? "unknown"})`));
  });
  setTimeout(() => reject(new Error("JupyterLab did not start within 30 seconds")), 30_000);
});

let context;
try {
  const url = await serverReady;
  context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    executablePath: chromeExecutable,
    args: ["--enable-unsafe-extension-debugging"],
    ignoreDefaultArgs: ["--disable-extensions", "--disable-component-extensions-with-background-pages"]
  });
  const browser = context.browser();
  const cdp = await browser.newBrowserCDPSession();
  const loaded = await cdp.send("Extensions.loadUnpacked", { path: extensionRoot });
  if (loaded.id !== expectedExtensionId) throw new Error("Jupyter canary loaded an unexpected extension ID");

  const worker = await (async () => {
    const deadline = Date.now() + 10_000;
    while (Date.now() < deadline) {
      for (const candidate of context.serviceWorkers()) {
        try {
          const manifest = await candidate.evaluate(() => chrome.runtime.getManifest());
          if (manifest.name === "UniBot Guardian Mantel") return candidate;
        } catch {
          // Browser-owned workers can disappear while the extension starts.
        }
      }
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    throw new Error("UniBot extension worker was not discovered");
  })();

  const page = await context.newPage();
  await page.goto(url, { waitUntil: "domcontentloaded" });
  await page.locator(".jp-Notebook").waitFor({ timeout: 20_000 });
  await page.locator(".jp-Notebook-cell").first().click();
  const selected = await worker.evaluate(async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) throw new Error("No active Jupyter tab");
    return chrome.tabs.sendMessage(tab.id, { type: "UNIBOT_GET_SELECTION" });
  });
  const cell = selected?.selectedCell || {};
  const source = typeof cell.source === "string" ? cell.source : "";
  const result = {
    schema_version: "UniBotLiveJupyterCanaryV1",
    source_commit: requireSourceCommit(),
    status: cell.adapter === "jupyterlab" && cell.confidence === "high" && source.length > 0 ? "pass" : "blocked",
    capture_status: cell.confidence === "low" ? "manual_selection_required" : "adapter_metadata_available",
    adapter: typeof cell.adapter === "string" ? cell.adapter : "none",
    adapter_version: typeof cell.adapterVersion === "string" ? cell.adapterVersion : "none",
    confidence: typeof cell.confidence === "string" ? cell.confidence : "low",
    cell_type: typeof cell.cellType === "string" ? cell.cellType : "unknown",
    cell_index: Number.isInteger(cell.cellIndex) ? cell.cellIndex : -1,
    source_text_omitted: true,
    notebook_code_executed: false,
    notebook_output_read: false,
    raw_cell_text_persisted: false,
    provider_calls: 0,
    source_url_kind: "local_synthetic_jupyterlab"
  };
  const output = `${JSON.stringify(result)}\n`;
  process.stdout.write(output);
  if (process.env.UNIBOT_JUPYTER_CANARY_OUTPUT) {
    fs.writeFileSync(process.env.UNIBOT_JUPYTER_CANARY_OUTPUT, output, { encoding: "utf-8", mode: 0o600 });
  }
  if (result.status !== "pass") process.exitCode = 1;
} finally {
  try {
    if (context) await context.close();
  } finally {
    await stopServer(server);
    fs.rmSync(canaryRoot, { recursive: true, force: true });
    fs.rmSync(userDataDir, { recursive: true, force: true });
  }
}

function requireSourceCommit() {
  const commit = process.env.UNIBOT_SOURCE_COMMIT || "local-unbound";
  return /^[0-9a-f]{40}$/.test(commit) ? commit : "local-unbound";
}

function findFreePort() {
  return new Promise((resolve, reject) => {
    const probe = net.createServer();
    probe.once("error", reject);
    probe.listen(0, "127.0.0.1", () => {
      const address = probe.address();
      if (!address || typeof address === "string") {
        probe.close();
        reject(new Error("Could not reserve a local Jupyter canary port"));
        return;
      }
      const port = address.port;
      probe.close((error) => error ? reject(error) : resolve(port));
    });
  });
}

async function stopServer(processHandle) {
  if (processHandle.exitCode !== null || processHandle.signalCode !== null) return;
  const exited = new Promise((resolve) => processHandle.once("exit", resolve));
  processHandle.kill("SIGTERM");
  await Promise.race([
    exited,
    new Promise((resolve) => setTimeout(resolve, 3000))
  ]);
  if (processHandle.exitCode === null && processHandle.signalCode === null) processHandle.kill("SIGKILL");
}
