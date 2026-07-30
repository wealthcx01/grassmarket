"""Brokerage end-to-end on staging: pipeline -> assessment -> deliverable -> earnings.

Drives the LIVE staging API over HTTP as the demo advisor. For each of Revolut / Hargreaves
Lansdown / WeBull it creates a prospect, moves it through the pipeline to Contracted, creates a
SANDBOX assessment (solo-finalisable), populates a faithful AssessmentDocument built from that
brokerage's completed widget review (V infra + 7 Powers + business metrics + the C-index customer
proposition), finalises it, opens an engagement, and generates deliverables. Prints scores and a
summary so the flow can be judged end to end.

The maturity and strength levels are grounded in each brokerage's completed widget checklist.
"""

from __future__ import annotations

import sys

import httpx
from bcap_contracts.assessments import (
    AssessmentDocument,
    MetricEntry,
    PowerEntry,
    SubcomponentRating,
)
from bcap_contracts.registry import load_registry

API = "https://grassmarket-api-staging.up.railway.app"
EMAIL, PASSWORD = "advisor@bruntsfieldcapital.com", "grassmarket-demo"

R = load_registry()
V_MODULES = {m.key: [s.key for s in m.subcomponents] for m in R.modules}
C_MODULES = {m.key: [s.key for s in m.subcomponents] for m in R.c_modules}
STAGES = ["workshop_scheduled", "workshop_delivered", "qualified", "scoped", "contracted"]
E3 = "E3"


def levels(module_map, base: dict, override: dict) -> list[dict]:
    """One SubcomponentRating per subcomponent: the module base level, with per-subcomponent
    overrides applied on top."""
    out = []
    for mod, subs in module_map.items():
        for sk in subs:
            lvl = override.get(sk, base.get(mod))
            if lvl is None:
                continue  # module left Not Assessed
            out.append(
                SubcomponentRating(
                    module_key=mod, subcomponent_key=sk, level=lvl, evidence_grade=E3
                ).model_dump(mode="json")
            )
    return out


def powers(spec: dict) -> list[dict]:
    return [
        PowerEntry(
            power_key=p,
            benefit=b,
            barrier=bar,
            benefit_grade=E3,
            barrier_grade=E3,
        ).model_dump(mode="json")
        for p, (b, bar) in spec.items()
    ]


def metrics(items: list[tuple]) -> list[dict]:
    return [
        MetricEntry(metric_key=k, raw=v, confidence=c).model_dump(mode="json") for k, v, c in items
    ]


# ---- Review-grounded specs (retail operating model = golden-master real coefficients) ------
REVOLUT = dict(
    subject="Revolut",
    metrics=[
        ("ACTIVE_CLIENTS", 3_000_000, "estimated"),
        ("AUA", 20_000_000_000, "estimated"),
        ("NET_REVENUE", 1_800_000_000, "estimated"),
        ("CLIENT_GROWTH_RATE", 25, "estimated"),
    ],
    powers={
        "BRANDING": ("Established", "Established"),
        "NETWORK_ECONOMIES": ("Emerging", "Emerging"),
        "SWITCHING_COSTS": ("Emerging", "Emerging"),
        "SCALE_ECONOMIES": ("Emerging", "Emerging"),
        "COUNTER_POSITIONING": ("Established", "Emerging"),
        "CORNERED_RESOURCE": ("None", "None"),
        "PROCESS_POWER": ("Emerging", "Emerging"),
    },
    v_base={
        "FRONTEND": "Advanced",
        "APP_SERVER": "Advanced",
        "MARKET_DATA": "Developing",
        "ORCHESTRATION": "Advanced",
        "CMS": "Developing",
        "BACKOFFICE": "Advanced",
        "OEMS": "Developing",
        "EMS_GATEWAY": "Developing",
        "LIQ_CONNECT": "Developing",
    },
    v_over={"FRONTEND_UX_NAVIGATION": "Frontier", "OEMS_ORDER_TYPES": "Basic"},
    c_base={
        "CUST_ONBOARDING": "Frontier",
        "CUST_UI_NAVIGATION": "Advanced",
        "CUST_TRADING_EXPERIENCE": "Developing",
        "CUST_FEES_PRICING": "Basic",
        "CUST_PRODUCT_RANGE": "Developing",
        "CUST_RESEARCH_EDUCATION": "Developing",
        "CUST_AI_PERSONALISATION": "Developing",
        "CUST_SUPPORT_COMMUNITY": "Basic",
        "CUST_SECURITY_REGULATION": "Advanced",
        "CUST_INNOVATION_DIFFERENTIATORS": "Advanced",
    },
    c_over={},
)
HL = dict(
    subject="Hargreaves Lansdown",
    metrics=[
        ("AUA", 155_300_000_000, "management_reported"),
        ("ACTIVE_CLIENTS", 2_000_000, "management_reported"),
        ("NET_REVENUE", 764_000_000, "estimated"),
    ],
    powers={
        "BRANDING": ("Established", "Established"),
        "SWITCHING_COSTS": ("Established", "Established"),
        "SCALE_ECONOMIES": ("Established", "Emerging"),
        "NETWORK_ECONOMIES": ("None", "None"),
        "COUNTER_POSITIONING": ("None", "None"),
        "CORNERED_RESOURCE": ("None", "None"),
        "PROCESS_POWER": ("Emerging", "Emerging"),
    },
    v_base={
        "FRONTEND": "Developing",
        "APP_SERVER": "Advanced",
        "MARKET_DATA": "Developing",
        "ORCHESTRATION": "Developing",
        "CMS": "Advanced",
        "BACKOFFICE": "Advanced",
        "OEMS": "Basic",
        "EMS_GATEWAY": "Developing",
        "LIQ_CONNECT": "Developing",
    },
    v_over={
        "BACKOFFICE_CUSTODY": "Advanced",
        "BACKOFFICE_REG_REPORTING": "Advanced",
        "OEMS_ORDER_TYPES": "Basic",
        "OEMS_ASSET_COVERAGE": "Basic",
        "FRONTEND_DEVICE_COVERAGE": "Developing",
    },
    c_base={
        "CUST_ONBOARDING": "Developing",
        "CUST_UI_NAVIGATION": "Developing",
        "CUST_TRADING_EXPERIENCE": "Basic",
        "CUST_FEES_PRICING": "Developing",
        "CUST_PRODUCT_RANGE": "Advanced",
        "CUST_RESEARCH_EDUCATION": "Advanced",
        "CUST_AI_PERSONALISATION": "Basic",
        "CUST_SUPPORT_COMMUNITY": "Developing",
        "CUST_SECURITY_REGULATION": "Advanced",
        "CUST_INNOVATION_DIFFERENTIATORS": "Basic",
    },
    c_over={},
)
WEBULL = dict(
    subject="WeBull",
    metrics=[
        ("ACTIVE_CLIENTS", 4_000_000, "estimated"),
        ("CLIENT_GROWTH_RATE", 15, "estimated"),
        ("NET_REVENUE", 400_000_000, "estimated"),
    ],
    powers={
        "PROCESS_POWER": ("Emerging", "Emerging"),
        "COUNTER_POSITIONING": ("Emerging", "Emerging"),
        "NETWORK_ECONOMIES": ("Emerging", "Emerging"),
        "BRANDING": ("Emerging", "Emerging"),
        "SCALE_ECONOMIES": ("Emerging", "Emerging"),
        "SWITCHING_COSTS": ("None", "None"),
        "CORNERED_RESOURCE": ("None", "None"),
    },
    v_base={
        "FRONTEND": "Developing",
        "APP_SERVER": "Advanced",
        "MARKET_DATA": "Advanced",
        "ORCHESTRATION": "Advanced",
        "CMS": "Developing",
        "BACKOFFICE": "Developing",
        "OEMS": "Frontier",
        "EMS_GATEWAY": "Advanced",
        "LIQ_CONNECT": "Developing",
    },
    v_over={
        "OEMS_ORDER_TYPES": "Frontier",
        "OEMS_ASSET_COVERAGE": "Advanced",
        "FRONTEND_UX_NAVIGATION": "Developing",
        "BACKOFFICE_PAYMENTS_FUNDING": "Basic",
    },
    c_base={
        "CUST_ONBOARDING": "Developing",
        "CUST_UI_NAVIGATION": "Developing",
        "CUST_TRADING_EXPERIENCE": "Frontier",
        "CUST_FEES_PRICING": "Advanced",
        "CUST_PRODUCT_RANGE": "Advanced",
        "CUST_RESEARCH_EDUCATION": "Advanced",
        "CUST_AI_PERSONALISATION": "Basic",
        "CUST_SUPPORT_COMMUNITY": "Advanced",
        "CUST_SECURITY_REGULATION": "Developing",
        "CUST_INNOVATION_DIFFERENTIATORS": "Advanced",
    },
    c_over={},
)
BROKERAGES = [REVOLUT, HL, WEBULL]


def main() -> None:
    s = httpx.Client(timeout=60.0)
    r = s.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=20)
    r.raise_for_status()
    s.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
    print(f"logged in as {EMAIL}\n")

    results = []
    for b in BROKERAGES:
        name = b["subject"]
        print(f"===== {name} =====")
        # 1. pipeline: prospect -> contracted
        pid = s.post(f"{API}/prospects", json={"company_name": name}, timeout=20).json()["id"]
        for st in STAGES:
            rr = s.patch(f"{API}/prospects/{pid}/stage", json={"stage": st}, timeout=20)
            if rr.status_code != 200:
                print(f"  stage {st} FAILED {rr.status_code}: {rr.text[:120]}")
        print(f"  prospect {pid} -> contracted")

        # 2. sandbox assessment + faithful document
        aid = s.post(
            f"{API}/assessments", json={"subject": name, "provenance": "sandbox"}, timeout=20
        ).json()["id"]
        doc = AssessmentDocument(
            subject=name,
            subcomponents=tuple(
                SubcomponentRating(**d) for d in levels(V_MODULES, b["v_base"], b["v_over"])
            ),
            metrics=tuple(MetricEntry(**d) for d in metrics(b["metrics"])),
            powers=tuple(PowerEntry(**d) for d in powers(b["powers"])),
            c_subcomponents=tuple(
                SubcomponentRating(**d) for d in levels(C_MODULES, b["c_base"], b["c_over"])
            ),
        ).model_dump(mode="json")
        pr = s.put(f"{API}/assessments/{aid}", json=doc, timeout=30)
        if pr.status_code != 200:
            print(f"  PUT document FAILED {pr.status_code}: {pr.text[:200]}")
            continue
        print(
            f"  assessment {aid}: {len(doc['subcomponents'])} infra + {len(doc['powers'])} powers "
            f"+ {len(doc['metrics'])} metrics + {len(doc['c_subcomponents'])} C-subs"
        )

        # 3. finalise (sandbox self-approves)
        fr = s.post(f"{API}/assessments/{aid}/finalise", timeout=30)
        if fr.status_code != 200:
            print(f"  FINALISE FAILED {fr.status_code}: {fr.text[:300]}")
            continue
        fin = fr.json()
        run = fin.get("scoring_run") or fin.get("latest_run") or {}
        v = run.get("v_index") or run.get("V") or fin.get("v_index")
        c = run.get("c_index") or fin.get("c_index")
        print(f"  FINALISED — V={v}  C={c}")

        # 4. engagement + deliverables
        eid = s.post(
            f"{API}/engagements",
            json={"prospect_id": pid, "title": f"{name} — delivery", "assessment_ids": [aid]},
            timeout=20,
        ).json()["id"]
        gens = []
        for dt in ("executive_summary", "platform_power_report", "infrastructure_heatmap"):
            gr = s.post(
                f"{API}/engagements/{eid}/deliverables",
                json={"deliverable_type": dt, "client_facing": False},
                timeout=45,
            )
            gens.append(f"{dt}={gr.status_code}")
        print(f"  engagement {eid}; deliverables: {', '.join(gens)}")
        results.append((name, v, c, aid, eid))
        print()

    print("===== SUMMARY =====")
    for name, v, c, _aid, _eid in results:
        print(f"  {name:22} V={v}  C={c}")


if __name__ == "__main__":
    sys.exit(main())
