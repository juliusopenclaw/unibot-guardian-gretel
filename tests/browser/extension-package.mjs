import { chromium } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const extensionRoot = path.join(root, "unibot", "browser_extension");
const expectedId = "cmbjhndgjhgpopcflkjoalmpfjhoiana";

const context = await chromium.launchPersistentContext("", {
  headless: false,
  args: [
    `--disable-extensions-except=${extensionRoot}`,
    `--load-extension=${extensionRoot}`
  ]
});

try {
  let workers = context.serviceWorkers();
  if (!workers.length) workers = [await context.waitForEvent("serviceworker", { timeout: 10_000 })];
  const workerUrl = workers[0].url();
  const extensionId = new URL(workerUrl).hostname;
  if (extensionId !== expectedId) throw new Error(`Unexpected extension ID: ${extensionId}`);

  const page = await context.newPage();
  await page.goto(`chrome-extension://${extensionId}/v2/sidepanel.html`);
  if ((await page.locator("h1").textContent()) !== "UniBot Guardian") throw new Error("Side panel did not render");
  if (await page.locator("input[value='A4']").count() !== 1) throw new Error("A4 control is missing");
  await page.waitForTimeout(1500);
  const companionConnected = (await page.locator("#connectionStatus").textContent()) === "Lokal bereit";
  if (process.env.UNIBOT_REQUIRE_NATIVE === "1" && !companionConnected) {
    throw new Error("Native companion was required but not discovered by this browser build");
  }
  if (companionConnected) {
    await page.locator("#startSession").click();
    await page.locator("#connectionStatus").filter({ hasText: "Sitzung aktiv" }).waitFor({ timeout: 10_000 });
  }
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  if (overflow) throw new Error("Side panel has horizontal overflow");
  process.stdout.write(JSON.stringify({
    status: "pass",
    extension_id: extensionId,
    sidepanel_rendered: true,
    native_companion_connected: companionConnected,
    learning_session_started: companionConnected
  }) + "\n");
} finally {
  await context.close();
}
