"""Independent, clean-room verification that the brokerage scores are engine-computed, not invented.

Fetches each finalised brokerage assessment's LOCKED document from staging, then recomputes V LOCALLY
with the same ATLAS engine and compares to the score the deployed system stored in its deliverable.
"""
import random
import httpx
from bcap_contracts.assessments import AssessmentDocument
from grassmarket.atlas.active import profile_scoring_context, profile_key_of, active_uncertainty_model
from grassmarket.assessments.service import compute_score

API = "https://grassmarket-api-staging.up.railway.app"
DEPLOYED = {"Revolut": 58.8, "Hargreaves Lansdown": 56.5, "WeBull": 53.5}  # from downloaded .docx headlines

s = httpx.Client(timeout=60)
s.headers["Authorization"] = "Bearer " + s.post(f"{API}/auth/login",
    json={"email": "advisor@bruntsfieldcapital.com", "password": "grassmarket-demo"}).json()["access_token"]

rows = []
for a in s.get(f"{API}/assessments").json():
    if a.get("state") == "finalised" and a.get("provenance") == "sandbox" and a["subject"] in DEPLOYED:
        detail = s.get(f"{API}/assessments/{a['id']}").json()
        doc = AssessmentDocument.model_validate(detail["document"])
        pk = profile_key_of(doc)
        reg, coeff = profile_scoring_context(pk)
        art = compute_score(doc, coeff, reg, active_uncertainty_model(pk), random.Random(20260706))
        local_v = art.result.v_display_0_100
        rows.append((a["subject"], DEPLOYED[a["subject"]], local_v, coeff.version,
                     art.result.engine_version, coeff.methodology_version, art.result.composite.c_index))

print(f"{'Brokerage':22} {'deployed V':>10} {'local recompute':>16} {'match':>7}  coeff_version")
for subj, dep, loc, cv, ev, mv, c in rows:
    print(f"{subj:22} {dep:>10} {loc:>16} {'YES' if abs(dep-loc)<0.05 else 'NO!':>7}  {cv}")
print()
print(f"engine_version={rows[0][4] if rows else '?'}  methodology_version={rows[0][5] if rows else '?'}")
print("C-index (reported alongside V):", {r[0]: r[6] for r in rows})
