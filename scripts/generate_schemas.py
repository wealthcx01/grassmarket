"""Regenerate the committed JSON Schemas from the Pydantic contract models.

Run this after changing any model in `bcap_contracts`. The pre-commit `schema-validate` hook
(scripts/validate_contracts.py) fails if the committed schemas drift from the models, so the
JSON Schema is always a faithful mirror — schemas win on conflict (CLAUDE.md non-negotiable #4).
"""

from __future__ import annotations

from bcap_contracts.schemas import export_all


def main() -> None:
    written = export_all()
    for path in written:
        print(f"wrote {path}")
    print(f"\n{len(written)} schema(s) regenerated.")


if __name__ == "__main__":
    main()
