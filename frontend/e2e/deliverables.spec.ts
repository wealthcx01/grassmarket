import { expect, test, type Page } from "@playwright/test";

// Matches scripts/seed_dev.py.
const EMAIL = "advisor@bruntsfieldcapital.com";
const PASSWORD = "grassmarket-demo";

async function login(page: Page): Promise<void> {
  await page.goto("/login");
  const signIn = page.getByRole("button", { name: "Sign in" });
  // Re-fill until the values stick — the login page is a client component, so an early fill can
  // land before React hydrates and get reset. The button enabling is the "state updated" signal.
  await expect(async () => {
    await page.locator("#email").fill(EMAIL);
    await page.locator("#password").fill(PASSWORD);
    await expect(signIn).toBeEnabled({ timeout: 1000 });
  }).toPass({ timeout: 15000 });
  await signIn.click();
  // Lands on the dashboard once the token is stored.
  await expect(page).toHaveURL(/\/$/);
}

async function openSeededEngagement(page: Page): Promise<void> {
  await page.goto("/engagements");
  await page.getByRole("link", { name: /Meridian/ }).first().click();
  await expect(page.getByRole("heading", { name: "Deliverables" })).toBeVisible();
}

test.describe("GRS-0019 slice 1 — deliverable library", () => {
  test("advisor generates an internal-draft deliverable and sees it in the library", async ({
    page,
  }) => {
    await login(page);
    await openSeededEngagement(page);

    // Internal draft is the default audience; choose a document and generate.
    await page.getByLabel("Deliverable type").selectOption("technical_appendix");
    await page.getByRole("button", { name: "Generate" }).click();

    // A plain-English success notice, and the document appears in the library table.
    await expect(page.getByText(/Generated Technical Appendix/i)).toBeVisible();
    await expect(
      page.getByRole("cell", { name: /Technical Appendix/ }).first(),
    ).toBeVisible();
    // Its audience badge reads DRAFT — never mistaken for a client pack.
    await expect(page.getByText("Draft").first()).toBeVisible();
  });

  test("client-facing generation is refused with a plain-English gate message", async ({
    page,
  }) => {
    await login(page);
    await openSeededEngagement(page);

    await page.getByLabel("Client-facing").check();
    await page.getByRole("button", { name: "Generate" }).click();

    // The client-usable gate refuses (draft coefficient set) — the human sees WHY, not a 409.
    const alert = page.getByRole("alert");
    await expect(alert).toBeVisible();
    await expect(alert).toContainText(/client-usable|client_usable=False/i);
  });
});
