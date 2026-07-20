# Brokerage App Reviews — Workbench content source

Provenance: OneDrive Content-Bank (`Business/Briefing/Content-Bank/Projects/Brokerage-App-Reviews/`), imported 2026-07-20. Three completed brokerage-app reviews (Revolut, WeBull, Hargreaves Lansdown), each comprising:

- `* - Brokerage App Review.docx` — the full review
- `* - Evaluation.docx` — the evaluation summary
- `* - Widget Checklist.docx` — the blank checklist template
- `*WidgetChecklist_COMPLETED_Claude.md` — the completed checklist (machine-readable; best ingestion source)

**Not in git (too large):** the screen recordings (~1.7 GB total, 5 × MP4) and raw screenshot archives remain in the OneDrive folder above. Reference them by filename if the Workbench ever needs stills/clips; do not commit them.

**Workbench wiring:** this folder is the content source for brokerage-app-review material in the Workbench (certification / drills / practice arena). When GRS-0024 (learning content + drills) is worked, ingest from here — prefer the `_COMPLETED_Claude.md` checklists for structured drill content and treat the .docx files as the human-authored originals. Per repo rules: AI-derived drill content generated from these must still flow through the ActiveGraph approval gates before reaching consultants.

**Repo size rule:** this repo's pre-commit hook caps files at 1 MB. Originals larger than that (the Revolut review .docx, the WeBull review .docx, screenshot archives, all videos) live in the OneDrive Content-Bank folder above — the machine-readable `_COMPLETED_Claude.md` checklists in git are the ingestion source and are complete on their own.
