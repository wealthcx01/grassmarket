"""Regenerate `docs/API-SURFACE.md` and `docs/openapi.json` from the live FastAPI app.

The front end is built against this surface, so it must come from the app rather than from
anyone's memory of it. Run after adding or changing a route:

    uv run python scripts/dump_api_surface.py
"""

from __future__ import annotations

import collections
import datetime
import json
import pathlib

from fastapi import FastAPI
from fastapi.routing import APIRoute

from grassmarket.web.app import create_app
from grassmarket.web.retired import retired_route

_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _api_routes(app: FastAPI):
    """Every APIRoute, reaching through FastAPI's included-router wrappers."""
    for entry in app.routes:
        inner = getattr(entry, "original_router", None)
        for route in inner.routes if inner is not None else [entry]:
            if isinstance(route, APIRoute):
                yield route


def _is_retired(route: APIRoute) -> bool:
    """Whether this route answers 410 Gone (ADR-0041), by looking for the guard dependency."""
    seen: set[int] = set()
    stack = list(route.dependant.dependencies)
    while stack:
        dependency = stack.pop()
        if dependency.call is retired_route:
            return True
        if id(dependency) in seen:
            continue
        seen.add(id(dependency))
        stack.extend(dependency.dependencies)
    return False


def _retired_operations(app: FastAPI) -> set[tuple[str, str]]:
    """The (METHOD, path) pairs that are retired.

    Derived from the app rather than listed by hand, so this document cannot claim a route is live
    after somebody retires it — or keep calling one retired after it is switched back on.
    """
    return {
        (method, route.path)
        for route in _api_routes(app)
        if _is_retired(route)
        for method in route.methods
        if method in _METHODS
    }


def main() -> None:
    app = create_app()
    spec = app.openapi()
    retired = _retired_operations(app)
    rows: dict[str, list[tuple[str, str, str]]] = collections.defaultdict(list)
    total = 0
    for path, ops in sorted(spec["paths"].items()):
        for method, op in ops.items():
            if method.upper() not in _METHODS:
                continue
            total += 1
            tag = (op.get("tags") or ["untagged"])[0]
            summary = (op.get("summary") or "").strip()
            if not summary:
                summary = (op.get("description") or "").strip().split("\n")[0][:110]
            rows[tag].append((method.upper(), path, summary))
    retired_rows = sorted(retired, key=lambda r: (r[1], r[0]))

    out: list[str] = [
        "# Grassmarket API surface\n",
        f"**Generated {datetime.date.today()} from the live FastAPI app** "
        f"(`create_app().openapi()`). **{total} endpoints** across {len(rows)} tags.\n",
        "This is the contract the front end is built against. Regenerate with "
        "`uv run python scripts/dump_api_surface.py`; the machine-readable spec is "
        "`docs/openapi.json`.\n",
        "Every route except `/health*`, `/auth/*` and the shared-report links requires a bearer "
        "JWT, and every owned resource is filtered by `owner_consultant_id` in the repository "
        "layer (non-negotiable #9). A cross-owner read returns **404, never 403** — the existence "
        "of another advisor's record is never revealed.\n",
        "## Retired routes — do not design against these\n",
        f"**{len(retired_rows)} of the routes below answer `410 Gone`.** They are listed because "
        "they still appear in the OpenAPI spec, so a design or a generated client will find them "
        "and assume they work. They do not.\n",
        "Peer rating, Rating Committee sign-off and calibration were built for a network larger "
        "than this one. **The founder signs what goes out instead** (ADR-0041, GRS-0188). The "
        "machinery behind them — repository sections, tables, the kappa/AC1 stats engine — is "
        "intact and still unit-tested, so reversing this is re-mounting routers, not rebuilding "
        "the feature. **Confirmed staying off, 2026-09-03.**\n",
        "What this means for a design: there is no blind/peer rating surface, no committee queue "
        "and no calibration session to build. `GET /queue` reports `rate` as a dormant kind, in "
        "words, for exactly this reason — see GRS-0253.\n",
        "Each is marked **RETIRED** in the tables below.\n",
        "| Method | Path |",
        "|---|---|",
        *[f"| `{method}` | `{path}` |" for method, path in retired_rows],
        "",
        "## Contents\n",
    ]
    for tag in sorted(rows):
        out.append(f"- [{tag}](#{tag.replace('-', '')}) — {len(rows[tag])}")
    out.append("")
    for tag in sorted(rows):
        out.append(f"\n## {tag}\n")
        out.append("| Method | Path | What it does |")
        out.append("|---|---|---|")
        for method, path, summary in sorted(rows[tag], key=lambda r: (r[1], r[0])):
            mark = "**RETIRED (410 Gone)** — " if (method, path) in retired else ""
            out.append(f"| `{method}` | `{path}` | {mark}{summary} |")

    (_ROOT / "docs" / "API-SURFACE.md").write_text("\n".join(out) + "\n")
    # Trailing newline like its sibling above: without one the end-of-file-fixer hook
    # rewrites this file on every commit that regenerates it, and the commit has to be
    # staged twice for no reason.
    (_ROOT / "docs" / "openapi.json").write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
    print(f"wrote docs/API-SURFACE.md and docs/openapi.json — {total} endpoints")


if __name__ == "__main__":
    main()
