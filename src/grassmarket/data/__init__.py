"""Data layer — the single place persistence happens (CLAUDE.md non-negotiable #5).

Feature code never writes a query. It goes through `Repository`, whose interface is shaped like
the future Holy Corner API resources so the backing store can swap from local Postgres to that
API without touching callers. Data scoping (non-negotiable #9) is enforced here and nowhere else.
"""
