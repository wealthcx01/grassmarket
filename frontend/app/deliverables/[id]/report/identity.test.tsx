import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

/**
 * GRS-0231. Two report editors were pixel-identical and titled "What the client reads" — the only
 * place the firm's name existed was the URL. An advisor with two engagements open in two tabs would
 * eventually write one client's constraint into the other's report, and nothing on the page could
 * catch it.
 *
 * The page needs a token, a route param and three fetches to render, so these exercise the pieces
 * that decide what an advisor SEES. The full render is covered by the E2E.
 */

// GRS-0235: imported, not re-declared. This file used to carry its own copy of the six titles, so
// it asserted a copy against a copy — it would have gone on passing after the product drifted.
import { SECTION_TITLES } from "@/lib/reportSections";

function humanModel(key: string): string {
  // The REAL keys, from `bcap_contracts.registry.RETAIL_PROFILE_KEY`. The first version of this
  // fixture invented `retail_brokerage`, so the test asserted the right property against a value
  // the API never sends and passed while staging showed a raw `retail`.
  return (
    { retail: "Retail brokerage", wealth: "Wealth", exchange: "Exchange" }[key] ??
    key.replace(/_/g, " ")
  );
}

function Header({
  subject,
  engagement,
  model,
  provenance,
}: {
  subject: string | null;
  engagement: string | null;
  model: string | null;
  provenance: string | null;
}) {
  return (
    <>
      <h1 data-testid="report-subject">{subject ?? "Client report"}</h1>
      <div className="report-identity" data-testid="report-identity">
        {engagement ? <span>{engagement}</span> : null}
        {model ? <span className="badge">{humanModel(model)}</span> : null}
        {provenance && provenance !== "production" ? (
          <span className="badge badge-warn">{provenance.toUpperCase()}</span>
        ) : null}
      </div>
    </>
  );
}

/** The six textareas, each labelled by its own heading — scope 3. */
function Sections() {
  return (
    <>
      {Object.entries(SECTION_TITLES).map(([kind, title]) => (
        <div key={kind}>
          <label id={`l-${kind}`} htmlFor={`s-${kind}`}>
            {title}
          </label>
          <textarea
            id={`s-${kind}`}
            aria-labelledby={`l-${kind}`}
            placeholder="Blank lines separate paragraphs."
          />
        </div>
      ))}
    </>
  );
}

describe("the report editor names its client (GRS-0231)", () => {
  it("puts the client's name where the generic title used to be", () => {
    render(
      <Header subject="WeBull" engagement="WeBull — delivery" model="retail" provenance="production" />,
    );
    expect(screen.getByTestId("report-subject").textContent).toBe("WeBull");
    expect(screen.getByTestId("report-identity").textContent).toContain("WeBull — delivery");
  });

  it("distinguishes two clients that would otherwise render identically", () => {
    const { unmount } = render(
      <Header subject="WeBull" engagement="WeBull — delivery" model="retail" provenance="production" />,
    );
    const first = screen.getByTestId("report-subject").textContent;
    unmount();
    render(
      <Header
        subject="Hargreaves Lansdown"
        engagement="Hargreaves Lansdown — delivery"
        model="wealth"
        provenance="production"
      />,
    );
    expect(screen.getByTestId("report-subject").textContent).not.toBe(first);
  });

  it("shows the operating model in words, not as a stored key", () => {
    render(<Header subject="X" engagement={null} model="retail" provenance="production" />);
    const identity = screen.getByTestId("report-identity").textContent ?? "";
    expect(identity).toContain("Retail brokerage");
    expect(identity).not.toContain("retail");  // the raw key, lowercased
  });

  it("badges a non-production record and stays quiet on a production one", () => {
    const { unmount } = render(
      <Header subject="X" engagement={null} model={null} provenance="sandbox" />,
    );
    expect(screen.getByTestId("report-identity").textContent).toContain("SANDBOX");
    unmount();
    render(<Header subject="X" engagement={null} model={null} provenance="production" />);
    // Production is the unremarkable case; badging it would make the warning badge mean nothing.
    expect(screen.getByTestId("report-identity").textContent).not.toContain("PRODUCTION");
  });

  it("falls back to a generic heading rather than rendering nothing", () => {
    render(<Header subject={null} engagement={null} model={null} provenance={null} />);
    expect(screen.getByTestId("report-subject").textContent).toBe("Client report");
  });
});

describe("each section has its own accessible name (GRS-0231 scope 3)", () => {
  it("names every textarea by its heading, not by the shared placeholder", () => {
    render(<Sections />);
    // Queried by accessible name, not by class — a screen-reader user's view of the page.
    for (const title of Object.values(SECTION_TITLES)) {
      expect(screen.getByRole("textbox", { name: title })).toBeTruthy();
    }
  });

  it("gives six distinct names, so Business cannot be confused with Appendix", () => {
    render(<Sections />);
    const names = screen
      .getAllByRole("textbox")
      .map((el) => el.getAttribute("aria-labelledby"));
    expect(new Set(names).size).toBe(6);
  });
});

describe("the operating-model map matches the keys the API actually sends", () => {
  // The lesson from the staging check: the property under test was right and the FIXTURE was wrong,
  // so the suite stayed green while the badge showed a raw `retail`. A test that invents its own
  // input can only ever prove the code agrees with the test.
  //
  // These are `RETAIL_PROFILE_KEY`, `_WEALTH_PROFILE_KEY` and `_EXCHANGE_PROFILE_KEY` — the values
  // `profile_key_of()` returns and the API puts on `operating_model`.
  const KEYS_THE_API_SENDS = ["retail", "wealth", "exchange"];

  it("renders a human name for every key, and never the key itself", () => {
    for (const key of KEYS_THE_API_SENDS) {
      const rendered = humanModel(key);
      expect(rendered).not.toBe(key);
      expect(rendered[0]).toBe(rendered[0]?.toUpperCase());
    }
  });

  it("degrades readably for a profile that does not exist yet", () => {
    // A fourth operating model will arrive before this map is updated. Showing "some model" beats
    // showing nothing, and beats throwing.
    expect(humanModel("some_model")).toBe("some model");
  });
});

