# `data/` — in-repo data for program execution

Everything the founder-feedback program (`docs/planning/founder-feedback-2026-07-23-program.md`)
needs to execute on a workbench VM that has **no access to OneDrive or Downloads**. The workbench
pulls this from git and runs.

## Layout

```
data/
├── reference/
│   └── 7powers-math-extraction.md      ← PRESENT. The Helmer mathematics extraction memo
│                                          (GRS-0180 authors the adaptation from this). Non-PII,
│                                          under the Helmer permission grant (ADR-0046).
├── gtm/
│   ├── lseg/                            ← the LSEG analyst dataset (GRS-0200 pull); see below
│   │   ├── analysts_unified.csv         ← 1,754 rows: ric, analyst_name, email, phone, job_role,
│   │   │                                   ctb_id, uid, create_date, est_rating, rec_rating_24m
│   │   ├── contributor_institution_map.csv  ← ctb_id → inferred institution (first-draft; curate)
│   │   └── pull_summary.json            ← the pull provenance + numbers
│   └── sources/                         ← source material for imports and content authoring
│       ├── exchange-supplier-list.xlsx  ← 1,001 audited supplier-service rows w/ contacts
│       ├── list-of-banks.xlsx           ← 150 institutions (Country, Company)
│       ├── barclays-influencer-map.xlsx ← the 3-tab LSEG influencer workbook
│       ├── barclays-influencer-brief.md ← the method write-up
│       ├── benzinga-product-catalog.xlsx← 37 products × 14 cols (Docs/Marketing URLs)
│       └── openbb-exchange-terminal-strategy.docx  ← the GTM strategy doc
```

## Provenance and consumers

| Path | Provenance | Consumed by |
|---|---|---|
| `reference/7powers-math-extraction.md` | Extracted 2026-07-23 from the 7 Powers supplement under Helmer's grant | GRS-0180 → GRS-0201 |
| `gtm/lseg/*` | LSEG/I-B-E-S via bcap-lseg, pulled 2026-07-23 (GRS-0200) | GRS-0193 (import), GRS-0194 (maps) |
| `gtm/sources/*` | Operator GTM estate | GRS-0193 (import), GRS-0191 (course content) |

## PII notice

`gtm/lseg/analysts_unified.csv` and `gtm/sources/exchange-supplier-list.xlsx` and
`barclays-influencer-map.xlsx` contain **named individuals' business contact details** (emails,
phone numbers) from LSEG/I-B-E-S and audited supplier records. By founder decision (2026-07-23),
this data is committed to this **private** repository so the workbench VM can execute the import
tickets without OneDrive access, reversing the prior OneDrive-only policy for these files. It
remains subject to the SAR/scrub paths once imported (GRS-0193 §7). Do not make this repository
public without first removing this directory from history.

## Not committed (deliberate)

- **`7Powers.pdf`** — the copyrighted source. Helmer's grant covers adapting the *mathematics*
  (captured in `reference/7powers-math-extraction.md`, which is what the workbench needs), not
  redistributing his file. The PDF stays out of git.
- Rendered PDF page images (working artifacts).
