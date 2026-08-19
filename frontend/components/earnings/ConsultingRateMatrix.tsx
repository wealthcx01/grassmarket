/**
 * The consulting rates as an actual 2×2 (GRS-0240 scope 3).
 *
 * These four rates were rendered as four look-alike cards, each headed with a compound label like
 * "Bruntsfield-led · Self-sourced". Four undefined terms in two dimensions, presented as though
 * they were four unrelated products. An advisor could read all four and still not see that the
 * rate depends on exactly two questions — *who delivers it* and *who brought it in* — which is the
 * only thing they need to know to work out what they will take on a given engagement.
 *
 * A grid says that with its shape. The axes are labelled and defined; the cells carry only numbers.
 *
 * Built from the carrots the API returns, never from a hardcoded 2×2: the schedule is config
 * (ADR-0026), and a rate change in `commissions.yaml` must reflow here with no frontend edit. If a
 * cell is missing from the schedule the grid says so rather than rendering an empty box that reads
 * as 0%.
 */

import { MoneyAmount } from "@/components/MoneyAmount";
import type { ConsultancyCommissionCarrot } from "@/lib/types";

export function ConsultingRateMatrix({ carrots }: { carrots: ConsultancyCommissionCarrot[] }) {
  if (carrots.length === 0) return null;

  // Axis values in the order the schedule returned them — first-seen order, so the grid follows
  // the config rather than an alphabetisation that would reorder on a rename.
  const deliveries: { key: string; label: string }[] = [];
  const sourcings: { key: string; label: string }[] = [];
  for (const c of carrots) {
    if (!deliveries.some((d) => d.key === c.delivery_type))
      deliveries.push({ key: c.delivery_type, label: c.delivery_label });
    if (!sourcings.some((s) => s.key === c.sourcing))
      sourcings.push({ key: c.sourcing, label: c.sourcing_label });
  }
  const cell = (delivery: string, sourcing: string) =>
    carrots.find((c) => c.delivery_type === delivery && c.sourcing === sourcing);

  return (
    <div style={{ overflowX: "auto" }} data-testid="consulting-rate-matrix">
      <table style={{ borderCollapse: "collapse", minWidth: "30rem" }}>
        <caption
          style={{
            textAlign: "left",
            fontSize: "0.8rem",
            color: "var(--color-ink-muted)",
            marginBottom: "0.5rem",
            maxWidth: "44rem",
          }}
        >
          Your rate depends on two things. <strong>Who delivers it</strong> — whether Bruntsfield
          runs the engagement or you do. <strong>Who brought it in</strong> — whether Bruntsfield
          sourced the client or you did. Find your row and column.
        </caption>
        <thead>
          <tr>
            <th scope="col" style={{ textAlign: "left", fontSize: "0.72rem", color: "var(--color-ink-faint)" }}>
              Delivered by ↓ &nbsp; Sourced by →
            </th>
            {sourcings.map((s) => (
              <th key={s.key} scope="col" style={{ textAlign: "left", fontSize: "0.82rem", padding: "0.4rem 0.7rem" }}>
                {s.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {deliveries.map((d) => (
            <tr key={d.key} style={{ borderTop: "1px solid var(--color-border)" }}>
              <th scope="row" style={{ textAlign: "left", fontSize: "0.82rem", padding: "0.55rem 0.7rem 0.55rem 0" }}>
                {d.label}
              </th>
              {sourcings.map((s) => {
                const c = cell(d.key, s.key);
                return (
                  <td key={s.key} style={{ padding: "0.55rem 0.7rem", verticalAlign: "top" }}>
                    {c ? (
                      <>
                        <span className="mono" style={{ fontSize: "0.82rem", color: "var(--color-accent)" }}>
                          {c.yr1_bps / 100}% first year
                        </span>
                        <br />
                        <span className="mono" style={{ fontSize: "0.78rem", color: "var(--color-ink-muted)" }}>
                          {c.thereafter_bps / 100}% thereafter
                        </span>
                        <br />
                        {/* Italic + the word, so an example can never be mistaken for a balance. */}
                        <span style={{ fontSize: "0.74rem", color: "var(--color-ink-muted)", fontStyle: "italic" }}>
                          Illustrative: <MoneyAmount money={c.yr1_commission} /> then{" "}
                          <MoneyAmount money={c.thereafter_commission} />
                        </span>
                      </>
                    ) : (
                      // Never an empty cell: a blank box in a rate table reads as zero.
                      <span style={{ fontSize: "0.78rem", color: "var(--color-ink-faint)" }}>
                        Not in the schedule
                      </span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
