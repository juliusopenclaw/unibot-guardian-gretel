import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const extensionRoot = path.join(root, "unibot", "browser_extension");

test("content script captures the active Jupyter cell without output text", async ({ page }) => {
  await page.setContent(`
    <main class="jp-Notebook">
      <section class="jp-Notebook-cell jp-CodeCell jp-mod-active">
        <div class="cm-content">values = [1, 2, 3]</div>
        <div class="output_area">private rendered output</div>
      </section>
    </main>
  `);
  await page.evaluate(() => {
    window.__unibotListener = null;
    window.chrome = {
      runtime: {
        onMessage: {
          addListener(listener) {
            window.__unibotListener = listener;
          }
        }
      }
    };
  });
  await page.addScriptTag({ path: path.join(extensionRoot, "content.js") });
  const response = await page.evaluate(() => new Promise((resolve) => {
    window.__unibotListener({ type: "UNIBOT_GET_SELECTION" }, {}, resolve);
  }));

  expect(response.selectedCell.cellType).toBe("code");
  expect(response.selectedCell.cellIndex).toBe(0);
  expect(response.selectedCell.source).toContain("values = [1, 2, 3]");
  expect(response.selectedCell.source).not.toContain("private rendered output");
});

test("content script captures the focused Colab cell without output text", async ({ page }) => {
  await page.setContent(`
    <main>
      <colab-code-cell class="focused">
        <div class="input_area"><div class="cm-content">import pandas as pd</div></div>
        <div class="output_area">private rendered Colab output</div>
      </colab-code-cell>
    </main>
  `);
  await page.evaluate(() => {
    window.__unibotListener = null;
    window.chrome = {
      runtime: {
        onMessage: {
          addListener(listener) {
            window.__unibotListener = listener;
          }
        }
      }
    };
  });
  await page.addScriptTag({ path: path.join(extensionRoot, "content.js") });
  const response = await page.evaluate(() => new Promise((resolve) => {
    window.__unibotListener({ type: "UNIBOT_GET_SELECTION" }, {}, resolve);
  }));

  expect(response.selectedCell.adapter).toBe("colab");
  expect(response.selectedCell.selector).toBe("colab-code-cell.focused");
  expect(response.selectedCell.confidence).toBe("high");
  expect(response.selectedCell.cellIndex).toBe(0);
  expect(response.selectedCell.source).toContain("import pandas as pd");
  expect(response.selectedCell.source).not.toContain("private rendered Colab output");
});

test("content script refuses ambiguous Colab cell detection instead of guessing", async ({ page }) => {
  await page.setContent(`
    <main>
      <colab-code-cell class="focused"><div class="input_area"><div class="cm-content">first = 1</div></div></colab-code-cell>
      <colab-code-cell class="focused"><div class="input_area"><div class="cm-content">second = 2</div></div></colab-code-cell>
    </main>
  `);
  await page.evaluate(() => {
    window.__unibotListener = null;
    window.chrome = {
      runtime: {
        onMessage: {
          addListener(listener) {
            window.__unibotListener = listener;
          }
        }
      }
    };
  });
  await page.addScriptTag({ path: path.join(extensionRoot, "content.js") });
  const response = await page.evaluate(() => new Promise((resolve) => {
    window.__unibotListener({ type: "UNIBOT_GET_SELECTION" }, {}, resolve);
  }));

  expect(response.selectedCell.adapter).toBe("colab");
  expect(response.selectedCell.adapterVersion).toBe("colab-v1");
  expect(response.selectedCell.confidence).toBe("low");
  expect(response.selectedCell.ambiguity).toBe("multiple_active_cells");
  expect(response.selectedCell.cellIndex).toBe(-1);
  expect(response.selectedCell.source).toBe("");
});

test("sidepanel starts a native session, captures a cell, requests A0-A4 help, and renders review metadata", async ({ page }) => {
  await page.addInitScript(() => {
    let onNativeMessage = null;
    window.__lastTutorPayload = null;
    const nativePort = {
      onMessage: { addListener(listener) { onNativeMessage = listener; } },
      onDisconnect: { addListener() {} },
      postMessage(message) {
        let response = {
          request_id: message.request_id,
          status: "ready",
          local_practice_status: "ready_for_local_practice",
          distribution_status: "blocked_human_release_gates"
        };
        if (message.type === "session.start") {
          response = {
            request_id: message.request_id,
            status: "active",
            contract: {
              session_id: "synthetic-session",
              assistance_mode: message.payload.assistance_mode,
              max_help_level: message.payload.max_help_level
            }
          };
        } else if (message.type === "tutor.turn") {
          window.__lastTutorPayload = message.payload;
          if (!["A0", "A1", "A2", "A3", "A4"].includes(message.payload.requested_help_level)) {
            throw new Error("unexpected help level");
          }
          response = {
            request_id: message.request_id,
            status: "ok",
            turn: {
              effective_help_level: message.payload.requested_help_level,
              hint_markdown: "Welche Laenge erwartest du vor dem Zugriff?",
              source_anchors: [{ label: "Python Tutorial" }],
              assistance_points_for_task: 5,
              assistance_points_delta: 5,
              next_allowed_help_level: "A3",
              blocked_reasons: []
            }
          };
        } else if (message.type === "session.report") {
          response = {
            request_id: message.request_id,
            status: "ok",
            report: {
              event_count: 1,
              own_attempt_count: 1,
              by_help_level: { A2: 1 },
              assistance_points_used: 5,
              accessibility_support_event_count: 1
            }
          };
        }
        queueMicrotask(() => onNativeMessage(response));
      }
    };
    window.chrome = {
      runtime: {
        connectNative(name) {
          if (name !== "de.gretel.unibot_companion") throw new Error("unexpected native host");
          return nativePort;
        },
        lastError: null
      },
      tabs: {
        async query() { return [{ id: 7 }]; },
        async sendMessage() {
          return {
            title: "Synthetic Jupyter",
            selectedCell: {
              source: "values = [1, 2, 3]",
              cellType: "code",
              cellIndex: 2,
              adapter: "jupyterlab",
              adapterVersion: "jupyterlab-v1",
              confidence: "high"
            }
          };
        }
      }
    };
  });

  await page.goto(pathToFileURL(path.join(extensionRoot, "v2", "sidepanel.html")).href);
  await expect(page.locator("#connectionStatus")).toHaveText("Lokal bereit");
  await expect(page.locator("#releaseStatus")).toHaveText("Lokaler Uebungsbetrieb: bereit. Allgemeine Verteilung: noch nicht freigegeben.");
  await page.locator("#startSession").click();
  await expect(page.locator("#connectionStatus")).toHaveText("Sitzung aktiv");

  await page.getByRole("tab", { name: "Hilfe", exact: true }).click();
  await page.locator("#capture").click();
  await expect(page.locator("#cellMeta")).toContainText("Zelle 2");
  await page.locator("#task").fill("Warum entsteht ein Indexfehler?");
  await page.locator("#attempt").fill("Ich pruefe zuerst die Listenlaenge.");
  await page.locator("#accessibilitySupport").check();
  await expect(page.locator("html")).toHaveAttribute("data-accessibility", "enhanced");
  await page.locator("#ask").click();
  await expect(page.locator("#helpOutput")).toContainText("Welche Laenge");
  await expect(page.locator("#helpOutput")).toContainText("5 Punkte");
  expect(await page.evaluate(() => window.__lastTutorPayload?.accessibility_used)).toBe(true);
  expect(await page.evaluate(() => window.__lastTutorPayload?.adapter_version)).toBe("jupyterlab-v1");

  await page.getByRole("tab", { name: "Rueckblick", exact: true }).click();
  await page.locator("#refreshReview").click();
  await expect(page.locator("#reviewOutput")).toContainText("Ereignisse: 1");
  await expect(page.locator("#reviewOutput")).toContainText("Barrierearme Unterstützung: 1 Ereignisse (kostenneutral)");
  await expect(page.locator("#exportReview")).toBeDisabled();
  await page.locator("#showExportPreview").click();
  await expect(page.locator("#exportPreview")).toContainText("Anzahl freiwillig markierter barrierearmer Unterstützungsereignisse");
  await expect(page.locator("#exportPreview")).toContainText("Nicht enthalten");
  await expect(page.locator("#exportReview")).toBeDisabled();
  await page.locator("#confirmExport").check();
  await expect(page.locator("#exportReview")).toBeEnabled();
  const downloadPromise = page.waitForEvent("download");
  await page.locator("#exportReview").click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("unibot-lernbericht-metadaten.json");
  await expect(page.locator("#reviewOutput")).toContainText("Export erstellt");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflow).toBe(false);
});

test("sidepanel imports a local notebook through the path-free chunked native handoff", async ({ page }) => {
  await page.addInitScript(() => {
    let onNativeMessage = null;
    const nativeTypes = [];
    window.__nativeTypes = nativeTypes;
    const nativePort = {
      onMessage: { addListener(listener) { onNativeMessage = listener; } },
      onDisconnect: { addListener() {} },
      postMessage(message) {
        nativeTypes.push(message.type);
        let response = {
          request_id: message.request_id,
          status: "ready",
          local_practice_status: "ready_for_local_practice",
          distribution_status: "blocked_human_release_gates"
        };
        if (message.type === "notebook.upload.start" || message.type === "notebook.upload.chunk") {
          response = { request_id: message.request_id, status: "uploading" };
        } else if (message.type === "notebook.upload.finish") {
          response = {
            request_id: message.request_id,
            status: "ok",
            notebook_id: "synthetic-notebook",
            manifest: {
              cell_count: 1,
              outputs_removed: 1,
              sanitized_sha256: "a".repeat(64)
            }
          };
        }
        queueMicrotask(() => onNativeMessage?.(response));
      }
    };
    window.chrome = {
      runtime: {
        connectNative() { return nativePort; },
        lastError: null
      }
    };
  });

  await page.goto(pathToFileURL(path.join(extensionRoot, "v2", "sidepanel.html")).href);
  const notebook = JSON.stringify({ cells: [{ cell_type: "code", metadata: {}, source: ["values = [1, 2, 3]"], outputs: [], execution_count: null }], metadata: {}, nbformat: 4, nbformat_minor: 5 });
  await page.locator("#notebookFile").setInputFiles({
    name: "practice.ipynb",
    mimeType: "application/x-ipynb+json",
    buffer: Buffer.from(notebook)
  });
  await page.locator("#importNotebook").click();
  await expect(page.locator("#notebookOutput")).toContainText("Bereinigtes Notebook bereit");
  const nativeTypes = await page.evaluate(() => window.__nativeTypes);
  expect(nativeTypes).toContain("notebook.upload.start");
  expect(nativeTypes).toContain("notebook.upload.chunk");
  expect(nativeTypes).toContain("notebook.upload.finish");
  expect(nativeTypes).not.toContain("notebook.import");
});

test("sidepanel remains usable at the narrow supported width", async ({ page }) => {
  await page.setViewportSize({ width: 300, height: 700 });
  await page.addInitScript(() => {
    window.chrome = {
      storage: { local: { async get() { return {}; }, async set() {} } },
      tabs: { async query() { return []; }, async sendMessage() { return {}; } }
    };
  });
  await page.goto(pathToFileURL(path.join(extensionRoot, "v2", "sidepanel.html")).href);
  await expect(page.locator("h1")).toHaveText("UniBot Guardian");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflow).toBe(false);
});

test("sidepanel exposes accessible status semantics and visible keyboard focus", async ({ page }) => {
  await page.setViewportSize({ width: 560, height: 700 });
  await page.goto(pathToFileURL(path.join(extensionRoot, "v2", "sidepanel.html")).href);

  await expect(page.locator("#connectionStatus")).toHaveAttribute("role", "status");
  await expect(page.locator("#connectionStatus")).toHaveAttribute("aria-live", "polite");
  await expect(page.locator("#session")).toHaveAttribute("role", "tabpanel");
  await expect(page.locator("nav button").first()).toHaveAttribute("aria-controls", "session");

  await page.locator("#startSession").focus();
  const focusStyle = await page.locator("#startSession").evaluate((element) => {
    const style = window.getComputedStyle(element);
    return { outlineStyle: style.outlineStyle, outlineWidth: style.outlineWidth };
  });
  expect(focusStyle.outlineStyle).not.toBe("none");
  expect(parseFloat(focusStyle.outlineWidth)).toBeGreaterThanOrEqual(2);
});

test("sidepanel supports keyboard tab navigation at the minimum supported width", async ({ page }) => {
  await page.setViewportSize({ width: 280, height: 700 });
  await page.goto(pathToFileURL(path.join(extensionRoot, "v2", "sidepanel.html")).href);

  const tabs = page.locator("nav button[role='tab']");
  await tabs.nth(0).focus();
  await page.keyboard.press("ArrowRight");
  await expect(tabs.nth(1)).toHaveAttribute("aria-selected", "true");
  await expect(page.locator("#help")).toBeVisible();
  expect(await page.evaluate(() => document.activeElement?.id)).toBe("help-tab");

  await page.keyboard.press("End");
  await expect(tabs.nth(2)).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("Home");
  await expect(tabs.nth(0)).toHaveAttribute("aria-selected", "true");
  expect(await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)).toBe(false);
});

test("sidepanel keeps the core flow usable at 200 percent zoom", async ({ page }) => {
  await page.setViewportSize({ width: 560, height: 900 });
  await page.goto(pathToFileURL(path.join(extensionRoot, "v2", "sidepanel.html")).href);
  await page.evaluate(() => {
    document.documentElement.style.zoom = "2";
  });

  await expect(page.locator("#startSession")).toBeVisible();
  await expect(page.locator("#pseudonym")).toBeVisible();
  await page.getByRole("tab", { name: "Hilfe", exact: true }).click();
  await expect(page.locator("#capture")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)).toBe(false);
});

test("sidepanel reconnects and resumes a local session after companion restart", async ({ page }) => {
  await page.addInitScript(() => {
    let onNativeMessage = null;
    let onDisconnect = null;
    let connectionCount = 0;
    const nativePort = {
      onMessage: { addListener(listener) { onNativeMessage = listener; } },
      onDisconnect: { addListener(listener) { onDisconnect = listener; } },
      disconnect() { onDisconnect?.(); },
      postMessage(message) {
        let response = {
          request_id: message.request_id,
          status: "stopped",
          local_practice_status: "ready_for_local_practice",
          distribution_status: "blocked_human_release_gates"
        };
        if (message.type === "companion.status") {
          response = connectionCount === 1
            ? {
                request_id: message.request_id,
                status: "ready",
                local_practice_status: "ready_for_local_practice",
                distribution_status: "blocked_human_release_gates",
                resume_available: false
              }
            : {
                request_id: message.request_id,
                status: "ready",
                local_practice_status: "ready_for_local_practice",
                distribution_status: "blocked_human_release_gates",
                resume_available: true,
                active_session_metadata: { session_id: "resumable-session" }
              };
        } else if (message.type === "session.resume") {
          response = {
            request_id: message.request_id,
            status: "active",
            contract: { session_id: "resumable-session", max_help_level: "A2" },
            report: { event_count: 2, own_attempt_count: 2, by_help_level: { A1: 1 }, assistance_points_used: 0 }
          };
        }
        queueMicrotask(() => onNativeMessage?.(response));
      }
    };
    window.__disconnectNative = () => nativePort.disconnect();
    window.chrome = {
      runtime: {
        connectNative(name) {
          if (name !== "de.gretel.unibot_companion") throw new Error("unexpected native host");
          connectionCount += 1;
          return nativePort;
        },
        lastError: null
      }
    };
  });

  await page.goto(pathToFileURL(path.join(extensionRoot, "v2", "sidepanel.html")).href);
  await expect(page.locator("#connectionStatus")).toHaveText("Lokal bereit");
  await expect(page.locator("#releaseStatus")).toContainText("Allgemeine Verteilung: noch nicht freigegeben");
  await page.evaluate(() => window.__disconnectNative());
  await expect(page.locator("#connectionStatus")).toHaveText("Sitzung fortgesetzt", { timeout: 5000 });
  await expect(page.locator("#reviewOutput")).toContainText("Ereignisse: 2");
});
