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

from grassmarket.web.app import create_app

_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
_ROOT = pathlib.Path(__file__).resolve().parents[1]


def main() -> None:
    spec = create_app().openapi()
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
            out.append(f"| `{method}` | `{path}` | {summary} |")

    (_ROOT / "docs" / "API-SURFACE.md").write_text("\n".join(out) + "\n")
    (_ROOT / "docs" / "openapi.json").write_text(json.dumps(spec, indent=2, sort_keys=True))
    print(f"wrote docs/API-SURFACE.md and docs/openapi.json — {total} endpoints")


if __name__ == "__main__":
    main()
