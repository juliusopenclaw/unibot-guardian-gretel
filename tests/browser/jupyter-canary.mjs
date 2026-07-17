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
  const result = await runNativeTutorCanary({ cell, source });
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

async function runNativeTutorCanary({ cell, source }) {
  const metadata = {
    schema_version: "UniBotLiveJupyterCanaryV1",
    source_commit: requireSourceCommit(),
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
    source_url_kind: "local_synthetic_jupyterlab",
    native_transport: true,
    session_started: false,
    session_stopped: false,
    session_deleted: false,
    tutor_flow_status: "blocked",
    effective_help_level: "none",
    source_anchor_count: 0,
    complete_solution_emitted: false,
    hint_text_omitted: true,
    local_tutor: "none"
  };
  let nativeClient = null;
  let sessionId = "";
  let sessionStarted = false;
  let sessionStopped = false;
  let sessionDeleted = false;
  let stage = "connect";
  try {
    if (cell.adapter !== "jupyterlab" || cell.confidence !== "high" || source.length === 0) {
      return { ...metadata, status: "blocked" };
    }
    nativeClient = createNativeHostClient();
    stage = "status";
    const status = await nativeClient.request("companion.status");
    if (status.session_active || status.resume_available || status.active_session_metadata) {
      return { ...metadata, status: "blocked", tutor_flow_reason: "existing_active_session" };
    }
    stage = "start";
    const started = await nativeClient.request("session.start", {
      pseudonym: "public-jupyter-canary",
      course_id: "synthetic-python-practice",
      assistance_mode: "fixed",
      fixed_help_level: "A2",
      max_help_level: "A2",
      planned_task_count: 1,
      practice_scope: "practice_only",
      practice_scope_confirmed: true
    });
    sessionId = typeof started.contract?.session_id === "string" ? started.contract.session_id : "";
    sessionStarted = started.status === "active" && sessionId.length > 0;
    if (!sessionStarted) return { ...metadata, status: "blocked", tutor_flow_reason: "session_start_blocked" };
    stage = "tutor";
    const turnResponse = await nativeClient.request("tutor.turn", {
      session_id: sessionId,
      task: "Wie pruefe ich die Laenge der Liste, bevor ich auf einen Index zugreife?",
      learner_attempt: "Ich pruefe zuerst, wie viele Elemente die Liste enthaelt.",
      cell_context: source,
      cell_type: cell.cellType || "code",
      cell_index: Number.isInteger(cell.cellIndex) ? cell.cellIndex : -1,
      adapter: "jupyterlab",
      adapter_version: cell.adapterVersion || "jupyterlab-v1",
      requested_help_level: "A2",
      confirm_escalation: false,
      accessibility_used: false
    });
    const turn = turnResponse.turn || {};
    const hint = typeof turn.hint_markdown === "string" ? turn.hint_markdown : "";
    const sourceAppearsInHint = source.trim().length > 0 && hint.includes(source.trim());
    const tutorPass = turnResponse.status === "ok"
      && ["allowed", "bounded"].includes(turn.status)
      && turn.effective_help_level === "A2"
      && Array.isArray(turn.source_anchor_ids)
      && turn.source_anchor_ids.length > 0
      && turn.raw_cell_stored === false
      && turn.raw_attempt_stored === false
      && hint.length > 0
      && !sourceAppearsInHint;
    stage = "stop";
    const stopped = await nativeClient.request("session.stop", { session_id: sessionId });
    sessionStopped = stopped.status === "stopped";
    stage = "delete";
    const deleted = await nativeClient.request("session.delete", { session_id: sessionId });
    sessionDeleted = deleted.status === "deleted";
    return {
      ...metadata,
      status: tutorPass && sessionStopped && sessionDeleted ? "pass" : "blocked",
      session_started: sessionStarted,
      session_stopped: sessionStopped,
      session_deleted: sessionDeleted,
      tutor_flow_status: tutorPass ? "pass" : "blocked",
      effective_help_level: typeof turn.effective_help_level === "string" ? turn.effective_help_level : "none",
      source_anchor_count: Array.isArray(turn.source_anchor_ids) ? turn.source_anchor_ids.length : 0,
      complete_solution_emitted: sourceAppearsInHint,
      local_tutor: typeof turn.local_realizer === "string" ? turn.local_realizer : "unknown"
    };
  } catch (error) {
    const errorName = error && typeof error === "object" && typeof error.name === "string" ? error.name : "unknown";
    return {
      ...metadata,
      status: "blocked",
      tutor_flow_reason: `native_flow_failed_${stage}_${errorName}`,
      session_started: sessionStarted,
      session_stopped: sessionStopped,
      session_deleted: sessionDeleted
    };
  } finally {
    if (nativeClient && sessionStarted && !sessionStopped) {
      await nativeClient.request("session.stop", { session_id: sessionId }).catch(() => {});
    }
    if (nativeClient && sessionStarted && !sessionDeleted) {
      await nativeClient.request("session.delete", { session_id: sessionId }).catch(() => {});
    }
    if (nativeClient) await nativeClient.close();
  }
}

function createNativeHostClient() {
  const manifestPath = process.env.UNIBOT_CHROME_NATIVE_MANIFEST || path.join(
    os.homedir(),
    "Library",
    "Application Support",
    "Google",
    "Chrome",
    "NativeMessagingHosts",
    "de.gretel.unibot_companion.json"
  );
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));
  if (
    manifest.name !== "de.gretel.unibot_companion"
    || manifest.type !== "stdio"
    || JSON.stringify(manifest.allowed_origins) !== JSON.stringify([`chrome-extension://${expectedExtensionId}/`])
    || !path.isAbsolute(manifest.path)
    || !fs.statSync(manifest.path, { throwIfNoEntry: false })?.isFile()
  ) {
    throw new Error("native_host_manifest_invalid");
  }
  const host = spawn(manifest.path, [], { stdio: ["pipe", "pipe", "ignore"] });
  let buffer = Buffer.alloc(0);
  let requestCounter = 0;
  const pending = new Map();
  const rejectPending = (error) => {
    for (const item of pending.values()) {
      clearTimeout(item.timeout);
      item.reject(error);
    }
    pending.clear();
  };
  host.stdout.on("data", (chunk) => {
    buffer = Buffer.concat([buffer, chunk]);
    while (buffer.length >= 4) {
      const length = buffer.readUInt32LE(0);
      if (length > 64 * 1024) {
        rejectPending(new Error("native_response_too_large"));
        return;
      }
      if (buffer.length < length + 4) return;
      const body = buffer.subarray(4, length + 4).toString("utf-8");
      buffer = buffer.subarray(length + 4);
      let response;
      try {
        response = JSON.parse(body);
      } catch {
        rejectPending(new Error("native_response_invalid_json"));
        return;
      }
      const item = pending.get(response?.request_id);
      if (!item) continue;
      clearTimeout(item.timeout);
      pending.delete(response.request_id);
      item.resolve(response);
    }
  });
  const hostError = new Error("native_host_disconnected");
  host.on("error", () => rejectPending(hostError));
  host.on("exit", () => rejectPending(hostError));
  return {
    request(type, payload = {}) {
      return new Promise((resolve, reject) => {
        const requestId = `jupyter-canary-${Date.now()}-${++requestCounter}`;
        const body = Buffer.from(JSON.stringify({
          schema_version: "unibot-companion-message-v1",
          request_id: requestId,
          type,
          payload
        }), "utf-8");
        const header = Buffer.alloc(4);
        header.writeUInt32LE(body.length, 0);
        const timeout = setTimeout(() => {
          pending.delete(requestId);
          reject(new Error("native_request_timeout"));
        }, 10_000);
        pending.set(requestId, { resolve, reject, timeout });
        host.stdin.write(Buffer.concat([header, body]));
      });
    },
    close() {
      return new Promise((resolve) => {
        if (host.exitCode !== null || host.signalCode !== null) {
          resolve();
          return;
        }
        const timer = setTimeout(() => {
          if (host.exitCode === null && host.signalCode === null) host.kill("SIGKILL");
          resolve();
        }, 3000);
        host.once("exit", () => {
          clearTimeout(timer);
          resolve();
        });
        host.stdin.end();
      });
    }
  };
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
