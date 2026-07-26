# Marcus Bell (Robinhood/retail) — FULL RE-MEASURE. Confidence 82/100 (was 68 orig, 72 last, **+10**)

"Noticeably hardened since prior runs. Remaining issues are polish, not breakage."
CONFIRMED FIXED: change-password now on Profile + robust (short→"12 chars", mismatch, wrong-current→friendly 401); bad routes redirect (no raw 422); /workbench/academy/<bad>→"Course not found"; empty/whitespace/double-submit guarded; negative metric fail-loud ("can't be below 0 GBP").

Remaining (polish/low): duplicate prospects allowed (med); bad-id routes redirect silently + log console 404/422 (low-med, add "not found" toast); retail metric emphasis AUA vs PFOF/trade-volume (med, segment — retail-neobroker metric set NOT built since retail=golden-master default); no upper-bound/min=0 on metric input (low); Settings "coming soon" (low).
