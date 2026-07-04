"""ASGI entrypoint. Run with: `uv run uvicorn grassmarket.web.main:app`.

Constructing `app` at import time calls `get_settings()`, which fails loud if `GM_JWT_SECRET`
is absent — the process refuses to start rather than boot with a weak default (config.py).
"""

from __future__ import annotations

from grassmarket.web.app import create_app

app = create_app()
