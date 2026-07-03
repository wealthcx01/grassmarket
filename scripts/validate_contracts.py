"""Pre-commit `schema-validate`: assert the committed JSON Schemas match the Pydantic models.

Fail-loud parity check. If a model changed but `scripts/generate_schemas.py` was not re-run,
this blocks the commit and tells you exactly which schema is stale. No silent drift.
"""

from __future__ import annotations

import sys

from bcap_contracts.schemas import check_parity


def main() -> int:
    mismatches = check_parity()
    if mismatches:
        print("schema-validate: committed JSON Schemas are out of date:", file=sys.stderr)
        for name in mismatches:
            print(f"  - {name}", file=sys.stderr)
        print(
            "\nRun:  uv run python scripts/generate_schemas.py   then commit the updated schemas.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
