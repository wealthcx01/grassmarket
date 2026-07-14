"""Production smoke suite (GRS-0034) — read-only checks + a solo write-and-cleanup lifecycle.

Runnable against a live Grassmarket API by URL, or in-process (``tests/test_prod_smoke.py``) so the
smoke logic itself is CI-covered and cannot silently rot. Exits non-zero on the first failure.

Coverage:
  * Health: ``/health`` (liveness) and ``/health/ready`` (DB ping). No auth.
  * Authenticated reads (with ``--email``/``--password``): ``/auth/me``, ``/registry``,
    ``/pipeline/board``, ``/prospects``, ``/assessments``, ``/engagements``, ``/earnings/summary``.
  * Write lifecycle (``--write``): create a disposable prospect, walk it through the stage machine
    to Contracted, open an assessment, autosave a scoreable document (built from the live registry),
    read its live score, then archive the prospect (Closed). Single-account. The prospect is
    archived; the disposable assessment is left behind as harmless owner-scoped residue (no
    delete-assessment endpoint — a draft assessment is immutable-by-design, never client-visible).

NOT covered here, by design: finalise → deliverable. Finalisation is governance-gated (dual-rating
consensus + Rating Committee sign-off, Methodology §8/§9) and needs a second rater and a committee
member seeded server-side — it cannot be driven by a single HTTP client. That full lifecycle is
exercised end-to-end in CI by ``tests/test_prod_smoke.py`` against an in-process app. This is
logged, never silently skipped.

Usage:
    uv run python scripts/prod_smoke.py --base-url https://advisors.bruntsfieldcapital.com \\
        --email OP_EMAIL --password OP_PASS            # read-only (safe on live prod)
    uv run python scripts/prod_smoke.py --base-url https://staging... \\
        --email OP_EMAIL --password OP_PASS --write     # + solo write-and-cleanup
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

# The client is any object exposing httpx's ``request(method, url, json=, headers=)`` — an
# ``httpx.Client`` (live URL) or a starlette ``TestClient`` (in-process CI). Typed ``Any`` because
# the two have compatible-but-not-identical signatures.
HttpClient = Any


class SmokeError(RuntimeError):
    """A smoke step failed — the API is not healthy for launch."""


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class Smoke:
    """Runs steps, prints a ✓/✗ line each, and remembers whether anything failed."""

    def __init__(self, client: HttpClient) -> None:
        self.client = client
        self.failures: list[str] = []

    def call(
        self,
        method: str,
        path: str,
        *,
        expect: int = 200,
        token: str | None = None,
        json: Any = None,
        label: str | None = None,
    ) -> Any:
        headers = _bearer(token) if token else {}
        label = label or f"{method} {path}"
        try:
            resp = self.client.request(method, path, json=json, headers=headers)
        except Exception as exc:  # noqa: BLE001 — a transport error is a smoke failure, report it
            self._fail(label, f"request raised {type(exc).__name__}: {exc}")
            raise SmokeError(label) from exc
        if resp.status_code != expect:
            body = resp.text[:200] if hasattr(resp, "text") else ""
            self._fail(label, f"expected {expect}, got {resp.status_code}. {body}")
            raise SmokeError(label)
        print(f"  ✓ {label} -> {resp.status_code}")
        return resp

    def _fail(self, label: str, detail: str) -> None:
        self.failures.append(f"{label}: {detail}")
        print(f"  ✗ {label} -> {detail}")


# --- Steps --------------------------------------------------------------------------------


def check_health(smoke: Smoke) -> str:
    """Liveness + readiness. Returns the reported environment."""
    body = smoke.call("GET", "/health", label="health (liveness)").json()
    if body.get("status") != "ok":
        raise SmokeError(f"/health status was {body.get('status')!r}, not 'ok'")
    smoke.call("GET", "/health/ready", label="health/ready (DB ping)")
    return str(body.get("env", "?"))


def login(smoke: Smoke, email: str, password: str) -> str:
    """Log in and return the bearer access token."""
    body = smoke.call(
        "POST", "/auth/login", json={"email": email, "password": password}, label="login"
    ).json()
    token = body.get("access_token")
    if not token:
        raise SmokeError("login returned no access_token")
    return str(token)


def read_only_checks(smoke: Smoke, token: str) -> None:
    """Every authenticated read a smoke check should touch — all owner-scoped, all must 200. This is
    a liveness probe of each path, not a data-correctness check: a 200 with unexpected body is a
    pass here. Data scoping / body correctness is covered by the test suite, not the smoke."""
    for path, label in (
        ("/auth/me", "who am I"),
        ("/registry", "registry"),
        ("/pipeline/board", "pipeline board"),
        ("/prospects", "prospects list"),
        ("/assessments", "assessments list"),
        ("/engagements", "engagements list"),
        ("/earnings/summary", "earnings summary"),
    ):
        smoke.call("GET", path, token=token, label=label)


def build_scoreable_document(registry: dict[str, Any], *, subject: str) -> dict[str, Any]:
    """Build the minimal scoreable AssessmentDocument from the LIVE registry, so the smoke doc never
    drifts from the deployed registry: all powers graded, one metric graded, one subcomponent rated.
    Enum values match the API's JSON serialisation (Emerging / E3 / Advanced / audited)."""
    powers = [
        {
            "power_key": p["key"],
            "benefit": "Emerging",
            "barrier": "Emerging",
            "benefit_grade": "E3",
            "barrier_grade": "E3",
        }
        for p in registry["powers"]
    ]
    metric = registry["metrics"][0]
    module = registry["modules"][0]
    subcomponent = module["subcomponents"][0]
    return {
        "subject": subject,
        "powers": powers,
        "metrics": [{"metric_key": metric["key"], "raw": 1.0, "confidence": "audited"}],
        "subcomponents": [
            {
                "module_key": module["key"],
                "subcomponent_key": subcomponent["key"],
                "level": "Advanced",
                "evidence_grade": "E3",
            }
        ],
    }


_TO_CONTRACTED = (
    "workshop_scheduled",
    "workshop_delivered",
    "qualified",
    "scoped",
    "contracted",
)


def write_lifecycle(smoke: Smoke, token: str) -> None:
    """Solo write path: prospect through the stage machine to Contracted, an assessment autosaved
    with a scoreable document + live-scored, then the prospect archived (Closed). The prospect is
    cleaned up; the disposable assessment remains (harmless, owner-scoped — no delete endpoint)."""
    pid = smoke.call(
        "POST",
        "/prospects",
        json={"company_name": "Smoke Test Co (disposable)"},
        expect=201,
        token=token,
        label="create prospect",
    ).json()["id"]

    for stage in _TO_CONTRACTED:
        smoke.call(
            "PATCH",
            f"/prospects/{pid}/stage",
            json={"stage": stage},
            token=token,
            label=f"stage -> {stage}",
        )

    registry = smoke.call("GET", "/registry", token=token, label="registry (for doc)").json()
    aid = smoke.call(
        "POST",
        "/assessments",
        json={"subject": "Smoke Test (disposable)"},
        expect=201,
        token=token,
        label="create assessment",
    ).json()["id"]
    smoke.call(
        "PUT",
        f"/assessments/{aid}",
        json=build_scoreable_document(registry, subject="Smoke Test (disposable)"),
        token=token,
        label="autosave scoreable document",
    )
    smoke.call("GET", f"/assessments/{aid}/live-score", token=token, label="live score")

    # Archive the disposable prospect (Closed is an off-ramp from any stage) — clean up after us.
    smoke.call(
        "PATCH",
        f"/prospects/{pid}/stage",
        json={"stage": "closed"},
        token=token,
        label="archive prospect (closed)",
    )


def run(
    smoke: Smoke,
    *,
    email: str | None,
    password: str | None,
    do_writes: bool,
) -> int:
    """Run the smoke suite. Returns a process exit code (0 = all green). A failed step stops the
    run (the API is unhealthy); the failure is reported, never a bare traceback."""
    try:
        print("== Health ==")
        env = check_health(smoke)
        print(f"   environment: {env}")

        if email and password:
            print("== Authenticated reads ==")
            token = login(smoke, email, password)
            read_only_checks(smoke, token)
            if do_writes:
                print("== Write lifecycle (disposable) ==")
                write_lifecycle(smoke, token)
            else:
                print("   (writes skipped — pass --write to exercise the solo write lifecycle)")
        else:
            print("   (no --email/--password — health only; pass creds for authenticated reads)")
    except SmokeError as exc:
        if not smoke.failures:  # a raise-without-record path (e.g. bad response body)
            smoke.failures.append(str(exc))

    print(
        "\nNote: finalise -> deliverable is governance-gated (dual-rating + committee, §8/§9) and "
        "needs server-seeded principals; it is NOT run here. It is covered end-to-end in CI by "
        "tests/test_prod_smoke.py."
    )
    if smoke.failures:
        print(f"\nSMOKE FAILED — {len(smoke.failures)} step(s):")
        for f in smoke.failures:
            print(f"  - {f}")
        return 1
    print("\nSMOKE PASSED.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Grassmarket production smoke suite.")
    parser.add_argument("--base-url", required=True, help="API base URL, e.g. https://advisors...")
    parser.add_argument("--email", help="Operator login email (enables authenticated reads).")
    parser.add_argument("--password", help="Operator login password.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Also run the solo write-and-cleanup lifecycle (prefer staging / a window).",
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="Per-request timeout seconds.")
    args = parser.parse_args(argv)

    import httpx

    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=args.timeout) as client:
        smoke = Smoke(client)
        return run(smoke, email=args.email, password=args.password, do_writes=args.write)


if __name__ == "__main__":
    sys.exit(main())
