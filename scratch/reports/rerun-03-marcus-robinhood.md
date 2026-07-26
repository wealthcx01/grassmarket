# Marcus Bell (Robinhood/retail) — RE-RUN. Confidence 72/100 (was 68, +4)

Confirmed fixed: bad routes redirect (/deliverables→/engagements, /academy→/workbench/academy); friendly branded 404; negative-metric gate ("can't be below 0 GBP (got -5000)"); empty/whitespace/duplicate-safe submit; no double-submit; /workbench/academy/<bad> → "Course not found".

Remaining:
1. **/engagements/<bad-id> → raw "Request failed (422)" (HIGH)** — GRS-0143 fixed prospects/[id]+assessments/[id] but MISSED engagements/[id]. Clean fix (treat 404/422 as not-found).
2. Malformed prospect/assessment IDs redirect OK but spray 422 to console/network (MED).
3. No UPPER-bound/plausibility on metrics — AUA 10^15 accepted (MED; min_raw:0 has no max).
4. Silent duplicate prospects (MED, recurring).
5. Raw `in_progress` enum leaks in Arena history; workbench tabs not URL-routable (LOW).
Segment: GBP for a US retail buyer; AUA headline vs MAU/funded-accounts/PFOF (retail metric set not built — only wealth was).
