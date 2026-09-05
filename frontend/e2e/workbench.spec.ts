import { expect, test, type Page } from "@playwright/test";

// Matches scripts/seed_dev.py.
const EMAIL = "advisor@bruntsfieldcapital.com";
const PASSWORD = "grassmarket-demo"; // pragma: allowlist secret  (local dev seed only)

async function login(page: Page): Promise<void> {
  await page.goto("/login");
  const signIn = page.getByRole("button", { name: "Sign in" });
  await expect(async () => {
    await page.locator("#email").fill(EMAIL);
    await page.locator("#password").fill(PASSWORD);
    await expect(signIn).toBeEnabled({ timeout: 1000 });
  }).toPass({ timeout: 15000 });
  await signIn.click();
  await expect(page).toHaveURL(/\/$/);
}

// GRS-0027: the Workbench is wired end-to-end against the real seeded backend. This smoke test
// exercises the actual API paths the component unit tests mock away (a wrong endpoint or response
// shape would fail here), and confirms the bench dashboard + a second tab render for a real advisor.
test.describe("GRS-0027 — Workbench", () => {
  test("the bench dashboard and certification tab load for a signed-in advisor", async ({ page }) => {
    await login(page);
    await page.goto("/workbench");

    // The bench-time dashboard is the landing tab: the prioritised queue + the performance panel.
    await expect(page.getByRole("heading", { name: "Your next actions" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "My performance" })).toBeVisible();
    // The queue always has at least one action — the item title "Opportunity Radar" also appears as
    // its kind badge, so scope to the bold item title to avoid a strict-mode double match.
    await expect(page.locator("strong", { hasText: "Opportunity Radar" }).first()).toBeVisible();
    // Performance metrics rendered (the "Level" label row is present).
    await expect(page.getByText("Level", { exact: true })).toBeVisible();

    // Switching tabs works and the certification ladder renders its rungs.
    await page.getByRole("tab", { name: "Certification" }).click();
    await expect(page.getByRole("heading", { name: "The ladder" })).toBeVisible();
    // Scoped to the ladder: since GRS-0242 a level name also appears in the provenance note
    // underneath ("the evidence recorded here supports Trained"), so a bare text match is
    // ambiguous. The assertion was always about the rung, and now says so.
    const ladder = page.getByTestId("certification-ladder");
    await expect(ladder.getByText("Trained")).toBeVisible();
    // The seeded advisor is marked Certified Lead with an empty ladder, so the rungs above what
    // the evidence supports render as held-not-earned rather than achieved (GRS-0242 scope 3).
    await expect(ladder.locator('li[data-state="earned"]')).toHaveText("Trained");
    await expect(ladder.locator('li[data-state="granted"]')).toHaveCount(3);
  });

  test("the advisor gets the four tabs, and no retired governance tab", async ({ page }) => {
    // ADR-0041 (GRS-0188): peer governance is retired, so Committee and Calibration are gone for
    // everyone — not role-gated. Founder review is absent because the seeded advisor is not the
    // founder reviewer; the Workbench asks the server rather than deciding that in the browser.
    await login(page);
    await page.goto("/workbench");
    await expect(page.getByRole("tab", { name: "Bench" })).toBeVisible();
    await expect(page.getByRole("tab")).toHaveText([
      "Bench",
      "Certification",
      // Renamed under GRS-0243 scope 2: the founder asked for "just the Academy" on 23/07.
      "Academy",
      "Practice Arena",
    ]);
    for (const gone of ["Committee", "Calibration", "Rating requests", "Founder review"]) {
      await expect(page.getByRole("tab", { name: gone })).toHaveCount(0);
    }
  });
});
