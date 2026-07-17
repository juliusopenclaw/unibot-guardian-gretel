import { chromium } from "playwright";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const extensionRoot = path.join(root, "unibot", "browser_extension");
const expectedId = "cmbjhndgjhgpopcflkjoalmpfjhoiana";

const launchOptions = {
  headless: false,
  args: []
};
if (process.env.UNIBOT_REQUIRE_NATIVE === "1" && !process.env.UNIBOT_CHROME_EXECUTABLE) {
  throw new Error(
    "Native Chrome canary requires UNIBOT_CHROME_EXECUTABLE pointing to the official Google Chrome binary"
  );
}
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

let chromeUserDataDir = "";
let context;
let developmentPairing = false;

async function loadChromeCanaryExtension() {
  if (!process.env.UNIBOT_CHROME_EXECUTABLE) return null;
  const browser = context.browser();
  if (!browser) throw new Error("Chrome browser session was not available");
  const cdp = await browser.newBrowserCDPSession();
  const result = await cdp.send("Extensions.loadUnpacked", { path: extensionRoot });
  if (result.id !== expectedId) {
    throw new Error(`Chrome loaded an unexpected UniBot extension ID: ${result.id}`);
  }
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    const installed = await cdp.send("Extensions.getExtensions");
    const extension = installed.extensions.find((item) => item.id === result.id);
    if (extension?.enabled) return result.id;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("Chrome did not enable the UniBot extension after loading it");
}

async function waitForUniBotWorker() {
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    for (const worker of context.serviceWorkers()) {
      try {
        const manifest = await worker.evaluate(() => chrome.runtime.getManifest());
        if (manifest.name === "UniBot Guardian Mantel") return worker;
      } catch {
        // A browser-owned component worker may disappear while Chrome starts.
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("UniBot extension service worker was not discovered");
}

try {
  if (process.env.UNIBOT_CHROME_EXECUTABLE) {
    if (process.platform !== "darwin") {
      throw new Error("The real Chrome canary harness currently requires macOS");
    }
    chromeUserDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "unibot-chrome-canary-"));
    const sourceManifest = process.env.UNIBOT_CHROME_NATIVE_MANIFEST || path.join(
      os.homedir(),
      "Library",
      "Application Support",
      "Google",
      "Chrome",
      "NativeMessagingHosts",
      "de.gretel.unibot_companion.json"
    );
    const nativeManifest = JSON.parse(fs.readFileSync(sourceManifest, "utf-8"));
    if (
      nativeManifest.name !== "de.gretel.unibot_companion"
      || nativeManifest.type !== "stdio"
      || JSON.stringify(nativeManifest.allowed_origins) !== JSON.stringify([
        `chrome-extension://${expectedId}/`
      ])
      || !path.isAbsolute(nativeManifest.path)
      || !fs.statSync(nativeManifest.path).isFile()
    ) {
      throw new Error("Installed Chrome Native Messaging manifest is not the expected UniBot host");
    }
    const targetDirectory = path.join(chromeUserDataDir, "NativeMessagingHosts");
    const targetManifest = path.join(targetDirectory, "de.gretel.unibot_companion.json");
    fs.mkdirSync(targetDirectory, { recursive: true, mode: 0o700 });
    fs.writeFileSync(targetManifest, `${JSON.stringify(nativeManifest)}\n`, { mode: 0o600 });
    fs.chmodSync(targetManifest, 0o600);
  }
  context = await chromium.launchPersistentContext(chromeUserDataDir, launchOptions);
  const loadedExtensionId = await loadChromeCanaryExtension();
  const worker = loadedExtensionId ? null : await waitForUniBotWorker();
  const workerUrl = worker?.url();
  const extensionId = loadedExtensionId || new URL(workerUrl).hostname;
  if (extensionId !== expectedId) {
    if (process.env.UNIBOT_ALLOW_DEVELOPMENT_PAIRING !== "1") {
      throw new Error(
        `Unpacked Chrome extension received temporary ID ${extensionId}; use a signed package or explicit development pairing`
      );
    }
    execFileSync(
      process.env.UNIBOT_PYTHON || "python3",
      ["-m", "unibot.cli", "companion", "install", "--extension-id", extensionId],
      { cwd: root, stdio: "ignore" }
    );
    developmentPairing = true;
  }

  let page = await context.newPage();
  let testSessionCreated = false;
  await page.goto(`chrome-extension://${extensionId}/v2/sidepanel.html`);
  if ((await page.locator("h1").textContent()) !== "UniBot Guardian") throw new Error("Side panel did not render");
  if (await page.locator("input[value='A4']").count() !== 1) throw new Error("A4 control is missing");
  if (process.env.UNIBOT_REQUIRE_NATIVE === "1") {
    await page.locator("#connectionStatus").filter({ hasText: /Lokal bereit|Sitzung fortgesetzt/ }).waitFor({ timeout: 10_000 });
  } else {
    await page.waitForTimeout(1500);
  }
  const connectionStatus = (await page.locator("#connectionStatus").textContent()) || "";
  const companionConnected = ["Lokal bereit", "Sitzung fortgesetzt", "Sitzung aktiv"].includes(connectionStatus);
  let sessionResumed = connectionStatus === "Sitzung fortgesetzt";
  if (process.env.UNIBOT_REQUIRE_NATIVE === "1" && !companionConnected) {
    throw new Error("Native companion was required but not discovered by this browser build");
  }
  if (companionConnected && !sessionResumed) {
    await page.locator("#practiceBoundary").check();
    await page.locator("#startSession").click();
    await page.locator("#connectionStatus").filter({ hasText: "Sitzung aktiv" }).waitFor({ timeout: 10_000 });
    testSessionCreated = true;
  }
  if (testSessionCreated) {
    await page.close();
    page = await context.newPage();
    await page.goto(`chrome-extension://${extensionId}/v2/sidepanel.html`);
    await page.locator("#connectionStatus").filter({ hasText: "Sitzung fortgesetzt" }).waitFor({ timeout: 10_000 });
    sessionResumed = true;
  }
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  if (overflow) throw new Error("Side panel has horizontal overflow");
  if (testSessionCreated) {
    await page.getByRole("tab", { name: "Rueckblick", exact: true }).click();
    page.once("dialog", (dialog) => dialog.accept());
    await page.locator("#deleteSession").click();
    await page.locator("#reviewOutput").filter({ hasText: "Keine Sitzungsdaten" }).waitFor({ timeout: 10_000 });
    await page.locator("#connectionStatus").filter({ hasText: "Lokal bereit" }).waitFor({ timeout: 10_000 });
  }
  process.stdout.write(JSON.stringify({
    status: "pass",
    extension_id: extensionId,
    extension_id_mode: developmentPairing ? "development_pairing" : "fixed_signed_package",
    sidepanel_rendered: true,
    native_companion_connected: companionConnected,
    learning_session_started: companionConnected,
    learning_session_resumed: sessionResumed
  }) + "\n");
} finally {
  try {
    if (context) await context.close();
  } finally {
    try {
      if (developmentPairing) {
        execFileSync(
          process.env.UNIBOT_PYTHON || "python3",
          ["-m", "unibot.cli", "companion", "install"],
          { cwd: root, stdio: "ignore" }
        );
      }
    } finally {
      if (chromeUserDataDir) fs.rmSync(chromeUserDataDir, { recursive: true, force: true });
    }
  }
}
