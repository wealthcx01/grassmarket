import { expect, test, type Page } from "@playwright/test";

// Matches scripts/seed_dev.py.
const EMAIL = "advisor@bruntsfieldcapital.com";
const PASSWORD = "grassmarket-demo";

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
    await expect(page.getByText("Trained")).toBeVisible();
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
      "Learning & Drills",
      "Practice Arena",
    ]);
    for (const gone of ["Committee", "Calibration", "Rating requests", "Founder review"]) {
      await expect(page.getByRole("tab", { name: gone })).toHaveCount(0);
    }
  });
});
