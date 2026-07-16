import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Settings — Advisor Studio",
  description: "Advisor Studio preferences.",
};

/**
 * Settings page (GRS-0087). A minimal placeholder reachable from the header account menu so the link
 * resolves. Preferences (notifications, display, session) land in a later Part-2 ticket.
 */
export default function SettingsPage() {
  return (
    <div className="stack" style={{ gap: "1.5rem", maxWidth: "38rem" }}>
      <div>
        <p className="eyebrow">Account</p>
        <h1 style={{ margin: "0.4rem 0 0.4rem" }}>Settings</h1>
        <p style={{ margin: 0, color: "var(--color-ink-muted)" }}>
          Preferences for notifications, display, and your session are coming soon.
        </p>
      </div>
      <div className="card" style={{ padding: "1.25rem 1.35rem", color: "var(--color-ink-muted)" }}>
        There is nothing to configure yet. To sign out, use the account menu in the header.
      </div>
    </div>
  );
}
