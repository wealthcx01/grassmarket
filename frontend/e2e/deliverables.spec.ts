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
    // Filter past Next.js's always-present empty #__next-route-announcer__ (also role="alert").
    const alert = page.getByRole("alert").filter({ hasText: /client-usable|client_usable=False|Refusing/i });
    await expect(alert).toBeVisible();
    await expect(alert).toContainText(/client-usable|client_usable=False/i);
  });
});

test.describe("GRS-0019 slice 2 — AI narrative review", () => {
  test("draft → edit → approve an AI narrative section", async ({ page }) => {
    await login(page);
    await openSeededEngagement(page);

    // Ensure a deliverable exists to attach narratives to.
    await page.getByLabel("Deliverable type").selectOption("platform_power_report");
    await page.getByRole("button", { name: "Generate" }).click();
    await expect(page.getByText(/Generated Platform Power Report/i)).toBeVisible();

    // Open the AI-narrative review on the deliverable we just generated. The library accumulates
    // rows across tests/retries and is ordered oldest-first, so `.first()` would target an
    // arbitrary earlier deliverable (possibly a different type with no Interpretation section) —
    // the source of the historical flake. `.last()` of this type's rows is *this* run's fresh,
    // un-drafted deliverable, deterministic across runs and retries.
    const row = page.getByRole("row").filter({ hasText: "Platform Power Report" }).last();
    await row.getByRole("button", { name: "Review AI" }).click();
    const draft = page.getByRole("button", { name: "Draft AI narratives" });
    if (await draft.isVisible().catch(() => false)) await draft.click();

    // Edit the AI draft and approve (the seeded advisor is Consultant-tier → may self-approve).
    const box = page.getByRole("textbox", { name: /Edit Interpretation/ }).first();
    await expect(box).toBeVisible();
    await box.fill("Reviewed interpretation for Meridian Securities.");
    await page.getByRole("button", { name: /Approve/ }).first().click();

    await expect(page.getByText(/Interpretation approved/i)).toBeVisible();
  });
});

test.describe("GRS-0019 slice 3 — review gate + approval queue", () => {
  test("unapproved AI sections show the pack as not client-ready", async ({ page }) => {
    await login(page);
    await openSeededEngagement(page);

    await page.getByLabel("Deliverable type").selectOption("executive_summary");
    await page.getByRole("button", { name: "Generate" }).click();
    await expect(page.getByText(/Generated Executive Summary/i)).toBeVisible();

    // Review the deliverable we just generated (see slice 2 for why `.last()`, not `.first()`).
    const row = page.getByRole("row").filter({ hasText: "Executive Summary" }).last();
    await row.getByRole("button", { name: "Review AI" }).click();
    const draft = page.getByRole("button", { name: "Draft AI narratives" });
    if (await draft.isVisible().catch(() => false)) await draft.click();

    // The review gate is visible: the queue banner warns the pack cannot go to a client yet
    // (the banner counts pending sections engagement-wide, so the fresh draft must land first).
    await expect(page.getByText(/awaiting approval/i)).toBeVisible();
  });
});
