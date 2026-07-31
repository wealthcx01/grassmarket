// GRS-0221 — measure the Stage 6 rail overlap the founder reported, then screenshot it.
// Usage: node measure-rail.mjs <before|after> <outdir>
//
// The founder's words were "the Platform Value Finalised box seems to be fixed on the page, and
// then when you scroll the 'recommended to sell' box moves underneath". That is a geometric claim,
// so it is measured geometrically: with the page scrolled, how many pixels of the sell panel are
// covered by the pinned score card. A style-declaration test cannot see this — GRS-0209 was the
// lesson (its unit test passed while the page was visibly wrong).
//
// Three numbers per viewport:
//   overlapPx     — how far the sell panel is underneath the score card. The defect. Must be 0.
//   unreachablePx — how much of a pinned rail sits below the viewport with no way to scroll to it,
//                   which is the short-viewport failure mode the ticket asks about separately.
//   hiddenBehindHeaderPx — how much of the pinned element is swallowed by the sticky site header.
//                   Not in the founder's report; found by auditing the step (scope item 3).
// playwright-core is CommonJS; the default-import form is the one that works under plain node.
import playwright from "/home/dev/projects/grassmarket/frontend/node_modules/playwright-core/index.js";
import { mkdirSync, writeFileSync } from "node:fs";

const { chromium } = playwright;

const [label, outdir] = process.argv.slice(2);
const BASE = "http://localhost:3000";
const EXE = "/home/dev/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome";
const ASSESSMENT = process.env.ASSESSMENT_ID;

// The three widths GRS-0209 used, plus the short viewport the ticket calls out (scope item 4).
// A finalised assessment opens on Summary & Interpretation, which is the founder's screen.
const VIEWPORTS = [
  { name: "1280", width: 1280, height: 950 },
  { name: "1440", width: 1440, height: 950 },
  { name: "1920", width: 1920, height: 1080 },
  { name: "short", width: 1440, height: 640 },
];

mkdirSync(outdir, { recursive: true });

const browser = await chromium.launch({ executablePath: EXE, headless: true });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 950 } });
const page = await ctx.newPage();

await page.goto(`${BASE}/login`, { waitUntil: "networkidle" });
await page.locator('input[type="email"]').first().fill("advisor@bruntsfieldcapital.com");
await page.locator('input[type="password"]').first().fill("grassmarket-demo"); // pragma: allowlist secret
await page.getByRole("button", { name: /sign in with email/i }).first().click();
await page.waitForURL((u) => !u.pathname.includes("/login"), { timeout: 20000 }).catch(() => {});
await page.waitForTimeout(1200);

const results = {};
for (const vp of VIEWPORTS) {
  await page.setViewportSize({ width: vp.width, height: vp.height });
  await page.goto(`${BASE}/assessments/${ASSESSMENT}`, { waitUntil: "networkidle" });
  await page.locator("[data-wizard-rail]").waitFor({ timeout: 20000 });
  await page.waitForTimeout(1500); // the rail's panels load their own data

  // The defect is something the founder sees *while scrolling* — the sell panel passing underneath
  // the pinned card — so a single scroll position proves nothing. (Measured at half-document first:
  // the panel is already above the viewport there, giving a large rectangle overlap that is not on
  // screen and is not what anyone sees.) Sweep the scroll range instead and keep the worst overlap
  // that is actually visible, then park the page there so the screenshot shows that moment.
  const worstY = await page.evaluate(() => {
    const rail = document.querySelector("[data-wizard-rail]");
    const kids = [...rail.children];
    const score = kids[0];
    const below = kids[kids.length - 1];
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    let best = { y: 0, visibleOverlap: -1 };
    for (let i = 0; i <= 60; i++) {
      const y = Math.round((maxScroll * i) / 60);
      window.scrollTo(0, y);
      const s = score.getBoundingClientRect();
      const b = below.getBoundingClientRect();
      // Overlap clamped to the viewport: only pixels a human could actually be looking at.
      const top = Math.max(s.top, b.top, 0);
      const bottom = Math.min(s.bottom, b.bottom, window.innerHeight);
      const visibleOverlap = Math.max(0, bottom - top);
      if (visibleOverlap > best.visibleOverlap) best = { y, visibleOverlap };
    }
    window.scrollTo(0, best.y);
    return best.y;
  });
  await page.waitForTimeout(700);

  const m = await page.evaluate(() => {
    const rail = document.querySelector("[data-wizard-rail]");
    const kids = [...rail.children];
    const score = kids[0]; // LiveSummary — the "Platform Value" card
    const below = kids[kids.length - 1]; // the sell / suggestions panel under it
    const box = (el) => {
      const r = el.getBoundingClientRect();
      return {
        top: +r.top.toFixed(1),
        bottom: +r.bottom.toFixed(1),
        height: +r.height.toFixed(1),
      };
    };
    const s = box(score);
    const b = box(below);
    const railBox = box(rail);

    // Overlapping rectangles are not proof that one is painted over the other, so probe the paint
    // stack. Probe inside the overlap AND inside the viewport — the panel's own top edge is often
    // scrolled off-screen, where elementFromPoint returns null and would read as a false clear.
    const probeX = Math.round(rail.getBoundingClientRect().left + rail.clientWidth / 2);
    const overlapTop = Math.max(b.top, s.top, 0);
    const overlapBottom = Math.min(b.bottom, s.bottom, window.innerHeight);
    const probeY = Math.round((overlapTop + overlapBottom) / 2);
    const probeValid = overlapBottom > overlapTop;
    // elementsFromPoint is the whole stack, topmost first: if the score card appears before the
    // panel, the panel is genuinely underneath it at a point they share.
    const stack = probeValid ? [...document.elementsFromPoint(probeX, probeY)] : [];
    const iScore = stack.findIndex((el) => score.contains(el));
    const iBelow = stack.findIndex((el) => below.contains(el));
    const coveredByScoreCard = probeValid && iScore !== -1 && iBelow !== -1 && iScore < iBelow;

    // A rail that is PINNED and taller than the viewport hides its own tail: nothing the user can
    // do brings the bottom into view. This only applies to a pinned rail — an unpinned one scrolls
    // with the page, so its tail is always reachable and counting it would invent a defect. It is
    // also 0 if the rail scrolls internally, which is the fix for exactly this.
    const railPinned = getComputedStyle(rail).position === "sticky";
    const railScrollable = rail.scrollHeight > rail.clientHeight + 1;
    const unreachablePx =
      !railPinned || railScrollable
        ? 0
        : +Math.max(0, railBox.bottom - window.innerHeight).toFixed(1);

    // The site header is itself sticky (z-index 50). A rail pinned above its bottom edge tucks
    // underneath it — the same "sticky thing covers content" defect one layer up, and the part it
    // ate was the score card's own heading. Found by auditing the step per scope item 3.
    // Measure whichever element is actually pinned — the rail after the fix, the score card before
    // it. Measuring only the rail would score the old layout a false 0, because there the rail is
    // static and it is the card that tucks under.
    const hdr = document.querySelector("header");
    const hdrBottom = hdr ? hdr.getBoundingClientRect().bottom : 0;
    const pinnedBox = railPinned
      ? railBox
      : getComputedStyle(score).position === "sticky"
        ? s
        : null;
    const hiddenBehindHeaderPx = pinnedBox
      ? +Math.max(0, hdrBottom - pinnedBox.top).toFixed(1)
      : 0;

    return {
      scoreCard: s,
      panelBelow: b,
      hiddenBehindHeaderPx,
      railPosition: getComputedStyle(rail).position,
      scoreCardPosition: getComputedStyle(score).position,
      railMaxHeight: getComputedStyle(rail).maxHeight,
      railOverflowY: getComputedStyle(rail).overflowY,
      // Positive = the panel below has slid under the score card by this many pixels.
      // The number that matters: pixels of the panel hidden behind the card, on screen.
      overlapPx: +Math.max(0, overlapBottom - overlapTop).toFixed(1),
      coveredByScoreCard,
      probeY: probeValid ? probeY : null,
      unreachablePx,
    };
  });

  // Reachability is a separate question from overlap and has to be asked where sticky is actually
  // engaged. At scroll 0 nothing is pinned yet, so a rail hanging below the fold there is just a
  // long page, not a trap — measuring it at the overlap-worst position (which is scroll 0 once the
  // overlap is fixed) reported a 238px "unreachable" tail that scrolling reaches perfectly well.
  const reach = await page.evaluate(() => {
    const rail = document.querySelector("[data-wizard-rail]");
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    window.scrollTo(0, Math.round(maxScroll * 0.8));
    const cs = getComputedStyle(rail);
    const r = rail.getBoundingClientRect();
    const railPinned = cs.position === "sticky";
    const railScrollable = rail.scrollHeight > rail.clientHeight + 1;
    return {
      atScrollY: Math.round(maxScroll * 0.8),
      railPinnedHere: railPinned,
      railScrollsInternally: railScrollable,
      // Pixels of a pinned rail that no scrolling can bring into view.
      unreachablePx:
        !railPinned || railScrollable ? 0 : +Math.max(0, r.bottom - window.innerHeight).toFixed(1),
    };
  });
  await page.waitForTimeout(300);

  results[vp.name] = { viewport: vp, worstScrollY: worstY, ...m, reach };
  await page.screenshot({ path: `${outdir}/${label}-${vp.name}.png` });
  console.log(
    `${label} ${vp.name} (${vp.width}x${vp.height}): overlap=${m.overlapPx}px ` +
      `covered=${m.coveredByScoreCard} unreachable=${reach.unreachablePx}px ` +
      `underHeader=${m.hiddenBehindHeaderPx}px ` +
      `rail=${m.railPosition} card=${m.scoreCardPosition}`
  );
}

writeFileSync(`${outdir}/${label}-measurements.json`, JSON.stringify(results, null, 2));
await browser.close();
