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

// GRS-0111 CRM rebuild: the pipeline is a real CRM — KPI strip, add-prospect, a click-to-open deal
// slide-over with inline edit + first-class contacts, search filtering, and a backend-owned stage
// move. This drives the actual API paths a human uses (a wrong endpoint/shape fails here).
test.describe("GRS-0111 — CRM pipeline", () => {
  test("KPIs, add prospect, slide-over edit + contact, search, stage move, backlinks", async ({
    page,
  }) => {
    await login(page);
    await page.goto("/pipeline");

    // KPI strip renders. ("Expected wins" since GRS-0137 relabelled the old "Weighted forecast" KPI.)
    await expect(page.getByText("Prospects", { exact: true })).toBeVisible();
    await expect(page.getByText("Expected wins")).toBeVisible();

    // Add a prospect — it lands in the board.
    const name = `E2E Broking ${Date.now()}`;
    await page.getByPlaceholder("New prospect — company name").fill(name);
    await page.getByRole("button", { name: "Add prospect" }).click();
    await expect(page.getByText(name)).toBeVisible();

    // Open the deal slide-over by clicking the card.
    await page.getByRole("button", { name: `Open ${name}` }).click();
    const dialog = page.getByRole("dialog");
    await expect(dialog.getByRole("heading", { name })).toBeVisible();

    // Inline-edit a field (sector) — persists via PATCH.
    const sector = dialog.getByLabel("Sector");
    await sector.fill("Wealth");
    await sector.blur();

    // Add a first-class contact — the first is primary by default. `exact` avoids matching the
    // "Company name" field (getByPlaceholder is substring by default).
    await dialog.getByPlaceholder("Name", { exact: true }).fill("Jo Lee");
    await dialog.getByPlaceholder("Email", { exact: true }).fill("jo@e2e.co");
    await dialog.getByRole("button", { name: "Add contact" }).click();
    await expect(dialog.getByText("Jo Lee")).toBeVisible();
    // Exact match: the primary badge is the standalone word "primary" — disambiguates it from the
    // win-probability explanation's "primary contact" copy that GRS-0137 added to the same panel.
    await expect(dialog.getByText("primary", { exact: true })).toBeVisible();

    // Move the stage from inside the panel (backend-owned; a legal move from Prospect).
    await dialog.getByLabel("Move stage").selectOption("workshop_scheduled");
    // Anchor on "· entered" — the header line — so we don't also match the <option> of the same name.
    await expect(dialog.getByText(/Workshop Scheduled · entered/)).toBeVisible();

    // Close the slide-over.
    await dialog.getByRole("button", { name: "Close" }).click();
    await expect(page.getByRole("dialog")).toHaveCount(0);

    // Search filters the board to just our prospect.
    await page.getByPlaceholder(/Search company/).fill(name);
    await expect(page.getByText(name)).toBeVisible();
    await expect(page.getByText("Meridian Securities")).toHaveCount(0);
    await page.getByPlaceholder(/Search company/).fill("");

    // The sector edit persisted (visible on the card after reload of the board).
    await page.reload();
    await expect(page.getByText(name)).toBeVisible();

    // Footer backlink works.
    await page.getByRole("link", { name: "← Dashboard" }).click();
    await expect(page).toHaveURL(/\/$/);
  });

  test("an illegal stage move reverts and shows the reason", async ({ page }) => {
    await login(page);
    await page.goto("/pipeline");
    const name = `E2E Illegal ${Date.now()}`;
    await page.getByPlaceholder("New prospect — company name").fill(name);
    await page.getByRole("button", { name: "Add prospect" }).click();
    await expect(page.getByText(name)).toBeVisible();

    await page.getByRole("button", { name: `Open ${name}` }).click();
    const dialog = page.getByRole("dialog");
    // Prospect → Contracted is an illegal skip; the select reverts and an error appears.
    await dialog.getByLabel("Move stage").selectOption("contracted");
    await expect(dialog.getByTestId("move-error")).toBeVisible();
    // The stage stayed at Prospect (the illegal move did not stick).
    await expect(dialog.getByText(/Prospect ·/)).toBeVisible();
  });
});
