// Browser-drive helper for mock-advisor agents (scenario stress test).
// Usage: bun agent_drive.mjs <email> <password> <steps.json> <outdir>
// Drives the LIVE product as a real user and prints a text transcript (URL + page text + console
// errors after each step) so an agent can observe outcomes without touching source code.
//
// Step shapes (JSON array):
//   {"do":"goto","url":"/pipeline","note":"open pipeline"}   // waits for the "Prospects" KPI marker
//   {"do":"goto","url":"/earnings","waitfor":"Earnings"}      // wait for a custom loaded-marker text
//   {"do":"fill","target":"placeholder:New prospect","value":"Acme"}
//   {"do":"click","target":"text:Add prospect"}
//   {"do":"select","target":"label:Move stage","value":"workshop_scheduled"}
//   {"do":"waittext","value":"Workshop Scheduled"}
//   {"do":"read"}                       // dump current page text
//   {"do":"shot","name":"pipeline"}     // screenshot
// target resolvers: text:  role:<role>:<name>  label:  placeholder:  #id  or a raw CSS selector.
import { chromium } from "/home/dev/projects/grassmarket/frontend/node_modules/playwright-core/index.js";
import { readFileSync } from "node:fs";

const [email, password, stepsPath, outdir] = process.argv.slice(2);
const BASE = "http://localhost:3000";
const EXE = "/home/dev/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome";
const steps = JSON.parse(readFileSync(stepsPath, "utf8"));

function locator(page, target) {
  if (target.startsWith("text:")) return page.getByText(target.slice(5), { exact: false }).first();
  if (target.startsWith("placeholder:")) return page.getByPlaceholder(target.slice(12)).first();
  if (target.startsWith("label:")) return page.getByLabel(target.slice(6)).first();
  if (target.startsWith("role:")) {
    const [, role, ...name] = target.split(":");
    return page.getByRole(role, name.length ? { name: name.join(":") } : {}).first();
  }
  return page.locator(target).first();
}

const trim = (s) => (s || "").replace(/\s+/g, " ").trim().slice(0, 1300);

const browser = await chromium.launch({ executablePath: EXE, headless: true });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 950 } });
const page = await ctx.newPage();
let consoleErrs = [];
const netErrs = [];
page.on("console", (m) => { if (m.type() === "error") consoleErrs.push(trim(m.text()).slice(0, 160)); });
page.on("pageerror", (e) => consoleErrs.push("PAGEERROR " + e.message.slice(0, 160)));
page.on("response", (r) => {
  const u = r.url();
  if (u.includes(":8000") && r.status() >= 400) netErrs.push(`HTTP ${r.status()} ${r.request().method()} ${u.split(":8000")[1]}`);
});

// The Next dev server's network never goes fully idle under concurrent agents, so `networkidle` waits
// flake and time out. Wait for `domcontentloaded` (reliable) and then a concrete on-page marker
// instead — the loaded content, not the absence of requests (stress-test infra lesson).
async function waitLoaded(target) {
  await page
    .getByText(target, { exact: false })
    .first()
    .waitFor({ timeout: 15000 })
    .catch(() => {}); // best-effort: the read step still captures whatever did render
}

async function login() {
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  await page.locator("#email").waitFor({ timeout: 15000 });
  await page.waitForTimeout(1500); // let React hydrate so controlled inputs keep state
  const btn = page.getByRole("button", { name: "Sign in" });
  for (let attempt = 0; attempt < 3; attempt++) {
    await page.locator("#email").click();
    await page.locator("#email").fill("");
    await page.locator("#email").type(email, { delay: 15 });
    await page.locator("#password").click();
    await page.locator("#password").fill("");
    await page.locator("#password").type(password, { delay: 15 });
    await page.waitForTimeout(400);
    if (await btn.isEnabled().catch(() => false)) break;
    await page.waitForTimeout(800);
  }
  await btn.click({ timeout: 8000 });
  await page.waitForURL(/\/$/, { timeout: 15000 });
}

// The concrete "this page has loaded" marker per route — replaces networkidle for the data-backed
// pages that flake. Pipeline board = the "Prospects" KPI; others fall back to domcontentloaded only.
function loadedMarker(url) {
  if (url.startsWith("/pipeline")) return "Prospects";
  return null;
}

try {
  await login();
  console.log(`### LOGGED IN as ${email}\n`);
  for (let i = 0; i < steps.length; i++) {
    const st = steps[i];
    consoleErrs = [];
    const before = netErrs.length;
    let status = "ok";
    try {
      if (st.do === "goto") {
        await page.goto(`${BASE}${st.url}`, { waitUntil: "domcontentloaded", timeout: 20000 });
        const marker = st.waitfor ?? loadedMarker(st.url);
        if (marker) await waitLoaded(marker);
      }
      else if (st.do === "fill") await locator(page, st.target).fill(st.value, { timeout: 8000 });
      else if (st.do === "click") await locator(page, st.target).click({ timeout: 8000 });
      else if (st.do === "select") await locator(page, st.target).selectOption(st.value, { timeout: 8000 });
      else if (st.do === "waittext") await page.getByText(st.value, { exact: false }).first().waitFor({ timeout: 10000 });
      else if (st.do === "shot") await page.screenshot({ path: `${outdir}/${st.name}.png` });
      else if (st.do === "read") {} // just dump below
      await page.waitForTimeout(600);
    } catch (e) {
      status = "FAILED: " + trim(e.message).slice(0, 200);
    }
    const url = page.url().replace(BASE, "");
    let text = "";
    if (st.do !== "shot") {
      try { text = trim(await page.locator("main, body").first().innerText()); } catch { text = "(no text)"; }
    }
    const newNet = netErrs.slice(before);
    console.log(`### STEP ${i + 1} [${st.do}${st.target ? " " + st.target : ""}${st.url ? " " + st.url : ""}${st.value ? " = " + st.value : ""}] ${st.note ? "— " + st.note : ""}`);
    console.log(`URL: ${url} | ${status}`);
    if (consoleErrs.length) console.log(`CONSOLE-ERR: ${consoleErrs.slice(0, 3).join(" || ")}`);
    if (newNet.length) console.log(`API-ERR: ${newNet.slice(0, 4).join(" || ")}`);
    if (text) console.log(`PAGE: ${text}`);
    console.log("");
  }
} catch (e) {
  console.log("FATAL:", e.message);
} finally {
  await browser.close();
}
