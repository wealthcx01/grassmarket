/**
 * UI gallery capture (grs-ci-ui-gate) — full-page screenshots of the key screens at desktop and
 * mobile viewports, for the `ui-gallery` CI artifact. Runs against the seeded app the E2E job
 * starts (offline fixtures via scripts/seed_dev.py — no live external calls, per CLAUDE.md).
 *
 * It logs in through the API to mint a token, injects it into localStorage (the app reads
 * `bas.access_token`), discovers the seeded prospect / engagement, and creates a workshop if the
 * seed left none — so every [id] route has real data to render. One route failing is logged but
 * never aborts the gallery.
 *
 * Env: E2E_BASE_URL (frontend, default http://localhost:3000), NEXT_PUBLIC_API_BASE_URL (API,
 * default http://localhost:8000), UI_GALLERY_OUT (output dir, default ./ui-gallery).
 */

import { chromium } from "playwright";
import { mkdirSync } from "node:fs";

const BASE = process.env.E2E_BASE_URL ?? "http://localhost:3000";
const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const OUT = process.env.UI_GALLERY_OUT ?? "ui-gallery";
const TOKEN_KEY = "bas.access_token"; // must match frontend/lib/api.ts
const EMAIL = "advisor@bruntsfieldcapital.com"; // seed_dev.py demo advisor
const PASSWORD = "grassmarket-demo";

const VIEWPORTS = [
  { tag: "desktop", width: 1280, height: 800 },
  { tag: "mobile", width: 390, height: 844 },
];

async function api(path, { method = "GET", token, body } = {}) {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${method} ${path} -> ${res.status} ${await res.text()}`);
  return res.json();
}

async function main() {
  mkdirSync(OUT, { recursive: true });

  const { access_token: token } = await api("/auth/login", {
    method: "POST",
    body: { email: EMAIL, password: PASSWORD },
  });

  const prospects = await api("/prospects", { token });
  const engagements = await api("/engagements", { token });
  // Workshop is best-effort: the seed leaves none, and creating one can fail depending on the
  // prospect's state. A missing workshop just drops that one screenshot — never abort the gallery.
  let workshops = [];
  try {
    workshops = await api("/workshops", { token });
    if (workshops.length === 0 && prospects.length > 0) {
      workshops = [
        await api("/workshops", { method: "POST", token, body: { prospect_id: prospects[0].id } }),
      ];
    }
  } catch (err) {
    console.error(`workshop setup skipped: ${err.message}`);
  }

  // Public route (no token) + authenticated routes (token injected). Detail routes only when seeded.
  const publicRoutes = [{ name: "login", path: "/login" }];
  const authRoutes = [
    { name: "dashboard", path: "/" },
    { name: "pipeline", path: "/pipeline" },
    { name: "engagements", path: "/engagements" },
    { name: "workbench", path: "/workbench" },
    { name: "earnings", path: "/earnings" },
  ];
  if (prospects[0]) authRoutes.push({ name: "prospect-detail", path: `/prospects/${prospects[0].id}` });
  if (workshops[0]) authRoutes.push({ name: "workshop-detail", path: `/workshops/${workshops[0].id}` });
  if (engagements[0]) authRoutes.push({ name: "engagement-detail", path: `/engagements/${engagements[0].id}` });

  const browser = await chromium.launch();
  let captured = 0;
  let failed = 0;
  try {
    for (const vp of VIEWPORTS) {
      // A fresh context per (viewport, auth-state): public routes see no token; auth routes get one.
      for (const [routes, withToken] of [
        [publicRoutes, false],
        [authRoutes, true],
      ]) {
        const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
        if (withToken) {
          await context.addInitScript(
            ([key, value]) => {
              try {
                window.localStorage.setItem(key, value);
              } catch {
                /* localStorage unavailable — the route will redirect to /login and still shoot */
              }
            },
            [TOKEN_KEY, token],
          );
        }
        const page = await context.newPage();
        for (const route of routes) {
          try {
            await page.goto(`${BASE}${route.path}`, { waitUntil: "networkidle", timeout: 30000 });
            await page.waitForTimeout(400); // let client fetches settle
            await page.screenshot({ path: `${OUT}/${route.name}.${vp.tag}.png`, fullPage: true });
            captured += 1;
            console.log(`captured ${route.name} (${vp.tag})`);
          } catch (err) {
            failed += 1;
            console.error(`FAILED ${route.name} (${vp.tag}): ${err.message}`);
          }
        }
        await context.close();
      }
    }
  } finally {
    await browser.close();
  }
  console.log(`\nUI gallery: ${captured} captured, ${failed} failed -> ${OUT}/`);
  // The gallery is informational (an artifact to review); a single missing shot must not fail CI.
  // A total wipe-out (nothing captured) does signal something is broken, so fail loud on that.
  if (captured === 0) process.exit(1);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
