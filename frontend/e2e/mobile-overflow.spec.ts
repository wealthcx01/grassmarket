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

// The top-level signed-in pages. Pages with an ID in the address share the same header, so the
// header fix covers them too.
const ROUTES = [
  "/",
  "/pipeline",
  "/prospecting",
  "/engagements",
  "/portfolio",
  "/deliverables",
  "/earnings",
  "/workbench",
  "/workbench/academy",
  "/workbench/courses",
  "/guide",
  "/profile",
  "/settings",
];

// GRS-0279: on a 393px phone the header's account button printed the whole email address, which
// made every signed-in page about 590px wide and scroll sideways. No page may be wider than the
// screen.
test.describe("GRS-0279 — no sideways scroll on a phone", () => {
  test.use({ viewport: { width: 393, height: 851 } });

  test("every top-level signed-in page fits a 393px screen", async ({ page }) => {
    test.setTimeout(120_000);
    await login(page);
    for (const route of ROUTES) {
      await page.goto(route);
      await expect(page.getByRole("button", { name: /account menu/i })).toBeVisible();
      await page.waitForLoadState("networkidle");
      const { scrollWidth, clientWidth } = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
      }));
      expect(scrollWidth, `${route} is ${scrollWidth}px wide on a ${clientWidth}px screen`)
        .toBeLessThanOrEqual(clientWidth);
    }
  });
});
