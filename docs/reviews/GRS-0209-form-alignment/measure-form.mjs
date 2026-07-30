// GRS-0209 — screenshot + measure the new-assessment form at three widths.
// Usage: bun shot.mjs <label> <outdir>
// Measures the real rendered geometry of the two controls and the submit button, so the
// misalignment is named in pixels rather than asserted from style declarations (which is exactly
// what GRS-0178's test did, and why it missed both causes).
import { chromium } from "/home/dev/projects/grassmarket/frontend/node_modules/playwright-core/index.js";
import { mkdirSync, writeFileSync } from "node:fs";

const [label, outdir] = process.argv.slice(2);
const BASE = "http://localhost:3000";
const EXE = "/home/dev/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome";
const WIDTHS = [1280, 1440, 1920];

mkdirSync(outdir, { recursive: true });

const browser = await chromium.launch({ executablePath: EXE, headless: true });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 950 } });
const page = await ctx.newPage();

// --- log in ---
await page.goto(`${BASE}/login`, { waitUntil: "networkidle" });
await page.locator('input[type="email"]').first().fill("advisor@bruntsfieldcapital.com");
await page.locator('input[type="password"]').first().fill("grassmarket-demo"); // pragma: allowlist secret
await page.getByRole("button", { name: /sign in with email/i }).first().click();
await page.waitForURL((u) => !u.pathname.includes("/login"), { timeout: 20000 }).catch(() => {});
await page.waitForTimeout(1200);

const results = {};
for (const width of WIDTHS) {
  await page.setViewportSize({ width, height: 950 });
  await page.goto(`${BASE}/assessments`, { waitUntil: "networkidle" });
  await page.locator("form.form-create-assessment").waitFor({ timeout: 20000 });
  await page.waitForTimeout(600);

  const m = await page.evaluate(() => {
    const form = document.querySelector("form.form-create-assessment");
    const input = form.querySelector('input[type="text"]');
    const select = form.querySelector("select");
    const button = form.querySelector('button[type="submit"]');
    const box = (el) => {
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { top: +r.top.toFixed(1), bottom: +r.bottom.toFixed(1), height: +r.height.toFixed(1) };
    };
    return {
      formAlignItems: getComputedStyle(form).alignItems,
      input: box(input),
      select: box(select),
      button: box(button),
    };
  });

  // The two numbers the ticket asks to be named.
  m.inputVsSelectTopDelta = +(m.select.top - m.input.top).toFixed(1);
  m.selectVsInputHeightDelta = +(m.select.height - m.input.height).toFixed(1);
  m.buttonVsSelectTopDelta = +(m.button.top - m.select.top).toFixed(1);
  results[width] = m;

  const form = page.locator("form.form-create-assessment");
  await form.screenshot({ path: `${outdir}/${label}-${width}.png` });
  console.log(
    `${label} ${width}: input.top=${m.input.top} select.top=${m.select.top} ` +
      `Δtop=${m.inputVsSelectTopDelta}px  Δheight=${m.selectVsInputHeightDelta}px ` +
      `button Δtop=${m.buttonVsSelectTopDelta}px  align-items=${m.formAlignItems}`
  );
}

writeFileSync(`${outdir}/${label}-measurements.json`, JSON.stringify(results, null, 2));
await browser.close();
